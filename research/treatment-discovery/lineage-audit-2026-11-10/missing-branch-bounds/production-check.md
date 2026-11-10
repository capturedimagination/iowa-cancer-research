# Independent production-bounds check

November 10, 2026. **Pass: no blocking arithmetic or fixed-grid driver issue identified before empirical execution.** This review imported the production arithmetic core, compared it with the independently frozen rational verifier, and read the empirical driver. It did not invoke the empirical driver or read its source graph. The earlier mathematical review, freeze and results were preserved.

- Production core SHA-256: `27bb3b07186b015a5d573d45ffe1da6515131ea0b3da09e677531c468eb4513e`.
- Driver SHA-256: `31dcbbeb9ff04c0ab6eb49ea99f5e1d63c9525cc69d0f3c1e3652cc63821d17c`.
- Empirical protocol SHA-256: `c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771`.

[Machine-readable checks](production-check.json), [checker](check_production_bounds.py), [pre-run provenance](production-check-freeze.json), [independent mathematical review](bounds-review.md).

## Arithmetic comparison

The reference enumerates every optional selected subset and every interval endpoint using exact fractions. It does not call production sorting or contrast functions to obtain the truth. The production implementation passed **810 ratio comparisons**, with maximum absolute error **1.1102230246251565e-16** against that reference. All **8,200 exact rational contrasts** across **399 nested status cases** fell within the production envelopes. The 39 cases without any positive later selection were retained as undefined cases.

Specific controls verify that:

- Optional rows with upper bound zero are removed from possible inclusion, including the count used by the nesting cap.
- Known later inclusion can coexist with optional earlier inclusion in the supplied marginal summaries; the single-possible-founder contrast still collapses to zero.
- Positive earlier survival in a family excluded at a later horizon contributes neither numerator nor denominator to that later selected average.
- Empty rosters and all-excluded rosters yield undefined ratios, not zero. Optional-only rosters retain the possible zero-denominator flag.
- Known selected rows with zero upper survival, invalid intervals and impossible nesting counts are rejected.

The generic `ratio_bounds` interface has no time argument. Endpoint compatibility therefore belongs to its caller: at t=T, positive live mass must imply inclusion. The driver computes status from the same mass at T, so it supplies that reduction correctly. The dedicated endpoint control applies the same logical reduction before invoking the generic function. At earlier t, positive survival must not automatically force later inclusion.

The contrast API receives aggregate envelopes and counts; it cannot itself certify row identity or every row's nesting constraint. The driver uses the same roster and earlier-time mass values at all horizons, checks monotone mass bounds and rejects known-later/known-extinct-earlier contradictions. Those caller conditions are essential to the contrast interpretation.

## Static driver audit

The nested loops retain all **20 scenarios**: five baseline frames × two annotation offsets × two ambiguity policies. Three horizons and five common evaluation times produce **300 ratio records**. Three ordered horizon pairs and the same five times produce **300 contrast records**. No scenario is selected for a favorable result.

Each baseline uses one common roster for both death offsets and ambiguity policies. The additional roster exclusion concerns apoptosis annotated at or before baseline, as declared in the frozen protocol; future division, survival and recording completeness do not select that roster. The core's offset-aware baseline API supports synthetic offset controls, while the empirical driver's stricter common eligibility remains unchanged.

The driver verifies pinned input and plan hashes, nominal frame coverage, conservation, monotonicity, time-zero ratios and containment under greater coarsening. Its outputs retain finite-record, nonsharp and non-inferential language; it contains no fitted rate model, p-value or population hypothesis test. These are code-inspection findings, not claims that empirical assertions have already passed.

Comparison tolerance was fixed at `1e-12`; the observed arithmetic discrepancy was much smaller. The production code uses ordinary floating-point arithmetic, not certified outward rounding. This check therefore verifies numerical agreement at the stated tolerance, not a last-bit interval certificate. Missing-information bounds remain distinct from sampling confidence intervals and from sharp bounds over all compatible trees.

Reproduce this synthetic check from the project root with `python3 research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds/check_production_bounds.py`. It rewrites only the production-check result, and does not run empirical analysis.
