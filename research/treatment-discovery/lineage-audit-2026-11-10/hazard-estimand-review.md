# What the sampled lineage can identify

November 10, 2026. **Do not estimate an unconditional division or death hazard from the workbook until the entry cohort, path-selection rule, event dictionary and observation times are verified.** This is a methods review and analytic control specification. No workbook measurements were analyzed, no biological rates were fitted, and no authors were contacted.

The [previous resource audit](../discovery-2026-11-10/mechanistic-simulation/v2/validation-data-route.md) identifies a potentially useful event-matrix deposit, not a validated hazard dataset. The decisive distinction is between following a randomly chosen daughter from every enrolled founder, following that same random path only in families selected for endpoint survival, and reconstructing an ancestry that necessarily reaches an endpoint survivor.

## What the primary paper establishes

Oren et al. describe forward tracking with random sister selection for nonpersisters. Persister founders were identified backward from final-frame cells, followed by one forward path per lineage. The survivor-path sister-choice algorithm and how these sampling groups form the final cohort remain insufficiently specified for an unconditional hazard analysis. Acquisition intervals change during the experiment. Reported cycle times also use different entry definitions for untreated and persister cells. [Primary author manuscript, Methods pp. 9–10 and Fig. 1](https://escholarship.org/content/qt71d7s3v6/qt71d7s3v6.pdf), [published article](https://www.nature.com/articles/s41586-021-03796-6).

The dictionary audit's reading of Extended Data Fig. 1b supports common forward tracking after founder identification; it does not establish complete cohort enrollment or certify a branch-selection/export algorithm. Do not assume that every deposited persister row is an endpoint-connected ancestry, or that every row is a prospectively sampled random path. Numeric trajectories alone cannot establish which sampling operation produced them.

## Distinct estimands

| Observation scheme | Defensible target with a complete dictionary | What cannot be inferred without additional information |
|---|---|---|
| All eligible day-0 founders enrolled; one daughter chosen randomly at each division, irrespective of future fate | Cause-specific division/death intensities along the sampled chronological paths, conditional on observed history and entry cohort | An unweighted population-cell hazard under heterogeneous growth, clone extinction, or tolerant-state exit |
| Founders selected because **any descendant** survives to time T; a genuinely random forward path is then followed | Hazards conditional on family survival and that sampling rule; the sampled path can die before T | Unconditional founder/path hazards by ignoring selection; a death-free ancestry interpretation |
| A path is reconstructed specifically to an endpoint surviving cell | Ancestral division history under the specified terminal-cell sampling rule | Unconditional death hazard; the ancestry has no death before T by construction |
| All founders and their complete trees are observed | Cell-population event intensities using all observed cell-time, and separately defined family survival/extinction outcomes | A functional tolerant-state transition without observed state labels |

Complete, mutually exclusive outcome strata could reconstruct a prospective cohort only if enrollment, overlap, inclusion probabilities and **the same path rule** are verified. Concatenating retrospectively selected survivors with differently sampled failures does not establish that property. Correcting for endpoint selection requires the selection mechanism, not merely a binary endpoint column.

Chronological, retrospective and tree sampling are established distinctions. [Nakashima et al., 2020](https://academic.oup.com/bioinformatics/article/36/9/2829/5714738) and [Igelbrink and Ischebeck, 2024](https://link.springer.com/article/10.1007/s00285-024-02105-9) provide relevant prior work. [Iyer et al., 2025](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013446) also treats division/death competing risks in cancer-cell histories. This review does not claim a new principle of sampling bias.

## Risk time, entry and censoring

For a prospective sampled path i, define `Y_i(t)=1` only when its currently tracked cell is alive, in observation and eligible at time t. Division ends a mother's cell episode and starts the selected daughter's episode; **the path risk count stays one, not two**. Death ends that path. A branch not selected is not a death. Its descendants' fate remains unobserved by that path, so path death is not family extinction.

In a calendar-time bin B, a descriptive exposure-based intensity is `division events / sum_i integral_B Y_i(t) dt`, with the same denominator for death events. It estimates a risk-time-weighted average of the chosen path hazards, not a rate per original row or per completed cycle. With exact event times, constant hazards have likelihood contributions `lambda^D mu^M exp[-(lambda+mu)A]`, where A is tracked cell-time, D divisions and M deaths. Daughter resets do not create extra person-time. Uncertainty must preserve founder dependence and independent experimental replicates; frame columns and repeated divisions are not independent biological replicates.

- **Clock:** time since drug exposure and age since the tracked cell's birth are different covariates. An initial cell may have an unknown birth time; its time to first observed division is not a complete cell cycle. Delayed observation requires explicit entry times.
- **Observation:** use actual timestamps, including acquisition gaps and changing frame intervals. If an event is only located between frames, retain that interval. Do not declare a regular matrix-column spacing without its export map or invent exact event ordering within a frame gap.
- **Competing events:** division and death compete within a cell episode. A daughter begins a new episode after division. Death removes the cell from division risk, but treating it as ordinary noninformative censoring in a naive Kaplan–Meier probability of eventual division changes the estimand. Cause-specific intensities and cumulative incidence are separate quantities.
- **Censoring:** distinguish administrative end of imaging, tracking loss, leaving the field and missing annotation from biological death. Conditional independent censoring is an assumption requiring support; fate-dependent loss can invalidate ordinary risk-set estimates.
- **Cycle summaries:** selecting a first mitosis after a landmark and averaging later cycles conditions on division and observation. It cannot by itself identify the next-division hazard among every cell alive at that landmark. Do not decode a `censoring_status` column from its name alone.

A population-cell target is possible under stronger design information. With verified prospective founder sampling and independent one-half daughter choices, a generation-g tracked cell has inclusion probability `2^(-g)` within its realized tree. Weighting its event/cell-time contribution by `2^g` (and any founder sampling weight) gives Horvitz–Thompson totals in expectation. Ratios require adequate independent founders and can have large variance. Missing generations, unknown branch choices or endpoint-selected founders invalidate this simple correction. It is **not authorized as a correction for the present workbook**.

## Independent analytic controls for the simulation

These are derivations under declared hypothetical models, not findings about Oren's cells. Let lambda be a constant binary-division hazard and mu a constant death hazard. Descendant cells evolve independently with identical hazards. A tracked mother is replaced by one randomly selected daughter; its sister starts an independent side branch.

**1. Prospective unselected path.** The tracked path is alive with probability `exp(-mu*t)`. Over a horizon T, expected at-risk time is `(1-exp(-mu*T))/mu`, with limit T when mu=0. Expected division count is lambda times this exposure; expected death count is `1-exp(-mu*T)`. Event/exposure ratios across many independent founders converge to lambda and mu. They are not asserted to be finite-sample unbiased ratios. Full population size instead has expectation `exp((lambda-mu)*t)` per founder; substituting this population count for the sampled-path denominator is wrong.

**2. Endpoint selection of the tracked path itself.** Conditioning on the path surviving to T forces observed death hazard to zero before T. Under these independent homogeneous clocks, division remains a Poisson process with rate lambda: selection does not automatically bias every division estimate. Conditioning on path death by T instead gives `mu / [1-exp(-mu*(T-t))]`, an increasing death hazard even though the generating rate is constant. These controls must remain distinct from family-survival selection.

**3. A surviving family followed by a random tagged path.** This independently checks the parent workflow's proposed primary null. Let q(s) be the extinction probability by s of the entire descendant tree from one cell:

```text
q(s) = mu * [1-exp(-(lambda-mu)*s)] /
       [lambda-mu*exp(-(lambda-mu)*s)]          if lambda != mu
q(s) = k*s/(1+k*s)                            if lambda = mu = k
A(t) = exp(lambda * integral_0^t [q(T-u)-1] du)
R(t) = exp(-mu*t) * [1-q(T-t)*A(t)]
```

Here R is the **joint** probability that the tag is at risk and its founder family survives to T. Divide R by `1-q(T)` to obtain the selected-cohort risk probability. Side-branch extinction probabilities multiply; averaging over the tag's Poisson division times gives A. A division at t produces two future descendant trees, whereas tag death leaves only earlier side branches. The marginal selected-cohort hazards therefore are:

```text
division(t) = lambda * [1-q(T-t)^2*A(t)] / [1-q(T-t)*A(t)]
death(t)    = mu     * [1-A(t)]          / [1-q(T-t)*A(t)]
```

The tag can die and the family still survive. At t=0, the division hazard is `lambda*(1+q(T))` and death hazard is zero. As t approaches T, division tends to lambda and death tends to `mu*(1-A(T))`, **not generally mu**. A strong conservation check is `R'(t) = -mu*exp(-mu*t)*(1-A(t))`: division renews the tag rather than removing it from risk.

For `r=lambda-mu != 0`, algebra independently yields:

```text
A(t) = [lambda*exp(r*(T-t))-mu] / [lambda*exp(r*T)-mu]
P(tag alive at t | family survives T)
     = [lambda*exp(-mu*t)-mu*exp(-lambda*t)]/(lambda-mu)
death(t) = lambda*mu*[1-exp(-r*t)]/[lambda-mu*exp(-r*t)]
```

The selected tag-risk probability and death hazard are independent of T for `0<=t<=T` in this model; the selected division hazard still depends on T. In the critical case lambda=mu=k, they reduce to `exp(-k*t)*(1+k*t)` and `k^2*t/(1+k*t)`. For k=1, T=2, t=1, q=1/2, A=2/3, selected division=1.25, selected death=0.5 and selected risk=2/e. Pure birth (mu=0) and no division (lambda=0) provide separate zero-boundary controls.

This model excludes inherited frailty, correlated/asymmetric sister fates, density dependence, age dependence, time-varying biology and informative tracking loss. A mismatch with its predictions would not prove biological memory. It is not a certified representation of the workbook's selection protocol.

**4. Same tree, different sampling rules.** Consider three terminal cells at generations 1, 2 and 2. Random daughter choices give probabilities 1/2, 1/4 and 1/4, so expected divisions along the path are 1.5. Uniform selection among the three terminal cells gives 5/3. Equal founder weighting does not make these within-founder rules identical. The weighted terminal-cell total has expectation `(1/2)*2+(1/4)*4+(1/4)*4=3`, checking the conditional `2^g` design weighting.

**5. First-event interval control.** If the first event in an observed interval of length delta is fully classified, constant competing hazards give `P(no event)=exp(-(lambda+mu)*delta)` and `P(event type k)=hazard_k/(lambda+mu)*[1-P(no event)]`. These sum to one. This is a first-event calculation, not permission to ignore a division followed by death or multiple divisions in an unresolved interval.

The [structured review](hazard-estimand-review.json) records formula checks and minimum gates. No empirical time-varying rate should be compared with these controls until the observation/selection mechanism has been fixed independently of the apparent result.

## Minimum analysis gate

1. **Cohort and selection:** a day-0 founder roster, enrollment/exclusion logic, sampling probabilities, outcome ascertainment, explicit forward versus retrospective branch rules and duplicate-founder handling. Verify which rows share a founder and how endpoint-selected and nonselected paths were combined.
2. **Dictionary and time:** verified event versus cumulative encoding, death versus missing/background values, row identities and cross-sheet joins, actual elapsed-time map, exposure history and valid tracking windows. A matrix shape or apparent monotonicity cannot certify these meanings.
3. **Risk and loss:** birth/entry times or a calendar-time-only estimand, end-of-follow-up reasons, lost-track handling, administrative horizon, lineage and independent-experiment IDs. Preserve all eligible nondividing/censored paths.
4. **Frozen target:** choose chronological-path, selected-family or population-cell inference; specify denominator, any justified weights, dependence/uncertainty method and observation model before fitting. Pass the relevant analytic controls and selection-misspecification simulations.
5. **Decision:** if selection/censoring/time fields remain unverified, retain a **no-go for hazard estimation**. Source-linked structural/descriptive checks can proceed with their limitations, but do not call them a validated event-rate model. Tolerant-to-sensitive exit remains no-go without same-lineage functional transitions and state-specific exposure, regardless of whether division/death gates pass.
