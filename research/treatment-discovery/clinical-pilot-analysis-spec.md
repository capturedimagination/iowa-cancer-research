# Frozen starter benchmark: NSCLC TMB and durable clinical benefit

Version 1.0, frozen 2026-10-29 before inferential benchmark computation. This is a retrospective replication plan written after inspecting the original publication, table schema, missingness, and descriptive group medians. It is not a blinded or prospectively registered analysis.

## Question and scope

In the public MSK anti-PD-(L)1 cohort `nsclc_pd1_msk_2018`, how strongly does the original continuous tumor mutation-rate field rank patients with recorded durable clinical benefit above patients with recorded no durable benefit?

This estimates a within-cohort biomarker association. It does not estimate an immunotherapy treatment effect, compare drugs, discover a cure, validate an individual treatment recommendation, or establish a deployable pretreatment predictor. The original study reports 36 post-treatment tumor samples whose timing cannot be identified in these public clinical tables.

## Frozen inputs and participant handling

- Read the local immutable snapshot `data/nsclc_pd1_msk_2018/2026-10-29/data_clinical_patient.txt` and `data_clinical_sample.txt`; verify their SHA-256 hashes against the adjacent `download-manifest.json`.
- Skip the four `#` metadata lines. Retain every original field as text in raw inputs. Preserve original logical file line numbers (header line 5; first observation line 6).
- Require unique `PATIENT_ID` in both tables and unique `SAMPLE_ID`, identical patient sets, and a one-to-one merge by `PATIENT_ID`. Expected: 240 patients and 240 samples. Abort on unexpected duplicates or unmatched records; do not silently choose one specimen.
- Primary outcome: existing `DURABLE_CLINICAL_BENEFIT`: `YES` = 1, `NO` = 0. Explicitly exclude `NE` and retain their IDs and exclusion reason. Expected analysis: 227 patients, 69 YES and 158 NO; excluded: 13 NE. Do not convert NE to NO or recreate DCB from PFS alone.
- Primary biomarker: `MUTATION_RATE`, continuous, untransformed, finite and nonnegative. No outcome-selected threshold, winsorization, outlier deletion, imputation, feature selection, or learned model. This original column is unchanged from the archived April 23, 2018 sample table; the later `TMB_NONSYNONYMOUS` column is a different measurement vintage and is not substituted.
- No exclusions for smoking, treatment line, histology, treatment class, or panel. No merging with other MSK cohorts in this pilot.

## Prespecified calculation

1. Report input/hash checks, cohort flow, panel counts, treatment classes, missing values and outcome totals.
2. Report each DCB group's biomarker median and interquartile range, with units and sample sizes.
3. Primary statistic: empirical rank AUC, `P(score_yes > score_no) + 0.5 * P(tie)`, with higher original mutation rate oriented toward YES. Report as **retrospective within-cohort discrimination**. The same statistic is a normalized Mann-Whitney U; it requires no fitted prediction model.
4. Uncertainty: 10,000 stratified patient bootstrap replicates with NumPy `default_rng(20261029)`, resampling 69 YES and 158 NO patients independently with replacement. Use the 2.5th and 97.5th empirical percentiles as an approximate conditional 95% interval. Record NumPy version and quantile method. The interval conditions on observed class sizes and does not cover selection, confounding, timing errors or distribution shift. Do not claim external validation from bootstrap resampling.
5. Show a simple distribution plot or empirical ROC only if its labels explicitly identify this retrospective cohort. Include all 227 patients; no selected "best" cutoff. Do not add significance searches, survival fitting, cross-validation, feature models or subgroup hypothesis tests to this starter.
6. Published DCB medians (~8.5 versus ~6.6 mutations/Mb) are a coarse replication check, not a ground truth that the code should force. Any discrepancy is reported. The paper's PD-L1-complete AUC uses a different stated sample subset and is not a numeric target for this full DCB-evaluable analysis.

## Interpretation and next gate

Report the result even if association/discrimination is weak. It is a benchmark of reproducing a known association from already published patient-level data, not a new discovery. No untreated randomized comparison is present, so treatment-benefit prediction cannot be separated from general prognosis or selection. Treatment selection, tobacco exposure, histology, treatment line, clinical-trial enrollment, and assay/tissue timing may all distort the association. Neither adjustment with these sparse columns nor a favorable AUC would identify a causal effect.

Before any future pretreatment predictor: obtain a permitted, timing-resolved independent cohort; resolve specimen dates, outcome definitions, treatment details, patient overlap and panel harmonization; freeze preprocessing and evaluation before external outcomes are inspected. Cross-study MSK records must be checked at the patient level rather than treated as independent validation automatically. Iowa geographic generalization is untested.

No model was fitted and no inferential benchmark was computed when this specification was saved.
