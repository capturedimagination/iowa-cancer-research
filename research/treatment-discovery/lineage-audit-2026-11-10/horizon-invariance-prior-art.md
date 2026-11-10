# Horizon invariance: prior art and proposed empirical use

Audit date: November 10, 2026. Scope: a bounded primary-literature check, not an exhaustive novelty search. **No exact empirical application of this particular cross-horizon survivor-function check was located in the inspected material. That is not a first-ever claim.** Its components—chronological sampling, survival-selection bias, branch weighting, competing risks and inherited-state models—have substantial prior art.

The proposed test also needed a scope correction. Horizon invariance holds when all cells share deterministic **calendar-time** birth and death schedules, including changing schedules. It cannot distinguish constant rates from that broader model. An [original finite-horizon derivation](horizon-invariance/proof.md), [frozen verification protocol](horizon-invariance/protocol.json), [complete numerical results](horizon-invariance/results.json) and [independent review](calendar-rate-independent-review.md) document this result without claiming a new theorem.

## Exact question

Start with one founder at time zero. Trace a prospective random daughter at every division, retaining the path after it dies. Separately, retain the founder if **any descendant** remains alive at selection horizon `T`. For a common earlier absolute time `t`, compare

`Q_T(t) = P(random tag alive at t | family has a living descendant at T)`.

The tag can be dead even though its family survives. Sampling an endpoint survivor and tracing its ancestry answers a different question and gives survival through the endpoint by construction. Comparing `Q_T(T)` for different endpoints also changes `t` and does not test the invariance.

## Six closely relevant primary sources

| Primary source and inspected material | Known contribution; relationship to this proposal |
|---|---|
| [Iyer et al., 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12469175/), DOI `10.1371/journal.pcbi.1013446`; main Methods/Results and [supplement](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1013446.s001&type=supplementary), especially sections 1, 5, 8 and 13 | Closest cancer analysis. Uses HCT116 full trees, U2OS random-sister paths, age-dependent competing risks, inherited states and endpoint-fate fluctuation analysis. Random forward-path sampling is already used for the latter. I did not locate the exact family-selected `Q_T(t)` comparison across selection horizons. Its age-dependent baseline is broader in a different direction than the shared-calendar model; a discrepancy here would not by itself demonstrate inheritance. |
| [Chakrabarti et al., 2018](https://www.nature.com/articles/s41467-018-07788-5), DOI `10.1038/s41467-018-07788-5`; main text, lineage-correlation results and tracking Methods | Source of the HCT116 full-lineage resource. Studies division/death timing, related-cell correlations and oscillatory fate models; explicitly discards ambiguous cell identities. This establishes relevant biology and a possible resource, not a complete prospective sampling frame. The exact cross-selection-horizon test was not located in the inspected main text. |
| [Genthon et al., 2023](https://arxiv.org/html/2305.05406v2), published DOI `10.1103/PRXLife.1.013014`; sections II–IV, especially incomplete-lineage sampling and the antibiotic-data application | Explicitly includes terminated lineages, separates reproductive and survival selection, and applies the framework to antibiotic-exposed mycobacteria. Time dependence, empirical survival bias and nonparametric rate inference under extra conditions are known ideas. Its survival conditioning concerns the sampled lineage, rather than our additional founder-any-survivor selection followed by a possibly dead tag. No exact empirical horizon-invariance test located. |
| [Nakashima et al., 2020](https://arxiv.org/html/1806.00215v4), published DOI `10.1093/bioinformatics/btaa040`; Figure 4, sections 3.1–3.3 and latent-state method | Explicitly distinguishes chronological random-daughter paths, retrospective endpoint ancestries and whole-tree sampling. A chronological path can terminate; a retrospective survivor ancestry cannot. Bias correction and latent-state inference from trees are already established. The proposed observation-rule distinction is therefore not new. No exact family-selected cross-horizon diagnostic located. |
| [Yamauchi et al., 2022](https://elifesciences.org/articles/72299), DOI `10.7554/eLife.72299`; theoretical background, empirical applications, Discussion and weighting Methods | Quantifies lineage selection using chronological and retrospective weights and applies it to bacterial and mammalian data, including changing growth conditions. General methods based on tree weights without fitting a detailed growth model already exist. This is close methodological context, but the inspected material does not give the particular family-selected tag-death invariant proposed here. |
| [Oren et al., 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC9209846/), DOI `10.1038/s41586-021-03796-6`; live-imaging Methods, Figure 1 and Extended Data Figure 1 | Motivates the ascertainment question: endpoint cells identify founder lineages, followed by one path per lineage. Random sister selection is explicit for nonpersisters; the exact rule and retained-dead-path handling for retrospectively selected founders remain unresolved. This source cannot presently be treated as an implementation of the mathematical sampling rule. The [dictionary audit](source-dictionary.md) remains the gate. |

The [earlier novelty ledger](novelty-and-identifiability.md) additionally reviews branching-process spine/backbone work and related finite-horizon sampling theory. This follow-up does not displace that substantial mathematical prior art.

## What the checked result supports

For shared deterministic calendar-time rates, write `L(t)=integral lambda` and `M(t)=integral mu`. The exact result is

```text
Q_T(t) = exp[-L(t)]
         + exp[-M(t)] integral_0^t lambda(u)exp[M(u)-L(u)]du,
         0 <= t <= T.
```

The expression is independent of the selection horizon. Nine frozen schedules, 270 evaluation points and 54 cross-horizon comparisons passed the independent numerical forms; maximum cross-horizon discrepancy was `2.976e-14` against the declared `1e-8` tolerance. This verifies implementation of a mathematical implication. It does not test a cancer dataset.

Horizon disagreement could falsify the conjunction of shared Markov branching and the specified observation rule. It would not identify which assumption failed. Cell-age hazards, inherited states, random environments, cell interactions and incomplete tracking are distinct possibilities. Deterministic treatment-time changes shared by all cells are **not** excluded by a passing result or identified by a failing result within this model.

Passing is also compatible with some genuine heterogeneity: constant-rate founder types with birth/death rates exchanged share exactly the same selected-tag death law. Every mixture of those types remains horizon invariant despite different family growth. General mixture weights are proportional to each type's family-survival probability at `T`; changes in those weights sometimes, but not always, produce an observable discrepancy. These are analytic limitations, not fitted examples.

## Proposed disconfirmatory design, not an executed analysis

1. **Freeze the cohort and observation rule.** Use the same prospectively eligible founders at one known origin for every horizon. Retain never-dividers, extinct families and dead tags. Do not change eligibility according to later division, survival, available descendants or horizon. Resolve treatment timing, missing identities, censoring and complete family ascertainment before any test. Current Oren files fail that gate; the [HCT116 resource audit](next-empirical-resource.md) has separate unresolved selection and tracking issues.
2. **Freeze common absolute times and endpoints.** Choose horizons from the verified observation schedule, before inspecting outcome curves. Compare only common `t` no later than the earliest chosen horizon, with a fixed dose/condition and explicit handling of repeated experiments. A new empirical protocol is required; this memo supplies no optimized cutoff or observed effect.
3. **Use prospective random paths or their exact tree weights.** One fate-independent tag per founder suffices. With complete binary trees, summing `2^(-k)` over each founder's cells alive at `t` gives its forward-path survival probability `U_i(t)`, where `k` is the number of divisions from that founder to the cell. Then estimate `Q_T(t)` by the mean of `U_i(t)` among founders alive as families at `T`. This uses established chronological weighting and avoids adding artificial tag-sampling noise; it is not a new weighting method.
4. **Respect dependence.** Horizon-selected sets are nested, and paths within a tree share ancestry. Resample the original independent units once and recompute every horizon contrast together; do not treat cells, sampled tags or endpoints as independent replicates. If treatment-start cells share earlier ancestors, use that original family cluster; if independent experiments are the relevant unit, preserve that level too. Freeze the contrast, interval/test procedure, multiplicity control and minimum information before outcomes. Naive permutation of family-survival labels is not justified by the null.
5. **Preserve interpretation and negative outcomes.** Publish the differences, intervals, numbers of independent founders and missing-family sensitivities, including a null result. A failed check warrants an observation audit and comparison against explicit age-dependent or heterogeneous alternatives. It does not establish a persister program. A passing check is limited agreement with one necessary model implication, not proof of the model.

A useful application would show whether a documented dataset departs from a consequence of shared Markov branching **without estimating birth/death rate parameters**. This could motivate a more specific follow-up model or reveal that selection/tracking prevents inference. Merely reproducing Iyer's division/death fits, lineage correlations or random-daughter endpoint counts would not accomplish that distinct check. No empirical curves, parameter estimates, investigator contact or biological discovery are reported here.

## Search bounds and provenance

Twelve additional web queries were run on November 10, 2026, alongside direct primary-source inspection and reuse of the prior audit's pinned originals. They covered lineage/horizon invariance, survival conditioning, chronological versus retrospective paths, time-inhomogeneous tagged branching and the closest cancer papers. Unrelated search hits and secondary reviews were not used as evidence. The exact queries, review scope, source URLs/hashes, numerical provenance and claim statuses are in the [machine-readable ledger](horizon-invariance-prior-art.json).

This was not a systematic review of every database, all mathematical texts, all supplementary code or unpublished work. Failed access to current Nature/PMC pages was supplemented by previously pinned publisher originals; those access paths are recorded. Absence of an exact match in these sources remains a bounded observation. The defensible contribution is a reproducible proposed application and a corrected statement of what it can falsify, pending eligible data and external scientific review.

The [packaging note](horizon-invariance/packaging-note.md) records a trailing-whitespace-only source cleanup and identical rerun. First-run provenance remains explicit; the protocol and scientific findings are unchanged.
