#!/usr/bin/env python3
"""Compare every frozen production field with the precomputed independent reference.

Post-results validation, pinned before comparison. Imports only the independent
verifier for unsaved per-type survival vectors; never imports production code.
Refuses first-output overwrite and preserves structural failures with context.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
from math import exp, isfinite
import hashlib
import json
import traceback
import numpy as np
import verify_age_lineage_models as reference

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"
PIN = "e7fe08e71d614f27f7d312a6afa7cf64d8022cba2af908cc92c7965d7d6caeb5"
REF_CODE = "4c6ed695f526d8ec07df9a4dafe4e4572e1bef0529c7d70a61a19f6a666e8883"
REF_OUTPUT = "0e53f27c4be7a362cad7a2aa093c35c3beb24bf7fa0afbc5c53bb491f13b7ef8"
PRODUCTION = "b02399e0f46b5f484dc8f1f7c9c9680e8d725898758db08e21f80ae7ca2a75f8"
STRICT = "3c145e400977760aba7892b0416fac9c56c0fd915cd93a53d99585dbe1609252"
TOL = 1e-8


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def indexed(rows, fields):
    result = {}
    for row in rows:
        k = tuple(row[f] for f in fields)
        if k in result:
            raise ValueError("Duplicate result key: " + repr(k))
        result[k] = row
    return result


def main():
    destination = BASE / "independent-comparison.json"
    if destination.exists():
        raise FileExistsError("Refusing to overwrite first comparison")
    completed, active = [], {}
    maxima, maximum_locations, counts, failures = {}, {}, Counter(), []
    input_hashes = {f: sha(BASE / f) for f in ("protocol.json", "results.json", "strict-results.json", "independent-reference.json")}
    assert input_hashes == {"protocol.json": PIN, "results.json": PRODUCTION,
                            "strict-results.json": STRICT, "independent-reference.json": REF_OUTPUT}
    assert sha(ROOT / "scripts/verify_age_lineage_models.py") == REF_CODE
    plan = json.loads((BASE / "protocol.json").read_text())
    base = json.loads((BASE / "results.json").read_text())
    strict = json.loads((BASE / "strict-results.json").read_text())
    refs = json.loads((BASE / "independent-reference.json").read_text())
    invalid = []
    reference.serializable({"primary": base, "strict": strict, "reference": refs}, invalid=invalid)
    assert not invalid, invalid
    assert base["protocol_sha256"] == strict["protocol_sha256"] == refs["protocol_sha256"] == PIN
    assert sha(ROOT / "scripts/age_lineage_models.py") == base["core_sha256"] == strict["core_sha256"]
    assert sha(ROOT / "scripts/run_age_lineage_models.py") == base["driver_sha256"] == strict["driver_sha256"]
    assert refs["script_sha256"] == REF_CODE
    pindex = indexed(base["cases"], ["case_id"])
    sindex = indexed(strict["cases"], ["case_id"])
    rindex = indexed(refs["cases"], ["case_id"])
    expected = {(c["case_id"],) for c in plan["cases"]}
    assert pindex.keys() == sindex.keys() == rindex.keys() == expected

    def compare(path, value, a, b, category, coefficient=False):
        gate = TOL * max(1, abs(value)) if coefficient else TOL
        if value is None:
            passed = a is None and b is None
            da = db = None
        else:
            passed = a is not None and b is not None
            da = None if a is None else abs(float(a) - float(value))
            db = None if b is None else abs(float(b) - float(value))
            passed &= da is not None and db is not None and da <= gate and db <= gate
            for name, error in (("primary", da), ("strict", db)):
                if error is not None:
                    key = category + "/" + name
                    if key not in maxima or error > maxima[key]:
                        maxima[key] = error
                        maximum_locations[key] = {"case_id": active["case_id"], "field": path}
        record = {"field": path, "reference": value, "primary": a, "strict": b,
                  "primary_absolute_difference": da, "strict_absolute_difference": db,
                  "gate": gate, "passed": bool(passed)}
        active["differences"].append(record)
        counts[category] += 1
        if not passed:
            failures.append({"case_id": active["case_id"], **record})

    try:
        for case in plan["cases"]:
            cid, mu = case["case_id"], case["mu"]
            p, s, r = pindex[cid,], sindex[cid,], rindex[cid,]
            assert p["configuration"] == s["configuration"] == r["model"] == case
            active = {"case_id": cid, "differences": [], "structural_checks_passed": False}
            pq = indexed(p["selected_path_survival"], ["selection_horizon", "evaluation_time"])
            sq = indexed(s["selected_path_survival"], ["selection_horizon", "evaluation_time"])
            rq = indexed(r["Q_records"], ["T", "t"])
            expected_q = {(h, t) for h in plan["times"]["selection_horizons"]
                          for t in set(plan["times"]["evaluation_times"] + [0.0, h])}
            assert pq.keys() == sq.keys() == rq.keys() == expected_q
            pf, sf = indexed(p["family_survival"], ["horizon"]), indexed(s["family_survival"], ["horizon"])
            assert pf.keys() == sf.keys() == {(h,) for h in plan["times"]["selection_horizons"]}
            for (h,), row in pf.items():
                compare(f"family/T{h}", rq[h, 0.0]["h"], row["probability"], sf[h,]["probability"], "family")
            for (h, t), row in rq.items():
                a, b = pq[h, t], sq[h, t]
                for name, target in (("value", row["Q"]), ("joint_probability", row["joint"]),
                                     ("unconditional_tag_survival", exp(-mu * t))):
                    compare(f"selected/T{h}/t{t}/{name}", target, a[name], b[name], "selected/" + name)
                if case["kind"] == "erlang":
                    compare(f"selected/T{h}/t{t}/positive_death_defect", 1 - row["Q"],
                            a["positive_death_defect"], b["positive_death_defect"], "ordinary_defect")
                    compare(f"selected/T{h}/t{t}/complement_error", 0.0, a["complement_error"], b["complement_error"], "complement")
            pc = indexed(p["contrasts"], ["earlier_horizon", "later_horizon", "evaluation_time"])
            sc = indexed(s["contrasts"], ["earlier_horizon", "later_horizon", "evaluation_time"])
            rc = indexed(r["contrasts"], ["earlier_T", "later_T", "t"])
            expected_c = {(a, b, t) for a, b in plan["times"]["contrast_pairs"] for t in plan["times"]["evaluation_times"]}
            assert pc.keys() == sc.keys() == rc.keys() == expected_c
            for key, row in rc.items():
                compare("contrast/" + repr(key), row["contrast"], pc[key]["value"], sc[key]["value"], "contrast")
            pp, sp, rp = indexed(p["pairs"], ["lag"]), indexed(s["pairs"], ["lag"]), indexed(r["pairs"], ["s"])
            assert pp.keys() == sp.keys() == rp.keys() == {(x,) for x in plan["times"]["pair_lags"]}
            for (lag,), row in rp.items():
                a, b = pp[lag,], sp[lag,]
                assert a["defined"] == b["defined"] == (row["qualification_probability"] > 0)
                for name, target in (("eligibility_probability", row["qualification_probability"]),
                                     ("covariance", row["covariance"]),
                                     ("daughter_survival_mean", row["daughter_mean"]),
                                     ("joint_daughter_survival", row["joint"])):
                    if name in a or name in b:
                        compare(f"pairs/s{lag}/{name}", target, a.get(name), b.get(name), "pair/" + name)
                target = row["maternal_weights"]
                if target is None:
                    assert a.get("qualifying_mother_type_weights") is None and b.get("qualifying_mother_type_weights") is None
                elif "qualifying_mother_type_weights" in a:
                    assert len(a["qualifying_mother_type_weights"]) == len(b["qualifying_mother_type_weights"]) == len(target)
                    for z, value in enumerate(target):
                        compare(f"pairs/s{lag}/maternal/{z}", value, a["qualifying_mother_type_weights"][z],
                                b["qualifying_mother_type_weights"][z], "pair/maternal_weights")
                if case["kind"] == "erlang":
                    k, death, alpha, kernel, initial = reference.setup(case)
                    ext = reference.extinction(k, death, tuple(alpha), case["rho"])
                    newborn = 1 - ext.sol(lag).reshape(len(alpha), k)[:, 0]
                    for name, vector in (("newborn_type_subtree_survival", newborn),
                                         ("daughter_survival_given_mother_type", kernel @ newborn)):
                        assert len(a[name]) == len(b[name]) == len(vector)
                        for z, value in enumerate(vector):
                            compare(f"pairs/s{lag}/{name}/{z}", float(value), a[name][z], b[name][z], "pair/" + name)
                    compare(f"pairs/s{lag}/closed_covariance_identity", row["two_type_identity"],
                            a["closed_covariance_identity"], b["closed_covariance_identity"], "pair/closed_identity")
                if case["kind"] == "calendar":
                    compare(f"pairs/s{lag}/residual", row["calendar_residual"],
                            a["birth_conditioned_residual_cross_product"], b["birth_conditioned_residual_cross_product"], "pair/calendar_residual")
            pe = indexed(p["deterministic_extra"], ["selection_horizon", "evaluation_time"])
            se = indexed(s["deterministic_extra"], ["selection_horizon", "evaluation_time"])
            re = indexed(r["deterministic_extras"], ["T", "t"])
            expected_extra = {(h, plan["times"]["deterministic_extra_evaluation_time"]) for h in plan["times"]["deterministic_extra_horizons"]} if case["kind"] == "deterministic" else set()
            assert pe.keys() == se.keys() == re.keys() == expected_extra
            for key, row in re.items():
                for name, value in (("value", row["Q"]), ("first_generation_formula", row["Q"]), ("family_survival", row["h"])):
                    compare("deterministic_extra/" + repr(key) + "/" + name, value, pe[key][name], se[key][name], "deterministic_extra")
            pa = indexed(p["early_time"], ["selection_horizon", "epsilon"])
            sa = indexed(s["early_time"], ["selection_horizon", "epsilon"])
            ra = indexed(r["early_records"], ["T", "epsilon"])
            expected_early = {(h, eps) for h in plan["times"]["selection_horizons"] for eps in (0.01, 0.001, 0.0001)} if case["kind"] == "erlang" else set()
            assert pa.keys() == sa.keys() == ra.keys() == expected_early
            for (h, eps), row in ra.items():
                a, b = pa[h, eps], sa[h, eps]
                assert a["nominal_order"] == b["nominal_order"] == row["power"]
                assert a["positive_leading_term"] == b["positive_leading_term"] == (mu > 0)
                for name, value in (("evaluation_time", row["t"]), ("coefficient", row["leading_coefficient"]),
                                    ("positive_death_defect", row["loss"]), ("leading_term", row["leading_coefficient"] * row["t"] ** row["power"]),
                                    ("ratio", row["ratio"]), ("conservative_lower", exp(-3 * eps)), ("conservative_upper", exp(6 * eps))):
                    compare(f"early/T{h}/eps{eps}/{name}", value, a[name], b[name], "early/" + name, coefficient=(name == "coefficient"))
                if mu == 0:
                    assert a["ratio"] is b["ratio"] is row["ratio"] is None
                    assert a["positive_death_defect"] == b["positive_death_defect"] == row["loss"] == 0
                else:
                    for name, value in (("primary", a["positive_death_defect"]), ("strict", b["positive_death_defect"])):
                        rel = abs(value / row["loss"] - 1)
                        metric = "early/positive_loss_relative_diagnostic/" + name
                        if metric not in maxima or rel > maxima[metric]:
                            maxima[metric] = rel; maximum_locations[metric] = {"case_id": cid, "T": h, "epsilon": eps}
            # Production controls are analytic zero-error diagnostics, not fitted quantities.
            assert len(p["controls"]) == len(s["controls"])
            for i, (a, b) in enumerate(zip(p["controls"], s["controls"])):
                assert {k: v for k, v in a.items() if k != "error"} == {k: v for k, v in b.items() if k != "error"}
                compare(f"control/{i}/{a['name']}", 0.0, a["error"], b["error"], "analytic_control_error")
            active["structural_checks_passed"] = True
            active["all_numeric_gates_passed"] = all(x["passed"] for x in active["differences"])
            completed.append(active)
            active = {}
        result = {
            "created_utc": datetime.now(timezone.utc).isoformat(), "status": "PASS" if not failures else "FAIL",
            "review_timing": "Comparator pinned after results existed but before comparison. Independent reference solver pinned and full reference generated before viewing production numerical outputs.",
            "input_sha256": input_hashes, "comparator_sha256": sha(__file__), "reference_script_sha256": REF_CODE,
            "primary_core_sha256": base["core_sha256"], "primary_driver_sha256": base["driver_sha256"],
            "absolute_gate": TOL, "coefficient_gate": "1e-8*max(1,abs(independent_reference_coefficient)); all probability/contrast/ratio gates absolute1e-8.",
            "counts": {"cases": len(completed), "Q_rows": sum(len(x["Q_records"]) for x in refs["cases"]),
                       "family_rows": 72 * 3, "contrasts": 72 * 12, "pairs": 72 * 3, "deterministic_extras": 6,
                       "early_rows": sum(len(x["early_records"]) for x in refs["cases"]),
                       "zero_death_undefined_early_ratios": sum(x["ratio"] is None for c in refs["cases"] for x in c["early_records"]),
                       "scalar_comparisons_each_against_primary_and_strict": sum(counts.values()), "by_category": dict(counts)},
            "maximum_differences": maxima, "maximum_locations": maximum_locations,
            "failures": failures, "full_case_differences": completed,
            "interpretation": ["All72 hypothetical models retained; deterministic numerical validation, not empirical replication or biological validation.",
                               "A small early-time power or covariance does not uniquely identify a biochemical death program or inherited cancer state.",
                               "Near-zero ratios compare stable scaled methods; full-tree MC cannot resolve arbitrary tiny probabilities.",
                               "No production, independent-reference or frozen protocol file was changed."]}
        reference.write_exclusive(destination, result)
        print(json.dumps({k: result[k] for k in ("status", "counts", "maximum_differences")}, indent=2))
    except (Exception, KeyboardInterrupt) as error:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        invalid = []
        failure = reference.serializable({"status": "FAILED_COMPARISON", "error": repr(error),
                                          "traceback": traceback.format_exc(), "input_sha256": input_hashes,
                                          "comparator_sha256": sha(__file__), "completed_cases": completed,
                                          "current_case": active, "numeric_failures": failures}, invalid=invalid)
        failure["nonfinite_diagnostics"] = invalid
        path = destination.with_name("independent-comparison.failure-" + stamp + ".json")
        reference.write_exclusive(path, failure)
        print(json.dumps({"status": "FAILED_COMPARISON", "failure_artifact": str(path)}))
        raise


if __name__ == "__main__":
    main()
