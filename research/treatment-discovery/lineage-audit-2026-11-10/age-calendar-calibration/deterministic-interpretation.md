# Full-grid deterministic interpretation

Status: descriptive analysis of completed, frozen hypothetical calculations. No new model run, fit, window selection, seed, threshold or biological claim was introduced. All 240 horizon contrasts, 60 case/lag pair profiles, 900 bin targets and 5,400 calibration settings are included. Counts and signs reproduce across primary, strict and independent calculations.

**Main finding:** the six tested models combining independent non-exponential division timers with changing shared calendar rates produce both horizon contrasts and pooled sister covariance without transmitted type. Exact birth-time conditioning removes the modeled covariance in these cases. Finite bins retain some context covariance, and estimating a shared baseline adds a separate, exactly calculable calibration artifact. Ordinary sample covariance is the simpler benchmark for a single bin.

This is a restricted common-clock construction: both division-stage and death hazards share the same deterministic multiplier. It does not validate a cancer mechanism or establish novelty. An unobserved persistent family environment can still imitate transmitted type.

## All contrasts and pair profiles

Contrast means `Q_later(t)-Q_earlier(t)` at the same t. The descriptive zero band is the frozen numerical-agreement scale, absolute value <=1e-8; it is not a significance test. Values near zero are retained in the JSON.

| Model stratum | Cases | Horizon contrasts: positive / negative / numerical zero | Positive pooled sister covariances / all case-lag profiles |
|---|---:|---:|---:|
| No transmission, exponential division | 3 | 0 / 0 / 36 | 5 / 9 |
| No transmission, age dependence, constant clock | 3 | 36 / 0 / 0 | 0 / 9 |
| No transmission, age dependence, changing clock | 6 | 72 / 0 / 0 | 15 / 18 |
| Transmitted type, constant clock | 2 | 0 / 24 / 0 | 6 / 6 |
| Transmitted type, changing clock | 4 | 0 / 48 / 0 | 12 / 12 |
| Zero death controls | 2 | 0 / 0 / 24 | 0 / 6 |
| Total | 20 | 108 / 72 / 60 | 38 / 60 |

All 72 contrasts in the combined no-transmission age/calendar stratum are positive, ranging from 0.000220052 to 0.0424374, or approximately 0.0220 to 4.2437 percentage points. All six cases also have positive pooled covariance at some declared lags; 15 of their 18 case/lag values are positive. The other three are the prespecified period-2/lag-2 aliases. Their exact birth-conditioned covariances are zero; their pooled covariance is entirely the variance of survival probability over birth times.

Across the entire 240-contrast grid, the minimum is -0.0496268 in A17 at t=1.5, selecting at 2 versus 4; the maximum is 0.0424374, first attained in A04 at t=2 for the same horizon pair. These are descriptive hypothetical extrema, not fitted biological effect sizes. A05 shares the maximum because the period-2 clock agrees at the relevant mapped endpoints.

The sign separation here is **not a general inheritance classifier**. This grid deliberately uses k=4 non-exponential age cases. The earlier published study already contains independently redrawn exponential-rate mixtures with negative contrasts and no transmitted type. Founder initialization, rate choices and model class matter.

## Context bins and exact aliases

All 180 transitions through the four nested birth partitions satisfy nonincreasing weighted context variance within numerical tolerance. Of the 60 case/lag profiles, 38 have context variance above 1e-8 and 22 are numerical-zero controls. Relative reductions are undefined for those 22 near-zero denominators; the profiles are retained.

Across the 38 nonzero profiles, reducing bin width from 2 to 0.25 lowers weighted context variance by 80.975%–97.082%, with an unweighted grid median of 92.249%. Among the 20 no-transmission profiles with nonzero context, the range is 80.975%–96.969% and the median is 91.861%. These are reductions of the modeled context contribution, not reductions of total inherited covariance, statistical error or biological risk. Fine bins remain different from exact conditioning.

The smallest reduction is A09 at lag 1; the largest is A13 at lag 0.5. Different bin masses are weighted by their qualifying birth probabilities. Equal weighting of bins would describe a different estimand. The grid median is a descriptive summary, not a population-weighted effect or an optimization recommendation.

The four no-transmission period-2/lag-2 aliases are A02, A05, A08 and A11. Their raw covariance vanishes because every birth time has the same operational follow-up duration. Three belong to the combined age/calendar stratum; the fourth is the exponential control. Do not extend this zero-covariance rule to transmitted-type cases: their qualifying maternal-type mixture can still depend on birth time.

All 585 applicable no-transmission bin bounds hold. Of these, 300 have a positive bound; the actual context variance is at most 0.117704 times the conservative bound in this grid. The bound is a check under the stated clock assumptions, not a universal threshold for inheritance.

Birth-time conditioning also changes composition in transmitted-type cases even under a constant clock: the maternal-type distribution among qualifying first divisions depends on b. Thus the decomposition's between-birth contribution is not exclusively a calendar-rate artifact. Exact birth-conditioned covariance is positive in all 18 positive-death transmitted-type case/lag profiles here, but a persistent shared family environment remains observationally compatible.

## Shared calibration versus ordinary sample covariance

There are 4,860 positive-death settings and 540 zero-death settings. Each m/n design contains 810 positive-death and 90 zero-death settings. All four methods' means and variances are exactly zero in the zero-death controls, so variance ratios are undefined there; these settings are retained.

For every positive-death setting, the uncorrected residual product has the predicted upward bias `p(1-p)/m` relative to bin covariance. Bias ranges from 0.00133584 to 0.05 in covariance units. The finite-binomial calculation matches that formula within 1.02e-16. The corrected residual mean matches bin covariance within 1.03e-16. Neither correction removes within-bin context mixing.

At the same number n of evaluation pairs, the corrected shared-calibration estimator has higher variance than ordinary unbiased sample covariance in all 4,860 positive-death settings, exceeding it by more than 1e-10 in each. The overall variance ratio ranges from 1.02806 to 101.575. The comparison uses the same n pairs; the calibrated estimator additionally requires m independent singles. It is not a comparison at matched total sampling cost and does not establish an optimal allocation.

| Calibration singles m | Evaluation pairs n | Corrected variance / sample-covariance variance: min–max | Median fraction of corrected variance from shared-calibration floor |
|---:|---:|---:|---:|
| 5 | 100 | 10.4115–11.3369 | 87.714% |
| 5 | 1,000 | 92.5502–101.575 | 98.619% |
| 20 | 100 | 1.56147–1.61798 | 32.357% |
| 20 | 1,000 | 5.89299–6.37670 | 82.709% |
| 100 | 100 | 1.02806–1.03113 | 1.942% |
| 100 | 1,000 | 1.20237–1.22265 | 16.530% |

The exact floor is `2[p(1-p)]^2/[m(m-1)]`. It persists as n grows with fixed m. This explains why evaluating more target pairs can sharply worsen the variance ratio while leaving the shared-calibration error. It is an estimator property, not evidence of a biological process.

The oracle using the true bin mean has slightly lower variance than sample covariance throughout the positive-death grid: ratios 0.989933–0.999085. The true probability is generally unavailable; the small oracle advantage does not justify substituting an estimated shared mean without accounting for its uncertainty. For a bin-level covariance target, ordinary sample covariance needs no external calibration. General regression over continuous context is a different problem, and the exact binomial correction is not a universal regression-bias correction.

The JSON also retains descriptive uncorrected mean-squared-error ratios (targeting bin covariance), all m/n summaries, extrema and their identifiers. These post-results summaries are not power calculations, confidence intervals or new hypothesis tests.

## Reproducible aggregation and checking

[interpret_age_calendar_grid.py](../../../../scripts/interpret_age_calendar_grid.py) reads only the frozen outputs and verified comparison, checks their hashes, and reconstructs this full-grid aggregation. The first `deterministic-interpretation.json` SHA256 is `e5b4d4408b4efc9b3bda2798c867d95d6008029a2f422e5406ba34d7678c92bc`.

[check_age_calendar_aggregation.py](../../../../scripts/check_age_calendar_aggregation.py) independently extracts all 240 signs, variance orderings, weighted context reductions and summary extrema from primary, strict and independent outputs. It exactly reproduces the primary counts, extrema and medians, and confirms all 240 sign labels and 4,860 variance orderings across all three calculations. Its PASS report, `deterministic-interpretation-checks.json`, has SHA256 `40ecdb1ac376c9b8f965b163b013c46623519d6f94ac903cb802759692fe6651`. A check-helper bookkeeping failure and correction are recorded in [aggregation-history.json](aggregation-history.json); no scientific input or aggregation changed. The first local artifacts remain preserved. Public promotion changed only portable code paths and provenance metadata, with exact scientific-content equality verified.

From the project root, choose new paths to preserve the first reports:

```sh
python scripts/interpret_age_calendar_grid.py --out tmp/age-calendar-2026-11-10/interpretation-reproduction.json
python scripts/check_age_calendar_aggregation.py --out tmp/age-calendar-2026-11-10/interpretation-checks-reproduction.json
```

The complete deterministic comparison checked 192,290 numeric primary/strict-to-reference differences without failure; its largest overall discrepancy was 5.47e-10 and its largest calibration discrepancy was 1.56e-11. That agreement supports implementation consistency. It does not validate assumptions about a cancer-cell dataset, infer inherited resistance, establish novelty or resolve prior empirical source limitations.
