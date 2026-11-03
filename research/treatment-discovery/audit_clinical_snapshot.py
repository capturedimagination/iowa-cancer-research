#!/usr/bin/env python3
"""Audit the frozen public NSCLC clinical tables without fitting a model."""
from __future__ import annotations

import collections
import csv
import hashlib
import io
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
SNAPSHOT = BASE / "data/nsclc_pd1_msk_2018/2026-10-29"


def read_table(name):
    path = SNAPSHOT / name
    lines = path.read_text().splitlines()
    assert len(lines) > 5 and all(line.startswith("#") for line in lines[:4])
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[4:])), delimiter="\t"))
    assert all(None not in row for row in rows), "Unexpected extra columns"
    return rows, [line[1:].split("\t") for line in lines[:4]]


def duplicates(rows, field):
    return sorted(k for k, count in collections.Counter(r[field] for r in rows).items() if count > 1)


def main():
    manifest = json.loads((SNAPSHOT / "download-manifest.json").read_text())
    checks = []
    for item in manifest["files"]:
        contents = (SNAPSHOT / item["filename"]).read_bytes()
        digest = hashlib.sha256(contents).hexdigest()
        assert digest == item["sha256"], item["filename"]
        assert len(contents) == item["bytes"], item["filename"]
        assert not contents.startswith(b"version https://git-lfs.github.com/spec/v1")
        checks.append({"filename": item["filename"], "sha256_verified": True, "bytes": len(contents)})

    patient, patient_meta = read_table("data_clinical_patient.txt")
    sample, sample_meta = read_table("data_clinical_sample.txt")
    original, _ = read_table("data_clinical_sample-original-2018-04-23.txt")
    for rows, fields in [(patient, ["PATIENT_ID"]), (sample, ["PATIENT_ID", "SAMPLE_ID"])]:
        for field in fields:
            assert not duplicates(rows, field), (field, duplicates(rows, field))
            assert all(r[field] for r in rows), f"Missing {field}"
    assert len(patient) == len(sample) == len(original) == 240
    patients = {r["PATIENT_ID"]: r for r in patient}
    original_by_sample = {r["SAMPLE_ID"]: r for r in original}
    assert set(patients) == {r["PATIENT_ID"] for r in sample}
    assert set(original_by_sample) == {r["SAMPLE_ID"] for r in sample}
    assert {r["DURABLE_CLINICAL_BENEFIT"] for r in patient} == {"YES", "NO", "NE"}
    assert {r["PFS_STATUS"] for r in patient} == {"0:Not Progressed", "1:Progressed"}

    qc = {
        "study_id": "nsclc_pd1_msk_2018",
        "snapshot_date": "2026-10-29",
        "operation": "Schema, provenance, identifier and missingness audit only; no model fitted",
        "hash_checks": checks,
        "total_source_bytes": sum(x["bytes"] for x in checks),
        "patient_rows": len(patient),
        "sample_rows": len(sample),
        "unique_patients": len(patients),
        "unique_samples": len({r["SAMPLE_ID"] for r in sample}),
        "patient_sample_join": "one_to_one",
        "unmatched_patients": [],
        "duplicate_patient_ids": [],
        "duplicate_sample_ids": [],
        "dcb_counts": dict(collections.Counter(r["DURABLE_CLINICAL_BENEFIT"] for r in patient)),
        "pfs_status_counts": dict(collections.Counter(r["PFS_STATUS"] for r in patient)),
        "gene_panel_counts": dict(collections.Counter(r["GENE_PANEL"] for r in sample)),
        "histology_counts": dict(collections.Counter(r["ONCOTREE_CODE"] for r in sample)),
        "treatment_counts": dict(collections.Counter(r["TREATMENT_TYPE"] for r in patient)),
        "trial_commercial_counts": dict(collections.Counter(r["IRB"] for r in patient)),
        "missing_counts": {
            kind: {field: sum(r[field] == "" for r in rows) for field in rows[0]}
            for kind, rows in [("patient", patient), ("sample", sample)]
        },
        "pdl1_nonmissing": sum(bool(r["PDL1_SCORE"]) for r in sample),
        "pdl1_nonmissing_dcb_counts": dict(collections.Counter(
            patients[r["PATIENT_ID"]]["DURABLE_CLINICAL_BENEFIT"] for r in sample if r["PDL1_SCORE"]
        )),
        "original_2018_mutation_rate_changed_values": sum(
            r["MUTATION_RATE"] != original_by_sample[r["SAMPLE_ID"]]["MUTATION_RATE"] for r in sample
        ),
        "original_2018_has_tmb_nonsynonymous": "TMB_NONSYNONYMOUS" in original[0],
        "current_tmb_columns_differ_rows": sum(
            r["MUTATION_RATE"] != r["TMB_NONSYNONYMOUS"] for r in sample
        ),
        "ne_all_censored_under_six_months": all(
            r["PFS_STATUS"] == "0:Not Progressed" and float(r["PFS_MONTHS"]) < 6
            for r in patient if r["DURABLE_CLINICAL_BENEFIT"] == "NE"
        ),
    }
    assert qc["dcb_counts"] == {"YES": 69, "NO": 158, "NE": 13}
    assert qc["original_2018_mutation_rate_changed_values"] == 0
    (BASE / "clinical-pilot-qc.json").write_text(json.dumps(qc, indent=2) + "\n")

    notes = {
        "PATIENT_ID": "Public pseudonymous participant key; retain as text. Repeated MSK cohorts may share patients.",
        "SAMPLE_ID": "Public specimen key; do not infer timing relative to treatment from suffixes.",
        "SEX": "Recorded source category; no additional categories or missingness inferred.",
        "AGE": "Source metadata labels diagnosis age; exact age reference date is not supplied. Do not relabel as age at ICI start.",
        "SMOKER": "Ever/Never only; no pack-years or smoking chronology.",
        "LINES_OF_TX": "Source stores as STRING; values 1-7. Treatment-line label does not identify prior regimens.",
        "IRB": "Clinical trial/Commercial context, not randomized allocation or IRB protocol ID.",
        "TREATMENT_TYPE": "Monotherapy/Combination ICI context; no drug names, doses or randomized control supplied.",
        "PFS_MONTHS": "Study-specific time from ICI start to progression or censoring at last scan. Do not assume standard progression-or-death endpoint; death handling cannot be resolved from this table.",
        "PFS_STATUS": "0:Not Progressed is censored; 1:Progressed is the recorded event. Death is not separately identified.",
        "DURABLE_CLINICAL_BENEFIT": "YES/NO/NE study adjudication. NE patients censored before six months; retain separately, never convert to NO. This is not a cure label.",
        "GENE_PANEL": "IMPACT341/410/468; different gene coverage and coding-region denominators. Panel is not a treatment.",
        "ONCOTREE_CODE": "LUAD/LUSC/LUNE/NSCLC; do not silently drop neuroendocrine or unspecified source cases.",
        "MUTATION_RATE": "Original published rate; study reports somatic nonsynonymous mutation count divided by panel coding Mb (0.98/1.06/1.22). Exact original values retained; primary replication biomarker.",
        "FGA": "Study fraction of genome with log2 copy-number gain >0.2 or loss <-0.2 relative to profiled genome; dimensionless. Not a mutational count.",
        "PDL1_SCORE": "Tumor PD-L1 percent, 0-100 when present; blank is missing, zero is measured zero. Current count differs from paper's stated analysis subset.",
        "CANCER_TYPE": "Source umbrella cancer category.",
        "CANCER_TYPE_DETAILED": "Source histologic label; preserve all four observed categories.",
        "SOMATIC_STATUS": "Matched for all samples; study used patient-matched blood normal. Not a diagnosis or outcome.",
        "TMB_NONSYNONYMOUS": "Later cBioPortal TMB field, absent from original 2018 clinical sample file and different from MUTATION_RATE in all rows. Do not mix, overwrite or treat as original published biomarker.",
    }
    with (BASE / "clinical-pilot-field-dictionary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["table", "field", "source_display_name", "source_description", "source_datatype", "missing_rows", "interpretation_and_caution"])
        writer.writeheader()
        for kind, rows, meta in [("patient", patient, patient_meta), ("sample", sample, sample_meta)]:
            for i, field in enumerate(rows[0]):
                writer.writerow({"table": kind, "field": field, "source_display_name": meta[0][i], "source_description": meta[1][i], "source_datatype": meta[2][i], "missing_rows": sum(r[field] == "" for r in rows), "interpretation_and_caution": notes[field]})
    print(json.dumps({key: qc[key] for key in ["patient_rows", "sample_rows", "patient_sample_join", "dcb_counts", "total_source_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
