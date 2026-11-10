# EGFR mechanism question: public-data feasibility

Historical preflight checked **October 29, 2026**. **Superseded for current readiness by the [November 10 update](updates/2026-11-10/README.md):** exact signature and malignant expression/QC are now verified, and an independent descriptive comparison is complete. The original findings below preserve what was known on October 29. [Dated source URLs and hashes](egfr-mechanism-feasibility.json)

## Metadata acquisition and reproducibility

The paper's author-code URL redirects to [czbiohub-sf/scell_lung_adenocarcinoma](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma), archived March 17, 2023. Selected code and rendered outputs are pinned to commit `de138c79bcfc2fa3a28c8a039a28ab560da78099`.

The README-linked [public CSV folder](https://drive.google.com/drive/folders/1VmPan5V19Hq--fMnFHOta67TIpO60srE) supplied the exact original **S01_metacells.csv**, saved immutably in the original local workspace. The source body is not mirrored in the public repository; [the manifest](sources/maynard-2026-10-29/manifest.json) preserves its source pointer and hash. Its size is **11,084,633 bytes**, matching the public listing, and SHA-256 is `b4f3f169516001e89bc8b3d8052e207331ff662ca6d236e1c2cf68eccffdf2a6`. The initial 5 MB preflight cap was explicitly lifted for this metadata file only. The **1,547,287,536-byte S01_datafinal.csv expression matrix remains undownloaded**.

Run `python3 scripts/audit_maynard_metadata.py` from the project folder to regenerate the [sample audit](sources/maynard-2026-10-29/egfr-main-sample-audit.csv) and [count/filter audit](sources/maynard-2026-10-29/egfr-main-metadata-audit.json). The script verifies the source hash, rejects conflicts in audited fields within a sample, preserves raw labels, and does no expression analysis. [Archive manifest](sources/maynard-2026-10-29/manifest.json)

## Actual main metadata contents

There are **27,489 rows with 27,489 unique cell IDs, 51 sample IDs and 33 patient IDs**. The original 42 columns include a row-index column; cell/well/plate identifiers; patient/sample identifiers; explicit driver gene and mutation; histology; biopsy date/site/status; response/group labels; treatment history, line, type, drug and start date; and outcome fields. The 15 audited non-cell fields are consistent within every sample.

These are supplied metadata counts **before malignant-cell annotation and analytic cell/sample QC**. They are not the paper's final 49-biopsy/30-patient analytic cohort; reconciliation with the inclusion/filtering code remains required. The separate neo-osi file was not merged into these counts.

| Explicit metadata filter | Patient IDs | Sample IDs | naive samples | grouped_pr samples | grouped_pd samples |
|---|---:|---:|---:|---:|---:|
| driver_gene = EGFR; histolgy = Adenocarcinoma | 14 | 24 | 8 | 9 | 7 |
| Above, plus driver_mutation = del19 or L858R | 13 | 23 | 7 | 9 | 7 |
| Above, plus treatment exactly = osimertinib | 8 | 14 | 6 | 6 | 2 |

Patient totals across state-specific columns must not be added: some patients appear in multiple states. The all-variant group includes an explicit L861Q record, which the common-variant filter excludes. No genotype was inferred from single-cell mutation absence.

Within the common-variant, osimertinib-coded main subset, **three patient IDs have both source analysis labels naive and grouped_pr**, corresponding to three observed two-sample pairs:

| Patient | naive sample/date/site | grouped_pr sample/date/site | Drug start | Site flag |
|---|---|---|---|---|
| TH205 | LT_S34; 2017-11-13; Pleura | LT_S46; 2018-01-22; Lung | 2018-01-04 | Changes site |
| TH218 | LT_S45; 2018-01-18; Adrenal | LT_S55; 2018-02-23; Adrenal | 2018-01-31 | Same source site |
| TH226 | LT_S52; 2018-02-14; Lung | LT_S57; 2018-03-07; Lung | 2018-02-19 | Same source site |

TH226 also has a source grouped_pd sample, LT_S82. These are **metadata-defined candidates**, not proof that enough matching malignant cells survive final QC, nor a power calculation. Pretreatment samples can have a future drug recorded in the treatment column; their dates and off-treatment status must be retained. `treatment_history = naive` also occurs during first-line therapy and cannot serve as a pretreatment filter. `grouped_pr` pools Early and PR, while `grouped_pd` can include early primary nonresponse. The source-group semantics require review before labeling a biological state.

## Separate neo-osi subset

The public **neo-osi_metadata.csv** is also archived (3,374 bytes). Its 16 plate rows resolve to five distinct sample records: four explicitly EGFR-labeled tumor samples from three patient IDs, plus one explicitly NAT sample excluded from tumor counts. AZ003 has an explicitly labeled naive/post-osimertinib tumor pair, AZ_01/AZ_03. These are additional-source-file counts; they were not silently added to the main cohort or described as independent validation.

## Exact signature remains unresolved

Author script NI16 explicitly contains a **17-gene AT2 differentiation vector**: SFTPC, SFTPB, SFTPD, PGC, CLDN18, AQP4, SCGB3A1, ABCA3, GATA6, NKX2-1, SFTA3, IGFBP2, HOPX, NAPSA, FOXA2, AGER and LAMP1. Its scaling and mean-expression code is retrievable, and [the extracted vector](sources/maynard-2026-10-29/derived-published-AT2-signature.json) records that source.

**This vector has not been verified as the exact paper alveolar-regenerative signature in Table S2. It is not yet the frozen target gene set.** Do not relabel an AT2 marker score as a validated regenerative-state score. Exact supplement mapping, assay/slot/version and scoring/normalization rules remain blockers. Internal separation of source states would still be a reproduction check because the paper's signature was partly developed using that source.

## Remaining readiness requirements

Obtain or construct the matching malignant-cell expression/QC object, reconcile the supplied source metadata with final paper inclusion, verify the exact target signature and scoring method, and identify an independent eligible osimertinib-treated cohort. No further acquisition was attempted in this update. The public metadata makes donor-level design review possible; it does not establish biological replication, clinical benefit or cure.
