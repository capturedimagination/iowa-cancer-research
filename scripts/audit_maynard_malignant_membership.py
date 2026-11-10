"""Audit saved Maynard malignant labels against author sample counts.

This joins existing labels; it does not rerun clustering or infer malignancy.
Raw author files are kept in ignored local paths and are not redistributed.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shlex
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "de138c79bcfc2fa3a28c8a039a28ab560da78099"
BASE = f"https://raw.githubusercontent.com/czbiohub-sf/scell_lung_adenocarcinoma/{COMMIT}/"
AUTHOR_INPUTS = {
    "data_out/NI03/results/inferCNV_annotation.csv": "f2b0cad6786932cb32e2a6f5336de04c98f683d8b7d1c2d180b85b4bc46949b5",
    "data_out/IM06/Table_of_ALL_cell_types_by_sample.csv": "d1823a81fd131f1650c1faf5eed601165819cf6e24f6a23451d621e0fcd39abc",
}
MAIN_HASH = "b4f3f169516001e89bc8b3d8052e207331ff662ca6d236e1c2cf68eccffdf2a6"
NEO_HASH = "0517f6e845384b45f4521d8235dfd7b6b60da30a31bfd961797f5f2275155a76"
NAT_ALIASES = {"TH179_NAT": "TH179", "TH238_NAT": "TH238", "AZ008_NAT": "AZ008"}


def checked(path, expected):
    body = path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    if digest != expected:
        raise ValueError(f"Source hash changed: {path.name}")
    return {"file_name": path.name, "bytes": len(body), "sha256": digest}


def unique(rows, key):
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError(f"Duplicate {key}: {row[key]}")
        result[row[key]] = row
    return result


def records(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def sample_metadata(rows, fields):
    result = {}
    for row in rows:
        value = {key: row[key] for key in fields}
        sample = row["sample_name"]
        if sample in result and result[sample] != value:
            raise ValueError(f"Conflicting sample metadata: {sample}")
        result[sample] = value
    return result


def audit(main_path, neo_path, author_dir):
    sources = [checked(main_path, MAIN_HASH), checked(neo_path, NEO_HASH)]
    sources[0]["url"] = "https://drive.google.com/uc?export=download&id=12g84ooMTsWV58JWbp2ql8TMfgS4ct8as"
    sources[1]["url"] = "https://drive.google.com/uc?export=download&id=1iw89l70ufpuvWbfuMkbHYOEhvBYCFcX1"
    for relative, digest in AUTHOR_INPUTS.items():
        sources.append(checked(author_dir / relative, digest) | {"url": BASE + relative, "repository_path": relative})
    main = records(main_path)
    neo = records(neo_path)
    main_cells = unique(main, "cell_id")
    neo_plates = unique(neo, "plate")
    fields = ["sample_name", "patient_id", "histolgy", "driver_gene", "driver_mutation", "analysis", "biopsy_site"]
    main_samples = sample_metadata(main, fields + ["treatment"])
    neo_samples = sample_metadata(neo, fields + ["sample_type", "treatment_status"])
    if set(main_samples) & set(neo_samples):
        raise ValueError("Main/neo sample overlap")
    annotations = records(author_dir / "data_out/NI03/results/inferCNV_annotation.csv")
    unique(annotations, "cell_id")
    merged = []
    for row in annotations:
        cell = row["cell_id"]
        meta = main_cells.get(cell)
        origin = "main"
        if meta is None:
            # Seurat author IDs use well_plate; neo source metadata are plate-level.
            meta = neo_plates.get(cell.rsplit("_", 1)[-1])
            origin = "neo_osimertinib"
        if meta is None:
            raise ValueError(f"Unmapped annotation cell: {cell}")
        if row["inferCNV_annotation"] not in ("tumor", "nontumor"):
            raise ValueError("Unexpected malignant label")
        merged.append({key: meta[key] for key in fields} | row | {"source_subset": origin})
    tumor = [x for x in merged if x["inferCNV_annotation"] == "tumor"]
    if any(not x["Epithelial_cluster"].startswith("epithelial ") for x in tumor):
        raise ValueError("Tumor-labeled control found; cannot equate labels with malignant epithelial membership")
    tumor_counts = Counter(x["sample_name"] for x in tumor)
    # R write.table uses quoted whitespace fields and an extra row-name column.
    lines = (author_dir / "data_out/IM06/Table_of_ALL_cell_types_by_sample.csv").read_text().splitlines()
    header = ["row_name"] + shlex.split(lines[0])
    count_rows = []
    for line in lines[1:]:
        values = shlex.split(line)
        if len(values) != len(header):
            raise ValueError("Malformed author cell-count table")
        count_rows.append(dict(zip(header, values)))
    count_by_sample = unique(count_rows, "Var1")
    for sample, row in count_by_sample.items():
        if int(row["tumor"]) != tumor_counts[sample]:
            raise ValueError(f"Malignant count mismatch for {sample}")
    if set(tumor_counts) - set(count_by_sample):
        raise ValueError("Tumor sample missing from final count table")
    samples = main_samples | neo_samples
    if set(count_by_sample) - set(samples):
        raise ValueError("Final sample missing from metadata")
    total_cells = sum(int(v) for row in count_rows for k, v in row.items() if k not in ("row_name", "Var1"))
    final_ids = sorted({samples[s]["patient_id"] for s in count_by_sample})
    alias_collapsed = sorted({NAT_ALIASES.get(x, x) for x in final_ids})
    candidates = []
    for sample, meta in sorted(main_samples.items()):
        if meta["driver_gene"] == "EGFR" and meta["histolgy"] == "Adenocarcinoma" and meta["driver_mutation"] in ("del19", "L858R") and meta["treatment"] == "osimertinib":
            candidates.append(meta | {"in_final_author_count_table": sample in count_by_sample, "malignant_cells": tumor_counts[sample]})
    by_patient = defaultdict(list)
    for row in candidates:
        by_patient[row["patient_id"]].append(row)
    pairs = []
    for patient, rows in sorted(by_patient.items()):
        naive = [x for x in rows if x["analysis"] == "naive"]
        residual = [x for x in rows if x["analysis"] == "grouped_pr"]
        if naive and residual:
            pairs.append({"patient_id": patient, "naive_samples": naive, "residual_samples": residual,
                          "both_states_at_least_one_malignant_cell": any(x["malignant_cells"] >= 1 for x in naive) and any(x["malignant_cells"] >= 1 for x in residual),
                          "both_states_at_least_ten_malignant_cells_sensitivity": any(x["malignant_cells"] >= 10 for x in naive) and any(x["malignant_cells"] >= 10 for x in residual)})
    absent = [{"sample_name": s, "patient_id": main_samples[s]["patient_id"], "input_cell_rows": sum(x["sample_name"] == s for x in main), "reason": "Absent from final saved sample table; specific upstream exclusion step not assigned by this audit"} for s in sorted(set(main_samples) - set(count_by_sample))]
    result = {
        "checked_date": "2026-11-10", "repository_commit": COMMIT,
        "scope": "Deterministic join of existing author malignant labels and sample counts; no clustering, expression scoring or efficacy analysis",
        "sources": sources,
        "checks": {"source_hashes": "pass", "unique_keys": "pass", "annotation_metadata_join": "all_rows_matched", "per_sample_malignant_counts_vs_author_table": "all_49_match", "tumor_labels_restricted_to_epithelial_clusters": True},
        "annotation_counts": {"all_rows": len(annotations), "epithelial_rows": sum(x["Epithelial_cluster"].startswith("epithelial ") for x in annotations), "control_rows": sum(not x["Epithelial_cluster"].startswith("epithelial ") for x in annotations), "tumor_rows": len(tumor), "tumor_main": sum(x["source_subset"] == "main" for x in tumor), "tumor_neo": sum(x["source_subset"] == "neo_osimertinib" for x in tumor), "tumor_samples": len(tumor_counts)},
        "cohort_reconciliation": {"main_input_samples": len(main_samples), "neo_input_samples": len(neo_samples), "combined_input_samples": len(samples), "final_samples": len(count_rows), "final_main_samples": len(set(main_samples) & set(count_by_sample)), "final_neo_samples": len(set(neo_samples) & set(count_by_sample)), "final_cells": total_cells, "final_literal_patient_ids": final_ids, "final_literal_patient_id_count": len(final_ids), "NAT_alias_crosswalk": NAT_ALIASES, "patient_count_after_explicit_NAT_alias_crosswalk": len(alias_collapsed), "crosswalk_basis": "Identifier suffixes and matched source resection/sample metadata; donor alias interpretation, not a new biological assignment. Preserve source IDs.", "excluded_main_samples": absent},
        "main_osimertinib_candidate_sample_counts": candidates,
        "main_osimertinib_pairs": pairs,
        "pair_summary": {"metadata_candidate_pairs": len(pairs), "pairs_with_any_malignant_cells_in_both_states": sum(x["both_states_at_least_one_malignant_cell"] for x in pairs), "pairs_with_at_least_ten_malignant_cells_per_state_sensitivity": sum(x["both_states_at_least_ten_malignant_cells_sensitivity"] for x in pairs)},
        "limitations": ["The >=10 malignant-cell threshold is an audit sensitivity, not the author's whole-sample >10-cell QC rule or a validated power threshold.", "The published malignant labels are accepted for reproduction; inferCNV and clustering are not independently re-estimated.", "The neo-osimertinib subset contributes to the same published discovery dataset and is not independent validation.", "A single cell at baseline does not support a robust population-level paired expression estimate; cells are not independent patient replicates.", "Zero malignant cells in this saved object is a data-availability statement, not evidence of no tumor in a patient."]
    }
    return result, tumor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-dir", type=Path, default=ROOT / "tmp/maynard-qc-2026-11-10")
    parser.add_argument("--main-metadata", type=Path, default=ROOT / "research/treatment-discovery/sources/maynard-2026-10-29/S01_metacells.csv")
    parser.add_argument("--neo-metadata", type=Path, default=ROOT / "research/treatment-discovery/sources/maynard-2026-10-29/neo-osi_metadata.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "research/treatment-discovery/updates/2026-11-10/malignant-membership-audit.json")
    parser.add_argument("--fetch-author-files", action="store_true", help="Retrieve the two pinned public author tables to --author-dir if absent")
    parser.add_argument("--membership-output", type=Path, help="Optional local-only per-cell join; place under ignored tmp/")
    args = parser.parse_args()
    if args.fetch_author_files:
        for relative, digest in AUTHOR_INPUTS.items():
            path = args.author_dir / relative
            if not path.exists():
                body = urllib.request.urlopen(BASE + relative, timeout=30).read()
                if hashlib.sha256(body).hexdigest() != digest:
                    raise ValueError(f"Downloaded source hash changed: {relative}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
    result, tumor = audit(args.main_metadata, args.neo_metadata, args.author_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if args.membership_output:
        args.membership_output.parent.mkdir(parents=True, exist_ok=True)
        fields = ["cell_id", "sample_name", "patient_id", "analysis", "source_subset", "Epithelial_cluster", "inferCNV_annotation"]
        with args.membership_output.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(sorted(tumor, key=lambda x: x["cell_id"]))
    print(json.dumps({"checks": result["checks"], "annotation_counts": result["annotation_counts"], "pair_summary": result["pair_summary"]}, indent=2))


if __name__ == "__main__":
    main()
