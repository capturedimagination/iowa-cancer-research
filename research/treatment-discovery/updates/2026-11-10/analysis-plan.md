# Independent alveolar-signature analysis plan

Written November 10, 2026 after reviewing source metadata and before calculating expression scores. This is a prospective computational plan within this project, not an external preregistration. A change to the plan must be dated and explained before its affected result is interpreted.

## Question and evidence level

Does the published Maynard 17-gene alveolar signature have higher sample-level expression in malignant nuclei from residual EGFR-mutant lung adenocarcinoma on osimertinib than in treatment-naive tumors in the independent GSE292469 cohort?

This is an observational, cross-sectional external reproduction of a molecular-state association. Each sample comes from a different patient, apart from two libraries/cores for specimen MRD2. It cannot estimate a within-patient treatment change, a causal drug effect, clinical efficacy, or whether inhibiting this state would help patients. The single-nucleus assay is different from the original single-cell assay.

## Inputs and gates

- Freeze the exact 17-gene list only after matching author code, the primary paper and Table S2. No substitute regenerative-state signature or selected subset will be used. If any required gene has ambiguous or absent feature mapping, stop the primary score rather than silently dropping genes.
- Use the November 1, 2026 public GSE292469 release, its raw UMI HDF5, cell metadata and sample records. Record downloaded bytes, SHA-256, URLs, retrieval time, schema and analysis environment. Original files remain local; publish provenance and original aggregate findings/code.
- Require unique cell identifiers, an exact matrix/metadata cell join, verified gene identifiers, integer nonnegative finite UMI counts, and consistency of per-cell counts with deposited QC metadata. Treat a mismatch as a failed gate until explained.
- Use only deposited `is_tumor_cell` true nuclei and singlets. Do not infer tumor status from the target signature. Preserve source annotations rather than fitting a new malignancy classifier.

## Score and analysis unit

Use each nucleus's total UMI count across the deposited gene-expression features as the library denominator. For gene g and nucleus c, calculate `log(1 + 10000 * count[g,c] / library_total[c])`. The cell score is the arithmetic mean of the 17 genes, including measured zeros. This follows the author-code mean-expression rule; it is not a z score, AddModuleScore, trained classifier, or proof of identical historical software behavior.

Average the cell scores within the specimen/patient. Merge MRD2's two cores into its single specimen, weighting its nuclei equally; also report a sensitivity giving its two cores equal weight. Each specimen then has one vote in between-state comparisons, regardless of cell yield. Report malignant nuclei per specimen; cells are never independent patient replicates.

Primary eligibility: TN or MRD source state, EGFR-mutant lung adenocarcinoma, at least 20 deposited malignant singlet nuclei, valid sample metadata and complete target genes. PD specimens are excluded from the primary comparison and can appear only in explicitly descriptive secondary summaries. All EGFR variants are included as defined by the series; a common-variant sensitivity is permitted only if source genotype labels can be unambiguously harmonized.

## Fixed reporting and uncertainty

Report sample/state counts and exclusions, the patient-score distribution, MRD-minus-TN mean and median differences, and rank AUC (probability that a randomly sampled MRD specimen has a higher score than a TN specimen, with half credit for ties). AUC here is a descriptive separation statistic; it is not a clinically validated prediction metric. Report Cliff's delta as `2*AUC - 1`.

Use 10,000 independent stratified patient bootstrap resamples with NumPy 2.3.5 and seed 20261110 for conditional percentile 95% intervals on the mean difference and AUC. Report the full bootstrap procedure and its limited coverage: it does not include batch, sampling, treatment selection, annotation, signature-development or model uncertainty. Do not use cellular bootstrap replicates or select a clinical cutoff. A p-value is not the primary output.

Prespecified sensitivity summaries: at least 100 malignant nuclei; lung biopsy site only; each shared library chemistry/kit separately where both states exist (excluding mixed-kit specimens from those subsets); canonical EGFR E746_A750del/L858R only; and equal-core weighting for MRD2. The canonical-variant subset requires an exact variant token after splitting source labels at commas/semicolons; retain co-mutations and amplification, but do not silently classify other exon-19 variants. Publish all feasible summaries, including reversal or loss of separation. If a subset lacks either state or has fewer than two specimens in either state, report insufficient comparison rather than an interval.

Always report treatment-state cross-tabs with tissue site, acquisition procedure, library kit and major EGFR genotype. Interpret observed separation alongside these confounders. No high-dimensional adjustment, target search, optimized gene weights, tuned threshold or survival model is planned for this small cohort.

### Metadata findings known before score calculation

The November 10 metadata audit identifies 26 TN and 9 MRD LUAD specimens meeting the 20-malignant-nucleus rule. The source's MRD specimen LX2019 is labeled SCLC and is excluded by the LUAD gate. Only one eligible TN specimen is stage IV, versus eight MRD specimens; that TN specimen is lymph node, so no stage-IV lung TN comparison exists. The series describes newer LX libraries as v4 while their individual sample protocol paragraphs say v3.1. Kit strata therefore use the explicit series assignment and retain the contradiction as uncertainty, not resolved fact. These imbalances prevent this comparison from isolating a drug-induced state even if the expression score separates groups.

## Original cohort audit

Separately check the published Maynard malignant-cell annotation against the author-provided processed tumor object and original sample metadata. Count pair attrition without treating the remaining single patient as a population-level validation. If an original-data score is calculated, label it an internal reproduction and keep it separate from the independent cohort.

## Sources

- [Maynard et al., Cell 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/)
- [Pinned author code](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/tree/de138c79bcfc2fa3a28c8a039a28ab560da78099)
- [GSE292469 public series](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292469)

Exact signature verification, data-use review and source-specific evidence are documented alongside this plan.
