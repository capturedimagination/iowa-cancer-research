# Independent review: shared calendar-time rates

Reviewed November 10, 2026. **The proposed finite-horizon formula is correct under the stated model.** This is an independent algebraic review, not an additional simulation, empirical validation, priority claim or journal peer review. The reviewed numerical plan and code are pinned in the [JSON record](calendar-rate-independent-review.json).

Let every cell share locally bounded nonnegative deterministic division and death rates `lambda(t)` and `mu(t)`. There is one founder at time zero, independent binary daughters, no interactions or tracking loss, and a future-blind uniform daughter choice for the chronological tag. A dead tag stays dead. Select founders with any descendant alive at `T`, weighting selected founders equally. Define `L(t)=integral_0^t lambda(u)du`, `M(t)=integral_0^t mu(u)du`. For `0 <= t <= T`, with positive inclusion probability,

```text
Q_T(t) = P(tag alive at t | family alive at T)
       = exp[-L(t)]
         + exp[-M(t)] integral_0^t lambda(u) exp[M(u)-L(u)] du.
```

This expression has no `T`. It compares **the same absolute time t** under different selection horizons at least as large as t. It does not say the endpoint quantity `Q_T(T)` stays constant as T changes.

## Independent derivation

Write `h(s,T)` for survival to T of one cell present at calendar time s. Backward conditioning on the first event gives

```text
d h(s,T)/ds = [mu(s)-lambda(s)]h(s,T) + lambda(s)h(s,T)^2,
h(T,T)=1.
```

Given tag survival through t, its divisions form a Poisson process with intensity lambda. Each discarded sister starts an independent family, surviving to T with probability `h(u,T)`. Thus the probability that all these sister families die out is

```text
A(t,T) = exp[-integral_0^t lambda(u)h(u,T)du].
```

The joint probability of a living tag at t and an included founder is

```text
R(t,T) = exp[-M(t)] {1 - [1-h(t,T)] A(t,T)}.
```

From the differential equation for log h,

```text
A(t,T) = h(0,T) exp[M(t)-L(t)] / h(t,T).
```

Set `z(s)=1/h(s,T)`. Then `z'=(lambda-mu)z-lambda`, so

```text
z(t)exp[M(t)-L(t)] = z(0) - integral_0^t lambda(u)exp[M(u)-L(u)]du.
```

Substitute these two expressions into `Q_T=R/h(0,T)`; the `z(0)` terms cancel, giving the formula above. The terminal condition enters h but disappears from Q on the permitted time interval.

## Checks and interpretation

- **Proper survival law:** let `x0=exp(-L)` and `x1=Q-x0`. They obey `x0'=-lambda*x0`, `x1'=lambda*x0-mu*x1`, initialized at `(1,0)`. This is a valid two-transient-state calendar-time chain. Consequently `Q(0)=1`, `0<=Q<=1`, and `Q'=-mu*x1<=0`. The selected death hazard is `mu(t)[1-exp(-L(t))/Q(t)]` wherever defined.
- **Endpoint accounting:** `h(T,T)=1` gives `Q_T(T)h(0,T)=exp[-M(T)]`, consistent with the tag's prospective survival. This algebraic identity is not an independent empirical falsifier.
- **Zero-rate controls:** lambda identically zero implies selection requires the tag itself to survive to T, giving Q=1 on `[0,T]`. Mu identically zero also gives Q=1. Both zero is included.
- **Constant-rate reduction:** unequal positive constants recover `(lambda*exp(-mu*t)-mu*exp(-lambda*t))/(lambda-mu)`; equal positive k recovers `exp(-kt)(1+kt)`.
- **Horizon boundary:** beyond T, if the tag continues under the same deterministic death schedule, its conditional survival is `Q_T(T)exp[-(M(t)-M(T))]`. Continuing the two-stage formula beyond T would generally be wrong.

The calendar-time two-state representation is a distributional equivalence. For nonconstant rates it is not generally a sum of independent exponential waiting times, and it is not evidence of two biological death steps.

## Rate exchange does not generalize

An exact analytical counterexample, **outside the frozen numerical grid**, is enough. Take T=1, lambda=1 and mu=0 in the first half, then lambda=0 and mu=1 in the second half. The two-state representation gives

```text
Q(1) = 1 - [1-exp(-1/2)]^2 = 0.8451818782538245.
```

Exchange the entire lambda and mu schedules: no tag can die after producing a sister, so any selected family has a surviving tag and `Q(1)=1`. Both schedules have `L(1)=M(1)=1/2`. Thus neither arbitrary rate-swap symmetry nor dependence only on integrated rates follows from the constant-rate identity.

The [frozen numerical checker](horizon-invariance/protocol.json), its implementation and reported results were inspected without rerunning them. The implementation uses the correct backward equation, sister-subtree functional, direct integral and forward chain, including separate integration at known discontinuities. No blocking mathematical or implementation issue was identified in this review. The numerical run remains the other reviewer's deterministic check, not a second independent run here.

A subsequent [packaging-only update](horizon-invariance/packaging-note.md) removed twelve spaces from a blank source line and reran the unchanged checker. This review independently reconstructed the first-run source and result bytes and recovered their original hashes, verified identical Python syntax trees and an unchanged protocol, and confirmed that only the result timestamp and script hash differ. The JSON preserves the original review provenance alongside the packaged hashes. No scientific conclusion changed, and this reviewer did not rerun the checker.

The conclusion covers shared deterministic calendar-time rates. It does not establish the same identity for cell-age effects, inherited states, founder frailty, random environments averaged across families, varying founder-entry times mixed together, cell interactions, incomplete observation or endpoint-connected ancestry sampling. Therefore horizon invariance alone cannot distinguish constant rates from this broader changing-rate model; an empirical test must specify which richer model and observation process it is trying to reject. Novelty and biological applicability remain unresolved.
