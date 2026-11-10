#!/usr/bin/env python3
"""Independent exact-enumeration and synthetic-subset checks of joint bounds.

No empirical graph, workbook or private per-cell file is read. The first 12
founders are taken from each full 300-founder forest already fixed and verified.
The subset is selected by creation index, never by outcome or completeness.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
from itertools import combinations_with_replacement, product
import json
from pathlib import Path
import platform

import numpy as np

from lineage_joint_bounds import joint_bounds
from lineage_missing_bounds import GraphMass, contrast_bounds, inclusion_status, ratio_bounds
from verify_lineage_missing_forest import (
    complete_truth, digest, encode_graph, generate_forest, mask_forest,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds"
JOINT_PLAN = BASE / "joint-refinement-plan.json"
PRIMARY_PLAN = BASE / "protocol.json"
PREVIOUS_FOREST_RESULTS = BASE / "forest-verification.json"
JOINT_MODULE = Path(__file__).with_name("lineage_joint_bounds.py")
JOINT_SHA = "f24fe1d3a99d2abfd3fdb453d74b87e2b28ad44017845cd3c8ac3b429984802d"
PINNED = {
    JOINT_PLAN: "531ac9e5c63a5ed000ca59d282038bee1d6ad66a192d54d4aeb8cf9a4811532b",
    PRIMARY_PLAN: "c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771",
    PREVIOUS_FOREST_RESULTS: "42ff99e11735d753df81a440804cb2ba0247c8a4a75d95a6614a62d56b0cf8d4",
    Path(__file__).with_name("lineage_missing_bounds.py"): "27bb3b07186b015a5d573d45ffe1da6515131ea0b3da09e677531c468eb4513e",
    Path(__file__).with_name("verify_lineage_missing_forest.py"): "9c4d02e1a8621e4299df644f4bc7d4de7b150c90a583352498961230e51cf05e",
}
DESIGN_STATED_AT_UTC = "2026-11-10T19:40:59Z"
TOLERANCE = 1e-12
INTERVALS = [(F(0), F(0)), (F(0), F(1)), (F(1, 4), F(3, 4)), (F(1, 2), F(1, 2))]
STATES = [(0, 0), (1, 0), (1, 1)]
SUBSET_COUNT = 12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allowed_states(row):
    lower, upper, early, late = row
    assert 0 <= lower <= upper <= 1 and early in (0, 1, None) and late in (0, 1, None)
    return [s for s in STATES if (early is None or s[0] == early)
            and (late is None or s[1] == late) and (upper > 0 or s == (0, 0))]


def exhaustive_truth(rows):
    """Enumerate joint selections and all common-u endpoint combinations.

    No optimized coefficient rule or dynamic program is used. Both selected
    means are evaluated directly with exact Fractions for each completed case.
    """
    choices = [allowed_states(row) for row in rows]
    if any(not choice for choice in choices):
        raise ValueError("No allowed state for a row")
    lower = upper = None
    zero_possible, pairs, completions = False, set(), 0
    for states in product(*choices):
        n1, n2 = sum(s[0] for s in states), sum(s[1] for s in states)
        if n2 == 0:
            zero_possible = True
            continue
        pairs.add((n1, n2))
        for u in product(*[tuple(sorted(set(row[:2]))) for row in rows]):
            q1 = sum((s[0] * p for s, p in zip(states, u)), F(0)) / n1
            q2 = sum((s[1] * p for s, p in zip(states, u)), F(0)) / n2
            value = q2 - q1
            lower = value if lower is None else min(lower, value)
            upper = value if upper is None else max(upper, value)
            completions += 1
    return {"lower": lower, "upper": upper, "zero_denominator_possible": zero_possible,
            "pairs": sorted(pairs), "endpoint_completion_count": completions}


def serial_rows(rows):
    return [[str(lo), str(hi), early, late] for lo, hi, early, late in rows]


def float_rows(rows):
    return [(float(lo), float(hi), early, late) for lo, hi, early, late in rows]


def rational(value):
    return None if value is None else {"value": float(value), "numerator": value.numerator,
                                      "denominator": value.denominator}


def compare_exact(rows, truth, got):
    reasons, maximum_error = [], 0.0
    defined = truth["lower"] is not None
    if got["defined_for_some_completion"] != defined:
        reasons.append("defined_status")
    if got["zero_denominator_possible"] != truth["zero_denominator_possible"]:
        reasons.append("zero_denominator_status")
    if sorted(tuple(x) for x in got["feasible_count_pairs"]) != truth["pairs"]:
        reasons.append("feasible_count_pairs")
    if got["feasible_count_pair_count"] != len(truth["pairs"]):
        reasons.append("feasible_count_pair_count")
    for side in ("lower", "upper"):
        if defined:
            if got[side] is None:
                reasons.append(side + "_missing")
            else:
                error = abs(got[side] - float(truth[side]))
                maximum_error = max(maximum_error, error)
                if error > TOLERANCE:
                    reasons.append(side + "_extremum")
        elif got[side] is not None:
            reasons.append(side + "_should_be_undefined")
    return reasons, maximum_error


def exact_checks():
    catalog = [(lo, hi, early, late) for lo, hi in INTERVALS
               for early, late in product((0, 1, None), repeat=2)
               if allowed_states((lo, hi, early, late))]
    assert len(catalog) == 28
    failures, outcomes = [], []
    maximum_error, solver_calls, endpoint_completions = 0.0, 0, 0
    multisets = [()]
    for size in (1, 2, 3):
        multisets.extend(combinations_with_replacement(range(len(catalog)), size))
    for case_id, indices in enumerate(multisets):
        rows = [catalog[i] for i in indices]
        truth = exhaustive_truth(rows)
        endpoint_completions += truth["endpoint_completion_count"]
        got = joint_bounds(float_rows(rows))
        solver_calls += 1
        reasons, error = compare_exact(rows, truth, got)
        maximum_error = max(maximum_error, error)
        reverse_checked = len(rows) >= 2
        if reverse_checked:
            reverse = joint_bounds(float_rows(rows[::-1]))
            solver_calls += 1
            reverse_reasons, error = compare_exact(rows[::-1], truth, reverse)
            maximum_error = max(maximum_error, error)
            reasons.extend("reversed_" + x for x in reverse_reasons)
        if reasons:
            failures.append({"case_id": case_id, "rows": serial_rows(rows), "reasons": reasons,
                             "got": got, "truth_lower": rational(truth["lower"]),
                             "truth_upper": rational(truth["upper"])})
        outcomes.append({"case_id": case_id, "catalog_indices": list(indices),
                         "truth_lower": rational(truth["lower"]), "truth_upper": rational(truth["upper"]),
                         "solver_lower": got["lower"], "solver_upper": got["upper"],
                         "defined": got["defined_for_some_completion"],
                         "zero_denominator_possible": got["zero_denominator_possible"],
                         "feasible_count_pairs": got["feasible_count_pairs"],
                         "endpoint_completions": truth["endpoint_completion_count"],
                         "reverse_order_checked": reverse_checked, "passed": not reasons})
    invalid_cases = [
        ("late_known_alive_early_known_extinct", [(0, 1, 0, 1)]),
        ("zero_upper_early_known_selected", [(0, 0, 1, None)]),
        ("zero_upper_late_known_selected", [(0, 0, None, 1)]),
        ("zero_upper_known_early_only", [(0, 0, 1, 0)]),
    ]
    invalid_results = []
    for name, rows in invalid_cases:
        rejected = False
        try:
            joint_bounds(rows)
        except ValueError:
            rejected = True
        invalid_results.append({"name": name, "rows": rows, "rejected": rejected})
        if not rejected:
            failures.append({"invalid_input_not_rejected": name})
    return {"catalog": serial_rows(catalog), "roster_sizes": [0, 1, 2, 3],
            "multiset_case_count": len(outcomes), "solver_calls": solver_calls,
            "endpoint_completions": endpoint_completions, "maximum_absolute_error": maximum_error,
            "undefined_later_cases": sum(not o["defined"] for o in outcomes),
            "all_cases": outcomes, "invalid_controls": invalid_results, "failures": failures}


def subset_mean(truth, frame, horizon, indices):
    selected = [i for i in indices if truth[horizon]["included"][i]]
    if not selected:
        return None
    return sum((truth[frame]["live"][i] for i in selected), F(0)) / len(selected)


def forest_checks(primary_plan, prior_results):
    spec = primary_plan["verification_before_empirical_run"]["synthetic_forest_plan"]
    clock = F(str(primary_plan["clock"]["hours_per_frame"]))
    def frames(hours):
        frame = F(str(hours)) / clock
        assert frame.denominator == 1
        return int(frame)
    times = [frames(x) for x in primary_plan["clock"]["common_evaluation_hours"]]
    horizons = [frames(x) for x in primary_plan["clock"]["selection_horizons_hours"]]
    pairs = [tuple(frames(x) for x in pair) for pair in primary_plan["contrasts"]["pairs_hours"]]
    query_frames = sorted(set(times + horizons))
    failures, results, cases = [], [], []
    defined_truth_checks = inside_primary_checks = 0
    maximum_containment_excess = maximum_primary_excess = 0.0
    indices = list(range(SUBSET_COUNT))
    for case_index, (p_division, p_death) in enumerate(spec["per_frame_division_death_probabilities"]):
        seed = spec["seed"] + 1000 * case_index
        # Regenerate the full300, not a newly drawn forest of size12.
        cells, founders = generate_forest(seed, spec["families_per_case"], spec["frame_horizon"],
                                          p_division, p_death)
        serialized = [{"id": c.identifier, "family": c.family, "born": c.born,
                       "generation": c.generation, "parent": c.parent, "exit": c.exit_frame,
                       "event": c.event, "children": c.children} for c in cells.values()]
        assert digest(serialized) == prior_results["cases"][case_index]["complete_forest_sha256"]
        truth = complete_truth(cells, spec["families_per_case"], query_frames)
        selected_founders = founders[:SUBSET_COUNT]
        assert len(selected_founders) == SUBSET_COUNT
        assert [cells[x].family for x in selected_founders] == indices
        case = {"case_index": case_index, "forest_seed": seed,
                "full_generated_founders": len(founders), "joint_validation_founders": SUBSET_COUNT,
                "selected_founder_ids": selected_founders,
                "complete_forest_sha256": digest(serialized),
                "true_selected_subset_families": {str(t): sum(truth[t]["included"][i] for i in indices) for t in horizons},
                "mask_checks": []}
        for policy_index, policy in enumerate(spec["missing_daughter_policies"]):
            mask_seed = None if policy == "none" else spec["seed"] + 1000 * case_index + 100 + policy_index
            kept, mask_metadata = mask_forest(cells, founders, spec["frame_horizon"], policy, mask_seed)
            previous_mask = prior_results["cases"][case_index]["masking_policies"][policy_index]
            assert mask_metadata["mask_sha256"] == previous_mask["mask_sha256"]
            case["mask_checks"].append({"policy": policy, "mask_sha256": mask_metadata["mask_sha256"],
                                         "matches_original_full_forest_mask": True})
            for offset in spec["death_annotation_offsets"]:
                graph = encode_graph(cells, kept, spec["frame_horizon"], offset)
                original_encoding = next(e for e in previous_mask["encodings"] if e["death_offset"] == offset)
                assert digest(graph) == original_encoding["graph_sha256"]
                model = GraphMass(graph)
                for ambiguity in primary_plan["annotation_sensitivities"]["ambiguity_policies"]:
                    context = {"case_index": case_index, "missing_policy": policy,
                               "death_offset": offset, "ambiguity_policy": ambiguity}
                    masses = {frame: [model.mass(str(root), frame, 0, offset, ambiguity)
                                       for root in selected_founders] for frame in query_frames}
                    for frame in times:
                        for earlier, later in pairs:
                            rows = [(m[0], m[0] + m[2], inclusion_status(e), inclusion_status(l))
                                    for m, e, l in zip(masses[frame], masses[earlier], masses[later])]
                            got = joint_bounds(rows)
                            early_mean = subset_mean(truth, frame, earlier, indices)
                            late_mean = subset_mean(truth, frame, later, indices)
                            value = None if late_mean is None else late_mean - early_mean
                            early_outer = ratio_bounds([(lo, hi, e) for lo, hi, e, l in rows])
                            late_outer = ratio_bounds([(lo, hi, l) for lo, hi, e, l in rows])
                            primary_outer = contrast_bounds(early_outer, late_outer)
                            location = {"frame": frame, "earlier_horizon": earlier,
                                        "later_horizon": later, **context}
                            reasons = []
                            if value is not None:
                                defined_truth_checks += 1
                                if not got["defined_for_some_completion"]:
                                    reasons.append("truth_defined_but_bound_undefined")
                                else:
                                    excess = max(got["lower"] - float(value), float(value) - got["upper"], 0.0)
                                    maximum_containment_excess = max(maximum_containment_excess, excess)
                                    if excess > TOLERANCE:
                                        reasons.append("truth_outside_joint_interval")
                            elif not got["zero_denominator_possible"]:
                                reasons.append("true_zero_denominator_excluded")
                            if got["defined_for_some_completion"]:
                                inside_primary_checks += 1
                                if not primary_outer["defined_for_some_completion"]:
                                    reasons.append("joint_defined_but_primary_undefined")
                                else:
                                    excess = max(primary_outer["lower"] - got["lower"],
                                                 got["upper"] - primary_outer["upper"], 0.0)
                                    maximum_primary_excess = max(maximum_primary_excess, excess)
                                    if excess > TOLERANCE:
                                        reasons.append("joint_not_inside_primary_outer_interval")
                            entry = {**location, "true_contrast": rational(value),
                                     "joint": got, "primary_outer": primary_outer, "passed": not reasons}
                            results.append(entry)
                            if reasons:
                                failures.append({**entry, "reasons": reasons})
                    model.mass.cache_clear()
        cases.append(case)
    return {"subset_rule": "First12 baseline founders by fixed creation index in each existing300-founder case; never selected by survival or completeness.",
            "joint_validated_unique_founders": SUBSET_COUNT * len(cases),
            "not_full900_joint_validation": True, "candidate_contrast_checks": len(results),
            "defined_truth_containment_checks": defined_truth_checks,
            "undefined_truth_contrasts": sum(r["true_contrast"] is None for r in results),
            "joint_intervals_inside_primary_checked": inside_primary_checks,
            "maximum_containment_excess": maximum_containment_excess,
            "maximum_primary_envelope_excess": maximum_primary_excess,
            "cases": cases, "all_contrast_results": results, "failures": failures}


def run():
    if JOINT_SHA is None:
        raise ValueError("The joint implementation must be pinned before the first verification run")
    all_pins = {**PINNED, JOINT_MODULE: JOINT_SHA}
    for path, expected in all_pins.items():
        if sha(path) != expected:
            raise ValueError("Pinned artifact differs: " + str(path))
    joint_plan = json.loads(JOINT_PLAN.read_text())
    primary_plan = json.loads(PRIMARY_PLAN.read_text())
    prior_results = json.loads(PREVIOUS_FOREST_RESULTS.read_text())
    assert joint_plan["optimization"]["numeric_tolerance"] == TOLERANCE
    exact = exact_checks()
    forests = forest_checks(primary_plan, prior_results)
    for path, expected in all_pins.items():
        assert sha(path) == expected, path
    failures = exact["failures"] + forests["failures"]
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if not failures else "FAIL", "failure_count": len(failures),
            "verification_design_stated_at_utc": DESIGN_STATED_AT_UTC,
            "post_primary_results_refinement": True,
            "knowledge_before_test": "Primary empirical outer intervals already all included zero; no joint empirical output or private per-cell input read. Exact-enumeration design and first12 forest subset fixed before joint test outcomes.",
            "environment": {"python": platform.python_version(), "numpy": np.__version__,
                            "platform": platform.platform(), "exact_arithmetic": "fractions.Fraction"},
            "tolerance": TOLERANCE, "seed_for_exact_checks": None,
            "forest_base_seed": primary_plan["verification_before_empirical_run"]["synthetic_forest_plan"]["seed"],
            "artifacts": [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in all_pins],
            "verification_script_sha256": sha(Path(__file__).resolve()),
            "exact_small_cases": exact, "frozen_forest_subset": forests,
            "failures": failures,
            "limits": ["Exact rational enumeration covers the stated finite small-case catalog, not every possible input.",
                       "Joint forest validation uses36 founders, first12 in each fixed case, not all900.",
                       "Closed rectangular nested-state relaxation: zero-lower selected values may be unattained biological infima.",
                       "No empirical source graph, workbook, private per-cell record, parameter fit or source-outcome tuning.",
                       "Containment and optimization checks are not population confidence coverage, tree-completion sharpness or a biological discovery."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE / "joint-verification.json")
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "failure_count": result["failure_count"],
                      "exact_cases": result["exact_small_cases"]["multiset_case_count"],
                      "exact_solver_calls": result["exact_small_cases"]["solver_calls"],
                      "exact_max_error": result["exact_small_cases"]["maximum_absolute_error"],
                      "forest_unique_founders": result["frozen_forest_subset"]["joint_validated_unique_founders"],
                      "forest_defined_checks": result["frozen_forest_subset"]["defined_truth_containment_checks"],
                      "forest_undefined_truth": result["frozen_forest_subset"]["undefined_truth_contrasts"],
                      "forest_max_error": result["frozen_forest_subset"]["maximum_containment_excess"],
                      "verification_script_sha256": result["verification_script_sha256"]}, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
