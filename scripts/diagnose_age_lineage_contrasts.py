#!/usr/bin/env python3
"""Posthoc read-only diagnostics of every frozen horizon contrast.

This was designed after the two flagged contrasts and their saved-root strata
were inspected. It does not generate new trees, change gates, or clear flags.
"""
from collections import Counter
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"
MC = BASE / "monte-carlo/results.json"
COMPARISON = BASE / "monte-carlo/comparison.json"
PRIMARY = BASE / "results.json"
OUTPUT = BASE / "monte-carlo/sparse-contribution-diagnostic.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def decomposition(u, f1, f2):
    """Independent loss-based arithmetic, with the founder as cluster."""
    u, f1, f2 = np.asarray(u, float), np.asarray(f1, bool), np.asarray(f2, bool)
    if np.any(f2 & ~f1):
        raise ValueError("Later selected set must be nested within earlier set")
    n, n1, n2 = len(u), int(f1.sum()), int(f2.sum())
    removed = f1 & ~f2
    nr = int(removed.sum())
    loss = 1 - u
    result = {"founders": n, "selected_early": n1, "selected_late": n2,
              "removed_families": nr,
              "positive_early_loss_earlier_selected": int(np.sum(loss[f1] > 0)),
              "positive_early_loss_later_selected": int(np.sum(loss[f2] > 0)),
              "positive_early_loss_removed": int(np.sum(loss[removed] > 0)),
              "weighted_loss_sum_earlier_selected": float(np.sum(loss[f1])),
              "weighted_loss_sum_later_selected": float(np.sum(loss[f2])),
              "weighted_loss_sum_removed": float(np.sum(loss[removed])),
              "zero_observed_removed_early_loss": nr > 0 and not np.any(loss[removed] > 0),
              "defined": n1 > 0 and n2 > 0, "contrast_from_losses": None,
              "contrast_from_disjoint_strata": None, "mcse_from_loss_influence": None,
              "mcse_from_nonnegative_strata_decomposition": None}
    if not result["defined"]:
        return result
    d1, d2 = float(np.mean(loss[f1])), float(np.mean(loss[f2]))
    h1, h2, hr = n1 / n, n2 / n, nr / n
    influence = f1 * (loss - d1) / h1 - f2 * (loss - d2) / h2
    se = math.sqrt(float(np.sum((influence - np.mean(influence)) ** 2)) / (n * (n - 1)))
    d_removed = float(np.mean(loss[removed])) if nr else None
    identity = nr / n1 * (d_removed - d2) if nr else 0.0
    v2 = float(np.mean((loss[f2] - d2) ** 2))
    vr = float(np.mean((loss[removed] - d_removed) ** 2)) if nr else 0.0
    # Empirical probabilities/conditional moments; ddof correction appears below.
    terms = [hr * hr * v2 / (h1 * h1 * h2), hr * vr / (h1 * h1),
             h2 * hr * (d2 - d_removed) ** 2 / h1 ** 3 if nr else 0.0]
    reconstructed_se = math.sqrt(sum(terms) / (n - 1))
    result.update(contrast_from_losses=d1 - d2, contrast_from_disjoint_strata=identity,
                  mcse_from_loss_influence=se,
                  mcse_from_nonnegative_strata_decomposition=reconstructed_se,
                  mean_loss_later_selected=d2, mean_loss_removed=d_removed,
                  empirical_influence_variance_terms={
                      "later_stratum": terms[0], "removed_stratum": terms[1],
                      "between_strata": terms[2]},
                  influence_mean=float(np.mean(influence)))
    return result


def fixture_checks():
    # Fixed constructed founders, no RNG or scientific cohort generation.
    u = np.array([1, .5, .75, .25, 1, 0.])
    f1 = np.array([1, 1, 1, 1, 1, 0], bool)
    f2 = np.array([1, 1, 1, 0, 0, 0], bool)
    row = decomposition(u, f1, f2)
    q_difference = float(np.mean(u[f2]) - np.mean(u[f1]))
    assert abs(row["contrast_from_losses"] - q_difference) < 1e-15
    assert abs(row["contrast_from_disjoint_strata"] - q_difference) < 1e-15
    assert abs(row["mcse_from_loss_influence"] - row["mcse_from_nonnegative_strata_decomposition"]) < 1e-15
    same = decomposition(u, f1, f1)
    assert same["contrast_from_losses"] == 0 and same["mcse_from_loss_influence"] == 0
    empty = decomposition(u, f1, np.zeros(6, bool))
    assert not empty["defined"] and empty["contrast_from_losses"] is None
    missing_contributors = decomposition(np.array([1., 1., .5]), np.ones(3, bool), np.array([0, 1, 1], bool))
    assert missing_contributors["zero_observed_removed_early_loss"]
    return {"status": "pass", "controls": 6,
            "checks": ["loss versus Q contrast", "disjoint-stratum contrast identity",
                       "nonnegative variance decomposition", "equal selection sets",
                       "undefined later denominator", "zero observed removed contributors"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mc", type=Path, default=MC)
    parser.add_argument("--primary", type=Path, default=PRIMARY)
    parser.add_argument("--comparison", type=Path, default=COMPARISON)
    parser.add_argument("--checkpoint-root", type=Path, default=ROOT,
                        help="Root against which relative batch paths in the MC aggregate resolve")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    fixtures = fixture_checks()
    mc = json.loads(args.mc.read_text())
    primary = json.loads(args.primary.read_text())
    comparison = json.loads(args.comparison.read_text())
    if not mc["protocol_sha256"] == primary["protocol_sha256"] == comparison["protocol_sha256"]:
        raise ValueError("Input protocols disagree")
    references = {c["case_id"]: c for c in primary["cases"]}
    prior = {(c["case_id"], c["t"], c["T_early"], c["T_late"]): c
             for c in comparison["quantity_diagnostics"] if c["quantity"] == "paired_horizon_contrast"}
    rows = []
    verified_batches = 0
    for case in mc["cases"]:
        if case["status"] != "complete":
            raise ValueError("Incomplete case must not disappear from a diagnostic")
        chunks = []
        times = None
        for expected_start, batch in enumerate(case["batch_files"]):
            path = args.checkpoint_root / batch["path"]
            if sha(path) != batch["sha256"]:
                raise ValueError("Saved founder checkpoint hash changed")
            with np.load(path, allow_pickle=False) as saved:
                metadata = json.loads(str(saved["metadata"]))
                if metadata["root_start"] != 250 * expected_start or metadata["case_id"] != case["case_id"]:
                    raise ValueError("Saved founder ordering/identity mismatch")
                if metadata["code_sha256"] != mc["code_sha256"] or metadata["protocol_sha256"] != mc["protocol_sha256"]:
                    raise ValueError("Checkpoint code/protocol mismatch")
                if times is not None and not np.array_equal(times, saved["query_times"]):
                    raise ValueError("Query-time mismatch")
                times = saved["query_times"].copy()
                chunks.append((saved["U"].copy(), saved["F"].copy()))
            verified_batches += 1
        u_all = np.concatenate([c[0] for c in chunks])
        f_all = np.concatenate([c[1] for c in chunks])
        if len(u_all) != 10000:
            raise ValueError("Founder count mismatch")
        index = {float(t): j for j, t in enumerate(times)}
        ref = references[case["case_id"]]
        href = {v["horizon"]: v["probability"] for v in ref["family_survival"]}
        qref = {(v["evaluation_time"], v["selection_horizon"]): v for v in ref["selected_path_survival"]}
        for saved in case["contrasts"]:
            t, t1, t2 = saved["t"], saved["T_early"], saved["T_late"]
            existing = prior[(case["case_id"], t, t1, t2)]
            if saved["defined"]:
                if (abs(existing["estimate"] - saved["estimate"]) > 1e-12 or
                        abs(existing["mcse"] - saved["mcse"]) > 1e-12):
                    raise ValueError("Supplied comparison labels do not describe these MC estimates/SEs")
            row = decomposition(u_all[:, index[t]], f_all[:, index[t1]], f_all[:, index[t2]])
            # Positive-defect fields avoid unnecessary cancellation where available.
            q1, q2 = qref[(t, t1)], qref[(t, t2)]
            d1 = q1.get("positive_death_defect", 1 - q1["value"])
            d2 = q2.get("positive_death_defect", 1 - q2["value"])
            row.update(case_id=case["case_id"], t=t, T_early=t1, T_late=t2,
                       saved_estimate=saved["estimate"], saved_mcse=saved["mcse"],
                       frozen_comparison_status=existing["status"], frozen_flagged=existing["flagged"],
                       original_simulation_precision_status=saved["precision"],
                       known_structural_constant=existing["structural_value"] is not None,
                       reference_contrast=existing["reference"],
                       reference_expected_removed_families_at_N10000=10000 * (href[t1] - href[t2]),
                       reference_expected_weighted_early_loss_in_removed_at_N10000=10000 * (href[t1] * d1 - href[t2] * d2),
                       reference_loss_source="Saved positive-death-defect where present; otherwise 1-Q")
            row["estimate_reproduction_absolute_error"] = abs(row["contrast_from_losses"] - saved["estimate"]) if row["defined"] else None
            row["mcse_reproduction_absolute_error"] = abs(row["mcse_from_loss_influence"] - saved["mcse"]) if row["defined"] else None
            row["disjoint_identity_absolute_error"] = abs(row["contrast_from_losses"] - row["contrast_from_disjoint_strata"]) if row["defined"] else None
            row["variance_identity_absolute_error"] = abs(row["mcse_from_loss_influence"] - row["mcse_from_nonnegative_strata_decomposition"]) if row["defined"] else None
            rows.append(row)
    if len(rows) != 864 or len(prior) != 864:
        raise ValueError("All 864 frozen contrasts must be diagnosed")
    summary = {
        "contrasts": len(rows), "verified_batch_hashes": verified_batches,
        "original_flags_retained": sum(r["frozen_flagged"] for r in rows),
        "frozen_status_counts": dict(Counter(r["frozen_comparison_status"] for r in rows)),
        "zero_removed_cohort_rows": sum(r["removed_families"] == 0 for r in rows),
        "positive_removed_cohort_but_zero_early_loss_contributors": sum(r["zero_observed_removed_early_loss"] for r in rows),
        "nonstructural_rows_with_removed_cohort_but_zero_early_loss_contributors": sum(r["zero_observed_removed_early_loss"] and not r["known_structural_constant"] for r in rows),
        "zero_removed_contributors_by_frozen_status": dict(Counter(r["frozen_comparison_status"] for r in rows if r["zero_observed_removed_early_loss"] and not r["known_structural_constant"])),
        "nonstructural_high_denominator_rows_with_zero_removed_contributors": sum(r["zero_observed_removed_early_loss"] and not r["known_structural_constant"] and min(r["selected_early"], r["selected_late"]) >= 100 for r in rows),
    }
    for field in ("estimate_reproduction_absolute_error", "mcse_reproduction_absolute_error",
                  "disjoint_identity_absolute_error", "variance_identity_absolute_error"):
        summary["max_" + field] = max((r[field] for r in rows if r[field] is not None), default=None)
    report = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "status": "posthoc_diagnostic_flags_unchanged", "script_sha256": sha(__file__),
              "simulation_code_sha256": mc["code_sha256"], "comparator_code_sha256": comparison["comparator_sha256"],
              "primary_core_sha256": primary["core_sha256"], "primary_driver_sha256": primary["driver_sha256"],
              "monte_carlo_sha256": sha(args.mc), "comparison_sha256": sha(args.comparison), "primary_sha256": sha(args.primary),
              "fixtures": fixtures, "summary": summary,
              "design_timing": "Exploratory after both flags and their saved-root strata had been inspected. The scope was expanded to all 864 existing contrasts, with no new draws or thresholds.",
              "oracle_variance_computed": False,
              "limits": ["Zero observed removed-stratum loss is a sampling description, not proof of a population zero.",
                         "Expected weighted loss mass is not the expected binary count of affected founders.",
                         "The frozen selected-denominator>=100 rule does not guarantee adequate observations in influential nested-selection strata.",
                         "The zero-contributor pattern is not unique to flagged contrasts and does not itself clear or create a flag.",
                         "A prospective analytic second-moment oracle could assess asymptotic variance; it would not by itself establish exact finite-sample Gaussian coverage."],
              "contrasts": rows}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(text)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
