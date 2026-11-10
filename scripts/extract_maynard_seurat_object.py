"""Extract and audit saved Maynard RNA matrices without executing any R code.

Requires rdata==1.1.0, NumPy, pandas and SciPy. Source objects and per-cell
exports remain local; the aggregate audit is suitable for publication.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
import rdata
from scipy.sparse import csc_matrix, save_npz

from audit_maynard_malignant_membership import audit

ROOT = Path(__file__).resolve().parents[1]
OBJECT_SHA256 = "5458c714d2fbcd587dec6ed75e17ae5ae14573ae3b9c238b99f3dec9d27100e5"
OBJECT_URL = "https://drive.google.com/uc?export=download&id=11pWeBoGxjhE7VDHl9eaErB8_7seCPJ8V"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def dereference(obj):
    while obj is not None and obj.referenced_object is not None:
        obj = obj.referenced_object
    return obj


def attributes(obj, converter):
    """Traverse an R pairlist without converting unrelated S4 command slots."""
    result = {}
    obj = dereference(obj)
    while obj is not None and obj.info.type.name not in ("NIL", "NILVALUE"):
        if obj.info.type.name != "LIST" or obj.tag is None:
            raise ValueError("Expected a tagged R pairlist")
        key = str(converter.convert(obj.tag))
        if key in result:
            raise ValueError(f"Duplicate R attribute: {key}")
        result[key] = dereference(obj.value[0])
        obj = dereference(obj.value[1])
    return result


def sparse_matrix(obj, converter):
    slots = attributes(obj.attributes, converter)
    if list(converter.convert(slots["class"])) != ["dgCMatrix"]:
        raise ValueError("Expected a double compressed sparse column matrix")
    shape = tuple(int(x) for x in converter.convert(slots["Dim"]))
    names = [[str(x) for x in row] for row in converter.convert(slots["Dimnames"])]
    if [len(x) for x in names] != list(shape) or any(len(set(x)) != len(x) for x in names):
        raise ValueError("Nonunique or misaligned matrix dimensions")
    matrix = csc_matrix((np.asarray(converter.convert(slots["x"])),
                         np.asarray(converter.convert(slots["i"])),
                         np.asarray(converter.convert(slots["p"]))), shape=shape)
    matrix.check_format(full_check=True)
    if not matrix.has_canonical_format or not np.all(np.isfinite(matrix.data)) or np.any(matrix.data <= 0):
        raise ValueError("Unexpected sparse entries or duplicate coordinates")
    return matrix, names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--object", type=Path, default=ROOT / "tmp/egfr-resistance-2026-11-10/NI04_tumor_seurat_object.RData")
    parser.add_argument("--author-dir", type=Path, default=ROOT / "tmp/maynard-qc-2026-11-10")
    parser.add_argument("--main-metadata", type=Path, default=ROOT / "research/treatment-discovery/sources/maynard-2026-10-29/S01_metacells.csv")
    parser.add_argument("--neo-metadata", type=Path, default=ROOT / "research/treatment-discovery/sources/maynard-2026-10-29/neo-osi_metadata.csv")
    parser.add_argument("--extract-dir", type=Path, default=ROOT / "tmp/maynard-qc-2026-11-10/extracted")
    parser.add_argument("--output", type=Path, default=ROOT / "research/treatment-discovery/updates/2026-11-10/seurat-object-audit.json")
    args = parser.parse_args()
    object_hash = digest(args.object)
    if object_hash != OBJECT_SHA256:
        raise ValueError("Saved Seurat object hash differs from the pinned snapshot")
    membership_audit, membership = audit(args.main_metadata, args.neo_metadata, args.author_dir)
    expected = {x["cell_id"]: x for x in membership}
    parsed = rdata.parser.parse_file(args.object)
    # Some untagged source strings are UTF-8; ASCII fallback yields bytes rather
    # than text and prevents data.frame conversion. No source strings are altered.
    converter = rdata.conversion.SimpleConverter(default_encoding="utf-8")
    objects = attributes(parsed.object, converter)
    if list(objects) != ["tiss_subset_tumor2"]:
        raise ValueError("Unexpected R workspace objects")
    slots = attributes(objects["tiss_subset_tumor2"].attributes, converter)
    metadata = converter.convert(slots["meta.data"])
    if metadata.index.has_duplicates or metadata["cell_id"].duplicated().any():
        raise ValueError("Duplicate metadata cell ID")
    if list(metadata.index) != list(metadata["cell_id"]):
        raise ValueError("Metadata row names do not equal cell IDs")
    if set(metadata.index) != set(expected):
        raise ValueError("Object cell membership differs from saved author annotation")
    compared_fields = ["sample_name", "patient_id", "analysis", "Epithelial_cluster", "inferCNV_annotation"]
    for cell, row in metadata.iterrows():
        for key in compared_fields:
            if str(row[key]) != expected[cell][key]:
                raise ValueError(f"Object/source label mismatch for {cell}: {key}")
    assay_names = list(converter.convert(attributes(slots["assays"].attributes, converter)["names"]))
    if assay_names != ["RNA"]:
        raise ValueError("Unexpected assays; this extraction is scoped to RNA")
    rna = attributes(slots["assays"].value[0].attributes, converter)
    counts, count_names = sparse_matrix(rna["counts"], converter)
    data, data_names = sparse_matrix(rna["data"], converter)
    if count_names != data_names or set(metadata.index) != set(count_names[1]):
        raise ValueError("Metadata/count/data identifiers mismatch")
    source_metadata_positions_differing = sum(a != b for a, b in zip(metadata.index, count_names[1]))
    # The saved object's metadata and matrix columns have different orders.
    # Join by verified unique cell ID; never treat their row positions as a join.
    metadata = metadata.loc[count_names[1]].copy()
    if not np.array_equal(counts.indices, data.indices) or not np.array_equal(counts.indptr, data.indptr):
        raise ValueError("Count/data sparse coordinate mismatch")
    if np.any(counts.data != np.floor(counts.data)):
        raise ValueError("Noninteger count values")
    totals = np.asarray(counts.sum(axis=0)).ravel()
    max_total_error = float(np.max(np.abs(totals - np.asarray(metadata["nCount_RNA"], dtype=float))))
    if max_total_error != 0:
        raise ValueError("Matrix column totals do not match source metadata nCount_RNA")
    detected = np.diff(counts.indptr)
    if not np.array_equal(detected, np.asarray(metadata["nFeature_RNA"], dtype=int)):
        raise ValueError("Detected-gene counts differ from metadata nFeature_RNA")
    predicted = np.log1p(counts.data * 10000 / np.repeat(totals, detected))
    normalization_error = float(np.max(np.abs(predicted - data.data)))
    if normalization_error > 1e-10:
        raise ValueError("Saved RNA data is not the expected log1p(count/column_sum*10000)")
    args.extract_dir.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name, matrix in (("counts", counts), ("data", data)):
        path = args.extract_dir / f"{name}.npz"
        save_npz(path, matrix)
        artifacts.append({"file_name": path.name, "bytes": path.stat().st_size, "sha256": digest(path), "local_only": True})
    names_path = args.extract_dir / "dimnames.json"
    names_path.write_text(json.dumps({"genes": count_names[0], "cells": count_names[1]}) + "\n")
    meta_path = args.extract_dir / "metadata.csv"
    metadata.to_csv(meta_path)
    for path in (names_path, meta_path):
        artifacts.append({"file_name": path.name, "bytes": path.stat().st_size, "sha256": digest(path), "local_only": True})
    result = {
        "checked_date": "2026-11-10",
        "scope": "Source-object integrity, cell membership and expression representation audit; no signature score or biological association calculated",
        "source": {"file_name": args.object.name, "url": OBJECT_URL, "bytes": args.object.stat().st_size, "sha256": object_hash},
        "environment": {"python": platform.python_version(), **{name: importlib.metadata.version(name) for name in ("rdata", "numpy", "pandas", "scipy")}},
        "object_name": "tiss_subset_tumor2", "assay": "RNA", "genes": counts.shape[0], "cells": counts.shape[1], "nonzero_entries_per_slot": counts.nnz,
        "metadata_columns": len(metadata.columns), "samples": int(metadata["sample_name"].nunique()), "literal_patient_ids": int(metadata["patient_id"].nunique()),
        "checks": {"source_hash": "pass", "all_cell_ids_match_saved_author_annotation": True, "metadata_label_fields_compared": compared_fields, "label_mismatches": 0, "source_metadata_positions_differing_from_matrix_columns": source_metadata_positions_differing, "metadata_alignment": "Explicit unique cell-ID reindex to matrix columns; original source object unchanged", "exported_counts_data_metadata_order": "identical", "counts_data_sparse_coordinates": "identical", "counts_nonnegative_integers": True, "nCount_RNA_max_absolute_error": max_total_error, "nFeature_RNA_exact_match": True, "minimum_nCount_RNA": float(totals.min()), "minimum_nFeature_RNA": int(detected.min()), "saved_data_transformation": "natural log1p(count / cell total * 10000)", "maximum_absolute_normalization_error": normalization_error},
        "membership_pair_summary": membership_audit["pair_summary"],
        "local_extractions": artifacts,
        "limits": ["This verifies a saved author object against saved author tables, not independent biological annotation.", "Only the RNA counts and data slots are exported; scale.data, dimensionality reductions, graphs and command objects are not converted or executed.", "A successful technical audit does not establish clinical efficacy or a treatment-resistance mechanism."]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"genes": result["genes"], "cells": result["cells"], "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
