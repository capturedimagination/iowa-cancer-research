"""Independent arithmetic checks without importing the main scoring script.

Read raw HDF5 columns for prespecified TN4, MRD6 and MRD2 malignant singlets.
Use Python scalar math for cell/sample means and comparison arithmetic.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "research/treatment-discovery/sources/egfr-resistance-2026-11-10"
RESULTS = ROOT / "research/treatment-discovery/results/gse292469-alveolar-2026-11-10"
UPDATES = ROOT / "research/treatment-discovery/updates/2026-11-10"
H5_SHA256 = "60c6aab4dd2b2baa5b5deb163aca7aff1bfc180bb24c6c3f5aa02c445bf7872e"
SPOT_SAMPLES = ("TN4", "MRD6", "MRD2")


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(16 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def text(x):
    return x.decode("utf-8") if isinstance(x, bytes) else str(x)


def close(a, b, label, tolerance=1e-12):
    if not math.isclose(a, b, rel_tol=0, abs_tol=tolerance):
        raise ValueError(f"Independent calculation disagrees: {label}: {a} vs {b}")


def raw_checks(h5_path, metadata_path, genes):
    h5_hash = sha256(h5_path)
    if h5_hash != H5_SHA256:
        raise ValueError("Raw HDF5 hash changed")
    selected = {}
    all_counts = Counter()
    with gzip.open(metadata_path, "rt", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["is_tumor_cell"].lower() == "true" and row["scDblFinder.class"] == "singlet":
                all_counts[row["sample_id"]] += 1
                if row["sample_id"] in SPOT_SAMPLES:
                    if row["cell_id"] in selected:
                        raise ValueError("Duplicate selected metadata cell")
                    selected[row["cell_id"]] = row
    by_core = defaultdict(list)
    cell_checks = []
    with h5py.File(h5_path, "r") as handle:
        matrix = handle["matrix"]
        symbols = [text(x) for x in matrix["features/name"][:]]
        gene_rows = {symbols.index(gene) for gene in genes}
        if any(symbols.count(gene) != 1 for gene in genes) or len(gene_rows) != 17:
            raise ValueError("Target symbols do not map uniquely")
        cell_positions = {text(cell): i for i, cell in enumerate(matrix["barcodes"][:]) if text(cell) in selected}
        if set(cell_positions) != set(selected):
            raise ValueError("Selected metadata/HDF5 cells differ")
        pointers = matrix["indptr"][:]
        for cell, column in sorted(cell_positions.items(), key=lambda item: item[1]):
            lo, hi = int(pointers[column]), int(pointers[column + 1])
            indices = matrix["indices"][lo:hi]
            values = matrix["data"][lo:hi]
            observed = [float(v) for v in values]
            if any(not math.isfinite(v) or v < 0 or v != int(v) for v in observed):
                raise ValueError("Invalid UMI count in direct check")
            library = sum(int(v) for v in observed)
            row = selected[cell]
            if library != int(row["nCount_RNA"]):
                raise ValueError("Direct UMI sum disagrees with metadata")
            if sum(v > 0 for v in observed) != int(row["nFeature_RNA"]):
                raise ValueError("Direct detected-feature count disagrees with metadata")
            if len(set(int(x) for x in indices)) != len(indices):
                raise ValueError("Duplicate sparse row in direct check")
            # Missing target entries contribute zero, while the fixed denominator
            # remains 17. This calculation uses neither SciPy nor the score code.
            score = math.fsum(math.log1p(10000 * int(v) / library)
                              for i, v in zip(indices, values) if int(i) in gene_rows) / 17
            by_core[(row["sample_id"], row["core_id"])].append(score)
            if len(cell_checks) < 6:
                cell_checks.append({"cell_id": cell, "sample_id": row["sample_id"], "core_id": row["core_id"], "library_UMI": library, "signature_score": score})
    out = {}
    for sample in SPOT_SAMPLES:
        cores = {core: vals for (sid, core), vals in by_core.items() if sid == sample}
        combined = [v for values in cores.values() for v in values]
        if len(combined) != all_counts[sample]:
            raise ValueError("Direct-check malignant count mismatch")
        out[sample] = {"malignant_nuclei": len(combined), "score_mean": statistics.fmean(combined),
                       "score_equal_core_mean": statistics.fmean(statistics.fmean(vals) for vals in cores.values()),
                       "cores": {core: {"n": len(vals), "score_mean": statistics.fmean(vals)} for core, vals in cores.items()}}
    return {"h5_sha256": h5_hash, "cell_metadata_sha256": sha256(metadata_path), "sample_checks": out,
            "first_six_direct_cell_checks": cell_checks, "all_malignant_counts": dict(all_counts)}


def pairwise_auc(mrd, tn):
    wins = ties = 0
    for a in mrd:
        for b in tn:
            wins += a > b
            ties += a == b
    pairs = len(mrd) * len(tn)
    return (wins + ties / 2) / pairs, wins, ties, pairs


def quantile(values, p):
    values = sorted(values)
    rank = (len(values) - 1) * p
    lower = math.floor(rank)
    upper = math.ceil(rank)
    return values[lower] + (rank - lower) * (values[upper] - values[lower])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SOURCES)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    parser.add_argument("--raw-cache", type=Path, default=ROOT / "tmp/gse292469-independent-raw-checks.json")
    parser.add_argument("--reuse-raw-cache", action="store_true", help="Reuse prior raw checks after verifying source size/mtime and metadata hash; prior HDF5 hash stays dated to that check")
    args = parser.parse_args()
    h5_path = args.source_dir / "GSE292469_counts.h5"
    meta_path = args.source_dir / "GSE292469_cell_metadata.tsv.gz"
    signature = json.loads((UPDATES / "signature-verification.json").read_text())
    genes = signature["signature"]["genes_supplement_order"]
    if len(genes) != len(set(genes)) or len(genes) != 17:
        raise ValueError("Independent signature list is not 17 unique genes")
    if args.reuse_raw_cache:
        raw = json.loads(args.raw_cache.read_text())
        if raw["h5_sha256"] != H5_SHA256 or raw["h5_size"] != h5_path.stat().st_size or raw["h5_mtime_ns"] != h5_path.stat().st_mtime_ns or raw["cell_metadata_sha256"] != sha256(meta_path):
            raise ValueError("Sources changed since raw independent checks")
    else:
        raw = raw_checks(h5_path, meta_path, genes)
        raw["h5_size"] = h5_path.stat().st_size
        raw["h5_mtime_ns"] = h5_path.stat().st_mtime_ns
        args.raw_cache.parent.mkdir(parents=True, exist_ok=True)
        args.raw_cache.write_text(json.dumps(raw, indent=2) + "\n")
    print(json.dumps(raw["sample_checks"], indent=2), flush=True)
    result_path = args.results_dir / "results.json"
    score_path = args.results_dir / "sample-scores.json"
    if not result_path.exists() or not score_path.exists():
        print("Raw checks saved; published results not yet present. Rerun with --reuse-raw-cache.")
        return
    results = json.loads(result_path.read_text())
    scores = json.loads(score_path.read_text())
    rows = {x["sample_id"]: x for x in scores}
    if len(rows) != len(scores):
        raise ValueError("Duplicate specimen scores")
    for sid, row in rows.items():
        if row["malignant_nuclei"] != raw["all_malignant_counts"].get(sid, 0):
            raise ValueError("Reported malignant count differs from independent metadata count")
    for sid, check in raw["sample_checks"].items():
        for field in ("score_mean", "score_equal_core_mean"):
            close(check[field], rows[sid][field], sid + ":" + field)
        for core, value in check["cores"].items():
            if value["n"] != rows[sid]["cores"][core]["n"]:
                raise ValueError("Core count mismatch")
            close(value["score_mean"], rows[sid]["cores"][core]["score_mean"], core)
    primary = [x for x in scores if x["state"] in ("TN", "MRD") and x["histology"] == "LUAD" and x["malignant_nuclei"] >= 20]
    if {x["sample_id"] for x in primary} != {x["sample_id"] for x in scores if x["primary_eligible"]}:
        raise ValueError("Reported eligibility differs from independent plan interpretation")
    subsets = {
        "primary": primary,
        "at_least_100_malignant_nuclei": [x for x in primary if x["malignant_nuclei"] >= 100],
        "lung_site": [x for x in primary if x["tissue"] == "Lung"],
        "canonical_E746_A750del_or_L858R": [x for x in primary if any(token.strip() in ("E746_A750del", "L858R") for token in re.split("[,;]", x["genotype"]))],
        "series_implied_kit_v3.1": [x for x in primary if x["kit_series_implied"] == "v3.1"],
        "series_implied_kit_v4": [x for x in primary if x["kit_series_implied"] == "v4"],
        "equal_core_weighting": primary,
    }
    comparisons = {}
    for label, subset in subsets.items():
        reported = results["comparisons"][label]
        if set(reported["sample_ids"]) != {x["sample_id"] for x in subset}:
            raise ValueError(f"Sensitivity membership differs: {label}")
        key = "score_equal_core_mean" if label == "equal_core_weighting" else "score_mean"
        mrd = [x[key] for x in subset if x["state"] == "MRD"]
        tn = [x[key] for x in subset if x["state"] == "TN"]
        if (len(mrd), len(tn)) != (reported["n_MRD"], reported["n_TN"]):
            raise ValueError("Comparison patient count mismatch")
        if min(len(mrd), len(tn)) < 2:
            if reported["status"] != "insufficient_comparison":
                raise ValueError("Insufficient subset incorrectly compared")
            comparisons[label] = {"n_MRD": len(mrd), "n_TN": len(tn), "status": "insufficient_comparison_verified"}
            continue
        rank, wins, ties, pairs = pairwise_auc(mrd, tn)
        difference = statistics.fmean(mrd) - statistics.fmean(tn)
        close(rank, reported["auc_MRD_above_TN"], label + " AUC")
        close(difference, reported["mean_difference_MRD_minus_TN"], label + " mean difference")
        close(statistics.median(mrd)-statistics.median(tn), reported["median_difference_MRD_minus_TN"], label + " median difference")
        close(2*rank-1, reported["cliffs_delta"], label + " Cliff's delta")
        comparisons[label] = {"n_MRD": len(mrd), "n_TN": len(tn), "wins": wins, "ties": ties, "pairs": pairs,
                              "auc": rank, "mean_difference": difference, "status": "arithmetic_and_membership_match"}
    # Independent implementation of the primary bootstrap using integer index
    # draws, scalar math and manually interpolated percentile quantiles.
    mrd = [x["score_mean"] for x in primary if x["state"] == "MRD"]
    tn = [x["score_mean"] for x in primary if x["state"] == "TN"]
    rng = np.random.default_rng(20261110)
    means, ranks = [], []
    for _ in range(10000):
        a = [mrd[int(i)] for i in rng.integers(0, len(mrd), size=len(mrd))]
        b = [tn[int(i)] for i in rng.integers(0, len(tn), size=len(tn))]
        means.append(statistics.fmean(a)-statistics.fmean(b))
        ranks.append(pairwise_auc(a, b)[0])
    boot = {"mean_difference_95pct": [quantile(means, p) for p in (.025, .975)], "auc_95pct": [quantile(ranks, p) for p in (.025, .975)]}
    for i in range(2):
        close(boot["mean_difference_95pct"][i], results["comparisons"]["primary"]["bootstrap_mean_difference_95pct"][i], "bootstrap mean")
        close(boot["auc_95pct"][i], results["comparisons"]["primary"]["bootstrap_auc_95pct"][i], "bootstrap AUC")
    final = {"review_date": "2026-11-10", "review_type": "independent implementation; no main scoring functions imported or called",
             "review_code_sha256": sha256(Path(__file__)), "results_sha256": sha256(result_path), "sample_scores_sha256": sha256(score_path),
             "raw_input_sha256": {"GSE292469_counts.h5": raw["h5_sha256"], "GSE292469_cell_metadata.tsv.gz": raw["cell_metadata_sha256"]},
             "raw_direct_sample_checks": raw["sample_checks"], "raw_nuclei_checked": sum(x["malignant_nuclei"] for x in raw["sample_checks"].values()),
             "all_sample_malignant_counts": "match", "comparisons": comparisons, "independent_primary_bootstrap": boot,
             "absolute_tolerance": 1e-12, "status": "pass",
             "limits": ["Raw expression was independently recalculated for three preselected specimens, not all nuclei.", "All reported sensitivity membership, point estimates and the primary bootstrap were independently checked.", "This is arithmetic and design review, not external peer review or validation of causal or clinical efficacy claims."]}
    (args.results_dir / "independent-review.json").write_text(json.dumps(final, indent=2) + "\n")
    print(json.dumps({"status": "pass", "raw_nuclei_checked": final["raw_nuclei_checked"], "primary": comparisons["primary"], "bootstrap": boot}, indent=2))


if __name__ == "__main__":
    main()
