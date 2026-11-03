# Public clinical pilot: NSCLC immunotherapy biomarker replication

Verified **October 29, 2026**. A tractable public cohort is available for a bounded retrospective replication. It supports learning a reliable treatment-response research workflow; it cannot establish a cure, a causal treatment effect, or an individual treatment recommendation. This is clinical research data and has no patient linkage to the Iowa county/environmental corpus.

## Selected cohort and access

Use cBioPortal study **`nsclc_pd1_msk_2018`**, “Non-Small Cell Lung Cancer (MSK, J Clin Oncol 2018),” associated with **Rizvi H et al., JCO 2018, DOI `10.1200/JCO.2017.75.3384`, PMID `29337640`, PMCID `PMC6075848`**. The official study metadata describes 240 MSK-IMPACT tumor/normal pairs treated with anti-PD-(L)1 therapy and labels the study `PUBLIC`. [Study metadata](https://raw.githubusercontent.com/cBioPortal/datahub/21caf38992efa145ab7b895919cacff2cea700b5/public/nsclc_pd1_msk_2018/meta_study.txt), [original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6075848/), [portal](https://www.cbioportal.org/study/summary?id=nsclc_pd1_msk_2018).

The repository's study-specific **ODbL 1.0** license permits reuse with attribution and share-alike conditions for publicly shared/adapted datasets. Retain the saved license and credit the study and cBioPortal when publishing outputs. This does not imply that unrelated project material must be published. No login, controlled access application, contact, names, addresses, raw sequencing reads or restricted records were used. Public case IDs remain pseudonymous research identifiers; no reidentification was attempted. [Study license](https://raw.githubusercontent.com/cBioPortal/datahub/21caf38992efa145ab7b895919cacff2cea700b5/public/nsclc_pd1_msk_2018/LICENSE).

## Saved originals and provenance

The dated snapshot is [`data/nsclc_pd1_msk_2018/2026-10-29/`](data/nsclc_pd1_msk_2018/2026-10-29/). It contains **98,943 bytes** across the clinical tables, metadata, license, original 2018 sample table, and sample-file history. URLs, retrieval times, byte counts, HTTP metadata and SHA-256 hashes are recorded in [`download-manifest.json`](data/nsclc_pd1_msk_2018/2026-10-29/download-manifest.json). Raw tables are preserved unchanged. GitHub raw `data_*.txt` links return Git LFS pointers; the archived tables came from the official `media.githubusercontent.com` endpoint and were checked to contain actual records.

| Actual filename | Grain and use |
|---|---|
| `data_clinical_patient.txt` | One record per patient: DCB, progression time/status and limited clinical context |
| `data_clinical_sample.txt` | One record per tumor sample: original mutation rate, later TMB, panel, histology, FGA and PD-L1 |
| `data_clinical_sample-original-2018-04-23.txt` | Historical official sample table at commit `632487fcf657eed6e25e81ad41d0499eb9296894`; distinguishes the publication-era biomarker from later additions |
| `meta_study.txt`, `meta_clinical_patient.txt`, `meta_clinical_sample.txt`, `Readme.txt`, `LICENSE` | Study/file scope, panel reference link and reuse terms |
| `clinical-sample-commit-history.json` | Official GitHub history, including the August 4, 2021 addition of TMB to targeted studies |

Current snapshot files are pinned to repository commit **`21caf38992efa145ab7b895919cacff2cea700b5`**, the most recent study-path commit returned at retrieval. This is a repository version, not a new clinical follow-up period. No mutation, copy-number, structural-variant, raw-read or large whole-repository download was needed for this pilot.

Run the non-modeling audit from the project folder:

```sh
python3 research/treatment-discovery/audit_clinical_snapshot.py
```

It verifies all saved hashes, schema, cardinality and missingness, then regenerates [`clinical-pilot-qc.json`](clinical-pilot-qc.json) and the complete [`field dictionary`](clinical-pilot-field-dictionary.csv). It makes no network request and fits no model. Each source table has four metadata rows, a header at logical line 5 and first observation at line 6; preserve these source-line references in analysis tables.

## Observed table audit

These are direct counts from the downloaded tables, not inferred from the article:

| Check | Observed result |
|---|---|
| Patients / samples | 240 / 240; unique patient IDs in each file and unique sample IDs; identical patient sets and a one-to-one join |
| DCB | 69 `YES`, 158 `NO`, 13 `NE`; 227 evaluable for the proposed binary association |
| Progression status | 198 `1:Progressed`, 42 `0:Not Progressed`; all 13 NE records are censored below 6 months |
| Treatment context | 206 `Monotherapy`, 34 `Combination`; 54 `Clinical trial`, 186 `Commercial` |
| Sequencing panel | 56 `IMPACT341`, 164 `IMPACT410`, 20 `IMPACT468` |
| Histology codes | 186 LUAD, 34 LUSC, 7 LUNE and 13 NSCLC; retain all source categories |
| Missingness | No blank primary TMB, DCB, PFS time/status, age, sex, smoking, treatment line or treatment-class values; PD-L1 is blank for 154/240 |

Keep `PATIENT_ID` and `SAMPLE_ID` as text. Their suffixes are not an admissible substitute for a documented biopsy date. A file with one tumor per patient does not imply that the patient had only one biopsy or treatment historically. If another cohort is added, deduplicate patients across study accessions before constructing training/validation sets; do not remove or merge records using names, outcomes or arbitrary specimen choices.

## Design, endpoint and measurement contract

The original study is a retrospective treated cohort: ICI starts April 2011–January 2017, database lock May 2017. RECIST 1.1 informed response assessment. DCB categorizes durable response/stability beyond six months; patients censored before six months without progression are NE. The study-specific PFS runs from ICI start to progression and censors nonprogressors at their last scan; real-time clinician-declared progression could count despite later RECIST adjudication. Do not silently replace this with a standard progression-or-death endpoint. [Original methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6075848/).

The TSV has `PFS_MONTHS`, `PFS_STATUS` and `DURABLE_CLINICAL_BENEFIT`, but **no raw start/scan/progression dates, death indicator, overall-survival fields, full RECIST response history, performance status, pack-years, treatment drug names/doses, biopsy-relative-to-treatment field, or post-treatment chronology**. Preserve DCB as adjudicated: do not derive it from PFS alone or recode NE as NO. A DCB label is not a cure label.

The paper's MSK-IMPACT assay used matched blood normal and panels of 341/410/468 genes, with coding denominators 0.98/1.06/1.22 Mb for its normalized somatic mutation rate. It reports **204/240 tumors sampled before ICI**; the other 36 cannot be identified from these clinical TSVs. The assay was not universally pretreatment. [Assay methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC6075848/).

### Two TMB columns must remain separate

`MUTATION_RATE` is present in the original 2018 sample table and has **zero changed values** in the current 240 matched samples. Its current median is 7.37704918 (publication rounded to 7.4) and its range is 0.819672131–91.83673469. It is the replication biomarker.

`TMB_NONSYNONYMOUS` is absent from that 2018 file, appears after the repository's 2021 TMB addition, and differs from `MUTATION_RATE` for **all 240 rows** (current median 7.7731849795). The file's short metadata do not supply a complete study-specific derivation for this later field. Do not assume matching denominators, variant inclusion, calibration or thresholds, and do not overwrite the original measure. Panel-specific coding coverage matters even when both fields are described informally as TMB. [Historical sample file](https://media.githubusercontent.com/media/cBioPortal/datahub/632487fcf657eed6e25e81ad41d0499eb9296894/public/nsclc_pd1_msk_2018/data_clinical_sample.txt), [2021 change](https://github.com/cBioPortal/datahub/commit/f7b301613baeecb8b3897fcbdd57669e8f8b248a).

### PD-L1 discrepancy remains explicit

Both the historical and current tables contain **86** nonblank `PDL1_SCORE` values, of which **79** are DCB-evaluable (24 YES, 55 NO, 7 NE). The article describes an 84-patient PD-L1 analysis. The exact subset reconciliation is unresolved. Blank and measured zero must remain distinct. PD-L1 is excluded from the starter benchmark, and the paper's PD-L1-complete AUC is not its numeric target.

## What comparison is and is not available

All 240 archived patients received ICI. The `TREATMENT_TYPE` and `IRB` fields describe clinical context; they are not random assignment, and monotherapy versus combination is confounded by line, trial selection, health and clinical decision making. The paper also describes a non-ICI reference series, but those controls are **not in these archived clinical tables**. Do not label this snapshot a randomized treatment/control dataset or borrow a control series without reconciling time origin, eligibility and patient overlap.

The selected benchmark requires no assumption that TMB caused benefit. Tobacco exposure, tumor histology/genetics, patient selection into MSK sequencing and ICI, treatment line, trial participation, disease severity, tissue availability and post-treatment sampling are plausible sources of confounding or selection. The available covariates cannot fully measure them. Missing biopsy timing creates information-leakage risk for a proposed pretreatment predictor. Reproducing a known association in the same cohort is not external validation, even with bootstrap intervals or a random split. Modern treatment practice, other panels, other institutions and Iowa populations require separate validation.

## Recommended first analysis

The frozen [`analysis specification`](clinical-pilot-analysis-spec.md) defines one calculation: empirical rank AUC of **continuous original `MUTATION_RATE`** for recorded DCB among 227 YES/NO patients, with a fixed patient bootstrap uncertainty procedure and no cutoff search or learned model. Call it a **retrospective within-cohort association benchmark**. Report all 13 NE exclusions, source hashes and assay timing limits. The specification was frozen after source/descriptive audit, so it is not a blinded preregistration.

This is a small, reproducible foundation for a future biomarker-validation program. Progress toward a new treatment requires independent timing-resolved data, a mechanistic hypothesis and experiments, and eventually prospective clinical evaluation; this dataset alone cannot supply that evidence.

## Review depth

The official repository's actual clinical files, metadata, license, historical file and commit history were inspected. The original article's HTML methods, main results and relevant appendix captions were read; supplemental tables and all original figure images were not fully reviewed. cBioPortal's JavaScript portal summary did not expose tabular data to the text browser, so archived record counts come from the official repository tables. See [`clinical-pilot-sources.json`](clinical-pilot-sources.json) for source roles and access boundaries.
