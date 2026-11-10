# Missing branches: prior art and interpretation limits

Audit date: November 10, 2026. **Conservative bounds over a fixed recorded roster can describe what its incomplete trees permit. They do not repair an unknown original cohort or, by themselves, test a population branching model.** Worst-case missing-data bounds and chronological lineage weights are established methods. No exact prior application of the proposed missing-daughter, family-selected `Q_T(t)` and cross-horizon envelopes was located in this bounded search; this is not evidence of first-ever novelty.

No cell-level outcomes were calculated or fitted for this audit. It reviews primary methods, the existing [structural audit](../hct116-structure/README.md) and the scope of the proposed calculation. The numerical bounds protocol and its implementation are separate work.

## Six relevant primary sources

| Source and review scope | Established result and boundary for this project |
|---|---|
| [Horowitz and Manski, 1998](https://doi.org/10.1016/S0304-4076(97)00077-8), *Censoring of outcomes and regressors due to survey nonresponse*; inspected the [October 1995 author manuscript](https://econwpa.ub.uni-muenchen.de/econ-wp/em/papers/9602/9602007.pdf), introduction and sections 2–3 | Derives worst-case conditional-mean bounds, including when missing outcomes also obscure the conditioning event. This is close prior art for unknown tag survival together with unknown family inclusion. Its response framework does not repair an unknown original cohort. The manuscript predates the final publication; the conditional bounding principle is established, although the proposed per-tree completion constraints differ. |
| [Imbens and Manski, 2004](https://doi.org/10.1111/j.1468-0262.2004.00555.x), *Confidence intervals for partially identified parameters*; publisher abstract and indexed opening of the [author-hosted paper](https://scholar.harvard.edu/files/imbens/files/confidence_intervals_for_partially_identified_parameters.pdf) | Explicitly separates an identification interval from a confidence interval accounting for estimation variability. Coverage of a parameter and coverage of its whole identified set are different objectives. This supports the interpretation boundary; its specific interval construction is not implemented or recommended here. Full PDF retrieval was blocked, so no full-proof review is claimed. |
| [Genthon et al., 2023](https://arxiv.org/html/2305.05406v2), published DOI `10.1103/PRXLife.1.013014`, *Cell lineage statistics with incomplete population trees*; sections II–III, empirical application, growth bounds and Discussion | Gives forward branch weights, includes terminated lineages, and derives bounds on population growth. Its broad termination category includes biological death and removal. Those growth bounds are not worst-case biological-fate bounds for an unobserved daughter. Its known lineage-ending status cannot license coding a missing biological branch as dead. |
| [Nakashima et al., 2020](https://arxiv.org/html/1806.00215v4), published DOI `10.1093/bioinformatics/btaa040`, *Lineage EM algorithm for inferring latent states from cellular lineage trees*; introduction, Figure 4 and sections 3.1–3.3 | Distinguishes random forward daughter paths, endpoint-surviving ancestries and whole-tree samples; discusses pruning and frequent tracking terminations. Bias-aware latent-state inference is already known. It does not supply the proposed nonparametric missing-branch family-selection envelope in the inspected material. |
| [Yamauchi et al., 2022](https://elifesciences.org/articles/72299), DOI `10.7554/eLife.72299`, *A unified framework for measuring selection on cellular lineages and traits*; weighting Methods and Discussion | Uses chronological/retrospective tree weights and identifies inference from incomplete tree information as an unresolved extension of that framework. This is direct prior recognition of the information problem. It does not establish that the specific envelope calculation here is new or biologically identifying. |
| [Iyer et al., 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12469175/), DOI `10.1371/journal.pcbi.1013446`, *Inheritable cell-states shape drug-persister correlations and population dynamics in cancer cells*; main Methods and [Supporting Text](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1013446.s001&type=supplementary), sections 1 and 13 | Uses random forward-daughter fate sampling in HCT116 trees. Its documented exclusions include never-dividing founders and lineages with missing cells; later-entering founders are also present. These choices cannot silently become an outcome-independent prospective roster for a different estimand. No missing-daughter worst-case `Q_T(t)` bounds were located in the reviewed material. |

The [earlier horizon audit](../horizon-invariance-prior-art.md) covers family selection, its mathematical null and substantial additional branching-process prior art. General lineage-selection bias, incomplete-data bounds and the `2^-g` weights are not proposed discoveries.

## Define the finite-record target first

Fix a recorded baseline roster `R`, a baseline frame and an event-timing convention before examining outcomes. For each possible completed set of trees compatible with the recorded information, let `u_i(t)` be the probability that a future-blind random daughter path from baseline cell `i` is alive at elapsed time `t`. Let `f_i(T)` indicate whether **any** descendant of that baseline cell is alive at selection horizon `T`. The finite-record summary is

```text
q_R,T(t) = sum_{i in R} f_i(T) u_i(t) / sum_{i in R} f_i(T),
```

provided at least one family is included. It averages equally over selected baseline cells; it is not a count weighted by clone size. A tag may be dead while another branch of the same family survives. Endpoint-survivor ancestry is a different sampling rule.

If a compatible completion has no selected family, the conditional summary is undefined there. An interval computed only over nonempty selected sets must state that restriction and separately retain zero-denominator feasibility.

An envelope ranges over compatible unknown facts while holding this roster fixed. Its usefulness is concrete: it can show which values are forced, excluded or unresolved **within that recorded roster and graph interpretation**, and how much missing branch information can matter. It can prioritize source clarification. It does not include unrecorded original founders merely because their descendants might have existed.

At a verified binary division, a daughter's chronological path weight is half its parent's. The relevant depth starts at the chosen baseline, not at an earlier source root. An absent daughter retains its unknown half-weight. Do not redistribute that mass onto the observed sister. These weights are probabilities of random paths within a tree; they are not inverse probabilities that a founder or tree entered the source file.

## Conservative bounds versus sharp completion bounds

Intervals `l_i(t) <= u_i(t) <= b_i(t)` combined with mandatory/optional family inclusion can provide a useful relaxation of the tree-completion problem. Optimizing the conditional average over this larger set gives conservative outer bounds if every legitimate completion is represented. Sharpness for the relaxed variables does not establish sharpness for biological trees.

At minimum, real completions couple the variables: tag survival is nonincreasing in time; family inclusion at a later horizon implies inclusion at every earlier horizon; a family extinct at `T` has zero tag-survival probability at `T`, but may have positive tag survival earlier. A family alive at `T` has positive endpoint tag weight in a finite resolved tree, although an unrestricted missing subtree can make its infimum approach zero. An infimum need not be attained. Missing identities, uncertain event times and mask conflicts can impose further constraints or require a wider completion set.

Subtracting separately valid marginal envelopes gives a valid outer envelope for a horizon difference, but generally loses information from the shared roster, nested inclusion and common tree completion. Even if zero lies in every pairwise contrast envelope, there need not be one joint completion making all curves equal. Conversely, an empty feasible completion set can indicate inconsistent graph/timing assumptions rather than a biological finding. These are mathematical review conditions, not assertions that the current implementation computes sharp joint bounds.

## Why complete-subtree filtering can change the target

Keeping only subtrees with no future tracking issue uses post-baseline information. It can depend on division count, survival time and the number of daughter observations needed. A simple analytic illustration is enough: if each of `B` required tracking links is independently observed with the same probability `p`, then the probability that the whole tree is complete is `p^B`. A constant local tracking success rate therefore still reweights trees by their number of tracking opportunities. This is an illustration of selection, not a model fitted to this dataset.

Complete cases can be a clearly labeled descriptive subset or a sensitivity analysis. They do not establish the prospective distribution without an applicable observation model or additional independence argument. Replacing an unobserved daughter by the visible sister, marking it dead, or repeatedly redrawing until a path reaches a visible endpoint also changes the target.

## Unknown original eligibility limits population claims

For an intended population, let `R` indicate inclusion in the recorded-baseline roster and `F_T` family survival. Write `pi_T=P(R=1 | F_T)`. Formally,

```text
Q_T(t) = pi_T E[u(t) | F_T,R=1]
         + (1-pi_T) E[u(t) | F_T,R=0].
```

If the recorded conditional population mean were known to lie in `[L,U]` and `pi_T` were known, the elementary `[0,1]` support restriction would give `[pi_T L, pi_T U + 1-pi_T]`. This is an explanatory missing-data decomposition, not a calculated population bound for the present records. The finite-record envelope is not automatically a bound on that conditional population mean.

When the relevant coverage `pi_T`, original eligible roster and selection mechanism are all unknown, extending recorded-roster conclusions to the original population generally has only trivial `[0,1]` restrictions in closure. A raw overall recording fraction would not by itself identify the family-survivor-specific coverage `pi_T`. A genuine original-cohort bound requires a stated denominator/coverage restriction, defensible inclusion model or additional source information; it cannot be obtained merely by tightening the trees already observed.

For the same reason, narrowing the envelope after choosing complete subtrees is not evidence that population inference improved. It may simply have changed which cells the calculation describes. Alternative baseline frames are separate rosters and timing sensitivities, not interchangeable replicates or a search for the most favorable result.

## A deterministic envelope is not a statistical rejection

The shared-calendar branching result concerns population conditional survivor functions. Even fully observed finite cohorts generated under that model can have unequal empirical horizon curves. A finite-record contrast envelope excluding zero says that all completions in the stated relaxation have the same sign for that empirical contrast. It does **not**, alone, reject the stochastic population null.

Population inference would additionally require a justified sampling frame, a model or design for recording, dependence-aware sampling uncertainty and prespecified multiplicity handling. Different baseline cells may share original ancestors; repeated horizons share the same trees. Unknown original families or replicate assignments cannot be solved by treating cells as independent observations. Bounds' width measures ambiguity from missing information, not a confidence level. No confidence procedure is selected or implemented in this audit.

## Decision and bounded search

The defensible project contribution is an auditable application of known bounding and path-weighting principles to a precisely defined incomplete record. It could establish recording-compatible ranges, expose sensitivity to missing daughters, and identify the data needed for a later test. **It presently supports no new cancer mechanism, no correction of the original biological conclusions, and no population falsification result.**

Six core primary sources were inspected at the scopes stated above. Sixteen focused web queries covered missing branches, incomplete cell trees, partial identification, worst-case bounds and selection. The exact queries, source URLs, versions, access limits, hashes and claim statuses are saved in [prior-art.json](prior-art.json). Broad queries returned many irrelevant hits; those were not treated as evidence. Two additional lineage-method papers were screened but do not establish the proposed envelope application. The search was not systematic or exhaustive and did not audit every source-code repository. No authors were contacted.
