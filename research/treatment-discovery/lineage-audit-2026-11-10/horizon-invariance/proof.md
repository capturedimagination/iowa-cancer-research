# Family selection and calendar-time rates

Checked November 10, 2026. This is an original derivation recorded for this project, not a claim of a new theorem. The [prior-art audit](../horizon-invariance-prior-art.md) distinguishes the proposed application from established branching and lineage-sampling ideas.

**Changing the survival-selection horizon is not a test for constant birth and death rates.** The invariance survives arbitrary shared deterministic calendar-time schedules under the conditions below. It provides a possible check of the broader branching and observation model.

## Model and estimand

A single founder starts at calendar time zero. Each living cell independently splits into two daughters at rate `lambda(t)` and dies at rate `mu(t)`. All cells share these deterministic nonnegative, locally bounded schedules. Daughters follow the same future schedules, independent of their ancestry. Thus cell age, inherited state, founder frailty, interactions and unobserved random environments are outside this model.

Define a tag prospectively: at each tagged division, choose either daughter with probability one half, independently of subsequent fate. Keep the path dead once it dies. At horizon `T`, retain the founder if **any** family descendant remains alive, `F_T={N(T)>0}`. Let

`Q_T(t) = P(tag alive at t | F_T)`, for `0 <= t <= T`.

This is not the ancestry of a randomly chosen surviving endpoint cell. That ancestry is necessarily alive through `T`. Equal founder weighting and complete family ascertainment are required.

Write `L(t)=integral_0^t lambda(u)du` and `M(t)=integral_0^t mu(u)du`. Then

```text
Q_T(t) = exp[-L(t)]
         + exp[-M(t)] integral_0^t lambda(u) exp[M(u)-L(u)] du.
```

The right-hand side contains no `T`. Compare the same absolute `t` across different `T`, not endpoint values `Q_T(T)` at different elapsed times. This holds on the common observed interval only, and conditional inclusion must have positive probability. Locally bounded rates over finite intervals ensure positive inclusion because the unbranched, surviving founder has positive probability.

## Finite-horizon derivation

Let `h(s,T)` be the probability that one cell present at `s` has at least one living descendant at `T`. The binary branching property gives the backward equation

```text
partial_s h(s,T) = [mu(s)-lambda(s)] h(s,T) + lambda(s) h(s,T)^2,
h(T,T) = 1.
```

The unconditioned tag survives to `t` with probability `exp[-M(t)]`. Conditional on that survival, tagged division times before `t` form an inhomogeneous Poisson process of intensity `lambda(u)`. A discarded sister born at `u` has no descendants at `T` with probability `1-h(u,T)`, independently of the other discarded subtrees. Hence their joint extinction probability, averaged over tagged division times, is

```text
A(t,T) = exp[-integral_0^t lambda(u) h(u,T) du].
```

The descendants of the tagged cell present at `t` become extinct by `T` with probability `1-h(t,T)`. Therefore

```text
Q_T(t) = exp[-M(t)] {1-[1-h(t,T)] A(t,T)} / h(0,T).           (1)
```

Divide the backward equation by `h` and integrate to obtain

```text
A(t,T) = [h(0,T)/h(t,T)] exp[M(t)-L(t)].                    (2)
```

Next put `z(s)=1/h(s,T)`. Its linear equation and integrating factor give

```text
z'(s) = [lambda(s)-mu(s)] z(s) - lambda(s),
exp[M(t)-L(t)]/h(t,T)
  = 1/h(0,T) - integral_0^t lambda(u) exp[M(u)-L(u)] du.     (3)
```

Substituting (2) and (3) into (1) cancels `T` exactly. Piecewise schedules obey the same integral equations; values assigned at isolated jump times do not affect the result. No infinite-horizon or immortal-spine limit is used in this proof.

## Sequential representation and boundaries

Define two transient-state probabilities by

```text
x1' = -lambda(t) x1,
x2' = lambda(t) x1 - mu(t) x2,
x1(0)=1, x2(0)=0.
```

Then `Q=x1+x2` is exactly the displayed formula and `Q'=-mu(t)x2<=0`. This represents a time-inhomogeneous two-step process whose transition rates use **calendar time**. It is not generally a sum of independent waiting times measured from each state's entry.

For constant positive rates, the earlier hypoexponential law is recovered; equal rates give an Erlang-two survivor function. Interchanging two arbitrary calendar schedules need not preserve `Q`; constant-rate exchange symmetry is a special case. If either rate is identically zero, `Q=1` on the selected observation interval. This does not posit an exponential distribution with rate zero.

At the selection endpoint,

```text
Q_T(T) h(0,T) = exp[-M(T)].
```

Thus a matched prospective family-survival denominator identifies cumulative mortality `M(T)` in this broader model, not an instantaneous or constant death rate without additional assumptions.

The identity concerns the distribution right-censored at `T`. If the tag is alive at `T`, the selection event has already occurred; after `T` its future death hazard is the ordinary `mu(s)`. The two-step representation need not describe the entire actual lifetime beyond the selection horizon.

## What horizon agreement cannot establish

Calendar-time invariance does not imply constant rates, absence of heterogeneity, or absence of inherited biological states. For a mixture of founder types `Z`, each satisfying the model conditionally, the pooled survivor function is

```text
Q_mix,T(t) = E[h_Z(0,T) Q_Z(t)] / E[h_Z(0,T)].
```

Type weights can change with `T`, producing a discrepancy. They need not do so detectably. In particular, two constant-rate types with exchanged birth and death rates have identical `Q_Z(t)` even though their family-survival probabilities and net growth differ. Every mixture of those types retains horizon invariance. This is an analytic counterexample to interpreting a passing test as evidence against all heterogeneity; no new numerical experiment or empirical calibration was performed for it.

Conversely, a discrepancy could reflect age-dependent hazards, inherited states, random family environments, cell interactions, nonbinary reproduction, founder eligibility, missing descendants, informative tracking loss or an incorrectly defined tag. It does not uniquely identify a cancer mechanism.

## Frozen numerical verification

The [protocol](protocol.json) was locally frozen before the first check, after the analytic derivation was known. It specifies nine schedules: unequal/equal constants, increasing rates, increasing birth with decreasing death, opposite piecewise rates, oscillatory rates and three zero controls. Four horizons and fixed time grids produce 270 case/horizon/time points, plus 54 comparisons at shared times.

The [checker](../../../../scripts/check_lineage_horizon_invariance.py) compares (i) backward branching survival plus Poisson-functional quadrature, (ii) the explicit integral and (iii) a separately solved forward two-state ODE. All fixed cases passed without a changed grid or tolerance. Maximum absolute discrepancies were `2.931e-14` between (i) and (ii), `4.441e-16` between (ii) and (iii), and `2.975e-14` across selection horizons. The declared tolerance was `1e-8`. Endpoint, probability, monotonicity and zero-rate checks passed. These are numerical agreement checks, not statistical uncertainty or biological validation.

[Complete results and environment](results.json) retain every evaluated point, protocol/code hashes and failures (none). An [independent mathematical review](../calendar-rate-independent-review.md) separately checks the derivation and its limitations.

Reproduce from the repository root with the treatment-research Python environment:

```sh
python scripts/check_lineage_horizon_invariance.py --out tmp/horizon-invariance-reproduction.json
```

The script requires no source workbook and performs no fitted analysis. The protocol SHA-256 is `752885ddeb5de119deaa3a36dcd1d28e2735cf6bc222add08bb3dfb150133996`; the first-run script SHA-256 is `7be17332f2f76dad913847ed8b15bc9efe6182186fe663866942597cc13b1aa1`.

A later [packaging-only cleanup](packaging-note.md) removed trailing spaces from one blank source line. The packaged script hash is `1a26eea7ec3b1bf734003e3fa691848d7d21e60f75622b7ee403380b8219be3c`. Rerunning the unchanged frozen checks produced exactly the same result fields except the generation timestamp and script hash; the note preserves both runs' provenance.
