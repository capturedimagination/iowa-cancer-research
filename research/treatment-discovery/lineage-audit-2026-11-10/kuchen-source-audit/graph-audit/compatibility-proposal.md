# Draft: finite-record sister-survival compatibility with incomplete tracking

Status: **theory and measurement proposal, not a frozen empirical analysis**. No workbook was reread, no graph was constructed, no lag was selected, and no new empirical or model outcome was calculated. The relevant starting points are the [graph-plan draft](../graph-plan-draft.md), [source audit](../README.md), and the [completed age/context/calibration study](../../age-calendar-calibration/README.md). An independent algebra-only review agreed with the ordered fixed-margin optimization below. The symmetrized formulas were proposed by the root analyst and independently checked here by constructive arguments; neither is claimed as a new theorem.

**A useful next measurement is a covariance compatibility range for a fixed roster of recorded sister pairs, retaining every unknown outcome.** It can be calculated without treating loss as death or assuming random missingness. Simple count-based endpoints are sharp when each unknown bit can be completed independently. Once shared lineage constraints are restored, those endpoints remain rigorous outer bounds, conditional on sound observed masks, but need not be jointly attainable by one lineage history.

## 1. The object to bound comes before a numerical lag

Take a fixed roster of N recorded birth pairs and a future, predeclared elapsed lag s. Define `X_i,Y_i` as whether each daughter's subtree has any living descendant at calendar time `birth_i+s`. This is subtree survival, not whether the original daughter has itself divided or died. The roster and weights cannot depend on future survival, completed cycles or complete follow-up.

Each outcome is certified 0, certified 1, or unknown under a separately frozen observation model. An observation loss, missing daughter or unresolved terminal time is not automatically a 0. A family can be certified alive by a valid living descendant; certifying extinction requires accounting for every possible descendant branch. Conflicting annotations cannot be silently converted to a convenient known fate.

The current source export's eligibility remains unresolved. Even perfect compatibility bounds on these rows describe the **retained recorded-pair roster**. They do not establish bounds for all original founders or all births that were omitted before export. That separate missing denominator cannot be recovered by completing the observed pairs' two outcomes.

There are two distinct finite-roster covariance targets:

```text
A = sum_i X_i,   B = sum_i Y_i,   J = sum_i X_i Y_i,   D=A+B

C_ordered = J/N - A*B/N^2
C_sym     = J/N - D^2/(4*N^2)
          = C_ordered - (A-B)^2/(4*N^2).
```

`C_ordered` uses the source's sibling-1/sibling-2 positions. `C_sym` is covariance under the empirical distribution that gives equal weight to each recorded pair and then randomly swaps its two positions. It is invariant to arbitrary within-pair relabelling. It does not assume the observed ordered margins are equal and does not create 2N independent pairs.

For a biologically unordered sister pair, C_sym is a natural candidate, but this is an **estimand choice to freeze**, not a post-results substitution. The usual sample covariance with denominator N-1 equals `N*C_ordered/(N-1)` for N>=2. Its population-unbiased interpretation needs sampling assumptions that are not established here. Multiplying C_sym by the same factor does not in general make it an unbiased population covariance estimator.

For N=0 both finite-roster functionals are undefined. For N=1, C_ordered is always zero, while C_sym can be -1/4 for a discordant pair; neither supplies an unbiased sample-covariance estimate from a single pair. Use covariance rather than correlation in an initial proposal: correlation introduces additional undefined zero-margin cases and changes the optimization problem.

## 2. Sharp endpoints for the symmetrized target under independent mask completion

First relax any cross-row lineage restrictions and allow each unknown bit to take either binary value. Collapse the nine ordered mask patterns into these counts:

- d: known `(1,1)` pairs.
- e: fully known discordant pairs `(0,1)` or `(1,0)`.
- f: one known 1 and one unknown.
- g: one known 0 and one unknown.
- h: two unknowns.
- z: known `(0,0)` pairs, so `N=d+e+f+g+h+z`.

The number of already known positive bits is `L=2*d+e+f`. Let k be the number of unknown bits assigned 1, so

`0<=k<=f+g+2*h`, `D=L+k`.

For each integer k the exact extreme feasible joint-positive counts are

```text
J_min(k) = d + max(0, k-g-h)

J_max(k) = d + min(k,f)
             + min(h, floor(max(0,k-f)/2))
         = d + min(k, f+h, floor((k+f)/2)).
```

Therefore the sharp minimum and maximum over this independent-completion set are

```text
lower_sym = min_k [4*N*J_min(k) - (L+k)^2] / (4*N^2)
upper_sym = max_k [4*N*J_max(k) - (L+k)^2] / (4*N^2).
```

All objectives and counts can remain exact integers until the final rational division. Enumerating k requires O(N) time and O(1) working storage after the mask counts. This is a special binary-mask problem, not a claim of an efficient algorithm for arbitrary interval-valued covariance.

### Constructive proof and witnesses

For the minimum at fixed k, at most g+h new positive bits can be added without a new `(1,1)` pair: one in each `0?` pair and one in each `??` pair. Every further added positive bit creates one new joint-positive pair. To attain the bound, fill those g+h available non-joint slots first, then fill `1?` slots and second-positive slots of `??` pairs as needed. The total capacity `f+g+2h` guarantees a completion.

For the maximum, an unknown positive in a `1?` pair produces one joint positive at cost one bit. Completing a `??` pair costs two bits per new joint positive. Fill up to min(k,f) of the first kind, then as many complete `??` pairs as possible. Any odd leftover bit fits in an unused `??` pair; if all such pairs are complete, the overall capacity condition guarantees available `0?` slots for remaining bits. This constructs J_max. Equivalently, the number of new joint positives is bounded by k, by f+h, and by floor((k+f)/2); the construction attains the smallest of these three bounds.

A deterministic witness can use the frozen roster order to choose among tied records. Its public certificate need only report counts, k, J, exact numerator/denominator and a private witness hash; raw per-cell completions stay private. The witness establishes sharpness for the **mask relaxation**, not a physically consistent cell history.

When every pair is unknown, the symmetrized lower bound is -1/4, attained by making every pair discordant. The upper bound is `floor(N^2/4)/N^2`, attained by a balanced-as-possible mixture of concordant 00 and 11 pairs. With all outcomes known, both endpoints collapse to C_sym. Refining any unknown to a valid known value cannot widen the feasible-completion range.

An independently implemented dynamic-programming check is available for later fixtures: for each pair, enumerate its allowed `(X+Y,XY)` contributions and propagate feasible total D with minimum/maximum J. This supplies an O(N^2) small-case reference without sharing the closed-count implementation. Exhaustive bit enumeration is another reference for sufficiently small synthetic masks. These checks are proposed, not run here.

### Proposed exact-enumeration verification freeze

A small, fully specified mathematical fixture plan can precede any empirical bound calculation:

1. Visit every ordered mask sequence of length N=0,...,4 over the nine 0/1/? pair patterns: 7,381 masks in total. Enumerating each mask's binary completions involves 69,905 completed mask/assignment combinations across this entire fixture set. These counts follow from geometric sums of 9^N and 16^N, not a numerical model run.
2. Compare exact integer extrema for both C_sym and C_ordered, separately at every feasible fixed D or A and globally. Verify the constructed witnesses, including odd/even parity and saturated capacities. Treat N=0 as undefined; do not divide by zero.
3. Check invariance of C_sym and its bounds to any within-pair relabelling. For C_ordered, require invariance only to swapping the two positions in every pair together; independent row swaps need not preserve that estimand.
4. For every available one-bit refinement `? -> 0` or `? -> 1`, verify feasible-set containment and endpoint nesting. Check complete-data collapse, fully unknown controls and the example with zero inside the endpoint interval but absent from the attainable set.
5. Independently verify the fixed-D symmetrized formula by the contribution-based dynamic program. Use a separate implementation from the greedy/count formula. Small graph-constraint fixtures should then test shared variables, absorbing extinction and parent-child OR restrictions against exhaustive joint enumeration; they must show when mask endpoints are unattainable jointly.
6. Pin both implementations and the exact fixture list before execution; preserve first failures and counterexamples. Passing mathematical fixtures does not authorize a lag choice, workbook outcome extraction or graph-based inference.

This remains a proposed fixture plan. No enumeration or new source-data computation was performed for this document.

## 3. Sharp ordered-covariance endpoints

Retain the nine mask counts `n00,n01,n10,n11,n0?,n1?,n?0,n?1,n??`, where the first position is X. Put

```text
A0 = n10+n11+n1?                 # known positive X values
u0 = n?0;  u1=n?1;  uh=n??
```

Fix an integer marginal total `a in [A0, A0+u0+u1+uh]`, and set `k=a-A0`. Write the integer objective `K=N*J-a*B`. The fixed-a exact endpoints are

```text
K_max(a) = (N-a)*(n11+n1?) - a*(n01+n?1)
           + N*min(k,u1) + (N-a)*min(max(k-u1,0),uh)

K_min(a) = (N-a)*n11 - a*(n01+n?1+n0?+n??)
           + a*min(max(k-u0,0),uh) + N*max(k-u0-uh,0).

lower_ordered = min_a K_min(a)/N^2
upper_ordered = max_a K_max(a)/N^2.
```

To prove this, write `K=sum_i Y_i*(N*X_i-a)`. At fixed a, maximizing over an unknown Y sets it to 1 when X=1 and to 0 when X=0. Starting with all unknown X set to 0, changing one X to 1 has gain N for known Y=1, N-a for unknown Y, and 0 for known Y=0. Allocate the required k ones in that order.

For minimization, an unknown Y is 1 when X=0 and 0 when X=1. The corresponding gains are 0 for known Y=0, a for unknown Y, and N for known Y=1. Allocate k ones in that order. The displayed base terms account for all rows before those changes. At a=0 or a=N, ties cause no problem. Since every feasible a is visited and the allocations construct valid completions, both endpoints are sharp for the independent mask set. Multiplication by N/(N-1) gives endpoints for the ordinary sample-covariance formula when N>=2.

The formulas deliberately optimize the joint count and both margins together. Bounding J, A and B separately and combining incompatible extremes can be much wider and cannot be called sharp. A known margin alone also does not encode the observed row-level pairing restrictions.

## 4. An interval is not the set of all attainable finite-data values

The endpoints above are attained in the relaxed binary-mask problem. Values between them need not all be attainable because a fixed completed dataset has integer counts.

For example, the abstract three-pair mask `(1,?), (0,1), (0,0)` has ordered covariance -1/9 or +1/9 depending on the sole unknown bit. Its smallest enclosing interval contains zero, but no completion has exactly zero covariance. This is a hand-derived discrete example, not an empirical result.

Accordingly, report **sharp minimum/maximum endpoints** or the **smallest interval containing feasible finite-record values**. Do not say that zero is compatible merely because it lies between endpoints. If exact zero feasibility is scientifically relevant, it requires a separate integer feasibility check, and graph constraints must be included. The same caution applies to differences between lags and to a joint vector of bin-level covariances.

## 5. Restore lineage consistency before claiming joint attainment

Recorded pair targets share a lineage graph even when each source child ID occurs in only one pair row. A later cell can contribute to the survival of its own subtree and of multiple ancestral subtrees. Different pairs also query different calendar times because their birth times differ. Thus the unknown outcome bits cannot generally be completed independently.

For a candidate graph and a finite set of query times, use a shared variable `S(v,t)` for survival of the subtree rooted at cell/branch v at absolute time t. Necessary restrictions include:

1. Identical branch-and-time queries reference the same variable, not duplicate free bits.
2. For a fixed branch, extinction is absorbing: `S(v,t2)<=S(v,t1)` for t2>=t1, with both times after its birth and no immigration/re-entry into that lineage.
3. After a verified division, `S(parent,t)=OR(S(child1,t),S(child2,t))` for a query at or after division under the frozen event-boundary convention. An unobserved daughter remains an unknown branch in this OR.
4. A valid observed alive/dead mask fixes the corresponding value. A valid observed descendant at a later time can logically imply earlier survival of its ancestral subtree; this is an outcome-identification implication, not permission to choose cohort eligibility using future observations.
5. A child subtree's survival implies survival of an ancestor at the same time when the ancestry and birth-time conditions are valid. Contradictory ancestry or event times must be quarantined according to the frozen dictionary, not forced into these constraints.
6. Loss terminates evidence, not the lineage. Unknown branches can die or persist consistently with future observations; no missing-at-random, independent-censoring, rate or treatment model is introduced merely to fill them.

Let F_mask be the independent-mask completion set, F_logic the set satisfying such necessary graph restrictions, and F_history the completions realizable by an admissible full event history. If the masks and restrictions are sound,

`F_history subseteq F_logic subseteq F_mask`.

The mask minimum is therefore no larger than the true-history minimum, and its maximum no smaller than the true-history maximum. This gives a mathematically certified **outer range** without solving a graph optimizer. A graph-constrained optimum is sharp for F_logic; calling it sharp for F_history additionally requires a proof or explicit construction that its optimizing assignment is realizable as one valid time-ordered lineage history.

A minimal abstract coupling example is `(Z,0),(Z,1)` with the same unknown Z in both targets. Their ordered covariance is always zero. Treating the two Z appearances as unrelated unknown bits instead gives endpoints -1/4 and +1/4. This is a logical fixture illustrating shared-variable dependence, not a claim that these exact rows occur in the workbook.

If the asserted graph and known masks have no feasible completion, report a structural inconsistency. Do not return an empty-set numeric bound, silently discard the offending pairs or adjust observations until a preferred covariance becomes possible. Any broader error-coarsening analysis is a separately declared sensitivity model.

### A possible graph-constrained optimizer

For a fixed ordered total A=a, introduce binary `Z_i=X_i AND Y_i` through `Z_i<=X_i`, `Z_i<=Y_i`, `Z_i>=X_i+Y_i-1`. Graph OR and monotonicity restrictions are linear constraints on binary variables. Minimize/maximize `N*sum Z_i-a*sum Y_i`, with `sum X_i=a`. Enumerating feasible a gives exact integer-program endpoints for the declared logical model if each optimization is certified complete.

For the symmetrized target, fix `D=sum(X_i+Y_i)=d_total` and minimize/maximize J under the same graph constraints; optimize `4*N*J-d_total^2` over possible d_total. The closed formulas above are cheap outer bounds and implementation controls for every such subproblem.

A single mixed-integer formulation can alternatively linearize A*B (ordered) or D^2 (symmetrized) through a binary expansion and standard binary-times-bounded-integer auxiliary variables. This is an implementation option, not a new mathematical claim or a commitment to an expensive full-cohort solve.

Distinguish feasible witness values (inner information) from lower/upper optimization certificates (outer information). A time-limited incumbent is not a certified extreme. Floating-point solver gap/status alone is not an exact mathematical certificate; use an independently checked rational/integer certificate, exhaustive small components, or explicitly retain the closed-form outer range. No actual optimizer or empirical lag is selected in this draft.

## 6. Context and repeated-target summaries

For fixed birth bins g with weights `w_g=N_g/N`, ordered empirical covariance decomposes exactly as

`C_ordered = sum_g w_g*C_ordered,g + Cov_w(A_g/N_g,B_g/N_g)`.

That between-bin term is not generally a variance because the two finite ordered margins differ. For the symmetrized empirical distribution, with `p_g=(A_g+B_g)/(2*N_g)`,

`C_sym = sum_g w_g*C_sym,g + Var_w(p_g)`.

This distinction matters when applying the earlier exchangeable model's covariance decomposition to actual finite records. Do not impose equal observed ordered margins just because sisters are biologically exchangeable.

Positive weighted sums of valid per-bin lower/upper endpoints provide valid outer bounds for the weighted within-bin statistic. They are jointly sharp only if a single admissible completion can attain all corresponding bin endpoints. The same graph may span bins, lags and outcomes. Independent endpoint subtraction gives a valid outer bound for a difference, but not a claim of joint attainment. Any tighter comparison must reuse the same variables and graph completion across all included targets.

Even a strictly positive finite-record covariance under every compatible completion is not proof of inherited intracellular state. Mixtures over birth time, measured/unmeasured shared environments, source selection and observation mechanisms remain alternatives. Bounds concern incomplete records; they are not confidence intervals, population identification regions, a null-model test or a power calculation.

## 7. Independent structural verification plan

Once a final structural protocol is available, an independently written verifier for `build_kuchen_graph` should be pinned before reading producer outputs. It must not import, copy or invoke production parsing, graph-construction or masking helpers. No verification implementation is shared in this draft.

Proposed separation:

- Independently read the original, hash-pinned workbook XML and schema. Preserve exact source strings and Excel coordinates. Use decimal/rational time arithmetic for source consistency checks where feasible; do not accept the producer's derived times as ground truth.
- Reconstruct source pair and child assertions directly, then compare full namespaced identity and provenance sets with producer outputs. Match by explicit keys, never row position. Keep raw comparison records private; publish aggregate mismatch counts and hashes.
- Rebuild component membership independently, for example by union-find on verified edges, and check ancestry acyclicity by an independent topological procedure. A source lineage label and an external parent reference are not an original founder.
- Audit every usable parent-child timing equality, daughter multiplicity, grandmother assertion, fate exclusivity and missing successor. Confirm that negative/ambiguous timings create uncertainty rather than repaired events or dropped rows.
- Verify masks from source assertions and the frozen event-boundary/precision rules, including a clean component beside an affected component. If only structural construction is authorized, do not query masks at a scientific lag or tabulate 00/01/10/11 outcomes.
- Test independent synthetic fixtures for shared IDs across sheets, duplicated assertions, cycles, missing branches, overlapping ancestral targets, absorbing extinction, arbitrary sister relabelling and exact-boundary events. Include the discrete zero-gap and repeated-variable examples above as theory controls only after their fixture protocol is approved.
- Check no future-outcome field enters roster eligibility and no complete-case/subtree filter is introduced. Preserve all unresolved source-ascertainment gates even if every structural check passes.
- Compare machine-readable schema, source hashes, record counts and all private graph fields, not only a few headline totals. Stop on mismatches before any covariance compatibility calculation.

This is a verification approach, not a graph result. The source audit's raw identity, timing and exclusion uncertainties remain as documented.

## 8. Suggested next freeze and useful stopping rules

After the dictionary/graph audit, a separate empirical compatibility protocol should declare the retained roster and weights; ordered versus symmetrized covariance; one or more scientifically motivated lags selected before querying outcomes; calendar support/tie rules; 0/1/unknown masks; source-error sensitivities; mask-only versus graph-coupled constraints; and exact proof/certificate standards. It should freeze whether per-bin summaries and between-lag differences are scalar outer bounds or jointly optimized targets.

A first useful output may simply show that current records cannot determine the sign or magnitude of covariance without additional observation assumptions. Preserve that result. Conversely, excluding zero from a valid outer range establishes only a sign property of every admissible completion of the declared retained roster. It does not solve source selection or identify a mechanism.

A later measurement-design question can ask which unresolved branches or observation times would reduce the compatibility range under both possible observed outcomes. That is different from choosing which records to follow because their eventual fate produced a desired association. No such ranking, window choice or new observation is made here.

Keep any per-cell graph, event history, masks and witness assignments in excluded local storage. Public artifacts should contain original code, protocols, formulas, aggregate bounds, counts, certificate hashes and source citations. No raw cell rows are included in this proposal.

## 9. Bounded primary-source prior-art check

Missing-data completion and bounding statistical functionals are established partial-identification ideas. Horowitz and Manski explicitly treat incomplete observations/interval measurements and emphasize optimizing over admissible distributions instead of imposing unverified missingness assumptions. The accessible publisher abstract/introduction was inspected; this is not a claim of full-paper review. [Horowitz and Manski, 2006](https://www.sciencedirect.com/science/article/pii/S030440760500062X).

Sharp covariance restrictions from bounded supports and known marginal means also have substantial prior art. Hössjer and Sjölander's Theorem 1 specializes to binary marginal covariance bounds, and their discussion cites earlier binary results. Their author preprint, including Theorem 1 and Corollary 3, was inspected. It does not by itself encode this workbook's row-level masks or ancestry constraints. [Hössjer and Sjölander, author preprint](https://arxiv.org/pdf/2106.10037).

General interval-data covariance optimization can be computationally difficult; Kishida's paper studies bounds using structured singular-value methods. Only its publisher abstract/highlights were accessible in this check. The O(N) formulas above exploit binary 0/1/? structure and do not contradict complexity statements for general interval data. [Kishida, 2017](https://doi.org/10.1016/j.ymssp.2016.07.037).

This focused search does not establish priority for the count formulas, covariance symmetrization, integer optimization or the biological application. The immediate value is a transparent, checkable measurement rule for this retained-record problem, with explicit distinctions between a convenient relaxation and jointly feasible lineage histories.
