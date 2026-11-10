# Joint-expression diagnostic for the 17-gene alveolar score

**The average score does not establish a coordinated cellular program.** In this exploratory diagnostic, preserving every gene's measured distribution while shuffling which genes appear together left all patient mean scores unchanged. It reduced score variability in all 35 patients. A separate measure—the fraction of nuclei detecting at least five signature genes—moved in the opposite direction overall.

These results identify joint dependence beyond a coarse depth-conditioned independence reference. They do not identify its cause or establish a persister mechanism, treatment target or cure. The permutation principle and gene-expression decomposition are established methods; see the [novelty audit](../novelty-audit.md).

## Frozen question and calculation

The [protocol](protocol.json) was frozen at **2026-11-10 18:29:27 UTC**, before loading the target-count cache or calculating these outcomes. Its SHA-256 is `c3ebe1106843832006e0757cd734da9a6e4a823df2f68efab485dfdeeb09e1b9`. This is a local freeze, not external preregistration. Prior patient mean scores and metadata were already known.

The cohort is unchanged: 121,083 deposited malignant singlet nuclei from 26 untreated and nine residual-disease LUAD patients. MRD2 remains one patient. Within each patient, nuclei were sorted into ten nearly equal depth-rank bins, using an independent seeded random tie break. Each gene's `ln(1 + 10000 × geneUMI / totalUMI)` values were independently shuffled within these fixed bins, 100 times. Detection traveled with its corresponding value. No cells were removed.

This preserves each gene's marginal distribution within each bin and each patient's mean score, while removing within-bin cross-gene association. It also preserves the mean number of detected signature genes. It does not preserve the fraction above a detection-breadth threshold or the variance of cell scores. These shuffled normalized vectors are a conditional association reference, not simulated molecular counts with a conserved total UMI count.

## Results

Each patient receives equal weight. “Excess” means observed minus that patient's mean across 100 shuffles.

| Prespecified endpoint | Observed patient mean | Shuffled patient mean | Mean excess | Conditional patient-bootstrap 95% interval for excess |
|---|---:|---:|---:|---:|
| Variance of cell signature scores, score² | 0.050424 | 0.030811 | +0.019612 | +0.014092 to +0.025841 |
| Nuclei detecting at least five genes | 75.8144% | 76.6927% | −0.8783 percentage points | −1.2549 to −0.4884 percentage points |

All 35 patients had positive variance excess; the median patient observed/null variance ratio was 1.4634. Detection-breadth excess was positive in seven and negative in 28 patients. These are descriptive counts, not individual-patient significance claims.

Greater covariance can widen a score distribution while decreasing the fraction above a particular threshold. In this cohort, detecting at least five genes is already common; it is not an established rare-state classifier. The two endpoints must not be substituted for one another or selectively reported.

Exploratory state comparisons retain the source kit uncertainty and opposite directions:

| Source-implied kit | Untreated / residual patients | Residual minus untreated variance excess | Residual minus untreated breadth excess, percentage points |
|---|---:|---:|---:|
| Pooled, including mixed-kit MRD2 | 26 / 9 | −0.015317 | +1.5095 |
| v3.1 | 24 / 3 | −0.019563 | +2.7841 |
| v4 | 2 / 5 | +0.005763 | −0.0477 |

These secondary contrasts are descriptive. The very small v4 untreated group and stage, site, assay and patient differences prevent a causal interpretation. Shuffling cannot alter the previous patient mean-score contrasts; their original directions remain intact by construction.

## What this changes about interpretation

A high mean score and coordinated expression are distinct properties. The data contain dependence that the shuffled reference removes, but the diagnostic does not distinguish co-regulation from residual depth variation, shared ambient contamination, cell quality, doublets, copy-number effects or mixtures of malignant cell states. Ten depth bins only condition on depth approximately. No new regulator or specific gene interaction was selected from these results.

Covariance cannot change the expected additive mean score when all gene marginals are fixed. This diagnostic therefore cannot explain the original mean-score reversal through covariance alone. Its useful contribution is showing why an average score should not, by itself, be labeled the prevalence or activity of a coordinated persister program.

## Verification and uncertainty

Input-cache hashes, gene order, patient IDs, unique nucleus IDs, counts, depths and prior patient means were checked. Across all 3,500 patient/permutation runs, maximum patient mean-score drift was **4.44 × 10⁻¹⁶**; mean detected-gene breadth was unchanged exactly. Per-gene marginal-sum checks passed.

Exact conditional-null expectations were calculated separately from permutation draws. Their equal-patient means were 0.030828 for score variance and 76.6837% for breadth, close to the empirical shuffle means. The largest absolute Monte Carlo deviation was 3.405 standard errors for variance and 1.968 for breadth across the 35 patients; no result was filtered using this diagnostic. Known all-zero and perfectly coexpressed synthetic fixtures passed. Separate scalar arithmetic also reproduced observed metrics for 7,297 nuclei across LX1846, MRD2 and TN13 without calling the analysis functions.

Bootstrap intervals use 10,000 resamples of the 35 patient-level excesses. They condition on observed patients, annotations, bins and the estimated shuffled reference; they do not cover confounding or incorrect biological assumptions. Permutation percentiles in the result file describe technical randomization variation, not patient treatment-effect uncertainty. No cell-level p-values were calculated. Computational checks are not independent biological validation or scientific peer review.

## Reproduction

[results.json](results.json) preserves all patient aggregates, both endpoint distributions across 100 shuffles, exact-null expectations, state/kit summaries, validation and hashes. No cell-level expression vectors are exported.

Use the project environment with NumPy 2.3.5. The local target-count cache and its provenance sidecar are generated by [the depth simulation script](../../../../scripts/simulate_signature_depth.py) from the pinned molecular source files; they remain ignored and are not redistributed. From the project root:

```sh
python scripts/audit_signature_coexpression.py --self-check-only
python scripts/audit_signature_coexpression.py
```

The [analysis script](../../../../scripts/audit_signature_coexpression.py) checks the frozen protocol and input hashes before running. It does not modify the protocol. Changing inputs, bins, threshold, eligibility or score requires a separately versioned analysis rather than rewriting this result.
