# Post-results interpretation review

**The useful result is a specificity limit: ordinary independent cell-cycle timing can change the family-selected survival curve across selection horizons. Neither the existence nor the sign of that change identifies inherited persistence.** Prospective sister-subtree covariance adds information within the specified models, but calendar mixing and shared family environment prevent a universal inheritance interpretation.

This review was written after the full fixed-grid outputs existed. It reads saved aggregates and the pre-results theory/prior-art record; it does not rerun models, fit empirical data, change the grid, or identify a cancer target. Exact input hashes, every case summary, all model strata, and every descriptive early-event count are in [interpretation-review.json](interpretation-review.json).

## Whole-grid findings

The review includes all 72 planned model records, 864 primary horizon contrasts, 216 pair records and 567 early-time records. The 12 pairs of identical k=1 founder initializations remain included as planned; these are model records, not independent replications. A contrast is called numerically nonzero here when its absolute value exceeds `1e-8`, the frozen numerical agreement scale. This is a descriptive numerical convention, not a significance test or a practical detection threshold. Exact zero statements below also have the mathematical identities in [theory.md](theory.md).

| Model class | Records | Horizon contrasts across the full declared grid | Sister-subtree covariance |
|---|---:|---|---|
| Homogeneous exponential renewal, positive death | 6 | All 72 consistent with zero; largest absolute residual below `7.2e-11` | Zero |
| Independent non-exponential renewal: homogeneous Erlang k>1 or independently redrawn timer mixtures | 30 | All 360 nonzero: 288 positive, 72 negative | Zero; largest numerical residual `1.24e-32` |
| Transmitted two-type models, positive death | 24 | All 288 nonzero: 255 negative, 33 positive; four records contain both signs at different declared comparisons | Positive in all 72 pair-lag records |
| Deterministic division age, positive death | 3 | 18 positive, 18 exactly zero before/at first division | Zero |
| Shared calendar division rate | 3 | All 36 zero | Positive in all nine pooled pair-lag records; birth-conditioned residual expectation zero |
| No division | 3 | All 36 zero | All nine pair records undefined |
| Zero death, including a persistent-type control | 3 | All 36 zero | Zero |

Across all classes there are 327 negative, 339 positive and 198 numerically zero contrasts. Fifty-seven model records have at least one nonzero contrast. The descriptive contrast range is `−0.0535797` to `0.0513442`, in conditional probability units. These extrema describe the fixed grid; they are not selected estimates of a biological effect.

The negative no-transmission results arise in the k=1 independently redrawn two-rate mixtures: all 72 such contrasts are negative. A fresh rate label is drawn independently for each daughter, so the marginal renewal timer is non-exponential even though it is conditionally exponential within a cell. Homogeneous Erlang k>1 and redrawn k=4 mixtures instead give positive contrasts throughout their declared comparisons. The sign therefore separates some timer constructions in this grid, not inheritance from non-inheritance. The deterministic controls independently show that a delay before the first division is enough to break full horizon invariance afterward.

A nonzero contrast at a declared point is sufficient to disprove full horizon invariance for that model. Numerical agreement at finitely many points would not prove invariance on all times; the exponential and shared-calendar controls have separate analytic proofs.

## What the added measurements distinguish—and where they fail

All 24 positive-death transmitted-type cases have positive sister covariance, from `2.35e-5` to `0.0177101` across their 72 declared pair lags. The independent-renewal cases have analytically independent newborn sister futures, hence zero covariance despite their nonzero horizon contrasts. This supplies a useful conditional distinction between these stipulated models. It requires prospective pair eligibility, equal elapsed lags, both extinct subtrees retained, and appropriate conditioning on shared context.

Raw covariance alone fails that distinction under the calendar controls: its range is `2.52e-5` to `0.000664326`, overlapping transmitted-type values. Both sisters share their birth time, and pooling different birth times mixes different subtree-survival probabilities. The known-model residual uses each exact `h(b,b+s)` and has expectation zero. This is a theoretical/model control; an experimental analyst would have to estimate that function and account for its uncertainty. Coarse birth-time bins or a fitted residual are not automatically equivalent to conditioning on known context.

The grid includes age dependence and calendar mixing as separate controls. It does not exhaust combinations of age dependence with shared changing context. A combined no-transmission model potentially producing both statistics would require a separately specified experiment; it has not been demonstrated by this run. More decisively, a permanent family environment with the same conditional tree laws is exactly observationally equivalent to a perfectly inherited type. No additional statistic of those same trees can universally distinguish that relabeling.

Zero death makes both the survival contrast and covariance vanish even in the persistent-type control. Equal type-specific subtree survival at a chosen lag is another analytic covariance blind spot, although it is not a new numerical case in this grid. No division leaves the sister estimand undefined. These failures must not be recoded as evidence of no inheritance.

The correct maternal weights are those among founders that divide before death and the cutoff. They differ from the initial type proportions. Founder initialization can therefore affect covariance magnitude through eligibility even though every daughter is newborn. The models share particular timer constructions; they do not match every observable marginal, growth rate or selected distribution. The numerical separation is not a general classification guarantee for arbitrary alternatives.

## Leading powers and coefficients

For the 18 positive-death newborn model records without transmitted type, the leading small-time coefficient is independent of selection horizon, with maximum relative numerical range `2.06e-16`. Nevertheless, 15 of those 18 records have nonzero finite-time horizon contrasts. **Matching leading coefficients does not establish invariance of the full curve.**

All 12 positive-death transmitted newborn records have a horizon-varying leading coefficient. Their relative ranges, `(max A_T−min A_T)/max A_T`, span about `0.00857` to `0.18793`. This is a distinction within the known-newborn, matching-initial-law construction. It fails as a general transmission diagnostic: all 12 no-transmission, k>1 uniform-stage records also have horizon-varying coefficients, with relative ranges about `0.00825` to `0.03815`.

Newborn Erlang order is `k+1`; uniform initial stages instead produce order 2 from the founders nearest division. Arbitrarily little initial mass near division can change the strict leading order. This is not generally a linear onset, and the specified uniform-stage law is not a claimed equilibrium age distribution. Deterministic newborn division has a flat initial interval, while zero death has zero loss and an undefined positive-leading-term ratio.

All 540 positive-leading-term epsilon records are retained. Their ratios of exact positive defect to leading term range from `0.990058` to `0.999998`; at the smallest epsilon, the maximum absolute departure from one is about `1.00e-4`. The 27 zero-death ratios remain undefined. These are numerical/asymptotic checks of the stipulated model. The order does not count biochemical killing stages or imply a globally equivalent multistep lifetime distribution. The [bounded prior-art audit](prior-art.md) already identifies familiar Erlang/convolution mathematics and close lineage-statistic work; no priority claim follows.

## Post-results event-count feasibility check

For every positive-death Erlang case and every selection horizon at the smallest frozen epsilon, this review computed

`expected selected tagged deaths = 10000 * P(F_T=1) * (1-Q_T(t))`.

All 180 records are included. The range is approximately **`2.20e-41` to `1.67e-5` expected events per 10,000 prospective founders**. Evaluation times range from `1.25e-5` to `1e-4` in uncalibrated model units. The nine positive-death non-Erlang controls have no frozen alpha-based epsilon record and are explicitly marked not applicable; the three zero-death controls are excluded from the positive-event calculation.

This expectation corresponds to one fair random tag per founder. Complete-tree `U` integrates all tag choices and instead supplies fractional weighted mass, but sampled trees still need realized rare contributions. The deterministic branching equations evaluate these tiny probabilities; the finite Monte Carlo cohort does not verify their sampling resolution. The computation is a post-results descriptive resolution check, **not a power analysis**, a sample-size recommendation, or a physical-time prediction. It argues against treating the tiny-time asymptotic signal as directly measurable in the current cohort design. Finite-time discrimination would need a separate prospective precision/power design.

## Research use and limits

The immediate use is a falsifiable stress test for lineage observation models: compare the same prospective founder population across horizons, keep the prospective sister cohort separate from endpoint selection, and examine finite-time joint patterns before attributing persistence to inheritance. The next bounded design should challenge that comparison with uncertain founder age, measured/shared calendar context and recording loss, and specify precision across the entire planned alternatives before new results. Near-zero coefficients are more useful here as theoretical checks than as an empirical endpoint.

An empirical application still requires a defensible original founder denominator, complete or honestly bounded daughter trees, known event/censoring rules, and uncertainty clustered by founder/experiment. This synthetic study does not resolve the source-data eligibility and missing-branch issues documented elsewhere in the project. Additional measured context or an intervention that changes the competing mechanisms would be required to break the exact shared-environment equivalence.

The primary result file records PASS and the complete-tree file contains all 72 completed cases. This interpretation does not independently redo the reference/Monte Carlo comparison; those numerical validation gates belong in their separate reports. It does not supply biological significance, clinical efficacy, a drug target, a cure, or a refutation of Iyer's already age-dependent models.
