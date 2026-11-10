"""Compute frozen descriptive bounds; no biological rate model or null test."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform

from lineage_missing_bounds import GraphMass, inclusion_status, ratio_bounds, contrast_bounds, self_checks

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=BASE / "results.json")
    ap.add_argument("--private-out", type=Path, default=ROOT / "tmp/hct116-missing-bounds/per-cell.json")
    args = ap.parse_args()
    plan = json.loads((BASE / "protocol.json").read_text())
    freeze = json.loads((BASE / "plan-freeze.json").read_text())
    assert sha(BASE / "protocol.json") == freeze["sha256"]
    for name in ("candidate_graph", "structure_results"):
        item = plan["source_inputs"][name]
        assert sha(ROOT / item["path"]) == item["sha256"]
    fixtures = self_checks()
    graph = json.loads((ROOT / plan["source_inputs"]["candidate_graph"]["path"]).read_text())
    model = GraphMass(graph)
    rows, contrasts, per_cell, roster_audit = [], [], [], []
    by_key = {}
    horizons = plan["clock"]["selection_horizons_hours"]
    times = plan["clock"]["common_evaluation_hours"]
    for baseline in plan["baseline_frames"]:
        source_roster = [r["node"] for r in graph["baseline_rosters"][str(baseline)]]
        assert len(set(source_roster)) == len(source_roster)
        roster = [n for n in source_roster if model.apoptosis[n] is None or model.apoptosis[n] > baseline]
        assert all(model.nodes[n]["first_frame"] <= baseline <= model.nodes[n]["last_frame"] for n in roster)
        roster_audit.append({"baseline_frame": baseline, "source_candidate_cells": len(source_roster),
                             "eligible_recorded_cells": len(roster),
                             "excluded_apoptosis_at_or_before_baseline": len(source_roster) - len(roster)})
        assert baseline + int(2 * max(horizons)) <= plan["clock"]["final_source_frame"]
        for offset in plan["annotation_sensitivities"]["apoptosis_death_frame_offsets"]:
            for policy in plan["annotation_sensitivities"]["ambiguity_policies"]:
                masses = {h: {n: model.mass(n, baseline + int(2 * h), baseline, offset, policy)
                              for n in roster} for h in sorted(set(times + horizons))}
                for n in roster:
                    old_lo = old_hi = 1.0
                    for h in sorted(masses):
                        live, dead, unknown = masses[h][n]
                        assert abs(live + dead + unknown - 1) < 1e-12
                        assert live <= old_lo + 1e-12 and live + unknown <= old_hi + 1e-12
                        old_lo, old_hi = live, live + unknown
                for horizon in horizons:
                    statuses = {n: inclusion_status(masses[horizon][n]) for n in roster}
                    for t in times:
                        values = [(masses[t][n][0], masses[t][n][0] + masses[t][n][2], statuses[n]) for n in roster]
                        bounded = ratio_bounds(values)
                        record = {"baseline_frame": baseline, "death_frame_offset": offset,
                                  "ambiguity_policy": policy, "selection_hours": horizon,
                                  "evaluation_hours": t, "recorded_baseline_cells": len(roster),
                                  "unknown_path_mass_sum": sum(masses[t][n][2] for n in roster), **bounded}
                        if t == 0 and bounded["defined_for_some_completion"]:
                            assert bounded["lower"] == bounded["upper"] == 1
                        rows.append(record)
                        by_key[(baseline, offset, policy, horizon, t)] = record
                    per_cell.append({"baseline_frame": baseline, "death_frame_offset": offset,
                                     "ambiguity_policy": policy, "selection_hours": horizon,
                                     "records": [{"node": n, "family_status": statuses[n],
                                                  "masses_by_elapsed_hour": {str(t): masses[t][n] for t in sorted(masses)}}
                                                 for n in roster]})
                for early, late in plan["contrasts"]["pairs_hours"]:
                    for n in roster:
                        e, l = inclusion_status(masses[early][n]), inclusion_status(masses[late][n])
                        assert not (l == 1 and e == 0)
                    for t in times:
                        a = by_key[(baseline, offset, policy, early, t)]
                        b = by_key[(baseline, offset, policy, late, t)]
                        bounded = contrast_bounds(a, b)
                        contrasts.append({"baseline_frame": baseline, "death_frame_offset": offset,
                                          "ambiguity_policy": policy, "earlier_selection_hours": early,
                                          "later_selection_hours": late, "evaluation_hours": t, **bounded})
    # Deliberately discarding additional episode history cannot narrow the relaxation.
    for (b, o, p, h, t), row in by_key.items():
        if p != "first_issue":
            continue
        wide = by_key[(b, o, "whole_episode", h, t)]
        if row["defined_for_some_completion"]:
            assert wide["defined_for_some_completion"]
            assert wide["lower"] <= row["lower"] + 1e-12
            assert wide["upper"] >= row["upper"] - 1e-12
    args.private_out.parent.mkdir(parents=True, exist_ok=True)
    args.private_out.write_text(json.dumps(per_cell, indent=2, allow_nan=False) + "\n")
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "protocol_sha256": freeze["sha256"],
              "script_sha256": sha(__file__), "core_sha256": sha(ROOT / "scripts/lineage_missing_bounds.py"),
              "source_graph_sha256": plan["source_inputs"]["candidate_graph"]["sha256"],
              "python": platform.python_version(), "scope": plan["scope"], "fixtures": fixtures,
              "rosters": roster_audit, "ratio_envelopes": rows, "contrast_envelopes": contrasts,
              "checks": {"mass_conserved": True, "survival_bounds_monotone": True,
                         "time_zero_defined_ratios_equal_one": True, "coarser_episode_bounds_contain_first_issue_bounds": True},
              "private_records_sha256": sha(args.private_out),
              "limits": ["Finite recorded-roster compatibility envelopes, not sampling confidence intervals.",
                         "Original eligibility, replicate mapping and annotation validity are not established by these bounds.",
                         "Rectangular and nesting relaxations can include incompatible tree completions; envelopes need not be sharp.",
                         "Neither zero exclusion nor zero inclusion proves or disproves the population branching model."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"rosters": roster_audit, "ratio_rows": len(rows), "contrast_rows": len(contrasts),
                      "checks": result["checks"], "protocol_sha256": freeze["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
