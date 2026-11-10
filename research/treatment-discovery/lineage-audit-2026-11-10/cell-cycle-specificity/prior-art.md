# Planned study: prior art and identification limits

2026-11-10. **Planning and source audit only.** No new simulation outcomes, empirical fitting, external contact or public edits. This supplements the earlier proposal; it does not freeze or change its grid.

The bounded search found close prior art for **paired sister-subtree statistics**, so that general idea should not be presented as new. The exact combination of a prospectively eligible, fixed-lag binary subtree-survival covariance and this project's family-selected horizon contrasts was not located in the inspected sources. That negative search result does not establish originality. A useful deliverable remains a reproducible specificity audit of explicitly defined measurements.

## Keep three observations distinct

Let a qualifying mother's division occur at calendar time `b`. Register both daughters at birth using only past information and fixed administrative follow-up. For daughter `j`, define `A_j(s)=1[N_j(b+s)>0]`, where `N_j` counts **living descendants at that instant**, including the daughter if still alive. The proposed statistic is `C(s)=Cov(A_1(s),A_2(s) | qualifying division)`, with common calendar/experimental context conditioned on when necessary.

This is neither correlation of sisters' cycle lengths nor correlation restricted to sisters that eventually divide or die. It is also not covariance of cumulative descendants ever born. An extinct subtree can contain many historical cells.

Separately, `Q_T(t)=P(prospective random tag alive at t | N_founder(T)>0)` and its common-time horizon contrasts condition on future **family** survival. The sister statistic must not inherit that future-survival filter. Keep dead random tags; an endpoint-survivor ancestry answers another question.

## Closest primary evidence

| Primary source and inspected scope | Relation to this study |
|---|---|
| [Korsnes & Korsnes, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10686135/), §§3.2, 3.4 and Discussion, Figs. 4 and 6 | Fig. 4 pairs first-generation sisters' descendant counts within 70 hours, with births within 20 hours. Fig. 6 instead pairs total descendant track lengths at 60 hours, with births within 30 hours, and stratifies by future tree death. The Discussion explicitly proposes covariance of sister-subtree summaries. This is close prior art, not merely cycle-time correlation. Whether Fig. 4 counts extant or cumulative descendants is not resolved by its caption/text; do not equate it with `A_j(s)`. No code audit was performed. |
| [Iyer et al., 2025](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013446), main Methods/Results and S1 §§1, 5, 8–13 | Direct cancer age-dependence/inheritance comparison; equations and observation distinctions are detailed below. |
| [Chakrabarti et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6299096/), fate-correlation Results and Fig. 2 | Individual end fates and lineage relations, including pre/post-drug sister groups; unrelated cells matched by distance and cell-cycle-phase checks address particular confounders. These are genuine existing controls. They do not certify our binary subtree estimand or exclude every latent family environment. |
| [Belluccini et al., author preprint 2021 / publication 2022](https://arxiv.org/abs/2112.00371), current author abstract; [published article](https://doi.org/10.1038/s41598-022-14202-0) | Competing Erlang division and exponential death are established. Current publisher access failed; this pass does not claim a full-paper/code re-audit. |
| [Genthon et al., 2023](https://arxiv.org/html/2305.05406v2), main sampling framework, with the existing project source audit | Forward/backward sampling and dead-lineage handling already distinguish different survival-selection mechanisms. No exact paired statistic was located in the inspected scope. |
| [Weinreb & Klein, 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7382289/), branching model, PGF moments and sister-choice assumptions | Clonal-count covariance and its dependence on branching assumptions are established. Their variables are developmental/barcode counts, not this prospective daughter pair's binary survival at a fixed elapsed lag. |

If Korsnes's count is eventually confirmed to be extant `N_j(s)`, binary survival is a straightforward coarsening of its joint counts. If it is cumulative, it cannot encode extinction that way. Either finding would narrow interpretation, not justify a new-method claim.

## What Iyer actually models

Its M0 is age structured, not limited to exponential timers. Main Eq. 1 / S1 Eq. 13 uses

`1 = 2∫ b(a) exp[−γa−∫₀ᵃ(b(u)+μ(u))du] da`.

S1 Eqs. 30–31 and 35–36 specify `h=f/S`, integrated-hazard survival, and cause-specific event density `h_m S_total`. EMG timers, treatment-straddling cells, drug-effect delay, quiescence and censored observations enter the inference. Exponential clocks are an illustrative competing-risks calculation, not the entire baseline.

M1 assigns pre-existing states/fates; M2 assigns drug-time fates without pre-existing states; M3 combines state-dependent fate probabilities with inheritance. Decay and lineage-fate patterns constrain those alternatives. Its fluctuation analysis follows a random daughter after division, then aggregates terminal tagged persisters; that differs from asking whether **any** descendant of each sister survives. [Main Methods](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013446), [S1 Text](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1013446.s001&type=supplementary).

Therefore an age-only counterexample for our new statistic does **not** refute Iyer's results or show that it omitted age dependence. This pass neither reproduces its numerical inference nor reconciles every straddler-clock expression with source code.

## What covariance can and cannot identify

The relevant reasoning is the ordinary branching property and law of total covariance, not a novel identity. Given a qualifying birth and fixed context, homogeneous newborn renewal clocks give independent future subtrees, hence `C(s)=0`, even for non-exponential division. With a perfectly shared type `Z`, conditional daughter independence gives

`C(s)=Var_w[h_Z(s)]`, where `h_Z(s)=P(N_j(s)>0|Z)`.

The weights `w` describe **eligible division pairs**, not the initial founder proportions. Equal `h_Z(s)` across types gives a blind spot. Partial transmission, correlated daughter innovations, maternal damage, unequal daughters and incomplete observations require their actual conditional model; do not apply the perfect-type formula automatically.

Shared calendar rates can generate covariance when birth times are pooled: both daughters inherit the same birth time, even without inherited biological type. Conditioning on exact birth time/context or using a correctly specified residual probability removes that particular mixture effect; coarse bins or estimated residuals do not guarantee it. Future-survival or future-completeness filtering also changes the null. A positive covariance alone does not prove inheritance, and a zero covariance does not exclude it.

There is an exact observational nonidentifiability counterexample. Let `O` be the entire observed tree and `K_z(O)` its distribution under a permanent inherited type. Re-label `z` as an unobserved permanent family environment with the same conditional event rules and mixing weights. Both models have

`P(O)=Σ_z π_z K_z(O)`.

Thus all tree statistics—including the joint distribution of `C` and horizon contrasts—are identical. This proves that a **universally valid** discriminator between those broad classes cannot exist from these observations alone. It does not assert that every partially transmitting state model equals a permanent environment. Distinguishing particular mechanisms requires additional restrictions, measured context or a designed intervention; spatial controls constrain specific environmental explanations, not all equivalent latent ones. This is a project-level identifiability argument, not an attribution of a novel theorem to the searched papers.

## Design implications to preserve before results

1. Keep the sister cohort prospective at birth and distinct from the endpoint-selected Q cohort. Retain both extinct subtrees and never-dividing daughters. Record unobserved outcomes as missing, not extinct.
2. Use the fixed birth cutoff and equal elapsed lags; condition calendar/context explicitly. Cluster uncertainty by original founder/experiment, not daughter or repeated endpoint.
3. Compare homogeneous renewal, independently redrawn latent labels and transmitted labels. Preserve the matched construction's actual limits: it matches initial timer mixtures, not every selected observable marginal.
4. Retain non-exponential no-inheritance controls, shared-calendar controls and a permanently shared-environment equivalence control. Explain identical models analytically rather than presenting a re-labeled simulation as independent support.
5. Describe the objective as distinguishing stipulated stochastic models and measuring failure modes. Do not imply a general inheritance assay, correction of Iyer, new cancer mechanism or cure.

## Access and audit limits

The companion [JSON ledger](prior-art.json) records all 12 additional queries, links, inspected scopes and local evidence hashes. Current PLOS main text, Korsnes PMC, Weinreb PMC, Genthon author manuscript and Belluccini author abstract were accessible. Iyer's supplement link failed in the web tool; its previously pinned PDF/text and cached primary HTML were read locally. Chakrabarti PMC was accessible initially but a later find request hit a challenge. Kuchen's PMC page and the lineage-variability-maps page also challenged access in this pass; they are screened related work, not fresh detailed evidence.

No attempt was made to bypass challenges, inspect private accounts, obtain author data, or exhaust all supplements, code, patents and unpublished work. The Korsnes count semantics and complete eligibility/censoring rules remain unresolved. These gaps limit exact-priority assessment but do not block a transparently bounded synthetic specificity study.

## Addendum: candidate early-time order law

Additional bounded check, 2026-11-10; seven targeted queries, before numerical outcomes. The parent supplied a symbolic candidate that is undergoing separate mathematical review. For an iid newborn renewal division timer with density `f_D(s)~c s^(k−1)`, independent constant death rate `μ`, and a fixed positive selection horizon T, the proposed result is

`1−Q_T(t) ~ μ c t^(k+1)/[k(k+1)]` as `t↓0`.

For Erlang division with shape k and **stage rate** α, this becomes `μ α^k t^(k+1)/(k+1)!`. The claim concerns a leading local term, not the full conditional distribution or global horizon invariance. The interpretation is that an early dead tag can belong to a surviving family only after an earlier division leaves a sister branch. To leading order, that sister's survival probability supplies the factor proposed to cancel the family-selection denominator. Exact regularity and remainder conditions remain the mathematical reviewer's responsibility.

**Prior-art assessment:** the multistep power and coefficient are familiar convolution mathematics. [Yates et al. (2017), §3.3, Eq. 30](https://arxiv.org/html/1705.09718v2) explicitly give the Erlang-plus-exponential convolution; its ordinary waiting-time CDF has this same leading coefficient. Their added stage is a division-timer construction, not our family-selected tagged-death event. [Belluccini et al.](https://arxiv.org/abs/2112.00371) already combine Erlang division with exponential death. Neither inspected scope supplied this exact fixed-T, family-conditioned early-tag-death statement. Existing project prior-art notes already constrain novelty for the k=1 birth–death case.

Two additional primary-source leads concern related concepts, not an exact match: [a tumor transit-compartment study](https://doi.org/10.1038/s41598-022-13836-4) uses Erlang/Coxian delayed death, and [an early-epidemic branching study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8596012/) examines survival-conditioned dynamics. Search-index excerpts located those topics, but current full-text requests failed/challenged; they are leads, not fully audited support. No broad citation chase or priority claim follows.

**Value judgment:** if the independent proof passes, this is a concise first-event asymptotic extension and a useful caution against counting biological killing stages from an endpoint-selected curve. The elementary convolution itself is not a substantial new method. The specific contribution would be the observation-rule explanation, finite-horizon cancellation and clearly tested boundaries. It does not contradict Iyer's age-dependent models or establish an empirical cancer finding.

**Boundaries to retain before freeze:** require one newborn founder, no atom of immediate division, independent renewal daughters and death clocks, a fate-independent forward tag, positive family inclusion, and a fixed T with `t≤T`; precise sufficient assumptions need review. A local `t^(k+1)` law must not be promoted to a global Erlang fit or stage count. Mixed-age/stage initialization changes the residual first-division law and can change the coefficient's horizon dependence. Loss of the newborn high order does not necessarily mean linear onset: a single aged founder with positive finite residual division density still requires a division followed by tag death. Pre-existing sister branches at the observation origin would constitute a different sampling model. These distinctions are proposed review/control requirements, not simulated results.
