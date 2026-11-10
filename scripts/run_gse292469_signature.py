"""Patient-level descriptive reproduction of a fixed published lung signature.

Inputs are public, deidentified deposited data obtained separately; nothing is
downloaded here. Read the frozen plan and source-specific terms before running.
Sparse UMI data are processed in column blocks, without loading the full matrix.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

ROOT = Path(__file__).resolve().parents[1]
UPDATE = ROOT / "research/treatment-discovery/updates/2026-11-10"
GENES = ["SFTPC", "SFTPB", "SFTPD", "PGC", "CLDN18", "AQP4", "SCGB3A1",
         "ABCA3", "GATA6", "NKX2-1", "SFTA3", "IGFBP2", "HOPX", "NAPSA",
         "FOXA2", "AGER", "LAMP1"]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def decode(values):
    return np.array([x.decode("utf-8") if isinstance(x, bytes) else str(x)
                     for x in values], dtype=object)


def auc(a, b):
    """Probability MRD a exceeds TN b; half credit for exact ties."""
    return float(((a[:, None] > b).sum() + .5 * (a[:, None] == b).sum())
                 / (len(a) * len(b)))


def compare(rows, score="score_mean", seed=20261110):
    a = np.array([r[score] for r in rows if r["state"] == "MRD"], dtype=float)
    b = np.array([r[score] for r in rows if r["state"] == "TN"], dtype=float)
    out = {"n_MRD": len(a), "n_TN": len(b), "sample_ids": [r["sample_id"] for r in rows]}
    if min(len(a), len(b)) < 2:
        return {**out, "status": "insufficient_comparison"}
    rng = np.random.default_rng(seed)
    draws = np.empty((10000, 2))
    for i in range(len(draws)):
        aa = rng.choice(a, len(a), replace=True)
        bb = rng.choice(b, len(b), replace=True)
        draws[i] = [aa.mean() - bb.mean(), auc(aa, bb)]
    rank = auc(a, b)
    return {**out, "status": "descriptive_only", "mean_MRD": float(a.mean()),
            "mean_TN": float(b.mean()), "median_MRD": float(np.median(a)),
            "median_TN": float(np.median(b)), "mean_difference_MRD_minus_TN": float(a.mean()-b.mean()),
            "median_difference_MRD_minus_TN": float(np.median(a)-np.median(b)),
            "auc_MRD_above_TN": rank, "cliffs_delta": 2*rank-1,
            "bootstrap_mean_difference_95pct": np.quantile(draws[:, 0], [.025, .975]).tolist(),
            "bootstrap_auc_95pct": np.quantile(draws[:, 1], [.025, .975]).tolist(),
            "bootstrap": {"unit": "patient/specimen", "resamples": 10000,
                          "stratified_by": "state", "seed": seed,
                          "interval": "conditional percentile; unmeasured confounding not included"}}


def canonical_variant(label):
    return bool({x.strip() for x in re.split(r"[,;]", label)} & {"L858R", "E746_A750del"})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--h5", type=Path, required=True)
    ap.add_argument("--cell-metadata", type=Path, required=True)
    ap.add_argument("--sample-metadata", type=Path, required=True)
    ap.add_argument("--source-manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    assert np.__version__ == "2.3.5", "Use the frozen NumPy 2.3.5 environment"
    freeze = json.loads((UPDATE / "analysis-plan-freeze.json").read_text())
    assert digest(ROOT / freeze["plan_path"]) == freeze["plan_sha256"], "Analysis plan changed"
    signature = json.loads((UPDATE / "signature-verification.json").read_text())
    assert signature["status"] == "exact_published_gene_set_verified"
    assert signature["signature"]["set_equal"] and set(signature["signature"]["genes_supplement_order"]) == set(GENES)
    manifest = json.loads(args.source_manifest.read_text())
    verified = {}
    for p in (args.h5, args.cell_metadata, args.sample_metadata):
        expected = next(x for x in manifest["files"] if x["filename"] == p.name)
        assert p.stat().st_size == expected["bytes"], f"Size mismatch: {p.name}"
        h = digest(p)
        assert h == expected["sha256"], f"Hash mismatch: {p.name}"
        verified[p.name] = h
    meta = pd.read_csv(args.cell_metadata, sep="\t", dtype={"cell_id": str, "sample_id": str, "core_id": str})
    required = {"cell_id", "sample_id", "core_id", "time_point", "is_tumor_cell",
                "scDblFinder.class", "nCount_RNA", "nFeature_RNA"}
    assert required <= set(meta.columns), "Missing cell metadata columns"
    assert not meta.cell_id.duplicated().any(), "Duplicate cell IDs"
    sample_doc = json.loads(args.sample_metadata.read_text())
    samples = {s["sample_id"]: s for s in sample_doc["samples"]}
    assert len(samples) == len(sample_doc["samples"]), "Duplicate sample IDs"
    assert set(samples) == set(meta.sample_id), "Sample metadata mismatch"
    for sid, group in meta.groupby("sample_id"):
        assert set(group.time_point) == {samples[sid]["state"]}, f"State conflict: {sid}"
    tumor = meta.is_tumor_cell.astype(str).str.lower()
    assert set(tumor) <= {"true", "false"}, "Unknown tumor flag"
    use = tumor.eq("true") & meta["scDblFinder.class"].eq("singlet")
    scores = np.full(len(meta), np.nan)
    total_mismatches = feature_mismatches = 0
    with h5py.File(args.h5, "r") as h:
        m = h["matrix"]
        barcodes = decode(m["barcodes"][:])
        assert len(barcodes) == len(set(barcodes)) == len(meta), "Matrix cell count/uniqueness mismatch"
        assert set(barcodes) == set(meta.cell_id), "Nonmatching cell identifiers"
        meta = meta.set_index("cell_id").loc[barcodes].reset_index()
        use = meta.is_tumor_cell.astype(str).str.lower().eq("true") & meta["scDblFinder.class"].eq("singlet")
        names = decode(m["features/name"][:])
        feature_ids = decode(m["features/id"][:])
        assert len(feature_ids) == len(names), "Feature ID/symbol dimensions disagree"
        types = decode(m["features/feature_type"][:])
        assert set(types) == {"Gene Expression"}, "Non-gene features require a versioned normalization decision"
        shape = tuple(int(x) for x in m["shape"][:])
        assert shape == (len(names), len(meta)), "Matrix dimensions disagree"
        positions = []
        for gene in GENES:
            hit = np.where(names == gene)[0]
            assert len(hit) == 1, f"Absent or ambiguous target gene: {gene}"
            positions.append(int(hit[0]))
        target_features = [{"symbol":g, "feature_id":str(feature_ids[i]), "row":i} for g,i in zip(GENES, positions)]
        assert len({x["feature_id"] for x in target_features}) == len(GENES), "Ambiguous target feature IDs"
        assert m["indptr"].dtype.kind in "iu" and m["indices"].dtype.kind in "iu", "Sparse indices must be integers"
        ptr = m["indptr"][:].astype(np.int64)
        assert ptr.shape == (len(meta)+1,) and ptr[0] == 0 and np.all(np.diff(ptr) >= 0)
        assert ptr[-1] == len(m["data"]) == len(m["indices"])
        for lo in range(0, len(meta), 4096):
            hi = min(lo + 4096, len(meta))
            start, end = int(ptr[lo]), int(ptr[hi])
            values = m["data"][start:end]
            indices = m["indices"][start:end]
            assert np.isfinite(values).all() and (values >= 0).all() and np.equal(values, np.floor(values)).all(), "Non-UMI values"
            assert (indices >= 0).all() and (indices < shape[0]).all(), "Out-of-bounds gene index"
            mat = csc_matrix((values.astype(np.float64), indices, ptr[lo:hi+1]-start), shape=(shape[0], hi-lo))
            assert mat.has_canonical_format, "Duplicate or unsorted sparse gene indices"
            totals = np.asarray(mat.sum(axis=0)).ravel()
            features = np.asarray((mat > 0).sum(axis=0)).ravel()
            expected_total = meta.nCount_RNA.iloc[lo:hi].to_numpy(dtype=float)
            expected_features = meta.nFeature_RNA.iloc[lo:hi].to_numpy(dtype=float)
            total_mismatches += int(np.count_nonzero(totals != expected_total))
            feature_mismatches += int(np.count_nonzero(features != expected_features))
            assert (totals > 0).all(), "Zero library denominator"
            targets = mat[positions, :].toarray()
            score = np.log1p(targets * (10000.0/totals)[None, :]).mean(axis=0)
            keep = use.iloc[lo:hi].to_numpy()
            scores[lo:hi] = np.where(keep, score, np.nan)
            print(f"Validated/scored {hi}/{len(meta)} nuclei", flush=True)
        assert total_mismatches == 0 and feature_mismatches == 0, "Deposited count QC mismatch; no results released"
    meta["signature_score"] = scores
    rows = []
    for sid in sorted(samples):
        s = samples[sid]
        cells = meta[(meta.sample_id == sid) & meta.signature_score.notna()]
        core = cells.groupby("core_id").signature_score.agg(["count", "mean"])
        n = len(cells)
        assert n == s["malignant_nuclei"], f"Malignant count mismatch: {sid}"
        reasons = []
        if s["state"] not in {"TN", "MRD"}: reasons.append("state_not_primary")
        if s["histology"] != "LUAD": reasons.append("histology_not_LUAD")
        if n < 20: reasons.append("fewer_than_20_malignant_nuclei")
        row = {k:s[k] for k in ["sample_id", "state", "histology", "tissue", "procedure", "stage", "genotype", "kit_series_implied", "kit_conflict"]}
        row.update(malignant_nuclei=n, primary_eligible=not reasons, exclusion_reasons=reasons,
                   score_mean=float(cells.signature_score.mean()) if n else None,
                   score_equal_core_mean=float(core["mean"].mean()) if n else None,
                   cores={str(k): {"n":int(v["count"]), "score_mean":float(v["mean"])} for k,v in core.iterrows()},
                   canonical_variant=canonical_variant(s["genotype"]))
        rows.append(row)
    primary = [r for r in rows if r["primary_eligible"]]
    subsets = {"primary": primary,
               "at_least_100_malignant_nuclei": [r for r in primary if r["malignant_nuclei"] >= 100],
               "lung_site": [r for r in primary if r["tissue"] == "Lung"],
               "canonical_E746_A750del_or_L858R": [r for r in primary if r["canonical_variant"]]}
    for kit in ("v3.1", "v4"):
        subsets[f"series_implied_kit_{kit}"] = [r for r in primary if r["kit_series_implied"] == kit]
    comparisons = {key: compare(value) for key,value in subsets.items()}
    comparisons["equal_core_weighting"] = compare(primary, score="score_equal_core_mean")
    cross = {}
    for field in ("tissue", "procedure", "stage", "kit_series_implied", "genotype"):
        cross[field] = {state: dict(Counter(r[field] for r in primary if r["state"] == state)) for state in ("TN", "MRD")}
    result = {"analysis_date_utc": datetime.now(timezone.utc).isoformat(), "source_accession": "GSE292469",
              "plan_sha256": freeze["plan_sha256"], "input_sha256": verified,
              "code_sha256": digest(Path(__file__)), "genes": GENES, "target_features": target_features,
              "qc": {"nuclei":len(meta), "sample_ids":len(samples), "features":shape[0],
                     "malignant_nuclei":int(use.sum()), "count_mismatches":total_mismatches,
                     "feature_count_mismatches":feature_mismatches, "exact_cell_join":True},
              "comparisons": comparisons, "primary_confounder_crosstabs":cross,
              "limitations": ["Unmatched patients; state, stage, site, sampling procedure and library kit are confounded.",
                              "Series/GSM library-kit descriptions conflict; kit sensitivity is conditional on series annotation.",
                              "Raw UMI normalization differs from SoupX-corrected expression in the cohort authors' plotting pipeline.",
                              "This is a descriptive molecular-state comparison, not a treatment effect or clinical prediction.",
                              "No cell-level inferential replication, trained model, optimized threshold or cure claim."],
              "environment": {"numpy": np.__version__, "pandas": pd.__version__, "h5py": h5py.__version__}}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    (args.out / "sample-scores.json").write_text(json.dumps(rows, indent=2, allow_nan=False)+"\n")
    print(json.dumps(comparisons["primary"], indent=2), flush=True)


if __name__ == "__main__":
    main()
