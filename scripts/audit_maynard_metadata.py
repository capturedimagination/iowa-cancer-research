#!/usr/bin/env python3
"""Audit supplied Maynard metadata; no expression analysis or model fitting.

Run from any directory. The default source is the immutable public snapshot.
Counts precede malignant-cell/sample QC and do not establish final eligibility.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "research/treatment-discovery/sources/maynard-2026-10-29"
EXPECTED_SHA256 = "b4f3f169516001e89bc8b3d8052e207331ff662ca6d236e1c2cf68eccffdf2a6"
FIELDS = [
    "patient_id", "driver_gene", "driver_mutation", "histolgy", "biopsy_date",
    "biopsy_site", "biopsy_time_status", "analysis", "treatment_history",
    "treatment_history_detail", "line_of_therapy", "treatment_type", "treatment",
    "treatment_start_date", "early_bx_day",
]


def summarize(samples: list[dict]) -> dict:
    states = collections.defaultdict(list)
    patients = collections.defaultdict(list)
    for sample in samples:
        states[sample["analysis"]].append(sample)
        patients[sample["patient_id"]].append(sample)
    pairs = []
    for patient, records in sorted(patients.items()):
        naive = [r for r in records if r["analysis"] == "naive"]
        residual = [r for r in records if r["analysis"] == "grouped_pr"]
        progression = [r for r in records if r["analysis"] == "grouped_pd"]
        if naive and residual:
            naive_sites = sorted({r["biopsy_site"] for r in naive})
            residual_sites = sorted({r["biopsy_site"] for r in residual})
            pairs.append({
                "patient_id": patient,
                "naive_samples": [r["sample_name"] for r in naive],
                "residual_group_samples": [r["sample_name"] for r in residual],
                "progression_group_samples": [r["sample_name"] for r in progression],
                "naive_biopsy_sites": naive_sites,
                "residual_biopsy_sites": residual_sites,
                "same_source_site_sets": naive_sites == residual_sites,
                "naive_biopsy_dates": [r["biopsy_date"] for r in naive],
                "residual_biopsy_dates": [r["biopsy_date"] for r in residual],
                "treatment_start_dates": sorted({r["treatment_start_date"] for r in naive + residual}),
            })
    return {
        "samples": len(samples),
        "patient_ids": len(patients),
        "state_samples": {k: len(v) for k, v in sorted(states.items())},
        "state_patient_ids": {
            k: len({r["patient_id"] for r in v}) for k, v in sorted(states.items())
        },
        "naive_residual_paired_patient_ids": len(pairs),
        "naive_residual_pair_records": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DIR / "S01_metacells.csv")
    parser.add_argument("--output", type=Path, default=SOURCE_DIR / "egfr-main-metadata-audit.json")
    parser.add_argument("--sample-csv", type=Path, default=SOURCE_DIR / "egfr-main-sample-audit.csv")
    args = parser.parse_args()
    raw = args.source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit("Source hash changed; review provenance before auditing a different snapshot.")
    with args.source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)
    by_sample = collections.defaultdict(list)
    for row in rows:
        by_sample[row["sample_name"]].append(row)
    samples = []
    for name, records in sorted(by_sample.items()):
        sample = {"sample_name": name, "metadata_cell_rows": len(records)}
        for field in FIELDS:
            values = {row[field] for row in records}
            if len(values) != 1:
                raise SystemExit(f"Within-sample conflict: {name}, {field}; resolve rather than selecting a value.")
            sample[field] = next(iter(values))
        samples.append(sample)
    egfr = [s for s in samples if s["driver_gene"] == "EGFR" and s["histolgy"] == "Adenocarcinoma"]
    common = [s for s in egfr if s["driver_mutation"] in ("del19", "L858R")]
    osimertinib = [s for s in common if s["treatment"] == "osimertinib"]
    output = {
        "source": args.source.resolve().relative_to(ROOT).as_posix() if args.source.resolve().is_relative_to(ROOT) else args.source.name, "source_sha256": digest,
        "source_bytes": len(raw), "columns": columns,
        "cell_rows": len(rows), "unique_cell_ids": len({r["cell_id"] for r in rows}),
        "sample_ids": len(samples), "patient_ids": len({r["patient_id"] for r in rows}),
        "scope": "Main metadata only, before analytic/malignant-cell QC; neo-osi subset not merged.",
        "filter_logic": {
            "EGFR_adenocarcinoma_any_variant": "driver_gene == 'EGFR' and histolgy == 'Adenocarcinoma'",
            "EGFR_adenocarcinoma_del19_or_L858R": "Previous filter and driver_mutation in ['del19', 'L858R']",
            "EGFR_adenocarcinoma_del19_or_L858R_treatment_exact_osimertinib": "Previous filter and treatment == 'osimertinib'",
            "pair": "Same patient_id has >=1 analysis == 'naive' and >=1 analysis == 'grouped_pr'; source labels preserved",
        },
        "metadata_defined_populations": {
            "EGFR_adenocarcinoma_any_variant": summarize(egfr),
            "EGFR_adenocarcinoma_del19_or_L858R": summarize(common),
            "EGFR_adenocarcinoma_del19_or_L858R_treatment_exact_osimertinib": summarize(osimertinib),
        },
        "limits": [
            "No mutation status inferred from RNA dropout; explicit metadata only.",
            "Repeated samples/cells are not independent patients.",
            "Source treatment_history == naive can describe first-line on-treatment samples; it is not a pretreatment filter.",
            "Source grouped_pr pools Early and PR; grouped_pd can include early primary nonresponse.",
            "No expression, signature, outcome score, model or final analytic eligibility was calculated.",
        ],
    }
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    with args.sample_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_name", "metadata_cell_rows"] + FIELDS)
        writer.writeheader()
        writer.writerows(egfr)
    print(json.dumps({"audit_json": str(args.output.resolve()), "sample_csv": str(args.sample_csv.resolve()),
                      "main_samples": len(samples), "main_patients": len({r['patient_id'] for r in rows}),
                      "common_variant_osimertinib": summarize(osimertinib)}))


if __name__ == "__main__":
    main()
