"""Draw the frozen descriptive comparison from saved patient-level results."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results_dir", type=Path)
    ap.add_argument("--preview", type=Path)
    args = ap.parse_args()
    results = json.loads((args.results_dir / "results.json").read_text())
    rows = json.loads((args.results_dir / "sample-scores.json").read_text())
    rows = [r for r in rows if r["primary_eligible"]]
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":10,
                         "axes.spines.top":False, "axes.spines.right":False,
                         "svg.fonttype":"none", "svg.hashsalt":"gse292469-2026-11-10"})
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    rng = np.random.default_rng(42)
    markers = {"v3.1":"o", "v4":"s"}
    for i, state in enumerate(("TN", "MRD")):
        group = sorted([r for r in rows if r["state"] == state], key=lambda r:r["sample_id"])
        for row, offset in zip(group, rng.uniform(-.13, .13, len(group))):
            color = "#b15b32" if row["stage"] == "IV" else "#315f75"
            ax.scatter(i+offset, row["score_mean"], s=45, marker=markers.get(row["kit_series_implied"], "D"),
                       color=color, edgecolor="white", linewidth=.55, zorder=3)
        median = np.median([r["score_mean"] for r in group])
        ax.plot([i-.21, i+.21], [median, median], color="#222222", lw=1.6, zorder=4)
    ax.set_xticks([0,1], [f"Untreated\n{sum(r['state']=='TN' for r in rows)} patients",
                           f"Residual on osimertinib\n{sum(r['state']=='MRD' for r in rows)} patients"])
    ax.set_xlim(-.5, 1.5)
    ax.set_ylabel("Patient mean of 17-gene log-normalized expression")
    ax.grid(axis="y", color="#e2e3e4", lw=.7, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title("Alveolar signature in unmatched lung adenocarcinomas", loc="left", pad=18, weight="bold", fontsize=12)
    stage_legend = [Line2D([],[],marker="o",ls="",color=c,label=l) for c,l in
                    [("#315f75","Stage other than IV"),("#b15b32","Stage IV")]]
    kit_legend = [Line2D([],[],marker=m,ls="",color="#555555",label=l) for m,l in
                  [("o","Series-implied v3.1"),("s","Series-implied v4"),("D","Mixed cores")]]
    legend = ax.legend(handles=stage_legend, loc="upper left", bbox_to_anchor=(1.02,1), frameon=False, fontsize=8)
    ax.add_artist(legend)
    ax.legend(handles=kit_legend, loc="upper left", bbox_to_anchor=(1.02,.72), frameon=False, fontsize=8)
    p = results["comparisons"]["primary"]
    fig.text(.1,.075, f"Dots: patients. Bars: medians. Rank AUC: {p['auc_MRD_above_TN']:.3f} (descriptive).", fontsize=9)
    fig.text(.1,.035, "Stage, site, sampling and kit differ between groups; this does not estimate a treatment effect.", fontsize=8)
    fig.subplots_adjust(left=.1, right=.7, bottom=.2, top=.86)
    svg = args.results_dir / "patient-signature-scores.svg"
    fig.savefig(svg, metadata={"Date":None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.preview, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
