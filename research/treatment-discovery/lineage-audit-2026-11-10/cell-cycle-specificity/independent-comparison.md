# Independent deterministic comparison

**Pass on the first full comparison.** All 72 frozen model records and every planned quantity were checked against an independently generated reference. No case was selected by sign, magnitude, or success. Every numerical difference satisfies the frozen tolerance policy.

The [complete comparison](independent-comparison.json) retains all 13,478 scalar comparisons, each against both the primary and tighter-tolerance production run, with case identifiers, reference values, both production values, differences, gates, and pass status. [The comparator](../../../../scripts/compare_age_lineage_references.py) preserves first outputs and does not import production code.

## Independence and execution order

The [reference solver](../../../../scripts/verify_age_lineage_models.py) was implemented and pinned before viewing production numerical outputs. It solves extinction probabilities and a forward weighted-spine equation instead of the production positive joint-probability equation. Sister qualification uses independent quadrature of the competing-risk density. Calendar controls use reciprocal-survival quadrature; deterministic-age controls use a discarded-sister product.

The early-time reference uses a scaled Volterra integral equation with Chebyshev-Lobatto collocation and mapped Gauss-Legendre quadrature, rather than the production scaled differential equation. Orders24/40 with quadrature48/80 agreed to at most `8.882e-15` in the normalized ratio. This is a numerical convergence check, not an interval-arithmetic certificate.

Seven separate mathematical fixtures passed before the full reference run. A requested pre-outcome change added overwrite refusal, finite-value checking, and partial-case failure artifacts without changing equations, grids, or solver settings. The original pin, source copy, and fixtures remain in ignored local provenance. Three synthetic harness controls then passed, including an intentionally triggered failure whose partial records and path-labeled nonfinite diagnostic were preserved.

The full reference was generated before any production output values were read. Its production-independent code hash is `4c6ed695f526d8ec07df9a4dafe4e4572e1bef0529c7d70a61a19f6a666e8883`; [independent-reference.json](independent-reference.json) has SHA256 `0e53f27c4be7a362cad7a2aa093c35c3beb24bf7fa0afbc5c53bb491f13b7ef8`. The comparator was separately pinned before numerical comparison, after result files and schemas existed: SHA256 `84606220d22bf264a5fca600569979f2c84f4ca2bf90da04687a87af5f3548ab`. Comparator timing is post-results validation, not a new preregistered scientific analysis.

## Complete coverage

| Quantity | Records checked |
|---|---:|
| Model cases | 72 |
| Family-survival probabilities | 216 |
| Selected-path queries, including validation endpoints | 1,224 |
| Primary horizon contrasts | 864 |
| Sister-pair lag records | 216 |
| Extra deterministic first-generation queries | 6 |
| Early-time records | 567 |

The case configurations and exact record-key sets match the frozen plan. The comparison covers family and joint probabilities, selected-path survival, ordinary positive death defects, contrasts, eligibility, qualifying maternal weights, per-type daughter survival, daughter means and joint survival, covariance, calendar residuals, deterministic control identities, early coefficients, losses, leading terms, ratios, and conservative envelopes.

All 27 early-time ratios in zero-death controls are undefined and retain zero loss; none is imputed as zero. The no-division controls retain undefined sister covariance. Fixed founder initialization, kernel, time grid, and pair qualification are unchanged.

## Maximum differences

The probability, contrast, and ratio gate is absolute `1e-8`. Only early-time coefficients use `1e-8*max(1,abs(reference coefficient))`, matching the declared coefficient scaling policy. No gate was loosened after comparison.

| Compared quantity | Primary versus reference | Strict versus reference |
|---|---:|---:|
| Family survival | 6.864e-10 | 5.094e-12 |
| Selected-path survival Q | 1.233e-9 | 1.241e-10 |
| Joint tag/family probability | 6.864e-10 | 5.094e-12 |
| Horizon contrast | 1.679e-9 | 1.372e-10 |
| Pair eligibility | 2.776e-16 | 2.776e-16 |
| Qualifying maternal weights | 1.110e-16 | 1.110e-16 |
| Sister covariance | 1.807e-11 | 4.674e-14 |
| Early-time coefficient | 3.348e-9 | 1.617e-10 |
| Early-time normalized ratio | 1.640e-10 | 4.607e-11 |

As an additional diagnostic, relative differences in positive early-time losses were at most `1.555e-9` for the primary run and `1.864e-10` for the strict run. This checks that agreement is not merely an absolute-error artifact for tiny probabilities. These diagnostics do not imply that a finite Monte Carlo cohort could measure those tiny losses.

The production pair covariance also agrees with the independently calculated moment representation and the analytic two-type identity. Calendar residual controls remain zero. All reference early-time records passed the frozen conservative envelope and smallest-epsilon check. Full per-field maxima and their locations are retained in the JSON.

## What this establishes

The independent formulations agree numerically on the specified hypothetical models. This supports implementation correctness within the checked grid. It does not validate an empirical cancer cohort, distinguish inherited state from every shared-environment alternative, or identify a biochemical death program from a small-time power. The separate full-tree Monte Carlo checks assess event-level simulation consistency; they are not replaced by agreement between deterministic calculations.

The [theory](theory.md) states the observation, initialization, independence, and small-time assumptions. The [protocol](protocol.json) preserves the pre-outcome scientific choices. Production code, result files, reference output, and frozen plans were not modified during comparison.
