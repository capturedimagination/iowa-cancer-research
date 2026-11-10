# Conservative bounds for incomplete recorded families

Derived and checked November 10, 2026. **The sorted-subset formulas below give safe outer bounds for the fixed recorded roster.** They are exact extrema of an interval/selection relaxation, not generally sharp over biological tree completions. No empirical outcomes, fitted rates or claims of priority are involved.

For one fixed roster of baseline cells, let `p_i(t)` be the probability that a future-blind, uniformly chosen daughter path is alive at t in the completed family tree. Let `f_i(T)` indicate any descendant alive at T. Each selected founder has equal weight:

```text
Q_T(t) = sum_i f_i(T) p_i(t) / sum_i f_i(T),    0 <= t <= T.
```

This is a finite-roster average of path probabilities, not a pooled descendant proportion or a population conditional probability. The same baseline roster and `p_i(t)` must be used when comparing horizons.

## Obtaining safe row bounds

Start a prospective tag with probability mass one. Each verified binary division sends half its incoming mass to each daughter. A verified death removes its mass after the death boundary. If only one daughter is recorded, the absent daughter's half remains unknown, not dead. Unknown subtrees must form a disjoint frontier: never count an unknown ancestor and its observed descendant twice.

At time t, if known-live mass is `a_i(t)` and unresolved mass is `r_i(t)`, a safe starting interval is `l_i=a_i`, `b_i=a_i+r_i`, capped by one. Only verified alive-at-t observations belong in `a_i`; tracking retained after an apoptosis annotation is not living mass. Ambiguous death times, identities or masks must be carried as uncertainty or handled by a declared sensitivity. New descendants, later observations and branch information can couple the row bounds to inclusion; ignoring that coupling widens the envelope.

At T, inclusion is known one if a verified living descendant exists; known zero only if every possible descendant path is verified extinct. Otherwise it is unknown. No observed survivor is insufficient evidence of extinction when a branch is missing.

For finite, nonexplosive binary trees, `f_i(T)=1` implies `p_i(t)>0` at every `t<=T`: a surviving descendant has a living ancestral path with positive probability. Thus `b_i(t)=0` rules out inclusion; a known included row with that upper bound is inconsistent. At **t<T**, later extinction can coexist with positive earlier survival. Do not set `p_i(t)=0` merely because `f_i(T)=0`.

At **t=T**, the stronger equivalence holds: `p_i(T)>0` if and only if `f_i(T)=1`. Consequently:

- Known exclusion requires an interval containing zero; set its endpoint probability to zero.
- An unknown inclusion with `l_i(T)>0` becomes mandatory inclusion.
- An unknown inclusion with `b_i(T)=0` becomes exclusion.
- A selected row with lower bound zero remains strictly positive, but may approach zero. With no uniform bound on unknown division depth, one surviving descendant can have arbitrarily small positive tag mass. A zero lower limit can therefore be an **unattained infimum**. Do not describe it as an attained extinct selected family.

## Marginal sorted-subset envelope

After these consistency reductions, write K for mandatory inclusions, O for optional inclusions and Z for exclusions. Let `n=|K|`, `m=|O|`, `A=sum_K l_i`, `B=sum_K b_i`. Sort the optional lower bounds increasingly as `l_(1),...,l_(m)` and optional upper bounds decreasingly as `b_[1],...,b_[m]`. Then:

```text
L_T(t) = min_k [A + sum_(j=1)^k l_(j)] / (n+k)
U_T(t) = max_k [B + sum_(j=1)^k b_[j]] / (n+k).
```

Use `k=0,...,m` when n is positive; use `k=1,...,m` when n is zero. For fixed k, selecting the k smallest lower bounds minimizes the numerator, and selecting the k largest upper bounds maximizes it. Taking the extrema over k proves the formulas. Z contributes neither numerator nor denominator, regardless of its earlier path survival.

These are infimum/supremum bounds for the relaxed intervals and selection indicators; strict positivity is represented by closure. Actual missing subtrees can impose additional compatibility constraints. The bounds therefore contain every compatible true value but need not be attainable, jointly attainable or tree-sharp.

**Denominator gate:** if n=m=0, Q is undefined, not zero. When n=0 and m>0, the formulas bound Q only over completions with at least one selected family. Marginal information also permits zero selection, so report that possibility separately rather than silently conditioning it away. Additional joint information could remove that possibility, but it must be documented.

At baseline t=0, every verified living baseline cell has `p_i(0)=1`, giving Q=1 whenever its denominator is positive. This is a useful control.

## Two horizons: safe subtraction and a nesting cap

Let `T2>T1>=t`, with the same roster and tag rule. Family survival is nested: `f_i(T2)<=f_i(T1)`. A known later inclusion forces earlier inclusion; a known earlier extinction forces later exclusion. Contradictory statuses must be resolved before interpretation. The contrast is defined only when later selection is nonempty, which also makes earlier selection nonempty.

For `Delta=Q_T2(t)-Q_T1(t)`, separate marginal envelopes imply:

```text
Delta in [L_T2(t)-U_T1(t), U_T2(t)-L_T1(t)].
```

This is conservative because it allows incompatible extremizing completions and ignores the shared path probabilities. A cheap tightening uses `N2<=N1`, the selected counts. Splitting the earlier selected set into later survivors and early-only families gives

```text
Delta = (1-N2/N1) [Q_later - Q_early_only],
|Delta| <= 1-N2/N1.
```

If `N1=N2`, the contrast is exactly zero; no early-only mean is needed. Let `a=max(1,|K2|)` and `b=|K1|+|O1|` after consistency reductions. Conditional on positive later selection, intersect marginal subtraction with `[-(1-a/b), +(1-a/b)]`. This assumes b is positive and `a<=b`; otherwise the statuses cannot describe a nonempty nested selection. The cap is still an outer bound.

For example, one founder selected at both horizons with `p in [1/4,3/4]` has marginal subtraction `[-1/2,1/2]`, although its actual contrast is zero. With two founders having probabilities 1 and 1/4, later retaining only the first or only the second gives contrasts +3/8 or −3/8. Nesting alone does not fix the sign.

A future joint tightening can fix N1,N2 and assign each row to states 00, 10 or 11. Their contrast coefficients are `0`, `-1/N1` and `1/N2-1/N1`. Minimization uses the upper interval endpoint in state 10 and the lower endpoint in state 11; maximization reverses them. Cardinalities and known statuses can be enforced by dynamic programming or a minimum-cost assignment. That would be exact for the common-probability/nested-selection relaxation, still not automatically tree-sharp. It is not implemented in this primary verifier.

## Verification and permissible conclusions

The [protocol](verification-protocol.json) and [code](verify_bounds.py) were [locally pinned](verification-freeze.json) before the first deterministic run. Exact rational arithmetic checked 11 fixed controls, 399 nested status cases and 8,200 selection/probability combinations. All checks passed; 39 status cases admitted no positive later selection and were recorded separately. [Results](verification-results.json).

The verifier enumerates the **closed rectangular relaxation**, including zero endpoint values that may only be limiting values for selected families. It checks the sorting formula, compatibility reductions, denominator handling and nesting envelope; it does not establish that every relaxed configuration is a possible experimental tree.

These are missing-information bounds for the fixed recorded cohort, not confidence intervals. If zero lies outside a conservative contrast interval, every compatible completion of that finite record has a nonzero contrast under the assumptions; this alone does **not** reject a stochastic population horizon-invariance theorem. Sampling variation, dependence and observation selection require a separate inferential design. If zero remains inside the envelope, this method has not excluded equality; loose bounds do not prove fundamental nonidentifiability or that a sharper method cannot help. Without coverage and selection assumptions, the result does not extend to an unknown original population. No empirical test is performed in this review.
