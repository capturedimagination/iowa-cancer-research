"""Small analytic and failure-path checks outside the frozen scientific grid."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math

from age_lineage_models import build_model
from run_age_lineage_models import audit, diagnostic_snapshot

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"


def main():
    checks = []
    case = {"kind": "erlang", "k": 1, "means": [1 / 1.3], "mu": 0.7,
            "rho": 0.0, "initialization": "newborn"}
    model = build_model(case, strict=True)
    for t in [0.0, 0.2, 0.7, 0.9]:
        expected = (1.3 * math.exp(-0.7 * t) - 0.7 * math.exp(-1.3 * t)) / 0.6
        q = model.selected_path_survival(t, 0.9)
        assert abs(q - expected) < 1e-9
        assert abs(q + model.selected_path_loss(t, 0.9) - 1) < 1e-9
    checks += ["one_stage_closed_form", "positive_loss_complement"]
    no_death = build_model({**case, "k": 2, "means": [1.0, 2.0], "mu": 0.0, "rho": 1.0}, strict=True)
    pair = no_death.pair_summary(0.3, cutoff=0.6)
    probabilities = [1 - math.exp(-a * 0.6) * (1 + a * 0.6) for a in [2, 1]]
    assert abs(pair["eligibility_probability"] - sum(probabilities) / 2) < 1e-12
    assert abs(pair["qualifying_mother_type_weights"][0] - probabilities[0] / sum(probabilities)) < 1e-12
    assert pair["covariance"] == 0
    checks += ["competing_clock_qualification", "selected_maternal_weights", "inherited_zero_death_blind_spot"]
    deterministic = build_model({"kind": "deterministic", "mu": 0.7, "division_age": 1.0})
    for T in [1.4, 1.7]:
        x, y = math.exp(-0.7 * 0.2), math.exp(-0.7 * (T - 1))
        assert abs(deterministic.selected_path_survival(1.2, T) - (1 + x - y) / (2 - y)) < 1e-12
    checks.append("deterministic_first_generation")
    without_division = build_model({"kind": "no_division", "mu": 0.7})
    assert without_division.selected_path_survival(0.3, 0.9) == 1
    assert not without_division.pair_summary(0.3)["defined"]
    checks.append("no_division_undefined_pairs")
    try:
        model.selected_path_survival(1.0, 0.9)
        raise AssertionError("Invalid horizon accepted")
    except ValueError:
        checks.append("invalid_horizon_rejected")
    try:
        audit({"probe": float("nan")})
        raise AssertionError("NaN accepted")
    except ArithmeticError:
        checks.append("nonfinite_outcome_rejected")
    diagnostics = []
    snapshot = diagnostic_snapshot({"probe": [float("inf"), float("nan")]}, nonfinite=diagnostics)
    assert [r["path"] for r in diagnostics] == ["/probe/0", "/probe/1"]
    assert snapshot["probe"] == ["NONFINITE:inf", "NONFINITE:nan"]
    json.dumps(snapshot, allow_nan=False)
    checks.append("invalid_numbers_preserved_explicitly")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "passed": True,
              "checks": checks, "check_count": len(checks), "script_sha256": sha(Path(__file__)),
              "core_sha256": sha(ROOT / "scripts/age_lineage_models.py"),
              "driver_sha256": sha(ROOT / "scripts/run_age_lineage_models.py"),
              "scope": "Separate analytic and failure-path fixtures, not a main-grid result or biological validation."}
    out = BASE / "primary-fixtures.json"
    if out.exists():
        raise FileExistsError("Preserve first fixture result; run in a disposable checkout")
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
