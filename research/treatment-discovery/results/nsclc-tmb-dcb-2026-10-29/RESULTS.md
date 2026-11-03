# NSCLC biomarker replication results

Analysis date: October 29, 2026. This is a retrospective association benchmark using the public MSK immunotherapy cohort, not a fitted treatment-selection model.

Among **227 DCB-evaluable patients**, the original continuous mutation-rate score had an empirical rank AUC of **0.614**, with a conditional 95% stratified-bootstrap interval of **0.531 to 0.695**. An AUC here describes how often the score ranks a recorded durable-benefit patient above a recorded no-benefit patient, with half credit for ties. It does not measure the probability that treatment cures someone.

| Source DCB group | Patients | Median mutations/Mb | Interquartile range |
|---|---:|---:|---:|
| YES | 69 | 8.49 | 4.10 to 16.04 |
| NO | 158 | 6.60 | 3.77 to 10.59 |

All 240 source patients and samples joined one-to-one. The 13 source NE outcomes were excluded explicitly and retained in `cohort-flow.jsonl`. No biomarker values were imputed, threshold selected, feature model trained or PFS-derived predictor used. The original `MUTATION_RATE` values match the 2018 archive for all 240 samples. The later `TMB_NONSYNONYMOUS` field was not substituted. Source data are ODbL 1.0; attribution and license remain in the adjacent source snapshot.

The statistic reproduces a known published association. The source paper reports 36 post-treatment specimens that cannot be isolated with the available clinical columns, so this cannot establish pretreatment performance. All participants received checkpoint blockade; there is no randomized treatment comparison. Patient selection, smoking, tumor biology, treatment line, assay panel and specimen timing can affect the association. The interval quantifies resampling uncertainty within this cohort, not those biases or external performance.

The next clinical benchmark requires a timing-resolved independent cohort with harmonized endpoint/panel definitions and patient-overlap checks. A resistance mechanism or drug combination additionally requires perturbation and experimental evidence.

Source: [Rizvi et al., JCO 2018](https://doi.org/10.1200/JCO.2017.75.3384); [pinned public cBioPortal study](https://github.com/cBioPortal/datahub/tree/21caf38992efa145ab7b895919cacff2cea700b5/public/nsclc_pd1_msk_2018). See the frozen protocol and clinical-data memo in the parent research folder for endpoint definitions and access details.
