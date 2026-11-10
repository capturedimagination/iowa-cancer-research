#!/usr/bin/env python3
"""Compare saved independent aggregates under the already frozen MC rules.

No simulator or deterministic model implementation is imported. Default action:
fixtures only. --freeze records source/code pins; --evaluate requires that pin.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform

import scipy
from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"
PROTOCOL = BASE / "protocol.json"
PRIMARY = BASE / "results.json"
STRICT = BASE / "strict-results.json"
MC = BASE / "monte-carlo/results.json"
OUTPUT = BASE / "monte-carlo/comparison.json"
REPORT = BASE / "monte-carlo/comparison.md"
FREEZE = BASE / "monte-carlo/comparison-freeze.json"
AMENDMENT = BASE / "monte-carlo/comparison-amendment.json"
PROTOCOL_SHA = "e7fe08e71d614f27f7d312a6afa7cf64d8022cba2af908cc92c7965d7d6caeb5"
MC_SHA = "3ab903e06c5a7ba80b0ca59b12cc6e9a56ad0fa62bbe6ca42f3492293ff21adb"
PROBABILITY_GATES = 331
PROBABILITY_THRESHOLD = .001 / PROBABILITY_GATES
NUMERIC_SLACK = 1e-8


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, allow_nan=False) + "\n"
    with path.open("x") as stream:
        stream.write(text)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def probability_check(k, n, probability):
    record = {"count": k, "denominator": n, "model_probability": probability,
              "p_value": None, "threshold": PROBABILITY_THRESHOLD, "flagged": False}
    if not isinstance(k, int) or not isinstance(n, int) or not 0 <= k <= n:
        record.update(status="invalid_count", flagged=True)
    elif not finite(probability) or not 0 <= probability <= 1:
        record.update(status="invalid_reference_probability", flagged=True)
    elif n == 0:
        record.update(status="undefined_zero_denominator")
    else:
        p = float(binomtest(k, n, probability, alternative="two-sided").pvalue)
        flagged = p < PROBABILITY_THRESHOLD
        record.update(p_value=p, flagged=flagged,
                      status="flagged_probability_mismatch" if flagged else "no_probability_flag")
    return record


def value_check(estimate, mcse, reference, count, defined=True, structural=None,
                model_defined=True):
    record = {"estimate": estimate, "mcse": mcse, "reference": reference,
              "relevant_count": count, "low_precision": count < 100,
              "difference": None, "absolute_difference": None,
              "six_se_plus_slack": None, "flagged": False,
              "structural_value": structural}
    if not model_defined:
        record["status"] = "expected_undefined" if not defined else "flagged_defined_against_undefined_model"
        record["flagged"] = defined
        return record
    if not finite(reference):
        record.update(status="invalid_reference_value", flagged=True)
        return record
    if not defined:
        record["status"] = "unresolved_undefined_estimate"
        return record
    if not finite(estimate) or not isinstance(count, int) or count <= 0:
        record.update(status="invalid_estimate_or_count", flagged=True)
        return record
    difference = estimate - reference
    record.update(difference=difference, absolute_difference=abs(difference))
    if mcse is not None and (not finite(mcse) or mcse < 0):
        record.update(status="invalid_mcse", flagged=True)
        return record
    if structural is not None:
        flagged = abs(estimate - structural) > NUMERIC_SLACK or abs(reference - structural) > NUMERIC_SLACK
        record.update(status="flagged_structural_mismatch" if flagged else "structural_agreement", flagged=flagged)
        return record
    if mcse is not None:
        record["six_se_plus_slack"] = 6 * mcse + NUMERIC_SLACK
    if count < 100:
        record["status"] = "unresolved_low_precision"
    elif mcse is None:
        record["status"] = "unresolved_missing_mcse"
    elif mcse == 0:
        record["status"] = "unresolved_zero_mcse"
    else:
        flagged = abs(difference) > record["six_se_plus_slack"]
        record.update(status="flagged_six_se_mismatch" if flagged else "no_six_se_flag", flagged=flagged)
    return record


def indexed(records, fields):
    answer = {}
    for record in records:
        key = tuple(record[field] for field in fields)
        if key in answer:
            raise ValueError(f"Duplicate reference key {fields}: {key}")
        answer[key] = record
    return answer


def structural_q_value(config, evaluation_time):
    if (evaluation_time == 0 or config["mu"] == 0 or config["kind"] == "no_division"
            or (config["kind"] == "deterministic" and evaluation_time <= config["division_age"])):
        return 1.0
    return None


def fixtures():
    tests = []

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        tests.append(label)

    check(abs(probability_check(0, 4, .5)["p_value"] - .125) < 1e-15, "exact two-sided binomial tail")
    check(probability_check(1, 10, 0)["flagged"] and probability_check(9, 10, 1)["flagged"], "p0 and p1 logical failures")
    check(not probability_check(0, 10, 0)["flagged"] and not probability_check(10, 10, 1)["flagged"], "p0 and p1 logical agreement")
    check(probability_check(0, 0, .5)["status"] == "undefined_zero_denominator", "empty conditional type sample retained")
    check(probability_check(5, 4, .5)["flagged"] and probability_check(1, 4, 1.01)["flagged"], "invalid count and probability rejected")
    check(probability_check(0, 4, .5)["p_value"] != probability_check(0, 10000, .5)["p_value"], "conditional mother-type denominator is eligible count")
    threshold = 6 * .1 + NUMERIC_SLACK
    check(not value_check(threshold, .1, 0, 100)["flagged"] and value_check(threshold + 1e-9, .1, 0, 100)["flagged"], "strict six-SE-plus-slack boundary")
    check(value_check(1, .01, 0, 99)["status"] == "unresolved_low_precision", "count99 cannot be called a precision pass")
    check(value_check(1, .01, 0, 100)["flagged"], "count100 enables frozen comparison")
    check(value_check(0, 0, 0, 100)["status"] == "unresolved_zero_mcse", "nontrivial zero-SE agreement stays unresolved")
    check(value_check(1, 0, 1, 1, structural=1)["status"] == "structural_agreement", "known exact identity can be checked at low count")
    check(value_check(None, None, 1, 0, defined=False, structural=1)["status"] == "unresolved_undefined_estimate", "no selected family is never zero-imputed")
    check(value_check(None, None, None, 0, defined=False, model_defined=False)["status"] == "expected_undefined", "no-division sister estimand stays undefined")
    check(value_check(float("nan"), .1, 0, 100)["flagged"] and value_check(0, float("nan"), 0, 100)["flagged"], "nonfinite numbers never pass")
    check(value_check(1, float("nan"), 1, 100, structural=1)["flagged"], "structural identities cannot mask nonfinite SE")
    check(value_check(0, 0, 1, 100, structural=1)["flagged"], "structural estimate mismatch retained")
    deterministic = {"kind": "deterministic", "mu": 1.0, "division_age": 1.0}
    check(structural_q_value(deterministic, 1.0) == 1.0 and
          structural_q_value(deterministic, 1.0 + 1e-12) is None,
          "deterministic first-division boundary is structural only through t=d")
    return {"status": "pass", "fixture_count": len(tests), "fixtures": tests,
            "scientific_comparisons_run": False, "created_utc": utc_now(),
            "comparator_sha256": sha(__file__)}


def input_pins():
    return {"protocol_sha256": sha(PROTOCOL), "primary_sha256": sha(PRIMARY),
            "strict_primary_sha256": sha(STRICT), "monte_carlo_sha256": sha(MC),
            "comparator_sha256": sha(__file__), "python_version": platform.python_version(),
            "scipy_version": scipy.__version__, "classification_amendment_sha256": sha(AMENDMENT)}


def freeze(report):
    pins = input_pins()
    if pins["protocol_sha256"] != PROTOCOL_SHA or pins["monte_carlo_sha256"] != MC_SHA:
        raise ValueError("Protocol or first MC aggregate changed")
    save_new(FREEZE, {"created_utc": utc_now(), "status": "frozen_before_comparison_evaluation",
                      **pins, "fixtures": report, "planned_probability_gates": PROBABILITY_GATES,
                      "rule": "All frozen probability and Monte Carlo diagnostics; no code/model imports, fitting or outcome-based changes."})


def evaluate():
    pinned = json.loads(FREEZE.read_text())
    if any(pinned.get(key) != value for key, value in input_pins().items()):
        raise ValueError("Comparison inputs/code/environment changed after freeze")
    protocol = json.loads(PROTOCOL.read_text())
    primary = json.loads(PRIMARY.read_text())
    strict = json.loads(STRICT.read_text())
    mc = json.loads(MC.read_text())
    if primary["status"] != "PASS" or len(strict["cases"]) != 72:
        raise ValueError("Deterministic reference did not report pass")
    if any(source["protocol_sha256"] != PROTOCOL_SHA for source in (primary, strict, mc)):
        raise ValueError("An aggregate refers to a different frozen protocol")
    expected_cases = {c["case_id"]: c for c in protocol["cases"]}
    pcase = indexed(primary["cases"], ["case_id"])
    mcase = indexed(mc["cases"], ["case_id"])
    if set(pcase) != {(c,) for c in expected_cases} or set(mcase) != set(pcase):
        raise ValueError("Case roster mismatch")
    probabilities, quantities, identities, case_reports = [], [], [], []
    for case_id, config in expected_cases.items():
        p, m = pcase[(case_id,)], mcase[(case_id,)]
        if p["configuration"] != config or m.get("case") != config or m["status"] != "complete":
            raise ValueError(f"Case completeness/configuration mismatch: {case_id}")
        if m["founders"] != 10000 or len(m["contrasts"]) != 12:
            raise ValueError(f"Frozen sample/contrast count mismatch: {case_id}")
        family = {r["horizon"]: r["probability"] for r in p["family_survival"]}
        qrefs = indexed(p["selected_path_survival"], ["evaluation_time", "selection_horizon"])
        for extra in p["deterministic_extra"]:
            family[extra["selection_horizon"]] = extra["family_survival"]
            qrefs[(extra["evaluation_time"], extra["selection_horizon"])] = extra
        refs = indexed(p["contrasts"], ["evaluation_time", "earlier_horizon", "later_horizon"])
        pair_refs = indexed(p["pairs"], ["lag"])
        mfamily = indexed(m["family"], ["T"])
        if set(mfamily) != {(t,) for t in family} or set(indexed(m["Q"], ["t", "T"])) != set(qrefs):
            raise ValueError("Missing/duplicate family or Q records")
        if set(indexed(m["contrasts"], ["t", "T_early", "T_late"])) != set(refs):
            raise ValueError("Missing/duplicate paired contrasts")
        if set(indexed(m["pairs"], ["lag"])) != set(pair_refs):
            raise ValueError("Missing/duplicate pair lags")
        expected_u_times = {0., .5, 1., 1.5, 2., 3., 4.}
        if config["kind"] == "deterministic":
            expected_u_times |= {1.25, 1.75}
        if set(indexed(m["U"], ["t"])) != {(t,) for t in expected_u_times}:
            raise ValueError("Missing/duplicate unconditional U times")
        prob_case, values_case, identity_case = [], [], []
        for row in m["family"]:
            check = probability_check(row["count"], m["founders"], family[row["T"]])
            prob_case.append({"case_id": case_id, "quantity": "family_survival", "T": row["T"], **check})
        eligibility = [r["eligibility_probability"] for r in p["pairs"]]
        if len(eligibility) != 3 or max(eligibility) - min(eligibility) > 1e-12:
            raise ValueError("Eligibility should be one shared probability across lags")
        check = probability_check(m["eligibility"]["count"], m["founders"], eligibility[0])
        prob_case.append({"case_id": case_id, "quantity": "pair_eligibility", **check})
        if len(config.get("means", [1])) == 2:
            weights = [r["qualifying_mother_type_weights"][0] for r in p["pairs"]]
            if max(weights) - min(weights) > 1e-12:
                raise ValueError("Qualifying mother weights differ across lags")
            observed = m["qualifying_mother_type"]
            if observed["eligible_pairs"] != m["eligibility"]["count"]:
                raise ValueError("Mother-type conditional denominator mismatch")
            check = probability_check(observed["type0_count"], observed["eligible_pairs"], weights[0])
            prob_case.append({"case_id": case_id, "quantity": "qualifying_mother_type0", **check})
        for row in m["Q"]:
            if row["selected"] != mfamily[(row["T"],)]["count"]:
                raise ValueError("Q selected denominator differs from family count")
            reference = qrefs[(row["t"], row["T"])]["value"]
            exact = structural_q_value(config, row["t"])
            check = value_check(row["estimate"], row["mcse"], reference, row["selected"], row["defined"], exact)
            values_case.append({"case_id": case_id, "quantity": "Q", "t": row["t"], "T": row["T"],
                                "simulation_precision_status": row["precision"], **check})
        for row in m["contrasts"]:
            if (row["selected_early"] != mfamily[(row["T_early"],)]["count"] or
                    row["selected_late"] != mfamily[(row["T_late"],)]["count"]):
                raise ValueError("Contrast denominator differs from family count")
            reference = refs[(row["t"], row["T_early"], row["T_late"])]["value"]
            exact = 0.0 if structural_q_value(config, row["t"]) is not None else None
            check = value_check(row["estimate"], row["mcse"], reference,
                                min(row["selected_early"], row["selected_late"]), row["defined"], exact)
            values_case.append({"case_id": case_id, "quantity": "paired_horizon_contrast",
                                "t": row["t"], "T_early": row["T_early"], "T_late": row["T_late"],
                                "simulation_precision_status": row["precision"], **check})
        for row in m["U"]:
            if row["founders"] != m["founders"]:
                raise ValueError("U founder denominator mismatch")
            exact = 1.0 if row["t"] == 0 or config["mu"] == 0 else None
            check = value_check(row["estimate"], row["mcse"], math.exp(-config["mu"] * row["t"]),
                                m["founders"], structural=exact)
            values_case.append({"case_id": case_id, "quantity": "unconditional_U", "t": row["t"],
                                "reference_source": "Frozen constant-death identity exp(-mu*t)",
                                "simulation_precision_status": row["precision"], **check})
        for row in m["pairs"]:
            if row["eligible_pairs"] != m["eligibility"]["count"]:
                raise ValueError("Sister covariance eligible denominator mismatch")
            reference = pair_refs[(row["lag"],)]
            check = value_check(row["estimate"], row["mcse"], reference["covariance"],
                                row["eligible_pairs"], row["defined"],
                                structural=0.0 if config["mu"] == 0 else None,
                                model_defined=reference["defined"])
            values_case.append({"case_id": case_id, "quantity": "sister_covariance", "lag": row["lag"],
                                "simulation_precision_status": row["precision"], **check})
            if config["kind"] == "calendar":
                residual = row["calendar_residual"]
                if residual["eligible_pairs"] != m["eligibility"]["count"]:
                    raise ValueError("Calendar residual eligible denominator mismatch")
                check = value_check(residual["estimate"], residual["mcse"],
                                    reference["birth_conditioned_residual_cross_product"],
                                    residual["eligible_pairs"], residual["defined"])
                values_case.append({"case_id": case_id, "quantity": "calendar_residual_mean", "lag": row["lag"],
                                    "simulation_precision_status": residual["precision"], **check})
        for name, success, value in (
            ("family_indicator_equals_positive_tag_mass", m["accounting"]["all_family_indicators_match_positive_U"] is True,
             m["accounting"]["all_family_indicators_match_positive_U"]),
            ("empirical_endpoint_product", finite(m["accounting"]["max_endpoint_product_error"]) and
             m["accounting"]["max_endpoint_product_error"] <= NUMERIC_SLACK,
             m["accounting"]["max_endpoint_product_error"]),
        ):
            identity_case.append({"case_id": case_id, "identity": name, "observed": value,
                                  "status": "accounting_agreement" if success else "flagged_accounting_mismatch", "flagged": not success})
        probabilities.extend(prob_case)
        quantities.extend(values_case)
        identities.extend(identity_case)
        case_reports.append({"case_id": case_id, "probability_checks": len(prob_case),
                             "quantity_checks": len(values_case), "accounting_checks": len(identity_case),
                             "flagged": sum(x["flagged"] for x in prob_case + values_case + identity_case),
                             "unresolved": sum(x["status"].startswith("unresolved_") for x in values_case)})
    probability_counts = dict(Counter(r["quantity"] for r in probabilities))
    quantity_counts = dict(Counter(r["quantity"] for r in quantities))
    if probability_counts != {"family_survival": 222, "pair_eligibility": 72, "qualifying_mother_type0": 37}:
        raise ValueError(f"Incomplete frozen probability roster: {probability_counts}")
    if quantity_counts != {"Q": 1230, "paired_horizon_contrast": 864, "unconditional_U": 510,
                           "sister_covariance": 216, "calendar_residual_mean": 9}:
        raise ValueError(f"Incomplete frozen quantity roster: {quantity_counts}")
    all_records = probabilities + quantities + identities
    flags = [r for r in all_records if r["flagged"]]
    unresolved = [r for r in quantities if r["status"].startswith("unresolved_")]
    report = {"created_utc": utc_now(), **input_pins(), "freeze_sha256": sha(FREEZE),
              "scope": "Numerical consistency of independently implemented hypothetical models; not biological significance or confidence intervals.",
              "status": "flags_present" if flags else "no_frozen_diagnostic_flags",
              "probability_threshold": PROBABILITY_THRESHOLD, "quantity_rule": "6*MCSE+1e-8 with relevant count>=100; nontrivial zero MCSE unresolved.",
              "probability_counts": probability_counts, "quantity_counts": quantity_counts,
              "probability_status_counts": dict(Counter(r["status"] for r in probabilities)),
              "quantity_status_counts": dict(Counter(r["status"] for r in quantities)),
              "accounting_status_counts": dict(Counter(r["status"] for r in identities)),
              "flag_count": len(flags), "unresolved_quantity_count": len(unresolved),
              "retained_simulation_precision_status_counts": dict(Counter(r["simulation_precision_status"] for r in quantities)),
              "cases": case_reports, "flagged_records": flags, "unresolved_records": unresolved,
              "probability_diagnostics": probabilities, "quantity_diagnostics": quantities,
              "accounting_diagnostics": identities,
              "limits": ["Low precision and zero-MCSE cases are not converted to successful validation.",
                         "Structural known constants can be checked directly while retaining low-count flags.",
                         "Six-SE diagnostics are approximate and are not asserted to be a simultaneous confidence band.",
                         "No near-zero early-time Monte Carlo expansion or empirical interpretation is made."]}
    save_new(OUTPUT, report)
    status_table = "\n".join(f"| {key} | {value} |" for key, value in report["quantity_status_counts"].items())
    text = ("# Independent complete-tree comparison\n\n"
            f"All 72 frozen cases are retained. There are **{len(flags)} flagged comparisons**, "
            f"**{len(unresolved)} unresolved quantity checks**, 331 exact-binomial probability diagnostics, "
            "2,829 quantity diagnostics and 144 accounting checks. These assess simulation consistency, not biological significance.\n\n"
            "| Quantity-check status | Count |\n|---|---:|\n" + status_table + "\n\n"
            "Probability gates use the frozen two-sided threshold `0.001/331`, including conditional mother-type counts among eligible pairs. "
            "Quantity diagnostics use `6*MCSE+1e-8` when the relevant denominator is at least 100. "
            "Paired horizon standard errors remain those saved by the independently reviewed simulator. "
            "Nontrivial zero standard errors and low counts remain unresolved; no-division sister estimands remain undefined. "
            "Known structural constants are checked directly, with their original precision labels retained.\n\n"
            "Before comparison evaluation, source review recognized deterministic-age Q=1 and horizon contrasts=0 through the first division time, including the division boundary. "
            "[The pre-evaluation classification note](comparison-amendment.json) preserves the original comparator pin and records this refinement; no simulation or primary outcomes were changed.\n\n"
            "[Complete comparison records](comparison.json) contain every flag, unresolved result and case. "
            "[Pre-evaluation pin](comparison-freeze.json) binds both saved reference files, the unchanged first Monte Carlo results, comparator code and fixtures. "
            "No simulator or primary model code was imported. The strict reference file is pinned as convergence provenance; "
            "the standard reference values supply the declared comparisons. No seeds, models, outcomes or simulation code changed.\n\n"
            "The approximate SE diagnostics are not a simultaneous confidence band. This comparison does not validate an empirical cohort, establish inheritance in cancer cells, or resolve the deterministic study's near-zero predictions with Monte Carlo.\n")
    with REPORT.open("x") as stream:
        stream.write(text)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    fixture_report = fixtures()
    print(json.dumps(fixture_report, indent=2))
    if args.freeze:
        freeze(fixture_report)
    if args.evaluate:
        result = evaluate()
        print(json.dumps({k: result[k] for k in ("status", "flag_count", "unresolved_quantity_count", "probability_status_counts", "quantity_status_counts")}, indent=2))


if __name__ == "__main__":
    main()
