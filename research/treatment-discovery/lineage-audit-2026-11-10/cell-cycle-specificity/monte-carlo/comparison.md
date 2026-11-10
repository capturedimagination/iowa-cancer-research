# Independent complete-tree comparison

All 72 frozen cases are retained. There are **2 flagged comparisons**, **168 unresolved quantity checks**, 331 exact-binomial probability diagnostics, 2,829 quantity diagnostics and 144 accounting checks. These assess simulation consistency, not biological significance.

| Quantity-check status | Count |
|---|---:|
| structural_agreement | 507 |
| no_six_se_flag | 2143 |
| unresolved_low_precision | 168 |
| flagged_six_se_mismatch | 2 |
| expected_undefined | 9 |

Probability gates use the frozen two-sided threshold `0.001/331`, including conditional mother-type counts among eligible pairs. Quantity diagnostics use `6*MCSE+1e-8` when the relevant denominator is at least 100. Paired horizon standard errors remain those saved by the independently reviewed simulator. Nontrivial zero standard errors and low counts remain unresolved; no-division sister estimands remain undefined. Known structural constants are checked directly, with their original precision labels retained.

Before comparison evaluation, source review recognized deterministic-age Q=1 and horizon contrasts=0 through the first division time, including the division boundary. [The pre-evaluation classification note](comparison-amendment.json) preserves the original comparator pin and records this refinement; no simulation or primary outcomes were changed.

[Complete comparison records](comparison.json) contain every flag, unresolved result and case. [Pre-evaluation pin](comparison-freeze.json) binds both saved reference files, the unchanged first Monte Carlo results, comparator code and fixtures. No simulator or primary model code was imported. The strict reference file is pinned as convergence provenance; the standard reference values supply the declared comparisons. No seeds, models, outcomes or simulation code changed.

The approximate SE diagnostics are not a simultaneous confidence band. This comparison does not validate an empirical cohort, establish inheritance in cancer cells, or resolve the deterministic study's near-zero predictions with Monte Carlo.
