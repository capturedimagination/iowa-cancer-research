# Independent review of the three-timepoint curvature design

**The mathematics and reported power calculations pass independent checks under the stated assumptions.** The result is a useful conditional precision calculation, not a new cancer mechanism or demonstrated optimal experiment. The bulk comparison supports only the particular conservative test used here.

This review did not import or rerun the simulation's implementation functions. It used numerical hazard quadrature and an integrating-factor solution for 243 alternative trajectories, matrix exponentials for constant-rate trajectories, and a standard-library Gaussian calculation for all 2,916 alternative power rows. The [review JSON](independent-review.json) records hashes, numerical results and literature searches. The frozen protocol, simulation code and simulation results were not changed. This is an independent agent review, not external scientific peer review.

## Derivation and numerical verification

For any positive P, let the interval-average net log-growth rates be `a1=(log P(T)-log P(0))/T` and `a2=(log P(2T)-log P(T))/T`. Then `C=T(a1-a2)`. It is a negative second finite difference: a positive value means growth slows between these intervals. Constant log-growth gives zero. This is not intrinsically a memory statistic.

Integrating the specified `P'/P = gP-b_inf*(1-exp(-t/tau))` gives the stated log trajectory. Its constant and linear terms cancel in C, leaving `b_inf*tau*(1-exp(-T/tau))²`. Under independent common Gaussian log errors, the contrast variance is `(1+4+1)*sigma²/r=6*sigma²/r`. Mean-unbiased lognormal measurements have a `-sigma²/2` log bias; it cancels only because the variance is common across times and contrast weights sum to zero.

Independent results:

| Check | Maximum absolute discrepancy |
|---|---:|
| State contrast, quadrature versus submitted result | 9.99 × 10⁻¹⁶ |
| Bulk contrast, integrating factor versus submitted ODE | 1.83 × 10⁻¹⁰ |
| All alternative Gaussian power values | 7.07 × 10⁻¹¹ |
| Constant-rate bulk contrast, matrix exponential | 3.16 × 10⁻¹⁴ |
| Minimum 80% detectable contrast | 5.87 × 10⁻¹⁴ |

Independent bisection gives the standardized 80% effect `2.80158178701358`, agreeing with the submitted value. Recounting gives 621/2,916 state-test settings and zero bulk-test settings reaching 80%. Initial fraction and constant state growth cancel from the state contrast, so the grid has repeated effect sizes; its hit fraction is not a real-world success probability.

## Review-only sensitivity: variance estimated from the experiment

The frozen simulation assumes known variance. If instead a common log variance is estimated from independent replicate wells within each of the three times, the pooled estimator has `df=3(r-1)`. Under independent Gaussian log errors it is independent of the mean contrast, and the contrast test uses a two-sided Student t threshold. Power then depends on a noncentral t distribution.

The reviewer calculated power by integrating conditional Gaussian rejection probabilities over an independent chi-square variance estimate, then solved for 80% power. This is a separately labeled mathematical sensitivity, not a revision of the frozen simulation or an empirical noise estimate.

| Independent wells per time | Variance degrees of freedom | Known-variance minimum C at 10% CV | Estimated-variance minimum C at 10% CV |
|---:|---:|---:|---:|
| 3 | 6 | 0.395218 | **0.474967** |
| 6 | 15 | 0.279462 | **0.299041** |
| 12 | 33 | 0.197609 | **0.203598** |

With one well per time, within-time variance cannot be estimated by this procedure. Neither table covers unequal variances, correlated wells, count zeros, uncertain state labels or biological replicate heterogeneity. A robust empirical design would need those assumptions checked. The calculation concerns means of logarithms, not logarithms of arithmetic means.

## Bulk comparator: correct within its narrow scope

Under constant rates and the chosen range `gP<=gS`, define `a=gS-gP+b` and `w=f0*(gS-gP)/a`. The total population can be written as

```text
N(t) = (1-w)*exp(gS*t) + w*exp((gP-b)*t).
```

Both weights are nonnegative. Consequently log N is convex and the negative second difference is nonpositive, even without changing transition rates. The zero-gap limit is a single exponential. This independently supports the decision not to test bulk C against zero.

However, 242 of 243 unique noiseless alternative/window contrasts fall inside the constant-rate envelope. For an interior mean, this envelope test remains low-powered as measurement noise shrinks. The one outside lies only 0.00406649 below the lower boundary. The maximum analytic bulk power in the tested settings is 3.7919%. Thus the comparison mostly measures overlap with a broad composite null for one scalar statistic. It does not show that bulk trajectories contain no usable information or that state assays are generally more cost-effective.

A continuous numerical search found the finite-grid lower bound misses minima by about 4.71 × 10⁻⁸ at T=1 and 5.39 × 10⁻⁶ at T=2. The latter is tiny compared with the smallest assumed noise SD, 0.0353333. This is not a material numerical failure, but neither that optimizer nor 64 held-out parameter points proves uniform error control throughout the continuous parameter domain.

State abundance assumes a validated functional label and direct absolute quantification, whereas bulk counts need no state label. Equal numbers of measurements and equal assumed CV do not establish equal assay information, practical precision or cost. The current README states this limitation appropriately.

## Biological specificity and prior art

Time-varying proliferation or changing marker retention can reproduce the entire labeled P trajectory. Constant-rate influx from another state can also make log P nonlinear. The current documentation correctly limits the null to constant net P growth without re-entry. Increasing P-only sampling cannot distinguish exact observational equivalents. It also would be inappropriate to substitute the unvalidated 17-gene mean-expression score for a functional abundance measurement.

The closest verified primary literature substantially limits novelty:

- [Harris et al., 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4887341/) already treat log-growth slopes, delayed drug effects and two-state dynamics.
- [Gunnarsson, Foo and Leder, 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10372878/) analyze curvature-based identifiability, cell counts versus fractions, and additional time points versus replicates. Their curvature argument is not the identical three-point log-state formula.
- [Wu et al., 2025](https://www.nature.com/articles/s41540-025-00560-8) demonstrate richer bulk-count inference with delayed drug effects and state plasticity.

The exact elementary contrast/precision table was not located in the bounded search. That is not evidence of first discovery. General curvature, lag detection, state inference and experimental design already have direct prior art. An accurate claim is an original reproducible implementation and a transparent precision/failure-boundary illustration. A claim of a new mechanism, new optimal design or first-ever test is unsupported.

## Reproduction

The review-only [checker](../../../../../scripts/check_egfr_curvature_design.py) imports none of the simulator's functions. In the pinned project environment (NumPy 2.3.5, SciPy 1.16.3), run from the repository root:

```sh
python scripts/check_egfr_curvature_design.py --out tmp/curvature-independent-checks.json
```

It verifies reviewed hashes, recomputes trajectories and power, explores the bulk envelope, and reproduces the separately labeled estimated-variance sensitivity. Its output corresponds to `numerical_checks` in the review JSON. Source papers and downloaded originals remain in ignored temporary storage; no full articles are republished.
