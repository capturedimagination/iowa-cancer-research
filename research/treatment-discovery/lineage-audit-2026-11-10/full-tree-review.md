# Independent full-tree verification

Completed November 10, 2026. **An explicit branching simulation agrees with the conditional tagged-path survival identity.** This independently checks the mathematical observation model; it does not establish that the Oren workbook follows that selection rule or identify a cancer mechanism.

The [review protocol](full-tree-review-protocol.json) and [hash/timestamp](full-tree-review-freeze.json) were fixed before this run: SHA-256 `9c00b14a08a36eb3ba585a9c396eee5f3a242c624da49cbd723bd4e17d6ef16d`. The reviewer used 20,000 founder trees for each of six fixed rate pairs, horizon T=1, seed 2026111005 and NumPy 2.3.5. Rates and time are hypothetical. No workbook event data were used.

## Independent implementation

The [checker](../../../scripts/check_lineage_family_sampling.py) maintains every currently living cell explicitly. Gillespie waiting times use total population event intensity `N*(lambda+mu)`. It selects the affected cell uniformly; division replaces that cell with two daughters, and death removes it. A separate random choice follows one daughter when the tagged cell divides. **The full tree continues after tag death.** Founder inclusion is determined only by whether any cell remains alive at T.

This implementation does not import the shortcut simulator, simulate side-branch extinction Bernoulli variables, or use the analytic survival formula to generate trees. Analytic formulas are used only after simulation for comparison. Every tree passed the exact population balance `N(T)=1+divisions−deaths`.

## Results

All 120,000 prespecified trees and all 54 probability comparisons are retained. Comparisons cover family inclusion, prospective tagged survival and family-selected tagged survival at t=0.25, 0.5, 0.75 and 1. The largest absolute deviation was **1.906 analytic binomial Monte Carlo SE**, within the prespecified six-SE computational-check bound. This bound is not a biological significance threshold. Exact zero-rate fixtures passed.

| Division lambda | Death mu | Selected families | Family inclusion: simulated / exact | Selected tag survival at T: simulated / exact | Tags dying in selected families |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 2 | 3,540 | 0.177000 / 0.177234 | 0.771751 / 0.763596 | 808 |
| 2 | 0.5 | 15,907 | 0.795350 / 0.794309 | 0.762432 / 0.763596 | 3,779 |
| 2 | 2 | 6,661 | 0.333050 / 0.333333 | 0.403693 / 0.406006 | 3,972 |
| 0 | 2 | 2,750 | 0.137500 / 0.135335 | 1 / 1 | 0 |
| 2 | 0 | 20,000 | 1 / 1 | 1 / 1 | 0 |
| 0 | 0 | 20,000 | 1 / 1 | 1 / 1 | 0 |

For unequal positive rates, the selected-tag survival law is `[lambda*exp(-mu*t)−mu*exp(-lambda*t)]/(lambda−mu)`. Equal rates k give `exp(-k*t)*(1+k*t)`. A zero rate has the corresponding degenerate limit. Swapping lambda and mu leaves this selected lifetime law unchanged, although family inclusion and division histories differ. Death-time information alone therefore cannot distinguish the two rate assignments in this idealized selected model.

The positive selected-tag death counts explicitly separate **family survival** from an ancestry required to reach a surviving endpoint cell. The latter cannot contain death before the endpoint. These sampling rules must not be exchanged when interpreting the source workbook.

## Scope and reproduction

The [complete JSON](full-tree-review.json) retains all counts, probability estimates, analytic and estimated Monte Carlo SEs, deviations, population totals and provenance hashes. Survival times within a tree are correlated; this is not 54 independent experiments. The check validates selected-survival probabilities, not every shortcut event-bin integral or an empirical hazard model.

Use the pinned project environment and run:

```sh
python scripts/check_lineage_family_sampling.py
```

The [hazard estimand review](hazard-estimand-review.md) supplies the derivation, competing sampling schemes and analysis gates. The [source dictionary](source-dictionary.md) still leaves required time, selection and censoring fields unresolved. No empirical division, death or tolerant-state exit rate is validated by this simulation.
