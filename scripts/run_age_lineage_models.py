"""Run all frozen hypothetical cell-cycle models; never fit empirical data."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import platform
import time

import numpy as np
import scipy

from age_lineage_models import build_model

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def homogeneous_formula(rate, mu, t):
    if rate == mu:
        return math.exp(-rate * t) * (1 + rate * t)
    return (rate * math.exp(-mu * t) - mu * math.exp(-rate * t)) / (rate - mu)


def evaluate(case, plan, strict=False, partial=None):
    times, horizons = plan["times"]["evaluation_times"], plan["times"]["selection_horizons"]
    family, selected, pairs, early, extra, controls = [], [], [], [], [], []
    output = {"case_id": case["case_id"], "configuration": case,
              "family_survival": family, "selected_path_survival": selected,
              "contrasts": [], "pairs": pairs, "deterministic_extra": extra,
              "early_time": early, "controls": controls}
    if partial is not None:
        partial.update(output)
        output = partial
    model = build_model(case, strict=strict)
    for horizon in horizons:
        h = model.family_survival(horizon)
        family.append({"horizon": horizon, "probability": h})
        for t in sorted(set([0.0, *times, horizon])):
            q = model.selected_path_survival(t, horizon)
            row = {"evaluation_time": t, "selection_horizon": horizon, "value": q,
                   "unconditional_tag_survival": math.exp(-case["mu"] * t),
                   "joint_probability": q * h if q is not None else None}
            if case["kind"] == "erlang":
                loss = model.selected_path_loss(t, horizon)
                row.update(positive_death_defect=loss, complement_error=q + loss - 1)
            selected.append(row)
    lookup = {(r["selection_horizon"], r["evaluation_time"]): r["value"] for r in selected}
    contrasts = [{"earlier_horizon": a, "later_horizon": b, "evaluation_time": t,
                  "value": lookup[b, t] - lookup[a, t]}
                 for a, b in plan["times"]["contrast_pairs"] for t in times]
    output["contrasts"] = contrasts
    for lag in plan["times"]["pair_lags"]:
        pairs.append({"lag": lag, **model.pair_summary(lag, plan["times"]["pair_birth_cutoff"])})
    if case["kind"] == "deterministic":
        t, age, mu = plan["times"]["deterministic_extra_evaluation_time"], case["division_age"], case["mu"]
        for horizon in plan["times"]["deterministic_extra_horizons"]:
            x, y = math.exp(-mu * (t - age)), math.exp(-mu * (horizon - age))
            extra.append({"evaluation_time": t, "selection_horizon": horizon,
                          "family_survival": model.family_survival(horizon),
                          "value": model.selected_path_survival(t, horizon),
                          "first_generation_formula": (1 + x - y) / (2 - y)})
    if case["kind"] == "erlang":
        for horizon in horizons:
            coefficient = model.early_time_coefficient(horizon)
            for epsilon in [0.01, 0.001, 0.0001]:
                t = epsilon / float(np.max(model.alpha))
                loss = model.selected_path_loss(t, horizon)
                leading = coefficient["coefficient"] * t ** coefficient["nominal_order"]
                ratio = loss / leading if coefficient["positive_leading_term"] else None
                early.append({"selection_horizon": horizon, "epsilon": epsilon,
                              "evaluation_time": t, **coefficient,
                              "positive_death_defect": loss, "leading_term": leading,
                              "ratio": ratio, "conservative_lower": math.exp(-3 * epsilon),
                              "conservative_upper": math.exp(6 * epsilon)})
    for row in selected:
        t, T, q = row["evaluation_time"], row["selection_horizon"], row["value"]
        if t == 0:
            controls.append({"name": "time_zero", "T": T, "error": q - 1})
        if t == T:
            controls.append({"name": "endpoint_product", "T": T,
                             "error": row["joint_probability"] - math.exp(-case["mu"] * T)})
        if case["kind"] == "no_division" or case["mu"] == 0:
            controls.append({"name": "constant_selected_survival", "T": T, "t": t, "error": q - 1})
        if case["kind"] == "erlang" and len(case["means"]) == 1 and case["k"] == 1:
            expected = homogeneous_formula(1 / case["means"][0], case["mu"], t)
            controls.append({"name": "homogeneous_closed_formula", "T": T, "t": t, "error": q - expected})
    return output


def audit(row, tolerance=1e-8):
    for path, value in numeric_leaves(row):
        if not math.isfinite(value):
            raise ArithmeticError(f"Nonfinite numeric field at {path}: {value!r}")
    probabilities = [r["probability"] for r in row["family_survival"]]
    assert all(-tolerance <= p <= 1 + tolerance for p in probabilities)
    assert all(a >= b - tolerance for a, b in zip(probabilities, probabilities[1:]))
    grouped = {}
    for value in row["selected_path_survival"]:
        assert -tolerance <= value["value"] <= 1 + tolerance
        grouped.setdefault(value["selection_horizon"], []).append(value)
        if "complement_error" in value:
            assert abs(value["complement_error"]) <= tolerance
    for group in grouped.values():
        assert all(a["value"] >= b["value"] - tolerance for a, b in zip(group, group[1:]))
    assert all(abs(r["error"]) <= tolerance for r in row["controls"])
    for extra in row["deterministic_extra"]:
        assert abs(extra["value"] - extra["first_generation_formula"]) <= tolerance
    for pair in row["pairs"]:
        assert -tolerance <= pair["eligibility_probability"] <= 1 + tolerance
        if pair["defined"]:
            assert -tolerance <= pair["covariance"] <= 0.25 + tolerance
            if "closed_covariance_identity" in pair:
                assert abs(pair["covariance"] - pair["closed_covariance_identity"]) <= tolerance
    for early in row["early_time"]:
        if early["positive_leading_term"]:
            assert early["conservative_lower"] - 1e-7 <= early["ratio"] <= early["conservative_upper"] + 1e-7
            if early["epsilon"] == 0.0001:
                assert abs(early["ratio"] - 1) <= 0.01
        else:
            assert early["positive_death_defect"] == 0 and early["ratio"] is None


def numeric_leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "configuration":
                continue
            yield from numeric_leaves(value, prefix + "/" + key)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from numeric_leaves(value, prefix + "/" + str(i))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        yield prefix, float(obj)


def diagnostic_snapshot(obj, path="", nonfinite=None):
    """Preserve invalid numeric diagnostics without emitting JSON NaN/null."""
    if nonfinite is None:
        nonfinite = []
    if isinstance(obj, dict):
        return {str(k): diagnostic_snapshot(v, path + "/" + str(k), nonfinite) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [diagnostic_snapshot(v, path + "/" + str(i), nonfinite) for i, v in enumerate(obj)]
    if isinstance(obj, (int, float)) and not isinstance(obj, bool) and not math.isfinite(obj):
        nonfinite.append({"path": path, "representation": repr(obj)})
        return "NONFINITE:" + repr(obj)
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE / "results.json")
    parser.add_argument("--strict-out", type=Path, default=BASE / "strict-results.json")
    args = parser.parse_args()
    if args.out.exists() or args.strict_out.exists():
        raise FileExistsError("Preserve existing results; choose new output paths")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.strict_out.parent.mkdir(parents=True, exist_ok=True)
    plan = json.loads((BASE / "protocol.json").read_text())
    freeze = json.loads((BASE / "plan-freeze.json").read_text())
    assert sha(BASE / "protocol.json") == freeze["protocol_sha256"]
    started = time.monotonic()
    rows, strict_rows, convergence = [], [], []
    provenance = {"created_utc": datetime.now(timezone.utc).isoformat(),
                  "protocol_sha256": freeze["protocol_sha256"], "driver_sha256": sha(__file__),
                  "core_sha256": sha(ROOT / "scripts/age_lineage_models.py"),
                  "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}
    current = {}
    try:
        for case in plan["cases"]:
            current = {"case_id": case["case_id"], "base": {}, "strict": {}}
            base = evaluate(case, plan, partial=current["base"])
            audit(base)
            strict = evaluate(case, plan, strict=True, partial=current["strict"])
            audit(strict)
            a, b = dict(numeric_leaves(base)), dict(numeric_leaves(strict))
            assert a.keys() == b.keys()
            differences = {key: abs(a[key] - b[key]) for key in a}
            # Only coefficients carry inverse-time powers; use a relative floor
            # for those quantities. All probability/contrast/ratio gates are absolute.
            violations = [key for key, value in differences.items()
                          if value > 1e-8 * (max(1, abs(b[key])) if key.endswith("/coefficient") else 1)]
            assert not violations, violations
            maximum = max(differences, key=differences.get)
            convergence.append({"case_id": case["case_id"], "numeric_fields_checked": len(a),
                                "maximum_absolute_difference": differences[maximum],
                                "maximum_difference_field": maximum, "all_gates_passed": True})
            rows.append(base)
            strict_rows.append(strict)
            print(json.dumps({"case_id": case["case_id"], "completed": len(rows),
                              "total": len(plan["cases"])}), flush=True)
        result = {**provenance, "runtime_seconds": time.monotonic() - started, "cases": rows,
                  "convergence": convergence, "scope": plan["scope"],
                  "status": "PASS", "planned_cases": len(plan["cases"]), "completed_cases": len(rows),
                  "primary_contrasts": sum(len(r["contrasts"]) for r in rows),
                  "early_time_rows": sum(len(r["early_time"]) for r in rows),
                  "limits": ["Deterministic probabilities of hypothetical models; no empirical or clinical fit.",
                             "Numerical checks are not a formal interval-arithmetic certificate.",
                             "Early-time powers are local asymptotics, not a globally equivalent multistep lifetime law.",
                             "Sister covariance does not universally identify inheritance."]}
        strict_result = {**provenance, "solver": "DOP853 rtol1e-12 atol1e-14", "cases": strict_rows}
        # Serialize both before writing either, and retain the complete state if
        # serialization or output fails. No first result is silently replaced.
        encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
        strict_encoded = json.dumps(strict_result, indent=2, allow_nan=False) + "\n"
        args.out.write_text(encoded)
        args.strict_out.write_text(strict_encoded)
    except Exception as error:
        failure = args.out.with_name(args.out.stem + "-failed-run.json")
        if failure.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            failure = failure.with_name(failure.stem + "-" + stamp + ".json")
        invalid = []
        snapshot = diagnostic_snapshot({**provenance, "incomplete": True,
            "failed_case_id": current.get("case_id"), "exception_type": type(error).__name__,
            "exception": str(error), "completed_cases": rows, "completed_strict_cases": strict_rows,
            "completed_convergence": convergence, "current_case": current}, nonfinite=invalid)
        snapshot["nonfinite_diagnostics"] = invalid
        failure.write_text(json.dumps(snapshot, indent=2, allow_nan=False) + "\n")
        raise
    print(json.dumps({"status": result["status"], "completed_cases": len(rows),
                      "primary_contrasts": result["primary_contrasts"],
                      "early_time_rows": result["early_time_rows"],
                      "runtime_seconds": result["runtime_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
