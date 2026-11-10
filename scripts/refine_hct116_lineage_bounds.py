"""Refine all frozen finite-record contrasts with a common-u nested relaxation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import time

from lineage_joint_bounds import joint_bounds
from lineage_missing_bounds import inclusion_status

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE / "joint-results.json")
    args = parser.parse_args()
    plan = json.loads((BASE / "joint-refinement-plan.json").read_text())
    freeze = json.loads((BASE / "joint-refinement-freeze.json").read_text())
    assert sha(BASE / "joint-refinement-plan.json") == freeze["sha256"]
    assert sha(BASE / "protocol.json") == plan["primary_protocol_sha256"]
    assert sha(BASE / "results.json") == plan["known_before_freeze"]["primary_results_sha256"]
    source = ROOT / plan["private_input"]["path"]
    assert sha(source) == plan["private_input"]["sha256"]
    prior = json.loads((BASE / "results.json").read_text())
    records = json.loads(source.read_text())
    grouped = {}
    for item in records:
        key = (item["baseline_frame"], item["death_frame_offset"], item["ambiguity_policy"], item["selection_hours"])
        assert key not in grouped
        grouped[key] = item["records"]
    tolerance = plan["optimization"]["numeric_tolerance"]
    output, started = [], time.monotonic()
    for outer in prior["contrast_envelopes"]:
        baseline, offset, policy = outer["baseline_frame"], outer["death_frame_offset"], outer["ambiguity_policy"]
        early, late, t = outer["earlier_selection_hours"], outer["later_selection_hours"], outer["evaluation_hours"]
        a, b = grouped[(baseline, offset, policy, early)], grouped[(baseline, offset, policy, late)]
        assert [x["node"] for x in a] == [x["node"] for x in b]
        rows = []
        for x, y in zip(a, b):
            assert x["masses_by_elapsed_hour"] == y["masses_by_elapsed_hour"]
            masses = x["masses_by_elapsed_hour"]
            assert x["family_status"] == inclusion_status(masses[str(early)])
            assert y["family_status"] == inclusion_status(masses[str(late)])
            live, dead, unknown = masses[str(t)]
            rows.append((live, live + unknown, x["family_status"], y["family_status"]))
        result = joint_bounds(rows)
        assert result["defined_for_some_completion"] == outer["defined_for_some_completion"]
        if result["defined_for_some_completion"]:
            assert result["lower"] >= outer["lower"] - tolerance
            assert result["upper"] <= outer["upper"] + tolerance
        entry = {k: outer[k] for k in ("baseline_frame", "death_frame_offset", "ambiguity_policy",
                                      "earlier_selection_hours", "later_selection_hours", "evaluation_hours")}
        entry.update(recorded_baseline_cells=len(rows), primary_lower=outer["lower"],
                     primary_upper=outer["upper"], **result)
        if t == 0 and result["defined_for_some_completion"]:
            assert abs(result["lower"]) <= tolerance and abs(result["upper"]) <= tolerance
        output.append(entry)
    assert len(output) == 300
    index = {(r["baseline_frame"], r["death_frame_offset"], r["ambiguity_policy"],
              r["earlier_selection_hours"], r["later_selection_hours"], r["evaluation_hours"]): r for r in output}
    for key, row in index.items():
        if key[2] != "first_issue" or not row["defined_for_some_completion"]:
            continue
        wide = index[(*key[:2], "whole_episode", *key[3:])]
        assert wide["lower"] <= row["lower"] + tolerance
        assert wide["upper"] >= row["upper"] - tolerance
    positive = sum(r["defined_for_some_completion"] and r["lower"] > tolerance for r in output)
    negative = sum(r["defined_for_some_completion"] and r["upper"] < -tolerance for r in output)
    defined = sum(r["defined_for_some_completion"] for r in output)
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "runtime_seconds": time.monotonic() - started,
              "joint_plan_sha256": freeze["sha256"], "primary_results_sha256": sha(BASE / "results.json"),
              "private_input_sha256": sha(source), "driver_sha256": sha(__file__),
              "joint_core_sha256": sha(ROOT / "scripts/lineage_joint_bounds.py"),
              "python": platform.python_version(), "contrast_envelopes": output,
              "summary": {"fixed_cases": len(output), "positive_beyond_tolerance": positive,
                          "negative_beyond_tolerance": negative,
                          "includes_zero_within_tolerance": defined - positive - negative,
                          "undefined_cases": len(output) - defined,
                          "comparison_tolerance": tolerance},
              "checks": {"same_roster_and_path_intervals_across_horizons": True,
                         "all_joint_intervals_inside_primary_envelopes": True,
                         "coarser_episode_bounds_contain_first_issue_bounds": True,
                         "time_zero_contrasts_equal_zero": True},
              "limits": ["Post-primary-results refinement, planned before joint empirical outcomes.",
                         "Exact combinatorial optimization of a closed rectangular/nested relaxation, evaluated in floating point.",
                         "Tree-level biological completion constraints are still omitted; these are outer bounds, not proven sharp biological bounds.",
                         "Finite recorded-roster summaries are not population confidence intervals or stochastic null tests."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"summary": result["summary"], "checks": result["checks"],
                      "runtime_seconds": result["runtime_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
