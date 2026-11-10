# Independent review of the primary empirical bounds

**Pass.** Every saved primary result agrees exactly with an independent recalculation. All 300 contrast intervals include zero, both exactly and at tolerance `1e-12`. This does not establish no effect, validate a population branching model, or prove fundamental nonidentifiability.

The reviewed [results.json](results.json) has SHA256 `a3919f4994d57c6d77ac43fbe249aa9b01ee332d1116d367f5a6c9d9e3481a9e`. Its code, frozen protocol, source graph, original workbook, and private-record hashes match. The result timestamp follows the protocol freeze. The complete pins, checks, and all 300 classifications are in [empirical-review.json](empirical-review.json).

## Independent checks

The reviewer used the pinned source graph and saved local cell records. A separate iterative path-frontier implementation used exact fractions for missing-daughter weights and fate accounting; it did not import or call the production mass, ratio, or contrast functions. Independent rational calculations checked the optional-selection ratios, followed by a separate evaluation of the frozen contrast formula.

The [standalone review checker](../../../../scripts/review_hct116_primary_bounds.py) was packaged after the primary results and independent review. It is byte-identical to the executed local checker: SHA256 `13c919067b5e9cbbb1e7048d9c76978ce476da2f2726de014bce715055e97eaf`. This is **post-results validation**, not a preregistered scientific analysis. Packaging did not tune the calculations or rerun empirical analysis. Raw inputs and cell-level records remain ignored local files. With those pinned files present, run `python3 scripts/review_hct116_primary_bounds.py` from the repository root; the checker writes only ignored local review aggregates. The executed check-output hash is recorded in the review JSON.

| Check | Result |
|---|---:|
| Fixed baseline/offset/ambiguity combinations | 20 of 20 |
| Private selection-horizon groups | 60 of 60 |
| Distinct cell/time mass vectors | 39,788 checked |
| Stored vectors including repetitions across horizons | 119,364 checked |
| Ratio cases | 300 of 300 |
| Contrast cases | 300 of 300 |
| Maximum mass, ratio, or contrast discrepancy | 0 |
| Maximum mass-conservation residual | 0 |
| Undefined or potentially zero-denominator ratio cases | 0 |

All five rosters match the source-derived baseline eligibility checked against the workbook in the [implementation review](implementation-review.md). Roster counts remain 277, 280, 284, 289, and 291. Every roster is reused across horizons and sensitivities; no future-completeness filter appears. There are no missing or duplicated cases or node records.

For each baseline, offset, policy, cell, and query time, the saved mass vector is identical across selection horizons. Family status matches the mass at its selection time, and the possible/mandatory inclusion sets respect horizon nesting. Mass components are nonnegative and sum to one; survival bounds decrease with elapsed time, while known-dead and unknown mass do not decrease.

Whole-episode coarsening contains the first-issue per-cell bounds, ratio intervals, and contrast intervals. Delaying the death annotation by one frame does not lower the per-cell survival bounds. No monotonic relationship between conditional ratios under the two offsets was assumed. Every defined time-zero ratio equals one and every time-zero contrast equals zero.

## Interpretation of all fixed contrasts

| Evaluation time | Contrasts checked | Include zero at `1e-12` |
|---:|---:|---:|
| 0 hours | 60 | 60 |
| 6 hours | 60 | 60 |
| 12 hours | 60 | 60 |
| 18 hours | 60 | 60 |
| 24 hours | 60 | 60 |

The 60 time-zero comparisons are necessarily `[0,0]`; they are not empirical evidence for a model. All 240 comparisons at later evaluation times also include zero. The primary outer envelopes therefore do not resolve a directional cross-horizon difference under the stated observation assumptions. Their rectangular and separate-horizon relaxations can admit incompatible completed histories, so zero containment can reflect looseness.

These are finite recorded-roster compatibility envelopes, not confidence intervals. Original population eligibility, replicate mapping, independent experiment counts, annotation validity, and the treatment-origin discrepancy remain unresolved. Cells in the roster may share ancestors. No population test, treatment-effect estimate, or patient conclusion was performed.

The next action is the separately frozen refinement on all the same 300 cases, preserving these primary results. A narrower calculation may remove mathematical looseness; it cannot repair an uncertified cohort or observation process. This reviewer did not read or run joint-refinement outputs. Any later change of windows or scientific assumptions requires its own prospective plan.
