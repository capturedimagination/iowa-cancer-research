"""Display every planned comparison; envelopes across settings are not CIs."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    source = BASE / "joint-results.json"
    result = json.loads(source.read_text())
    rows = result["contrast_envelopes"]
    assert len(rows) == 300 and all(r["defined_for_some_completion"] for r in rows)
    nonzero = [r for r in rows if r["evaluation_hours"] != 0]
    assert len(nonzero) == 240
    reductions = []
    for row in nonzero:
        primary_width = row["primary_upper"] - row["primary_lower"]
        joint_width = row["upper"] - row["lower"]
        assert primary_width > 0 and 0 < joint_width < primary_width
        reductions.append(100 * (1 - joint_width / primary_width))
    pairs, times = [(24, 48), (24, 60), (48, 60)], [0, 6, 12, 18, 24]
    display = []
    for early, late in pairs:
        for t in times:
            group = [r for r in rows if (r["earlier_selection_hours"], r["later_selection_hours"],
                     r["evaluation_hours"]) == (early, late, t)]
            assert len(group) == 20
            display.append({"earlier_selection_hours": early, "later_selection_hours": late,
                            "evaluation_hours": t, "configuration_count": len(group),
                            "primary_hull_lower": min(r["primary_lower"] for r in group),
                            "primary_hull_upper": max(r["primary_upper"] for r in group),
                            "joint_hull_lower": min(r["lower"] for r in group),
                            "joint_hull_upper": max(r["upper"] for r in group)})
    summary = {"source_sha256": sha(source), "plot_script_sha256": sha(__file__),
               "presentation_scope": "Post-result descriptive summary of the full frozen grid; no cases omitted.",
               "nonzero_time_cases": len(nonzero), "all_nonzero_time_intervals_narrowed": True,
               "median_width_reduction_percent": statistics.median(reductions),
               "minimum_width_reduction_percent": min(reductions),
               "maximum_width_reduction_percent": max(reductions),
               "all_300_joint_intervals_include_zero_exactly": all(r["lower"] <= 0 <= r["upper"] for r in rows),
               "display": display,
               "display_limit": "Hulls combine different recorded baselines and annotation assumptions. They are not a single identified set, sampling confidence interval, or population null test."}
    plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"],
                         "font.size": 11, "svg.hashsalt": "hct116-missing-branches-2026-11-10"})
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.2), sharey=True)
    for ax, (early, late) in zip(axes, pairs):
        group = [r for r in display if (r["earlier_selection_hours"], r["later_selection_hours"]) == (early, late)]
        ax.fill_between(times, [100*r["primary_hull_lower"] for r in group],
                        [100*r["primary_hull_upper"] for r in group], color="#d9ddd9", label="Initial bounds")
        ax.fill_between(times, [100*r["joint_hull_lower"] for r in group],
                        [100*r["joint_hull_upper"] for r in group], color="#4c8483", alpha=.72, label="Joint bounds")
        ax.axhline(0, color="#333333", lw=.8, ls="--")
        ax.set_title(f"{late} h selection minus {early} h selection", fontsize=11)
        ax.set_xticks(times)
        ax.set_xlim(0, 24)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_xlabel("Time from recorded baseline (h)")
        ax.grid(axis="y", alpha=.18)
    axes[0].set_ylabel("Selected path-survival difference\n(percentage points)")
    axes[0].set_ylim(-13, 12)
    axes[2].legend(loc="upper left", frameon=False, fontsize=10)
    fig.suptitle("Missing branches: narrower bounds, no established direction", fontsize=15, y=.98)
    fig.text(.5, .025, "Shading spans all 20 planned settings per comparison; not confidence intervals.",
             ha="center", fontsize=11)
    fig.subplots_adjust(left=.08, right=.99, bottom=.20, top=.80, wspace=.12)
    args.out.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out / "missing-branch-bounds.svg", metadata={"Date": None})
    svg = args.out / "missing-branch-bounds.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    (args.out / "display-summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.preview, dpi=150)
    print(json.dumps({k: v for k, v in summary.items() if k != "display"}, indent=2))


if __name__ == "__main__":
    main()
