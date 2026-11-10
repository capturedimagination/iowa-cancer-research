# Novelty audit: alveolar signatures in EGFR residual disease

**Audit date: November 10, 2026. No new cancer mechanism or new general analysis method is established by this audit.** A careful, reproducible measurement audit of the expanded GSE292469 cohort could still be useful. Its contribution would be an exact quantitative diagnosis and reusable falsification benchmark, not the discovery that sequencing depth, ambient RNA or persister heterogeneity exist.

This is a bounded primary-literature and author-code search, not a systematic review or proof that nobody has tried an idea. The companion [JSON ledger](novelty-audit.json) records source versions, inspection depth, exact recorded queries, hypotheses and code hashes. No models were fit and no hypotheses were experimentally validated in this audit.

## What is already known

| Candidate claim | Prior evidence | Novelty decision |
|---|---|---|
| Log1p scores can change with sparse-count sampling | Booeshaghi and Pachter 2021; OSCA | Established. |
| Downsampling then rescoring tests depth sensitivity | OSCA; Noureen et al. 2022 cancer signature benchmark | Established experimental design. |
| A multinomial UMI null separates sampling from biological heterogeneity | Townes et al. 2019 | Established model. |
| Separate detection frequency from positive expression | MAST 2015 | Established decomposition. |
| Ambient lung RNA can spread alveolar markers into other cell types | Koenitzer et al. 2020; SoupX 2020 | Established; relevance to these tumors remains to be measured. |
| Rank-based scoring is insensitive to every technical difference | UCell methods and current parameter guidance | Unsupported. Ranks still depend on detected genes and rank cutoff. |
| Residual lung tumors contain heterogeneous lineage states | Maynard 2020; Zatzman 2025; HOPX 2025 | Established biological concept. |
| FAK-YAP, ASCL1 or HOPX are previously unknown persister mechanisms | Direct published model studies below | False novelty claim. |

The fixed score here is a mean of 17 log-normalized gene values. It is not Seurat AddModuleScore, so the latter's dataset-dependent control-bin mechanism must not be attributed to it. Likewise, different methods called “alveolar signatures” need not have the same genes or estimand.

## The source study already contains related findings

The original 62-patient [Zatzman 2025 preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12248098/) reports decreasing patient-aggregated alveolar, LUAD and MAPK scores from treatment-naive through residual to progressive disease, alongside heterogeneous persister states. Therefore a lower pooled alveolar score is not a previously unknown biological observation. Its signatures and method differ from the frozen Maynard17 calculation, so this does not establish exact equivalence or resolve the present direction reversal.

The current [author repository](https://github.com/shahcompbio/egfr_nucseq/tree/c4211458564c92b32c1276badaed2e6731ad1a68) was pinned at `c4211458564c92b32c1276badaed2e6731ad1a68`. Inspection found:

- [UCell rankings](https://github.com/shahcompbio/egfr_nucseq/blob/c4211458564c92b32c1276badaed2e6731ad1a68/code/12_ucell_cohort_ranks.qmd) use SoupX-corrected counts. The raw H5/log-mean17 analysis does not reproduce this assay or score.
- [Signature assembly](https://github.com/shahcompbio/egfr_nucseq/blob/c4211458564c92b32c1276badaed2e6731ad1a68/code/14_score_signatures_ucell.qmd) includes a separate 67-metaprogram source CSV. That exact CSV is not present in the inspected repository tree.
- [Figure3 code](https://github.com/shahcompbio/egfr_nucseq/blob/c4211458564c92b32c1276badaed2e6731ad1a68/code/91_figure3.qmd) displays `mp44_alveolar`, Travaglini AT1 and AT2 separately. Specimen-average signature comparisons use Wilcoxon tests and global BH correction, without an explicit kit/depth term in that comparison.
- The same figure notebook includes `log(nCount_RNA)` in its gene-level mixed model with sample effects, and displays library quality metrics. It would be inaccurate to say the authors ignored depth.
- [RPCA integration](https://github.com/shahcompbio/egfr_nucseq/blob/c4211458564c92b32c1276badaed2e6731ad1a68/code/05_sketch_integration.qmd) operates on corrected data by sample/library. An integrated embedding does not establish that the separate specimen signature comparisons are kit-adjusted.

A separate [trajectory-input alveolar metaprogram](https://github.com/mjz1/meta_programs_tirosh/blob/f56a579fbcfa7413de83f2f071cd00e5951d37aa/tirosh_mp_patched.txt) has 50 genes and overlaps only 9/17 Maynard genes: ABCA3, HOPX, NAPSA, PGC, SCGB3A1, SFTA3, SFTPB, SFTPC and SFTPD. This source is referenced by the trajectory notebook. It must not be silently substituted for the unavailable current 67-metaprogram score table.

No exact Maynard17 kit-stratified reversal or depth-thinning result was found in the inspected key notebooks. This is a search result, not proof of absence from all versions or unpublished work. The 2025 preprint and expanded 2026 release/current code are different versions.

## Three falsifiable explanations worth testing

### H1: finite UMI sampling contributes to the direction reversal

For a cell with total UMI `N`, signature-gene count `Xg`, and scale `K=10000`, the score is `S=(1/17) sum_g log(1+K Xg/N)`. Under a fixed-composition multinomial model, `E[Xg/N]=pg`, but concavity gives `E[log(1+K Xg/N)] <= log(1+K pg)`. Sampling variance and nondetection can change the score even when expected transcript fractions do not. This is an application of known mathematics and normalization work, not a new theorem.

**Prediction:** a technical null evaluated at observed depths changes log scores while the expected17-gene UMI fraction remains constant. Repeated thinning reduces a purely depth-driven contrast. **Falsifier:** the observed contrast lies outside reasonable depth-only nulls, or a substantial difference persists in count fractions and overlapping-depth comparisons. Neither outcome alone identifies the biological cause.

Use the same patient eligibility and weights; freeze a depth grid and report retained patients/cells. Include injected biological shifts to measure power lost by thinning. Treat repeats as technical replicates, with patients as the inferential unit. Thinning cannot undo gene-specific capture efficiency or reconstruct unobserved molecules. TotalUMI itself may contain biological variation, so depth standardization changes the question being asked.

### H2: ambient alveolar RNA interacts with low endogenous nuclear RNA

**Prediction:** surfactant contributions track library background, appear in justified negative cell types, and can be reproduced by a plausible ambient-mixture model. If roughly fixed ambient molecules are added to nuclei with less endogenous RNA, the contamination fraction rises. Uniform thinning of an already contaminated profile preserves its expected mixture fraction and does not simulate that mechanism.

**Falsifiers:** valid negative cells/empty droplets lack the relevant signal; plausible mixture fractions cannot explain its magnitude; or independent lineage anchors and orthogonal same-cell localization retain the contrast after correction. Compare raw and author-corrected assays when available, preserving their different definitions.

Use gene-specific negative controls for SFTPC/SFTPB/SFTPD and assess doublets/misannotation. Do not call all 17 genes alveolar-specific: broad genes such as LAMP1 invalidate a whole-signature zero-expression assumption in immune cells. A filtered matrix alone cannot identify ambient truth. The healthy-mouse lung evidence supports plausibility, not an attribution in this human cohort. SoupX sensitivity is informative but model-dependent.

### H3: mean score and coordinated lineage state describe different things

**Prediction:** a specimen can have a high mean from scattered marker expression while having few nuclei with a coordinated program. Conversely a rare coherent state can coexist with a low specimen mean. At fixed total17-gene abundance, distributing signal across more genes can also increase the concave log score. Test marginal gene contributions, breadth, and joint marker behavior separately.

A useful falsification is to permute genes within patient and narrow depth strata, preserving per-gene marginals while disrupting joint expression. The aggregate mean additive score must remain unchanged; joint co-detection and score tails may change. **Covariance alone cannot explain a change in expected additive mean score with fixed gene marginals.** Such permutations are diagnostics, not necessarily valid synthetic count vectors; an 18-category multinomial null for 17 genes plus other preserves count competition.

**Falsifiers:** apparent coherence is reproduced by depth/ambient/marginal-matched nulls, disappears with doublet controls, or also occurs in inappropriate negative cells. Freeze biological anchor groups independently of current group differences. Include coordinated-state injections and unrelated abundance-matched controls. Coexpression is neither a causal dependency nor treatment efficacy; sparse-data nondetection cannot exclude a real state.

## Decision and usable contribution

The strongest immediate deliverable is a transparent decomposition of the exact 17-gene score into transcript fraction, detection, marginal abundance distribution and joint coherence, with separate depth and ambient nulls. Report all directions, including the small kit strata, and quantify which explanations the simulations can and cannot reject. If the models reproduce the reversal, the result is a demonstration of measurement fragility under those assumptions. If they cannot, that rejects the specified artifact model; it does not prove a new persister mechanism.

The frozen cohort has unmatched patients, strong stage/site imbalance, conflicting kit records and only two untreated v4 specimens. Additional cells cannot resolve those design limitations. The result could support a methods/resource audit and a focused request for corrected assay outputs or balanced/paired validation. It cannot yet support a therapeutic claim. No contact or submission was made in this audit.

A defensible description is: “We tested the sensitivity of a published alveolar signature to finite UMI sampling and within-cell gene coherence in a recently expanded, unmatched lung-cancer cohort; ambient-mixture explanations remain to be tested.” Avoid claiming that this is the first such method or that a new resistance target has been found.

## Primary-source ledger

Evidence types are intentionally separate: methods establish prior art; observational patients establish associations; preclinical perturbations establish effects in those models; code establishes implemented operations; simulations establish conditional consequences. None of these labels substitutes for clinical validation.

- **BP2021 — [Normalization of single-cell RNA-seq counts by log(x + 1) or log(1 + x)](https://academic.oup.com/bioinformatics/article/37/15/2223/6155989)** (2021; peer reviewed methods). Log-pseudocount expectation and conditioning on positive counts can distort comparisons. This already excludes novelty of the generic log1p/zero-selection artifact.
- **OSCA — [Normalization, redux: downsampling instead of scaling](https://www.bioconductor.org/books/3.19/OSCA.advanced/more-norm.html)** (Bioconductor 3.19; primary software documentation). Explicitly demonstrates residual library-size effects after log normalization and downsampling as a sensitivity analysis; notes information loss.
- **TOWNES2019 — [Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model](https://pubmed.ncbi.nlm.nih.gov/31870412/)** (2019; peer reviewed methods). Multinomial UMI sampling null and normalization-induced false variation are established; such a null is not a new model.
- **MAST 2015 — [MAST: a flexible statistical framework for assessing transcriptional changes and characterizing heterogeneity in single-cell RNA sequencing data](https://link.springer.com/article/10.1186/s13059-015-0844-5)** (2015; peer reviewed methods). Detection versus positive abundance, cellular detection-rate covariates and residual coexpression analyses are established ideas.
- **NOUREEN2022 — [Signature-scoring methods developed for bulk samples are not adequate for cancer single-cell RNA sequencing data](https://elifesciences.org/articles/71994)** (2022; peer reviewed methods). Cancer signature benchmarking already uses within-cell downsampling followed by renormalization as a technical null and compares rank-based and expression-based scores. It does not validate the present17-gene score.
- **UCELL2021 — [UCell: Robust and scalable single-cell gene signature scoring](https://pmc.ncbi.nlm.nih.gov/articles/PMC8271111/)** (2021; peer reviewed methods). Within-cell ranks reduce dependence on dataset composition. Composition robustness is not a guarantee of depth invariance.
- **UCELL_PARAMS — [Some important parameters for UCell](https://bioc-release.r-universe.dev/UCell/doc/UCell_parameters.html)** (retrieved 2026-11-10; primary software documentation). The authors advise choosing maxRank with regard to detected-gene counts, explicitly acknowledging sparsity sensitivity.
- **SOUPX2020 — [SoupX removes ambient RNA contamination from droplet-based single-cell RNA sequencing data](https://pmc.ncbi.nlm.nih.gov/articles/PMC7763177/)** (2020; peer reviewed methods). Ambient mixture correction and negative marker/cell controls are established; no-expression assumptions must be defensible.
- **LUNG2020 — [Single-Nucleus RNA-Sequencing Profiling of Mouse Lung. Reduced Dissociation Bias and Improved Rare Cell-Type Detection Compared with Single-Cell RNA Sequencing](https://pmc.ncbi.nlm.nih.gov/articles/PMC7790136/)** (2020; peer reviewed biological comparison). Healthy mouse lung nuclei show ambient epithelial contamination; SoupX improves many markers but Sftpc is incompletely removed. This is direct lung prior art, not proof of contamination in these human tumors.
- **MAYNARD2020 — [Therapy-Induced Evolution of Human Lung Cancer Revealed by Single-Cell RNA Sequencing](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/)** (2020; peer reviewed patient observational). The17-gene alveolar signature and residual-state observation are published prior art. Reusing it is external application, not signature discovery.
- **ZATZMAN2025 — [Complementary modes of resistance to EGFR TKI in lung adenocarcinoma through MAPK activation and cellular plasticity](https://pmc.ncbi.nlm.nih.gov/articles/PMC12248098/)** (2025-05-10 version1; preprint patient observational). Original62-patient preprint reports declining patient-aggregated alveolar/LUAD/MAPK signatures and heterogeneous persister states. It uses UCell and malignant metaprograms, not a demonstrated identical Maynard17 score.
- **AUTHOR_CODE — [egfr_nucseq author code](https://github.com/shahcompbio/egfr_nucseq/tree/c4211458564c92b32c1276badaed2e6731ad1a68)** (commit c4211458564c92b32c1276badaed2e6731ad1a68; primary analysis code). Current code uses SoupX-corrected UCell scoring, sample/library integration, specimen-average comparisons, QC plots, and a depth-adjusted gene-level mixed model. Different stages have different adjustments.
- **METAPROGRAM — [Malignant alveolar metaprogram referenced in trajectory code](https://github.com/mjz1/meta_programs_tirosh/blob/f56a579fbcfa7413de83f2f071cd00e5951d37aa/tirosh_mp_patched.txt)** (commit f56a579fbcfa7413de83f2f071cd00e5951d37aa; primary analysis code). This trajectory-input set overlaps9 of17 Maynard genes. It is not proof of the exact contents of the separate current 67-metaprogram score CSV.
- **HOPX 2025 — [Epigenomic analysis identifies DTP subpopulation using HOPX to develop targeted therapy resistance in lung adenocarcinoma](https://pmc.ncbi.nlm.nih.gov/articles/PMC12063144/)** (2025; peer reviewed preclinical intervention). HOPX-associated persister heterogeneity, transient lineage-gene induction and delayed regrowth after HOPX deletion are already reported in treated models; this is not a new target proposal.
- **ASCL12024 — [ASCL1 Drives Tolerance to Osimertinib in EGFR Mutant Lung Cancer in Permissive Cellular Contexts](https://pmc.ncbi.nlm.nih.gov/articles/PMC11142404/)** (2024; peer reviewed preclinical intervention). ASCL1-dependent tolerance is context-dependent in cell and patient-derived models. Generic plasticity or universal ASCL1 dependence would rebrand or overstate prior results.
- **FAKYAP2024 — [Focal adhesion kinase-YAP signaling axis drives drug-tolerant persister cells and residual disease in lung cancer](https://www.nature.com/articles/s41467-024-47423-0)** (2024; peer reviewed preclinical intervention). FAK-YAP promotion of persistence has direct model-based prior evidence. It is not a new mechanism inferred from the17-gene score.

## Search and inspection limits

Searches ran November 10, 2026 using source-title searches, `GSE292469` with `Maynard`, `alveolar`, `kit`, `depth` and `v4`, and signature/depth/ambient/persister terms. Exact recorded queries are in the JSON. Primary articles, author code and author-maintained documentation support the claims; search mirrors and reviews were navigation aids only. Some publisher/PMC requests returned access errors; inspection depth is recorded per source rather than implying every full text was reviewed. The current revised manuscript and exact current 67-metaprogram gene table remain unverified.

Source code and the fetched metaprogram remain in ignored `tmp/discovery-novelty/`; public outputs contain original analysis notes, links and hashes, not copied papers or source matrices. Search incompleteness, evolving releases and unpublished work prevent an absolute novelty guarantee.


## Follow-up: three-timepoint curvature design

The separate [independent review](mechanistic-simulation/v2/independent-review.md) verifies the synthetic mathematics and adds an estimated-variance sensitivity. It does not establish novelty. [Harris2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4887341/), [Gunnarsson2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10372878/) and [Wu2025](https://www.nature.com/articles/s41540-025-00560-8) provide close prior art for log-growth dynamics, curvature-based identifiability, experiment design and richer bulk inference. No first-ever claim is supportable.

Execution status was updated after the original ledger: the separate finite-UMI and coexpression analyses have run. Ambient-mixture explanations remain proposed and untested. Biological mechanism and clinical efficacy remain unvalidated.
