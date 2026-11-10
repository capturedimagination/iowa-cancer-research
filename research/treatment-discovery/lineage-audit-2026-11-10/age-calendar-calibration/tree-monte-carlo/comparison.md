# Complete-tree Monte Carlo comparison

The first run completed 20 cases and 200,000 prospective founders. All 800 saved checkpoint hashes match the first aggregates.

The frozen comparison contains 3,070 exact-binomial diagnostics and 720 bounded-mean Bernstein diagnostics. It retains 0 flags and 0 undefined zero-denominator checks.

Exact-binomial status counts: `{'not_flagged': 3070}`.
Bounded-mean status counts: `{'not_flagged': 576, 'structural_agreement': 144}`.

Each diagnostic family has its own alpha of 0.001; the union bound across these two families is 0.002, conditional on the model probabilities and declared numerical approximation.

Conditional Q checks use the observed selected count. Removed-stratum loss is an unconditional prospective-founder mean, including zeros. Sister covariance and horizon contrasts are descriptive alongside their frozen component checks; no new Gaussian standard-error threshold is applied.

These are synthetic model checks. They do not establish biological inheritance, a cancer mechanism, treatment benefit, or novelty. Earlier study flags remain unchanged. Probability roundoff and numerical slack are retained; the integration calculations are not interval arithmetic.

Every case, reference, count, threshold, flag and undefined status is retained in [the comparison JSON](comparison.json).
