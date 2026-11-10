# Discovery work: simulations, failed explanations and a validation route

November 10, 2026. **We found useful measurement limits and a testable experimental design, not a new cancer mechanism or cure.** The discovery goal remains open. A bounded literature search cannot prove that nobody has previously considered an idea; prior work already covers several tempting claims.

**Subsequent work:** the [lineage-sampling audit](../lineage-audit-2026-11-10/README.md) derives and checks a finite-horizon selection counterexample, inspects the original PC9 event workbook, and records why its empirical hazard interpretation remains unresolved. Prior-art checks narrow the originality claim; the existing protocols and numerical outputs below remain unchanged.

This extension asks which observations could distinguish competing explanations for residual cancer-cell states. It combines a fixed public lung-cancer cohort with separate hypothetical cell-state simulations. The two tracks do not validate one another: an alveolar expression signature is not an established functional label for drug tolerance, and synthetic model parameters are not fitted patient biology.

## Findings that change the next experiment

| Question tested | Result | What it supports | What it does not establish |
|---|---|---|---|
| Does equal-depth thinning remove the opposing signature directions? | Opposite source-implied kit directions persist after all 121,083 nuclei are sampled to 1,000 UMIs. Raw relative abundance also reverses. | Depth standardization is insufficient under this observed-molecule intervention; investigate assay, ambient RNA and cohort differences. | Exclusion of every depth/capture model, a biological cause, corrected kit labels or a treatment effect. |
| Does a mean signature score demonstrate coordinated expression within cells? | Gene shuffling preserves every patient's mean while changing score variance and detection breadth. | Mean score and joint expression answer different questions. | A specific regulator, a causal persister state or covariance as an explanation for changed additive means. |
| Can a few early bulk measurements identify recovery memory? | No primary V1 design reaches 80% power; a flexible constant-rate competitor matches both burden endpoints in all 81 cases. | Reject the sparse design as sufficient evidence under these tested models. | That every bulk-data method is uninformative. |
| What does a more informative measurement design require? | Three equally spaced absolute state-abundance measurements yield a conditional precision rule. With known 10% CV and three independent replicates per time, log-curvature ≥0.395 gives 80% detection. | A calculable requirement to assess before collecting data. | Specific detection of memory: changing growth, label retention and state re-entry can also curve the trajectory. |
| Is the design robust to wrong measurement-error assumptions? | Doubling final-time CV while assuming it is unchanged raises false positives to about 11%. | Calibrate time-specific error; adding replicates cannot repair a wrong noise model. | That the idealized precision rule applies to an uncalibrated real assay. |

The [independent design review](mechanistic-simulation/v2/independent-review.md) also examines estimating variance from the experiment rather than assuming it known. Its review-only sensitivity requires approximately **0.475** log-curvature at three replicates per time and 10% CV, rather than 0.395. It assumes independent wells and equal normally distributed log errors. These are conditional study-design calculations, not measured biological effect sizes.

## Evidence and reproducible outputs

- [Depth falsification report](depth-simulation/README.md), [frozen plan](depth-simulation-plan.json), [all results](depth-simulation/results.json) and [independent calculation](depth-simulation/independent-review.md).
- [Joint-expression diagnostic](coexpression/README.md), [frozen protocol](coexpression/protocol.json) and [all patient/permutation results](coexpression/results.json).
- [V1: sparse-design failure](mechanistic-simulation/README.md), with its original protocol, result grid and negative findings retained.
- [V2: precision, power and counterexamples](mechanistic-simulation/v2/README.md), [frozen protocol](mechanistic-simulation/v2/protocol.json), [all simulation results](mechanistic-simulation/v2/results.json) and [independent review](mechanistic-simulation/v2/independent-review.md).
- [Empirical validation-data audit](mechanistic-simulation/v2/validation-data-route.md): three candidate resources inspected. Oren's published PC9 division/death matrices offer a conditional growth benchmark; none supplies verified joint withdrawal/state-transition histories.
- [Novelty audit](novelty-audit.md), [source/search ledger](novelty-audit.json), [research destinations](research-destinations.md) and [review-ready proposal](proposal.md).

The cohort work preserves the earlier 26 untreated/nine residual-patient inclusion rule. The 100 thinning or permutation repetitions are technical simulations; they are not additional patients. The dynamics work uses synthetic parameter grids, separate null tests, explicit error distributions and exact competing trajectories. Its time units are hypothetical doubling times, not days or drug schedules. Computational reviewers use separate formulas/checks, but they are part of this project and are not external scientific peer reviewers.

## Novelty decision

The source study's [2025 preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12248098/) already reported declining alveolar signatures. Log-normalization sensitivity, downsampling, gene coexpression decomposition, reversible tolerance and curvature-based state inference also have prior art. Rebranding them would not be a discovery. The exact dataset-specific sensitivity results and this reproducible benchmark may be useful contributions, but first-ever novelty has not been established.

The original study's corrected UCell analysis differs from this raw-UMI Maynard17 calculation. Its authors included depth in a gene-level model; this project does not claim they ignored depth. The present small kit strata, stage/site imbalance, conflicting chemistry metadata and unmeasured ambient RNA prevent a mechanistic conclusion.

## Where the research can go

The strongest immediate route is a **measurement-validation collaboration**. The [destination audit](research-destinations.md) identifies the source study's MSK investigators for assay/chemistry clarification and the University of Iowa IIHG Bioinformatics/Biostatistics division for independent analysis/design consultation. Service eligibility, fees and investigator participation would need confirmation; no affiliation or collaboration is implied.

The [proposal](proposal.md) gives a concrete scope: reproduce the corrected assay; resolve chemistry metadata; assess whether a functional state can be tracked with calibrated error; and measure proliferation/death and marker stability alongside state transitions. A preprint or journal submission would require accountable human scientific review and additional validation. GitHub is the public research record, not peer review. No messages, consultation requests, submissions or payments have been made.

## Next decision gates

1. Obtain a verifiable corrected assay and kit map, or record the unresolved gap. Do not infer contamination fractions from a filtered matrix alone.
2. Evaluate empirical validation data for observable transitions, division/death and stable labels. More snapshots of the same ambiguous marker cannot identify the mechanism.
3. If a usable assay/data source exists, freeze a new analysis that separates growth, re-entry and marker drift before testing a memory explanation. Calibrate the observation model from data, preserving zeros and replicate dependence.
4. Seek a result that survives the competing models and literature audit. Preserve null results and stop unsupported mechanism claims. A drug target would require a separate perturbation and safety/translation program.

All files are saved in the project reference library for future work. Rebuilding the searchable index makes these findings retrievable; it does not train a model or guarantee context outside this project. [Publication and reproduction instructions](../../../PUBLICATION.md).
