"""Post-result displays of the entire fixed grid and an explicit central slice."""
from pathlib import Path
import argparse
import hashlib
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(fig, name, out, preview):
    target = out / (name + ".svg")
    fig.savefig(target, metadata={"Date": None})
    target.write_text("\n".join(line.rstrip() for line in target.read_text().splitlines()) + "\n")
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        fig.savefig(preview / (name + ".png"), dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data = json.loads((BASE / "results.json").read_text())
    assert len(data["cases"]) == 72
    plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"],
                         "font.size": 11, "svg.hashsalt": "age-lineage-specificity-2026-11-10"})
    groups = {"Independent renewal (39)": ("#657977", "o"),
              "Partial type transmission (12)": ("#cf8b2b", "^"),
              "Persistent type (12)": ("#8b4e75", "s"),
              "Shared calendar rates (3)": ("#416ba2", "D"),
              "Zero-death controls (3)": ("#222222", "x")}
    displays, event_counts = [], []
    for c in data["cases"]:
        p = c["configuration"]
        largest = max(c["contrasts"], key=lambda r: abs(r["value"]))
        defined_pairs = [r for r in c["pairs"] if r["defined"]]
        if p["kind"] == "no_division":
            group = "Undefined pair target (3)"
        elif p["mu"] == 0:
            group = "Zero-death controls (3)"
        elif p["kind"] == "calendar":
            group = "Shared calendar rates (3)"
        elif p.get("rho", 0) == 0.5:
            group = "Partial type transmission (12)"
        elif p.get("rho", 0) == 1:
            group = "Persistent type (12)"
        else:
            group = "Independent renewal (39)"
        displays.append({"case_id": c["case_id"], "group": group,
                         "signed_largest_absolute_contrast": largest,
                         "largest_pair_covariance": max(r["covariance"] for r in defined_pairs) if defined_pairs else None})
        hs = {r["horizon"]: r["probability"] for r in c["family_survival"]}
        for r in c["early_time"]:
            if r["epsilon"] == 0.0001 and r["positive_leading_term"]:
                event_counts.append({"case_id": c["case_id"], "initialization": p["initialization"],
                                     "horizon": r["selection_horizon"], "evaluation_time": r["evaluation_time"],
                                     "founders": 10000,
                                     "expected_selected_tagged_deaths": 10000 * hs[r["selection_horizon"]] * r["positive_death_defect"]})
    assert len(event_counts) == 180
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.3), gridspec_kw={"width_ratios": [1.2, 1]})
    for group, (color, marker) in groups.items():
        rows = [r for r in displays if r["group"] == group]
        axes[0].scatter([100*r["signed_largest_absolute_contrast"]["value"] for r in rows],
                        [r["largest_pair_covariance"] for r in rows], c=color, marker=marker,
                        alpha=.72, s=30, label=group)
    axes[0].axvline(0, color="#777777", lw=.7)
    axes[0].axhline(0, color="#777777", lw=.7)
    axes[0].set_xlabel("Largest absolute horizon contrast, with its sign\n(percentage points; 12 fixed comparisons)")
    axes[0].set_ylabel("Largest sister-subtree covariance\n(three fixed lags)")
    axes[0].set_title("Different explanations overlap")
    axes[0].legend(frameon=False, fontsize=9, loc="upper right")
    for c, color in zip([c for c in data["cases"] if c["configuration"]["kind"] == "calendar"],
                        ["#40677b", "#a77336", "#854c72"]):
        axes[1].plot([r["lag"] for r in c["pairs"]], [1000*r["covariance"] for r in c["pairs"]],
                     marker="o", color=color, label=f"Death rate {c['configuration']['mu']:g}")
    axes[1].axhline(0, color="#333333", ls="--", lw=1, label="Birth-time residual: zero")
    axes[1].set_xticks([.5, 1, 2])
    axes[1].set_xlabel("Equal elapsed lag after sister birth")
    axes[1].set_ylabel("Raw covariance × 1,000")
    axes[1].set_title("Calendar mixing creates covariance")
    axes[1].legend(frameon=False, fontsize=9)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=.13)
    fig.suptitle("Selection and correlated fates do not uniquely identify inheritance", fontsize=15, y=.98)
    fig.text(.5, .025, "Hypothetical model probabilities. Left: all 69 defined pair targets; three no-division targets are undefined.",
             ha="center", fontsize=10)
    fig.subplots_adjust(left=.08, right=.98, top=.85, bottom=.21, wspace=.38)
    save(fig, "selection-specificity", args.out, args.preview)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.3))
    colors = {1: "#356b75", 2: "#a77935", 4: "#855478", 8: "#617b44"}
    slice_ids = []
    for c in data["cases"]:
        p = c["configuration"]
        if p.get("family") != "homogeneous" or p["mu"] != 1:
            continue
        slice_ids.append(c["case_id"])
        rows = sorted([r for r in c["early_time"] if r["selection_horizon"] == 3], key=lambda r: r["evaluation_time"])
        axes[0].loglog([r["evaluation_time"] for r in rows], [r["positive_death_defect"] for r in rows],
                       color=colors[p["k"]], marker="o" if p["initialization"] == "newborn" else "s",
                       ls="-" if p["initialization"] == "newborn" else "--", markersize=4)
    assert len(slice_ids) == 8
    handles = [Line2D([0], [0], color=colors[k], label=f"Division stages k={k}") for k in colors]
    handles += [Line2D([0], [0], color="#333333", ls="-", marker="o", label="Newborn: power k+1"),
                Line2D([0], [0], color="#333333", ls="--", marker="s", label="Uniform stage: power 2")]
    axes[0].legend(handles=handles, frameon=False, fontsize=9, loc="lower right")
    axes[0].set_xlabel("Early time, dimensionless")
    axes[0].set_ylabel("Conditional tagged-death probability")
    axes[0].set_title("Same one-step death; different early powers")
    ordered = sorted(event_counts, key=lambda r: r["expected_selected_tagged_deaths"])
    for init, color, label in [("newborn", "#356b75", "Newborn founders"),
                                ("uniform_stage", "#a77935", "Uniform-stage founders")]:
        xy = [(i+1, r["expected_selected_tagged_deaths"]) for i, r in enumerate(ordered) if r["initialization"] == init]
        axes[1].scatter([x for x, y in xy], [y for x, y in xy], s=13, color=color, label=label)
    axes[1].axhline(1, ls="--", color="#333333", lw=1, label="One expected event")
    axes[1].set_yscale("log")
    axes[1].set_ylim(1e-43, 10)
    axes[1].set_xlabel("All 180 positive-death model/horizon settings\n(sorted by expected count)")
    axes[1].set_ylabel("Expected selected tagged deaths / 10,000 founders")
    axes[1].set_title("The asymptotic window is too sparse here")
    axes[1].legend(frameon=False, fontsize=9, loc="lower right")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=.13)
    fig.suptitle("A local order law, with a severe measurement limit", fontsize=15, y=.98)
    fig.text(.5, .025, "Left: μ=1, T=3, all four homogeneous stage counts and both initializations. Right: smallest fixed ε; not a power analysis.",
             ha="center", fontsize=10)
    fig.subplots_adjust(left=.08, right=.98, top=.85, bottom=.21, wspace=.38)
    save(fig, "early-time-order", args.out, args.preview)
    summary = {"source_sha256": sha(BASE / "results.json"), "plot_script_sha256": sha(__file__),
               "status": "Post-results descriptive display; frozen data/model grid unchanged.",
               "all_case_display": displays, "early_time_central_slice_case_ids": slice_ids,
               "all_smallest_epsilon_expected_event_counts": event_counts,
               "expected_event_count_range": [min(r["expected_selected_tagged_deaths"] for r in event_counts),
                                              max(r["expected_selected_tagged_deaths"] for r in event_counts)],
               "limits": ["Signed maxima and covariance maxima may refer to different times; neither is a fitted or significance-selected estimate.",
                          "No-division sister targets are undefined, not zero; all three remain in the result files.",
                          "Near-zero expected counts use a future-blind random tag; integrated tree weights in the simulator are a different observation implementation of the same expectation.",
                          "Expected counts are model arithmetic, not a power calculation or calibrated real-world sampling recommendation."]}
    (args.out / "display-summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"cases": len(displays), "early_slice_cases": len(slice_ids),
                      "expected_event_count_range": summary["expected_event_count_range"]}, indent=2))


if __name__ == "__main__":
    main()
