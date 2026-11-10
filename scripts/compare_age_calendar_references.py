#!/usr/bin/env python3
"""Complete frozen-grid primary/strict versus independent-reference audit.

Pin before evaluation. No production or reference solver imports. Expected
keys come from the frozen protocol; reference probabilities drive all moment
comparisons. Passing values remain in immutable inputs; this report saves
per-case/category coverage and maxima, and every failed comparison.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from math import cos, isfinite, pi
from pathlib import Path
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration"
PIN = BASE / "comparison-code-pin.json"
PROTOCOL_SHA = "53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919"
REFERENCE_SHA = "4660e68638657dd109254a9afd5996b3d579a65cf158603929a6ca785603f1bd"
PRIMARY_CODE = "6f5d8279ca762bbd0ac6b4614806edd898bdbcf5c46b7ea7ec1a475a4b88a261"
REFERENCE_CODE = "b8b404480cb4586fddf2d45d22a572ab001e7f0ad76c4fa309a29df8b1a7f626"
METHODS = ("oracle_bin_mean", "shared_fitted_mean", "shared_fitted_mean_corrected",
           "unbiased_target_sample_covariance")
EXPECTED_COUNTS = {"family": 60, "Q": 340, "U": 140, "contrasts": 240,
                   "bins": 300, "pairs": 900, "calibration": 5400}
KEYS = {"family": ("T",), "Q": ("t", "T"), "U": ("t",),
        "contrasts": ("t", "T_early", "T_late"), "bins": ("bin_id",),
        "pairs": ("bin_id", "lag"), "calibration": ("bin_id", "lag", "m", "n")}
IGNORED = {
    "primary_and_strict": ["Q[].complement_error", "pairs[].joint_reconstruction_error",
                           "controls[] (production self-checks, not independent targets)",
                           "top-level execution metadata and primary/strict convergence diagnostics"],
    "reference": ["bins[].adaptive_quadrature_error_estimate", "pairs[].adaptive_quadrature_error_estimate",
                  "partition_eligibility_errors (reference self-check)", "top-level execution metadata"],
    "reason": "These are explicitly named numerical diagnostics, not omitted scientific estimands. Every numeric leaf is still checked finite."
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return "<external>/" + Path(path).name


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key: " + key)
        result[key] = value
    return result


def finite(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            finite(child, path + "." + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            finite(child, f"{path}[{index}]")
    elif isinstance(value, float) and not isfinite(value):
        raise ValueError("Nonfinite number at " + path + ": " + repr(value))


def read(path):
    value = json.loads(path.read_text(), object_pairs_hook=unique_object)
    finite(value)
    return value


def write_once(path, value):
    finite(value)
    payload = json.dumps(value, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(payload)


def index_rows(rows, fields, expected=None):
    result = {}
    for row in rows:
        key = tuple(row[field] for field in fields)
        if key in result:
            raise ValueError("Duplicate result key: " + repr(key))
        result[key] = row
    if expected is not None and set(result) != set(expected):
        raise ValueError("Key mismatch: missing=" + repr(sorted(set(expected) - set(result)))
                         + "; extra=" + repr(sorted(set(result) - set(expected))))
    return result


def exact_fields(row, fields):
    if set(row) != set(fields):
        raise ValueError("Field schema mismatch: " + repr(sorted(set(row) ^ set(fields))))


def hashes():
    files = [BASE / name for name in ["protocol.json", "results.json", "strict-results.json",
                                      "independent-reference.json"]]
    files += [ROOT / "scripts" / name for name in ["age_calendar_calibration.py",
               "verify_age_calendar_calibration.py", "age_lineage_models.py"]]
    return {portable(path): sha(path) for path in files}


class Audit:
    def __init__(self, report):
        self.report = report
        self.active = None
        report.update({"cases": [], "summary": {}, "failures": [],
                       "numeric_fields_per_source": 0, "matched_undefined_fields": 0})

    def compare(self, field, target, primary, strict, category, gate=1e-8):
        location = {"case_id": self.active["case_id"], "field": field}
        if target is None:
            passed = primary is None and strict is None
            self.report["matched_undefined_fields"] += int(passed)
            if not passed:
                self.report["failures"].append({**location, "reference": None,
                    "primary": primary, "strict": strict, "reason": "undefinedness mismatch"})
            return
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x)
               for x in [target, primary, strict]):
            raise ValueError("Invalid numeric comparison at " + repr(location))
        self.report["numeric_fields_per_source"] += 1
        for label, observed in [("primary", primary), ("strict", strict)]:
            error = abs(observed - target)
            name = category + "/" + label
            for store in [self.report["summary"], self.active["summary"]]:
                item = store.setdefault(name, {"count": 0, "maximum_absolute_difference": -1.0,
                                               "gate": gate, "failed": 0})
                item["count"] += 1
                item["failed"] += int(error > gate)
                if error > item["maximum_absolute_difference"]:
                    item.update({"maximum_absolute_difference": error, "maximum_location": location,
                                 "reference_at_maximum": target, "observed_at_maximum": observed})
            if error > gate:
                self.report["failures"].append({**location, "source": label,
                    "reference": target, "observed": observed, "absolute_difference": error, "gate": gate})


def fixture_checks():
    passed = []
    def rejected(label, fn):
        try:
            fn()
        except (ValueError, KeyError):
            passed.append(label)
            return
        raise AssertionError("Fixture failed to reject " + label)
    rejected("duplicate_result_keys", lambda: index_rows([{"x": 1}, {"x": 1}], ["x"]))
    rejected("missing_expected_key", lambda: index_rows([{"x": 1}], ["x"], {(1,), (2,)}))
    rejected("extra_result_key", lambda: index_rows([{"x": 1}, {"x": 2}], ["x"], {(1,)}))
    rejected("NaN_nested", lambda: finite({"x": [float("nan")]}))
    rejected("infinity_nested", lambda: finite({"x": {"y": float("inf")}}))
    rejected("duplicate_JSON_key", lambda: json.loads('{"x":1,"x":2}', object_pairs_hook=unique_object))
    rejected("unknown_schema_field", lambda: exact_fields({"x": 1, "unplanned": 2}, ["x"]))
    report = {}
    audit = Audit(report)
    audit.active = {"case_id": "fixture", "summary": {}}
    audit.compare("under", 0.0, 0.5e-10, -0.5e-10, "calibration", 1e-10)
    audit.compare("over", 0.0, 2e-10, 0.0, "calibration", 1e-10)
    audit.compare("undefined", None, None, 0.0, "bound")
    assert len(report["failures"]) == 2
    assert report["numeric_fields_per_source"] == 2
    rejected("None_not_a_number", lambda: audit.compare("bad", 0.0, None, 0.0, "q"))
    passed.extend(["frozen_gate_and_undefinedness_failures_retained", "numeric_coverage_count"])
    return {"status": "PASS", "checks": passed, "count": len(passed), "scientific_comparison_run": False}


def execute(report):
    plan = read(BASE / "protocol.json")
    primary, strict, ref = [read(BASE / name) for name in ["results.json", "strict-results.json", "independent-reference.json"]]
    assert primary["status"] == ref["status"] == "PASS"
    for obj in [primary, strict, ref]:
        assert obj["protocol_sha256"] == PROTOCOL_SHA
    assert primary["code_sha256"] == strict["code_sha256"] == PRIMARY_CODE
    assert ref["code_sha256"] == REFERENCE_CODE
    assert ref["primary_outputs_read"] is False
    configs = {c["case_id"]: c for c in plan["cases"]}
    assert len(configs) == len(plan["cases"]) == 20
    objects = [index_rows(obj["cases"], ["case_id"], {(cid,) for cid in configs}) for obj in [primary, strict, ref]]
    report["record_counts"] = {}
    for name, obj in zip(["primary", "strict", "reference"], [primary, strict, ref]):
        counts = {kind: sum(len(c[kind]) for c in obj["cases"]) for kind in EXPECTED_COUNTS}
        assert counts == EXPECTED_COUNTS, (name, counts)
        report["record_counts"][name] = counts
    audit = Audit(report)
    widths, lags = plan["times"]["birth_bin_widths"], plan["times"]["pair_lags"]
    specs = {f"w{w:g}-b{i}": {"width": w, "left": i*w, "right": (i+1)*w}
             for w in widths for i in range(round(plan["times"]["pair_birth_cutoff"] / w))}
    for cid, config in configs.items():
        a, b, r = [obj[cid,] for obj in objects]
        active = {"case_id": cid, "summary": {}, "exact_key_and_schema_checks": "IN_PROGRESS"}
        audit.active = active
        report["current_case"] = active
        assert a["configuration"] == b["configuration"] == r["configuration"] == config
        assert set(a) == set(b) == {"case_id", "configuration", *KEYS, "partitions", "controls",
                                  "eligibility_probability", "eligible_mother_type_weights"}
        assert set(r) == {"case_id", "configuration", *KEYS, "eligibility_gamma_reference", "partition_eligibility_errors"}
        expected = {
            "family": {(T,) for T in plan["times"]["selection_horizons"]},
            "Q": {(t, T) for T in plan["times"]["selection_horizons"]
                  for t in set(plan["times"]["evaluation_times"] + [0.0, T])},
            "U": {(t,) for t in plan["times"]["unconditional_path_queries"]},
            "contrasts": {(t, lo, hi) for lo, hi in plan["times"]["contrast_pairs"]
                          for t in plan["times"]["evaluation_times"]},
            "bins": {(bid,) for bid in specs}, "pairs": {(bid, lag) for bid in specs for lag in lags},
            "calibration": {(bid, lag, m, n) for bid in specs for lag in lags
                            for m in plan["calibration"]["m"] for n in plan["calibration"]["n"]}}
        ix = [{kind: index_rows(obj[kind], KEYS[kind], expected[kind]) for kind in KEYS} for obj in [a, b, r]]
        for kind in KEYS:
            for key in sorted(expected[kind]):
                pa, pb, rr = [i[kind][key] for i in ix]
                prefix = kind + "/" + repr(key)
                if kind == "family":
                    exact_fields(pa, ["T", "operational_T", "probability"])
                    exact_fields(pb, pa)
                    exact_fields(rr, ["T", "probability"])
                    T = key[0]
                    mapped = T + config["amplitude"]*config["period"]/(2*pi)*(1-cos(2*pi*T/config["period"]))
                    audit.compare(prefix+"/operational_T", mapped, pa["operational_T"], pb["operational_T"], "family/operational_T")
                    audit.compare(prefix+"/probability", rr["probability"], pa["probability"], pb["probability"], "family/probability")
                elif kind == "Q":
                    exact_fields(pa, ["t", "T", "value", "positive_loss", "joint_probability", "complement_error"])
                    exact_fields(pb, pa)
                    exact_fields(rr, ["t", "T", "value", "joint_probability"])
                    for field, target in [("value", rr["value"]), ("joint_probability", rr["joint_probability"]),
                                          ("positive_loss", 1-rr["value"])]:
                        audit.compare(prefix+"/"+field, target, pa[field], pb[field], "Q/"+field)
                elif kind == "U":
                    for row in [pa, pb, rr]:
                        exact_fields(row, ["t", "value"])
                    audit.compare(prefix, rr["value"], pa["value"], pb["value"], "U")
                elif kind == "contrasts":
                    exact_fields(pa, ["t", "T_early", "T_late", "value", "positive_removed_loss"])
                    exact_fields(pb, pa)
                    exact_fields(rr, ["t", "T_early", "T_late", "value", "removed_loss_mean"])
                    audit.compare(prefix+"/value", rr["value"], pa["value"], pb["value"], "contrasts/value")
                    audit.compare(prefix+"/removed_loss", rr["removed_loss_mean"], pa["positive_removed_loss"], pb["positive_removed_loss"], "contrasts/removed_loss")
                elif kind == "bins":
                    fields = ["bin_id", "width", "left", "right", "probability", "mother_type_weights"]
                    exact_fields(pa, fields); exact_fields(pb, fields)
                    exact_fields(rr, fields+["adaptive_quadrature_error_estimate"])
                    for row in [pa, pb, rr]:
                        assert all(row[f] == value for f, value in specs[key[0]].items())
                        assert len(row["mother_type_weights"]) == len(config["means"])
                    audit.compare(prefix+"/probability", rr["probability"], pa["probability"], pb["probability"], "bins/probability")
                    for z, target in enumerate(rr["mother_type_weights"]):
                        audit.compare(prefix+f"/mother_type/{z}", target, pa["mother_type_weights"][z], pb["mother_type_weights"][z], "bins/mother_type_weights")
                elif kind == "pairs":
                    shared = ["bin_id", "lag", "p", "j", "c", "mean_conditional_covariance", "birth_probability_variance", "no_transmission_bound"]
                    exact_fields(pa, shared+["direct_joint_integral", "joint_reconstruction_error"])
                    exact_fields(pb, pa)
                    exact_fields(rr, shared+["adaptive_quadrature_error_estimate"])
                    for field in shared[2:]:
                        audit.compare(prefix+"/"+field, rr[field], pa[field], pb[field], "pairs/"+field)
                    audit.compare(prefix+"/direct_joint_integral", rr["j"], pa["direct_joint_integral"], pb["direct_joint_integral"], "pairs/direct_joint_integral")
                else:
                    for row in [pa, pb, rr]:
                        exact_fields(row, ["bin_id", "lag", "m", "n", "methods"])
                        assert set(row["methods"]) == set(METHODS)
                    for method in METHODS:
                        ma, mb, mr = [row["methods"][method] for row in [pa, pb, rr]]
                        for row in [ma, mb, mr]:
                            exact_fields(row, ["mean", "variance", "range"])
                            assert len(row["range"]) == 2
                        for field in ["mean", "variance"]:
                            audit.compare(prefix+"/"+method+"/"+field, mr[field], ma[field], mb[field], "calibration/"+method+"/"+field, 1e-10)
                        for bound in [0, 1]:
                            audit.compare(prefix+f"/{method}/range/{bound}", mr["range"][bound], ma["range"][bound], mb["range"][bound], "calibration/"+method+"/range", 0.0)
        audit.compare("eligibility_probability", r["eligibility_gamma_reference"], a["eligibility_probability"], b["eligibility_probability"], "eligibility")
        pooled_bin = ix[2]["bins"]["w2-b0",]
        for obj in [a, b]:
            assert len(obj["eligible_mother_type_weights"]) == len(config["means"])
        for z, target in enumerate(pooled_bin["mother_type_weights"]):
            audit.compare(f"eligible_mother_type_weights/{z}", target, a["eligible_mother_type_weights"][z], b["eligible_mother_type_weights"][z], "eligible_mother_type_weights")
        parts = [index_rows(obj["partitions"], ["lag", "width"], {(s,w) for s in lags for w in widths}) for obj in [a,b]]
        for lag in lags:
            pooled = ix[2]["pairs"]["w2-b0",lag]
            for width in widths:
                selected = [row for row in r["bins"] if row["width"] == width]
                mass = sum(row["probability"] for row in selected)
                reference_parts = {"probability_sum": mass}
                for field, pairfield in [("weighted_within_covariance", "c"),
                                         ("weighted_conditional_covariance", "mean_conditional_covariance"),
                                         ("remaining_context_variance", "birth_probability_variance")]:
                    reference_parts[field] = sum(row["probability"] * ix[2]["pairs"][row["bin_id"],lag][pairfield] for row in selected)/mass
                reference_parts["between_bin_mean_variance"] = sum(row["probability"]*(ix[2]["pairs"][row["bin_id"],lag]["p"]-pooled["p"])**2 for row in selected)/mass
                pa, pb = [part[lag,width] for part in parts]
                exact_fields(pa, ["lag", "width", *reference_parts]); exact_fields(pb, pa)
                for field, target in reference_parts.items():
                    audit.compare(f"partitions/{lag}/{width}/{field}", target, pa[field], pb[field], "partitions/"+field)
        active["exact_key_and_schema_checks"] = "PASS"
        report["cases"].append(active)
        report["current_case"] = None
    report["cases_checked"] = len(report["cases"])
    report["numeric_comparisons_both_sources"] = 2*report["numeric_fields_per_source"]
    report["status"] = "PASS" if not report["failures"] else "FAILED_NUMERICAL_GATES"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--pin", action="store_true")
    choice.add_argument("--fixtures", action="store_true")
    choice.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    failed = args.out.with_name(args.out.stem+".failure.json")
    if args.out.exists() or failed.exists():
        raise FileExistsError("Refusing first-output or failure overwrite")
    report = {"created_utc": datetime.now(timezone.utc).isoformat(), "script": portable(__file__),
              "code_sha256": sha(__file__), "status": "STARTED", "ignored_fields": IGNORED,
              "tolerances": {"probabilities_and_contrasts": 1e-8, "calibration_mean_variance": 1e-10,
                             "declared_ranges": "exact equality", "keys_configurations_and_schemas": "exact equality"},
              "review_status": "post-results, comparator pinned before evaluating numerical differences",
              "interpretation": "Numerical agreement is not empirical validation, theorem priority, or statistical coverage."}
    start = time.monotonic()
    try:
        report["input_hashes"] = hashes()
        assert report["input_hashes"][portable(BASE/"protocol.json")] == PROTOCOL_SHA
        assert report["input_hashes"][portable(BASE/"independent-reference.json")] == REFERENCE_SHA
        assert report["input_hashes"]["scripts/age_calendar_calibration.py"] == PRIMARY_CODE
        assert report["input_hashes"]["scripts/verify_age_calendar_calibration.py"] == REFERENCE_CODE
        if args.pin:
            report["status"] = "PINNED_BEFORE_COMPARISON"
        else:
            pin = read(PIN)
            assert pin["code_sha256"] == report["code_sha256"]
            assert pin["input_hashes"] == report["input_hashes"]
            if args.fixtures:
                report["fixtures"] = fixture_checks()
                report["status"] = "PASS"
            else:
                execute(report)
        report["elapsed_seconds"] = time.monotonic()-start
        write_once(args.out, report)
    except Exception as exc:
        report["status"] = "FAILED_PRESERVED"
        report["error"] = {"type": type(exc).__name__, "message": str(exc).replace(str(ROOT), "<project>"),
                           "traceback": traceback.format_exc().replace(str(ROOT), "<project>")}
        report["elapsed_seconds"] = time.monotonic()-start
        write_once(failed, report)
        raise
    print(json.dumps({"status": report["status"], "sha256": sha(args.out),
                      "numeric_fields_per_source": report.get("numeric_fields_per_source"),
                      "output": portable(args.out)}))
    if report["status"].startswith("FAILED"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
