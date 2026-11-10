#!/usr/bin/env python3
"""Post-results independent audit of all frozen HCT116 joint bounds.

Uses integer-cost scalar dynamic programming, not the production NumPy solver.
Reads pinned ignored per-cell inputs; publishes only aggregate review metadata
and the already public scenario keys. No biological model is fitted or tested.
Run from any directory with Python 3; all dependencies are standard library.
"""
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from fractions import Fraction
from itertools import product
from math import lcm
from pathlib import Path
from statistics import median
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds"
KEYS = ("baseline_frame", "death_frame_offset", "ambiguity_policy",
        "earlier_selection_hours", "later_selection_hours", "evaluation_hours")
STATES = ((0, 0), (1, 0), (1, 1))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def status(m):
    return 1 if m[0] > 0 else 0 if m[0] + m[2] == 0 else None


@lru_cache(maxsize=None)
def integer_reference(rows):
    """Exact extrema for the closed common-u/nested-state relaxation.

    With dyadic interval scale S and selected counts N1,N2, multiplying costs
    by S*N1*N2 gives integer coefficients: -N2*u for state10 and
    (N1-N2)*u for state11. All optimization below is exact integer arithmetic.
    """
    scale = lcm(*(Fraction(x).denominator for row in rows for x in row[:2]))
    fixed, variable = [], []
    zero_possible = True
    for lo, hi, early, late in rows:
        allowed = tuple(s for s in STATES
                        if (early is None or early == s[0])
                        and (late is None or late == s[1])
                        and (hi > 0 or s == (0, 0)))
        assert allowed
        zero_possible &= any(s[1] == 0 for s in allowed)
        a, z = int(Fraction(lo) * scale), int(Fraction(hi) * scale)
        (fixed if len(allowed) == 1 else variable).append((a, z, allowed))
    fixed_counts = tuple(sum(v[2][0][j] for v in fixed) for j in (0, 1))
    reachable = {(0, 0)}
    for _, _, allowed in variable:
        reachable = {(a + x, b + y) for a, b in reachable for x, y in allowed}
    pairs = sorted((a + fixed_counts[0], b + fixed_counts[1])
                   for a, b in reachable if b + fixed_counts[1] > 0)
    values = {}
    for n1, n2 in pairs:
        assert n1 >= n2 > 0
        target = (n1 - fixed_counts[0], n2 - fixed_counts[1])

        def cost(lo, hi, s):
            if s == (0, 0):
                return (0, 0)
            if s == (1, 0):
                return (-hi * n2, -lo * n2)
            return (lo * (n1 - n2), hi * (n1 - n2))

        fcost = [cost(a, z, s[0]) for a, z, s in fixed]
        low_fixed, high_fixed = (sum(v[j] for v in fcost) for j in (0, 1))
        table = {(0, 0): (0, 0)}
        for lo, hi, allowed in variable:
            updated = {}
            for (a, b), (low, high) in table.items():
                for s in allowed:
                    key = (a + s[0], b + s[1])
                    if key[0] > target[0] or key[1] > target[1]:
                        continue
                    cl, ch = cost(lo, hi, s)
                    value = (low + cl, high + ch)
                    if key in updated:
                        old = updated[key]
                        value = (min(old[0], value[0]), max(old[1], value[1]))
                    updated[key] = value
            table = updated
        low, high = table[target]
        denominator = scale * n1 * n2
        values[(n1, n2)] = (Fraction(low + low_fixed, denominator),
                           Fraction(high + high_fixed, denominator))
    return {"pairs": pairs, "values": values, "zero_denominator_possible": zero_possible,
            "fixed_rows": len(fixed), "variable_rows": len(variable),
            "lower": min((x[0] for x in values.values()), default=None),
            "upper": max((x[1] for x in values.values()), default=None)}


def main():
    plan = json.loads((BASE / "joint-refinement-plan.json").read_text())
    freeze = json.loads((BASE / "joint-refinement-freeze.json").read_text())
    primary_plan = json.loads((BASE / "protocol.json").read_text())
    primary = json.loads((BASE / "results.json").read_text())
    joint = json.loads((BASE / "joint-results.json").read_text())
    private_path = ROOT / plan["private_input"]["path"]
    private = json.loads(private_path.read_text())
    tol = plan["optimization"]["numeric_tolerance"]
    assert tol == 1e-12
    assert sha(BASE / "joint-refinement-plan.json") == freeze["sha256"] == joint["joint_plan_sha256"]
    assert sha(BASE / "protocol.json") == plan["primary_protocol_sha256"] == primary["protocol_sha256"]
    assert sha(BASE / "results.json") == plan["known_before_freeze"]["primary_results_sha256"] == joint["primary_results_sha256"]
    assert sha(private_path) == plan["private_input"]["sha256"] == joint["private_input_sha256"] == primary["private_records_sha256"]
    assert sha(ROOT / "scripts/refine_hct116_lineage_bounds.py") == joint["driver_sha256"]
    assert sha(ROOT / "scripts/lineage_joint_bounds.py") == joint["joint_core_sha256"]
    assert primary["created_utc"] < plan["frozen_at_utc"] < joint["created_utc"]
    graph_path = ROOT / primary_plan["source_inputs"]["candidate_graph"]["path"]
    assert sha(graph_path) == primary["source_graph_sha256"]
    graph = json.loads(graph_path.read_text())
    bs = primary_plan["baseline_frames"]
    offsets = primary_plan["annotation_sensitivities"]["apoptosis_death_frame_offsets"]
    policies = primary_plan["annotation_sensitivities"]["ambiguity_policies"]
    hs = primary_plan["clock"]["selection_horizons_hours"]
    ts = primary_plan["clock"]["common_evaluation_hours"]
    pairs = list(map(tuple, primary_plan["contrasts"]["pairs_hours"]))
    groups = {}
    for item in private:
        k = tuple(item[x] for x in ("baseline_frame", "death_frame_offset", "ambiguity_policy", "selection_hours"))
        assert k not in groups
        groups[k] = item["records"]
    assert set(groups) == set(product(bs, offsets, policies, hs))
    source_nodes = {n["id"]: n for n in graph["nodes"]}
    rosters = {}
    for b in bs:
        rosters[b] = [r["node"] for r in graph["baseline_rosters"][str(b)]
                      if not any(f <= b for f in source_nodes[r["node"]]["apoptosis_annotation_frames_in_episode"])]
    for (b, o, p, h), rows in groups.items():
        assert [x["node"] for x in rows] == rosters[b]
        assert len({x["node"] for x in rows}) == len(rows)
        for x in rows:
            assert x["family_status"] == status(x["masses_by_elapsed_hour"][str(h)])
    prior_index, index = {}, {}
    for row in primary["contrast_envelopes"]:
        key = tuple(row[x] for x in KEYS)
        assert key not in prior_index
        prior_index[key] = row
    expected = {(b, o, p, e, l, t) for b, o, p, (e, l), t in product(bs, offsets, policies, pairs, ts)}
    assert set(prior_index) == expected
    reductions, classifications, cases = [], Counter(), []
    max_error = 0.0
    all_count_pairs = 0
    for row in joint["contrast_envelopes"]:
        key = tuple(row[x] for x in KEYS)
        assert key not in index
        index[key] = row
        outer = prior_index[key]
        b, o, p, e, l, t = key
        a, z = groups[b, o, p, e], groups[b, o, p, l]
        assert len(a) == len(z) == row["recorded_baseline_cells"] == row["rows"]
        rows = []
        for x, y in zip(a, z):
            assert x["node"] == y["node"]
            assert x["masses_by_elapsed_hour"] == y["masses_by_elapsed_hour"]
            lo, dead, unknown = x["masses_by_elapsed_hour"][str(t)]
            assert lo >= 0 and dead >= 0 and unknown >= 0 and abs(lo + dead + unknown - 1) <= tol
            assert not (x["family_status"] == 0 and y["family_status"] != 0)
            assert not (y["family_status"] == 1 and x["family_status"] != 1)
            rows.append((lo, lo + unknown, x["family_status"], y["family_status"]))
        ref = integer_reference(tuple(rows))
        assert row["defined_for_some_completion"] == bool(ref["pairs"]) == outer["defined_for_some_completion"]
        assert row["zero_denominator_possible"] == ref["zero_denominator_possible"]
        assert row["feasible_count_pairs"] == [list(x) for x in ref["pairs"]]
        assert row["feasible_count_pair_count"] == len(ref["pairs"])
        assert row["fixed_rows"] == ref["fixed_rows"] and row["variable_rows"] == ref["variable_rows"]
        all_count_pairs += len(ref["pairs"])
        assert row["primary_lower"] == outer["lower"] and row["primary_upper"] == outer["upper"]
        if ref["pairs"]:
            for end, j in (("lower", 0), ("upper", 1)):
                error = abs(row[end] - float(ref[end]))
                max_error = max(max_error, error)
                assert error <= tol
                witness = tuple(row[end + "_count_pair"])
                assert witness in ref["values"]
                assert abs(row[end] - float(ref["values"][witness][j])) <= tol
            assert outer["lower"] - tol <= row["lower"] <= row["upper"] + tol <= outer["upper"] + 2 * tol
            label = "positive" if row["lower"] > tol else "negative" if row["upper"] < -tol else "includes_zero"
            if t == 0:
                assert abs(row["lower"]) <= tol and abs(row["upper"]) <= tol
            old_width, new_width = outer["upper"] - outer["lower"], row["upper"] - row["lower"]
            reduction = None
            if t != 0:
                assert old_width > 0
                reduction = 100 * (old_width - new_width) / old_width
                reductions.append(reduction)
        else:
            label, reduction = "undefined", None
        classifications[label] += 1
        cases.append({**dict(zip(KEYS, key)), "classification_at_tolerance": label,
                      "primary_width": outer["upper"] - outer["lower"],
                      "joint_width": row["upper"] - row["lower"],
                      "relative_width_reduction_percent": reduction})
    assert set(index) == expected and len(index) == 300 and len(reductions) == 240
    for key, row in index.items():
        if key[2] == "first_issue":
            wide = index[(*key[:2], "whole_episode", *key[3:])]
            assert wide["lower"] <= row["lower"] + tol and wide["upper"] >= row["upper"] - tol
    assert joint["summary"]["includes_zero_within_tolerance"] == classifications["includes_zero"]
    assert joint["summary"]["positive_beyond_tolerance"] == classifications["positive"]
    assert joint["summary"]["negative_beyond_tolerance"] == classifications["negative"]
    assert joint["summary"]["undefined_cases"] == classifications["undefined"]
    result = {
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_POST_RESULTS_INDEPENDENT_EMPIRICAL_JOINT_REVIEW",
        "review_timing": "Designed after joint outcomes and reported median were known; validation only, no new scientific endpoint or optimization tuning.",
        "tolerance": tol,
        "pins": {"joint_plan_sha256": sha(BASE / "joint-refinement-plan.json"),
                 "primary_protocol_sha256": sha(BASE / "protocol.json"),
                 "primary_results_sha256": sha(BASE / "results.json"),
                 "joint_results_sha256": sha(BASE / "joint-results.json"),
                 "private_records_sha256": sha(private_path),
                 "source_graph_sha256": sha(graph_path),
                 "joint_core_sha256": joint["joint_core_sha256"],
                 "joint_driver_sha256": joint["driver_sha256"],
                 "review_script_sha256": sha(__file__)},
        "method": "Independent scalar dictionary dynamic program with exact integer objective costs over every feasible selected-count pair; convert rational extrema to float for comparison. Production core not imported or called.",
        "counts": {"planned_and_present_cases": len(index), "nonzero_time_width_cases": len(reductions),
                   "time_zero_cases": len(index) - len(reductions),
                   "feasible_count_pairs_across_cases": all_count_pairs,
                   "distinct_optimization_inputs": integer_reference.cache_info().currsize},
        "maximum_absolute_extremum_error": max_error,
        "checks": {"pins_and_pre_joint_freeze_order_match": True,
                   "all_300_cases_unique_and_complete": True,
                   "same_source_roster_and_u_across_horizons": True,
                   "statuses_match_horizon_mass_and_nesting": True,
                   "exact_integer_extrema_and_count_pairs_match": True,
                   "reported_extremum_count_pairs_are_valid": True,
                   "all_joint_intervals_within_primary": True,
                   "time_zero_intervals_zero": True,
                   "whole_episode_contains_first_issue": True,
                   "summary_classifications_match": True},
        "classification_counts_at_tolerance": dict(classifications),
        "width_reduction": {"definition_percent": "100*(primary_width-joint_width)/primary_width",
                            "case_filter": "Exactly all 240 planned cases with evaluation_hours !=0; no sign or width-based selection.",
                            "denominator": len(reductions), "median_percent": median(reductions),
                            "minimum_percent": min(reductions), "maximum_percent": max(reductions),
                            "strictly_narrower_cases": sum(x > 0 for x in reductions)},
        "interpretation": ["Finite recorded-roster outer ranges, not confidence intervals or population null tests.",
                           "Zero inside an optimized range does not establish an attainable zero-valued completion, even in a relaxation with discrete selection choices; complete biological tree constraints are also omitted.",
                           "Width reduction measures a tighter mathematical relaxation, not reduced biological variability, improved treatment response, or an effect size.",
                           "Original cohort eligibility, source annotation accuracy, replicate mapping and treatment timing remain unresolved."],
        "all_case_widths_and_classifications": cases,
        "production_code_results_and_plans_modified": False,
    }
    output = BASE / "joint-empirical-review.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "counts", "maximum_absolute_extremum_error",
                                           "classification_counts_at_tolerance", "width_reduction")}, indent=2))


if __name__ == "__main__":
    main()
