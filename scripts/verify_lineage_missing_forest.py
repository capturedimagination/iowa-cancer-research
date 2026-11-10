#!/usr/bin/env python3
"""Independent synthetic-forest containment check; never reads empirical data.

Complete biological lifetimes and exact rational chronological weights provide
ground truth independently of the bounds implementation. Only the frozen plan
and data-free core module are read. The fixed grid is not tuned after outcomes.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from math import fsum
from pathlib import Path
import platform
import random

from lineage_missing_bounds import GraphMass, contrast_bounds, inclusion_status, ratio_bounds

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds"
PROTOCOL = BASE / "protocol.json"
CORE = Path(__file__).with_name("lineage_missing_bounds.py")
PROTOCOL_SHA = "c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771"
CORE_SHA = "27bb3b07186b015a5d573d45ffe1da6515131ea0b3da09e677531c468eb4513e"
TOLERANCE = 1e-12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


@dataclass
class Cell:
    identifier: int
    family: int
    born: int
    generation: int
    parent: int | None
    exit_frame: int | None = None
    event: str | None = None
    children: list[int] = field(default_factory=list)

    def alive(self, frame):
        return self.born <= frame and (self.exit_frame is None or frame < self.exit_frame)

    @property
    def weight(self):
        return Fraction(1, 2 ** self.generation)


def generate_forest(seed, count, horizon, division_probability, death_probability):
    """Independent discrete biological generator, before graph encoding."""
    rng = random.Random(seed)
    cells = {i + 1: Cell(i + 1, i, 0, 0, None) for i in range(count)}
    founders = list(cells)
    active = founders.copy()
    for frame in range(horizon):
        next_active = []
        for identifier in active:
            cell = cells[identifier]
            draw = rng.random()
            if draw < division_probability:
                cell.event, cell.exit_frame = "division", frame + 1
                for _ in range(2):
                    child_id = len(cells) + 1
                    cells[child_id] = Cell(child_id, cell.family, frame + 1,
                                           cell.generation + 1, identifier)
                    cell.children.append(child_id)
                    next_active.append(child_id)
            elif draw < division_probability + death_probability:
                cell.event, cell.exit_frame = "death", frame + 1
            else:
                next_active.append(identifier)
        active = next_active
    for cell in cells.values():
        if cell.event == "division":
            assert len(cell.children) == 2
            for child_id in cell.children:
                child = cells[child_id]
                assert child.parent == cell.identifier and child.born == cell.exit_frame
                assert child.born > cell.born and child.family == cell.family
                assert child.generation == cell.generation + 1
        else:
            assert not cell.children
        if cell.exit_frame is not None:
            assert cell.born < cell.exit_frame <= horizon
    assert len(founders) == count
    return cells, founders


def complete_truth(cells, count, frames):
    """Use explicit alive cells and dead leaves with exact dyadic weights."""
    truth = {}
    for frame in frames:
        live, dead = [Fraction(0) for _ in range(count)], [Fraction(0) for _ in range(count)]
        descendants = [0] * count
        for cell in cells.values():
            if cell.alive(frame):
                live[cell.family] += cell.weight
                descendants[cell.family] += 1
            if cell.event == "death" and cell.exit_frame <= frame:
                dead[cell.family] += cell.weight
        for family in range(count):
            assert live[family] + dead[family] == 1
            assert bool(live[family]) == bool(descendants[family])
        truth[frame] = {"live": live, "dead": dead,
                        "included": [n > 0 for n in descendants],
                        "living_descendants": descendants}
    return truth


def mask_forest(cells, founders, horizon, policy, seed):
    survives = {}
    for identifier in reversed(list(cells)):
        cell = cells[identifier]
        survives[identifier] = cell.alive(horizon) or any(survives[c] for c in cell.children)
    rng = random.Random(seed) if seed is not None else None
    removed = {}
    for identifier, cell in cells.items():
        if cell.parent is None:
            continue
        probability = {"none": 0.0, "independent0.1": 0.1, "independent0.3": 0.3}.get(policy)
        if policy == "terminal_survivor_dependent0.3":
            probability = 0.3 if survives[identifier] else 0.0
        if probability is None:
            raise ValueError(policy)
        removed[identifier] = False if rng is None else rng.random() < probability
    kept = set(founders)
    for identifier, cell in cells.items():
        if cell.parent is not None and cell.parent in kept and not removed[identifier]:
            kept.add(identifier)
    assert set(founders).issubset(kept)
    gaps = [c for c, flag in removed.items() if flag and cells[c].parent in kept]
    return kept, {"retained_cells": len(kept), "hidden_cells": len(cells) - len(kept),
                  "missing_daughter_edges_at_observed_parents": len(gaps),
                  "missing_edges_whose_true_subtree_survives": sum(survives[c] for c in gaps),
                  "mask_sha256": digest(sorted(kept)), "mask_seed": seed}


def encode_graph(cells, kept, horizon, offset):
    nodes, edges, divisions, deaths = [], [], [], []
    for identifier in sorted(kept):
        cell = cells[identifier]
        annotations = []
        if cell.event == "division":
            last = cell.exit_frame - 1
            divisions.append([identifier, last])
        elif cell.event == "death":
            annotation = cell.exit_frame - offset
            last, annotations = annotation, [annotation]
            deaths.append([identifier, annotation])
        else:
            last = horizon
        nodes.append({"id": str(identifier), "label": identifier,
                      "first_frame": cell.born, "last_frame": last,
                      "apoptosis_annotation_frames_in_episode": annotations})
        for child in cell.children:
            if child in kept:
                edges.append({"parent": str(identifier), "child": str(child)})
                assert cells[child].born == last + 1
        assert cell.born <= last <= horizon
    return {"nodes": nodes, "edges": edges,
            "event_annotation_keys": {"Divisions": divisions, "Apoptosis": deaths}, "issues": []}


def exact_mean(truth, frame, horizon):
    selected = [i for i, flag in enumerate(truth[horizon]["included"]) if flag]
    if not selected:
        return None
    return sum((truth[frame]["live"][i] for i in selected), Fraction(0)) / len(selected)


def rational_record(value):
    return None if value is None else {"value": float(value), "numerator": value.numerator,
                                      "denominator": value.denominator}


def run_verification():
    if sha(PROTOCOL) != PROTOCOL_SHA or sha(CORE) != CORE_SHA:
        raise ValueError("Frozen plan or reviewed pre-outcome core hash differs")
    plan = json.loads(PROTOCOL.read_text())
    spec = plan["verification_before_empirical_run"]["synthetic_forest_plan"]
    clock = Fraction(str(plan["clock"]["hours_per_frame"]))
    def frame_number(hours):
        value = Fraction(str(hours)) / clock
        assert value.denominator == 1
        return int(value)
    times = [frame_number(x) for x in plan["clock"]["common_evaluation_hours"]]
    horizons = [frame_number(x) for x in plan["clock"]["selection_horizons_hours"]]
    pairs = [tuple(frame_number(x) for x in pair) for pair in plan["contrasts"]["pairs_hours"]]
    frames = sorted(set(times + horizons))
    assert times == [0, 12, 24, 36, 48] and horizons == [48, 96, 120]
    seed, count, horizon = spec["seed"], spec["families_per_case"], spec["frame_horizon"]
    failures, cases, ratios, contrasts = [], [], [], []
    checks = {k: 0 for k in ["mass_containment", "mass_conservation", "inclusion_status",
                             "ratio_containment", "contrast_containment", "complete_exact_mass",
                             "complete_exact_ratio", "annotation_offset_equivalence",
                             "ambiguity_policy_equivalence", "baseline_ratio_one"]}
    maxima = {k: 0.0 for k in ["mass", "ratio", "contrast", "mass_conservation",
                               "complete_mass", "complete_ratio"]}

    def contain(kind, value, lo, hi, context):
        checks[kind + "_containment"] += 1
        excess = max(lo - float(value), float(value) - hi, 0.0)
        maxima[kind] = max(maxima[kind], excess)
        if excess > TOLERANCE:
            failures.append({"check": kind + "_containment", "truth": float(value),
                             "lower": lo, "upper": hi, **context})

    for case_index, (p_division, p_death) in enumerate(spec["per_frame_division_death_probabilities"]):
        forest_seed = seed + 1000 * case_index
        cells, founders = generate_forest(forest_seed, count, horizon, p_division, p_death)
        truth = complete_truth(cells, count, frames)
        serialized = [{"id": c.identifier, "family": c.family, "born": c.born,
                       "generation": c.generation, "parent": c.parent, "exit": c.exit_frame,
                       "event": c.event, "children": c.children} for c in cells.values()]
        case = {"case_index": case_index, "division_probability": p_division,
                "death_probability": p_death, "forest_seed": forest_seed,
                "founders": len(founders), "complete_cells": len(cells),
                "complete_divisions": sum(c.event == "division" for c in cells.values()),
                "complete_deaths": sum(c.event == "death" for c in cells.values()),
                "first_interval_founder_deaths": sum(c.parent is None and c.event == "death" and c.exit_frame == 1 for c in cells.values()),
                "maximum_generation": max(c.generation for c in cells.values()),
                "complete_forest_sha256": digest(serialized),
                "true_selected_families": {str(t): sum(truth[t]["included"]) for t in horizons},
                "masking_policies": []}
        for policy_index, policy in enumerate(spec["missing_daughter_policies"]):
            mask_seed = None if policy == "none" else seed + 1000 * case_index + 100 + policy_index
            kept, mask_record = mask_forest(cells, founders, horizon, policy, mask_seed)
            mask_record.update({"policy": policy, "encodings": []})
            offset_reference = None
            for offset in spec["death_annotation_offsets"]:
                graph = encode_graph(cells, kept, horizon, offset)
                calculator = GraphMass(graph)
                mask_record["encodings"].append({"death_offset": offset, "graph_sha256": digest(graph),
                                                  "recorded_nodes": len(graph["nodes"]),
                                                  "recorded_edges": len(graph["edges"])})
                policy_reference = None
                for ambiguity_policy in plan["annotation_sensitivities"]["ambiguity_policies"]:
                    context = {"case_index": case_index, "missing_policy": policy,
                               "death_offset": offset, "ambiguity_policy": ambiguity_policy}
                    masses = {}
                    for frame in frames:
                        masses[frame] = []
                        for family, founder in enumerate(founders):
                            mass = calculator.mass(str(founder), frame, 0, offset, ambiguity_policy)
                            masses[frame].append(mass)
                            live, dead, unknown = mass
                            err = abs(fsum(mass) - 1.0)
                            checks["mass_conservation"] += 1
                            maxima["mass_conservation"] = max(maxima["mass_conservation"], err)
                            location = {"family": family, "frame": frame, **context}
                            if min(mass) < -TOLERANCE or err > TOLERANCE:
                                failures.append({"check": "mass_conservation", "mass": mass, **location})
                            contain("mass", truth[frame]["live"][family], live, live + unknown,
                                    {"component": "live", **location})
                            contain("mass", truth[frame]["dead"][family], dead, dead + unknown,
                                    {"component": "dead", **location})
                            status = inclusion_status(mass)
                            checks["inclusion_status"] += 1
                            if status is not None and bool(status) != truth[frame]["included"][family]:
                                failures.append({"check": "inclusion_status", "status": status, **location})
                            if policy == "none":
                                checks["complete_exact_mass"] += 1
                                error = max(abs(live - float(truth[frame]["live"][family])),
                                            abs(dead - float(truth[frame]["dead"][family])), abs(unknown))
                                maxima["complete_mass"] = max(maxima["complete_mass"], error)
                                if error > TOLERANCE:
                                    failures.append({"check": "complete_exact_mass", "error": error, **location})
                    if policy_reference is None:
                        policy_reference = masses
                    else:
                        checks["ambiguity_policy_equivalence"] += 1
                        if masses != policy_reference:
                            failures.append({"check": "ambiguity_policy_equivalence", **context})
                    for frame in times:
                        frame_bounds = {}
                        for selection_horizon in horizons:
                            rows = [(m[0], m[0] + m[2], inclusion_status(h))
                                    for m, h in zip(masses[frame], masses[selection_horizon])]
                            bounds = ratio_bounds(rows)
                            frame_bounds[selection_horizon] = bounds
                            value = exact_mean(truth, frame, selection_horizon)
                            location = {"frame": frame, "selection_horizon": selection_horizon, **context}
                            ratios.append({**location, "truth": rational_record(value), "bounds": bounds})
                            if value is not None:
                                if not bounds["defined_for_some_completion"]:
                                    failures.append({"check": "ratio_falsely_undefined", **location})
                                else:
                                    contain("ratio", value, bounds["lower"], bounds["upper"], location)
                                    if policy == "none":
                                        checks["complete_exact_ratio"] += 1
                                        error = max(abs(bounds["lower"] - float(value)), abs(bounds["upper"] - float(value)))
                                        maxima["complete_ratio"] = max(maxima["complete_ratio"], error)
                                        if error > TOLERANCE:
                                            failures.append({"check": "complete_exact_ratio", "error": error, **location})
                            elif not bounds["zero_denominator_possible"]:
                                failures.append({"check": "zero_denominator_falsely_excluded", **location})
                            if frame == 0 and bounds["defined_for_some_completion"]:
                                checks["baseline_ratio_one"] += 1
                                if bounds["lower"] != 1 or bounds["upper"] != 1:
                                    failures.append({"check": "baseline_ratio_one", **location})
                        for earlier, later in pairs:
                            bounds = contrast_bounds(frame_bounds[earlier], frame_bounds[later])
                            early_value, late_value = exact_mean(truth, frame, earlier), exact_mean(truth, frame, later)
                            value = None if late_value is None else late_value - early_value
                            location = {"frame": frame, "earlier_horizon": earlier,
                                        "later_horizon": later, **context}
                            contrasts.append({**location, "truth": rational_record(value), "bounds": bounds})
                            if value is not None:
                                if not bounds["defined_for_some_completion"]:
                                    failures.append({"check": "contrast_falsely_undefined", **location})
                                else:
                                    contain("contrast", value, bounds["lower"], bounds["upper"], location)
                            elif not bounds["zero_denominator_possible"]:
                                failures.append({"check": "contrast_zero_denominator_falsely_excluded", **location})
                    # Method-level lru_cache keys include self: release each scenario.
                    calculator.mass.cache_clear()
                if offset_reference is None:
                    offset_reference = policy_reference
                else:
                    checks["annotation_offset_equivalence"] += 1
                    if policy_reference != offset_reference:
                        failures.append({"check": "annotation_offset_equivalence", "case_index": case_index,
                                         "missing_policy": policy})
            case["masking_policies"].append(mask_record)
        cases.append(case)
    assert sha(PROTOCOL) == PROTOCOL_SHA and sha(CORE) == CORE_SHA
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if not failures else "FAIL", "seed": seed,
            "protocol_sha256": sha(PROTOCOL), "core_sha256": sha(CORE),
            "verification_script_sha256": sha(Path(__file__).resolve()),
            "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                            "platform": platform.platform(), "rng": "Python random.Random Mersenne Twister",
                            "truth_arithmetic": "fractions.Fraction exact dyadic weights and rational averages"},
            "configuration": {"families_per_case": count, "frame_horizon": horizon,
                              "evaluation_frames": times, "selection_horizons": horizons,
                              "all_mass_query_frames": frames, "contrast_pairs": pairs,
                              "death_annotation_offsets": spec["death_annotation_offsets"],
                              "ambiguity_policies": plan["annotation_sensitivities"]["ambiguity_policies"],
                              "tolerance": TOLERANCE},
            "pre_outcome_clarification": "Core baseline API uses actual death=annotation+offset. The empirical caller separately preserves its frozen common eligibility rule. This clarification preceded every forest draw and retains first-interval dying founders under offset1.",
            "generator_rules": {"events": "One mutually exclusive division/death/stay draw per living cell per frame; event takes effect at f+1.",
                                "order": "Current active-list order; staying cells retain order and daughters replace their parent in order. All founders created before frame0 draws.",
                                "forest_seed": "base_seed+1000*zero_based_case_index",
                                "mask_seed": "None for none; otherwise base_seed+1000*case_index+100+zero_based_policy_index",
                                "mask_draws": "One draw per biological daughter in ascending ID order, including descendants of already removed ancestors.",
                                "dependent_policy": "Drop with probability0.3 iff complete daughter subtree has any frame120 survivor; otherwise0.",
                                "encoding": "Division flag at actual_event-1, daughters at actual_event. Death annotation at actual_death-offset, last recorded frame=annotation; offset0 includes one post-death record.",
                                "truth": "Independent complete-cell birth/exit histories, exact path weight2^-generation; family inclusion from living descendant counts."},
            "checks": checks, "maximum_numerical_excess": maxima,
            "failure_count": len(failures), "failures": failures,
            "undefined_truth_ratios": sum(x["truth"] is None for x in ratios),
            "undefined_truth_contrasts": sum(x["truth"] is None for x in contrasts),
            "ratio_zero_denominator_possible_count": sum(x["bounds"]["zero_denominator_possible"] for x in ratios),
            "cases": cases, "all_ratio_results": ratios, "all_contrast_results": contrasts,
            "limits": ["Containment conditional on each synthetic tree, not confidence coverage.",
                       "No empirical graph, workbook, roster, calibration or fitting.",
                       "Not a proof of tree-completion sharpness or original-cohort eligibility.",
                       "Synthetic issues are empty; ambiguity policies should agree. Other ambiguities have separate core fixtures.",
                       "No probability, grid, horizon or missingness tuning after outcomes."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE / "forest-verification.json")
    args = parser.parse_args()
    result = run_verification()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ["status", "checks", "maximum_numerical_excess",
                                            "failure_count", "protocol_sha256", "core_sha256",
                                            "verification_script_sha256"]}, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
