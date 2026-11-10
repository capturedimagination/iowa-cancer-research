# Independent arithmetic and design review

Reviewed November 10, 2026 against the fixed [analysis plan](../../updates/2026-11-10/analysis-plan.md). **The implemented calculation passes the independent checks. The pooled result runs opposite to the proposed enrichment direction, and its direction changes across the small library-kit strata.** Neither result establishes a treatment effect or disproves the biological mechanism.

## Checks completed

The independent [review script](../../../../scripts/review_gse292469_signature.py) does not import or call the main scoring functions. It verifies the full raw-HDF5 SHA-256, reads individual sparse columns, and uses Python scalar `log1p`, integer UMI sums and arithmetic means for three specimens selected before scores were available. All **2,934 malignant singlet nuclei** in those specimens were recalculated, including both MRD2 cores. Results agree with the main calculation within absolute tolerance `1e-12`.

| Direct raw-data check | Malignant nuclei | Independent mean score |
|---|---:|---:|
| TN4 | 82 | 0.8733954727964267 |
| MRD6 | 91 | 0.41345145478766177 |
| MRD2, nuclei weighted equally | 2,761 | 0.8730719032523735 |
| MRD2, cores weighted equally | 183 and 2,578 | 0.934065758158634 |

All 73 specimen malignant-cell counts match a separate reading of deposited cell metadata. Every sensitivity's membership, state counts, mean and median difference, rank AUC and Cliff's delta were checked from the published sample scores. The primary bootstrap was also independently reconstructed with integer index draws and manually interpolated percentile endpoints, using the fixed NumPy version, 10,000 resamples and seed 20261110.

The primary comparison has 9 MRD and 26 TN specimens. There are **51 MRD-above-TN pairs, no ties, and 234 total pairs**, giving AUC `51/234 = 0.21794871794871795`. MRD-minus-TN mean difference is `-0.26314443975839474`. Independently reproduced conditional 95% bootstrap intervals are `[-0.4528338152404544, -0.08216085666809074]` for the mean difference and `[0.07692307692307693, 0.3888888888888889]` for AUC.

## Sensitivity findings that affect interpretation

| Prespecified comparison | MRD / TN specimens | MRD-minus-TN mean | AUC, MRD above TN |
|---|---:|---:|---:|
| Primary | 9 / 26 | −0.2631 | 0.2179 |
| At least 100 malignant nuclei | 8 / 25 | −0.2402 | 0.2500 |
| Lung site only | 7 / 25 | −0.2559 | 0.2171 |
| Exact canonical EGFR variant tokens | 6 / 13 | −0.2136 | 0.2821 |
| Series-implied v3.1 library kit | 3 / 24 | −0.4611 | 0.0417 |
| Series-implied v4 library kit | 5 / 2 | **+0.3620** | **0.9000** |
| Equal-core weighting | 9 / 26 | −0.2564 | 0.2308 |

The v4 comparison contains only two TN specimens and cannot supply a stable adjusted treatment estimate. The series and individual sample records also disagree about some library-kit descriptions. Retain that uncertainty rather than treating the kit strata as verified experimental controls. These opposing strata show that the pooled direction is not consistent across every prespecified subset; they do not identify which technical or biological factor produced the difference.

Stage is particularly imbalanced: 8 of 9 MRD specimens are stage IV, compared with 1 of 26 TN specimens. That sole stage-IV TN specimen is from a lymph node, leaving no stage-IV lung TN comparison. Acquisition procedure, tissue, patient selection, single-nucleus versus original single-cell assay, and raw-UMI versus SoupX-corrected expression further limit comparability.

## Review conclusion

No mathematical, cell-ID alignment or replication-unit error was found in the checked implementation. The code follows the fixed plan: each nucleus's score includes all 17 genes and measured zeroes; each specimen receives one vote; MRD2 cores are merged; and bootstrap resampling uses specimens rather than cells. It preserves the observed unfavorable direction and the subgroup reversal.

The bootstrap intervals describe conditional sampling variability under this dataset and procedure. They do not cover unmeasured confounding, source annotation, library-kit uncertainty, ambient-RNA correction or assay differences. This review verifies arithmetic and adherence to the analysis plan; it is not external peer review, a clinical validation, or evidence supporting a treatment recommendation. Exact checks, hashes and limitations are recorded in [independent-review.json](independent-review.json).
