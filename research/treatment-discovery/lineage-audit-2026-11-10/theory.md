# A two-stage lifetime law from family selection

Derived November 10, 2026. This is an exact identity for a specified synthetic observation model. The [prior-art audit](novelty-and-identifiability.md) found related two-exponential laws as specializations of known limiting spine/backbone constructions. It did not locate this exact finite-horizon formulation/application in its bounded search. This is not presented as a newly established theorem; priority remains unresolved.

## Model and observation

Start one founder cell at time zero. Each living cell divides into two at constant rate `lambda` and dies at constant rate `mu`. Clocks and daughters are independent and homogeneous. At each division of a tagged cell, choose one daughter uniformly to continue a chronological path. Choose independently of future fate. When the tag dies, its path ends, while its other relatives can continue.

At a fixed horizon `T`, retain the founder if **any descendant is alive**. For a retained founder, observe the prechosen random path, including its death if it died before T. This differs from following an ancestry that must reach an endpoint survivor. Define `F = {N(T)>0}` and tagged death time `D`.

For `0 <= t <= T` and positive unequal rates:

```text
P(D > t | F) = [lambda exp(-mu t) - mu exp(-lambda t)] / (lambda - mu).
```

At equal positive rates `lambda = mu = k > 0`:

```text
P(D > t | F) = exp(-k t) (1 + k t).
```

These are the survival functions of `Exp(lambda) + Exp(mu)` and its equal-rate Erlang-2 limit, **observed with right censoring at T**. They do not imply two biological death stages. The underlying cell death clock has one exponential stage and constant hazard `mu`.

The equality does not generally extend beyond T. If the tagged cell survives T, its subsequent death hazard in this memoryless model is `mu`; extending the two-stage curve beyond the selection horizon would be incorrect.

## Proof by discarded sister branches

Let `q(s)` be the probability that the descendants of one cell are extinct by elapsed time s. For unequal rates:

```text
q(s) = mu [1 - exp(-(lambda-mu)s)] / [lambda - mu exp(-(lambda-mu)s)].
```

The critical limit is `q(s)=ks/(1+ks)`. With no death, q is zero; with no division, `q(s)=1-exp(-mu s)`.

The unselected tag survives t with probability `exp(-mu t)`. Conditional on that survival, its previous division times form a rate-lambda Poisson process. Every division leaves one independent discarded sister subtree. The probability that all those sister subtrees are extinct at T, averaged over their birth times, is the Poisson generating functional:

```text
A(t) = exp(lambda * integral_0^t [q(T-u)-1] du).
```

For unequal rates this simplifies to:

```text
A(t) = [lambda exp((lambda-mu)(T-t)) - mu]
       / [lambda exp((lambda-mu)T) - mu].
```

At equal rates, `A(t)=[1+k(T-t)]/[1+kT]`.

Given a live tag at t, the remaining tagged subtree is extinct at T with probability `q(T-t)`. Thus the joint probability of being at risk and belonging to a retained founder is:

```text
R(t) = P(D > t, F) = exp(-mu t) [1-q(T-t)A(t)].
```

Divide by `P(F)=1-q(T)` and simplify to obtain the stated identity. This derivation is supported by independent quadrature, matrix-exponential and full-tree checks, not only by the shortcut simulator. [Independent derivation and estimands](hazard-estimand-review.md), [500-case numerical identity check](identity-check-results.json), [explicit-tree verification](full-tree-review.md).

## Observed hazards can vary while biological rates stay constant

At a tagged division, both new subtrees must fail for the family to be extinct at T. At tagged death, only previously discarded sisters can keep the family alive. Dividing the corresponding joint event densities by R gives:

```text
selected division hazard = lambda [1-q(T-t)^2 A(t)] / [1-q(T-t)A(t)]
selected death hazard    = mu [1-A(t)] / [1-q(T-t)A(t)].
```

Initially, selected death hazard is zero and selected division hazard is `lambda [1+q(T)]`. This is conditioning on a future outcome, not a change in the original clocks. At equal rates the selected death hazard simplifies to `k^2 t/(1+kt)`. It rises over the observation window although the true death rate remains k.

These are marginal hazards among at-risk tagged paths in the selected founder sample. They are not the full population's per-cell event rates, clone-extinction hazard or a functional tolerant-state exit rate. The independent review also explains when carefully justified inverse-probability branch weighting could recover population totals from a prospective sample.

## Identical selected deaths can accompany opposite population growth

The selected tagged survival function is unchanged by exchanging lambda and mu. Unconditional whole-population mean size per initial founder is `E[N(t)] = exp((lambda-mu)t)`, counting extinct families as zero, which does change. The selected-family mean at the horizon is instead `E[N(T)]/P(F)`.

For T=1:

| Division / death rates | Selected tag survival at T | Unconditional mean population size at T | Family survival probability |
|---|---:|---:|---:|
| 0.5 / 2 | 0.763596 | 0.223130 | 0.177234 |
| 2 / 0.5 | 0.763596 | 4.481689 | 0.794309 |

A selected-tag death curve alone cannot identify which rate governs death and which governs division, or even the sign of net population growth, under this model. Division histories or independently known inclusion information can distinguish these cases. The claim concerns death-only selected observations; it does not say all lineage data are uninformative.

## A missing denominator can restore rate identity

Write `Q(T)=P(D>T|F)` and `h(T)=P(F)`. Since tag survival implies family survival:

```text
Q(T) h(T) = P(D>T) = exp(-mu T)
mu = -log(Q(T) h(T)) / T.
```

This requires a verified prospective founder denominator and complete or correctly weighted family ascertainment, together with unbiased forward tag choice. Counting only retained families cannot supply h. A mixture of selected survivors and separately sampled nonpersisters does not automatically supply it either. For complete ascertainment, the product of the two empirical fractions reduces to tagged survivors divided by all eligible prospective founders. Uncertainty, missing observations and zero-survivor cases still require appropriate treatment.

This denominator identity is a mathematical corollary, not an empirically validated estimator for the Oren workbook. That workbook lacks the certified sampling/identity information required to apply it. [Source audit](source-dictionary.md).

## Conditions that could break the conclusion

Inherited frailty, correlated or asymmetric daughters, age-dependent division/death, density effects, changing drug exposure, state switching, future-informed path choice and informative tracking loss change the observation model. The exact two-stage equivalence is not a universal law of persisters. It is a counterexample to identifying a biological two-stage process from the shape of a selected death curve alone.
