# Independent empirical review of the joint refinement

**Pass.** All 300 planned joint intervals match an independent exact-integer optimization within `1.88e-16`, well below the frozen `1e-12` comparison tolerance. The median relative width reduction is **51.56508439473909% across exactly the 240 nonzero-time cases**. Every one of those 240 intervals narrowed. All 300 intervals still include zero at the stated tolerance.

The audit checks [joint-results.json](joint-results.json), SHA256 `615f048074d62addf4138e1a71304116075580bdcf86cda0c96e47ff8057d784`, against the frozen joint plan, the primary results, the source graph, and saved local cell records. Full hashes, every case's width and classification, and audit checks are in [joint-empirical-review.json](joint-empirical-review.json).

## Method and timing

This is a **post-results independent validation**. The joint outcomes and reported median were already known when the audit was designed. No scientific endpoint, window, eligibility rule, or production optimization was changed.

The [standalone audit script](../../../../scripts/review_hct116_joint_bounds.py) does not import or call the production solver. It independently derives each row's allowed nested selection states, enumerates feasible selected-count pairs, and uses scalar dictionary dynamic programming. Dyadic interval endpoints are scaled to integers; for fixed counts `N1,N2`, the objective is multiplied by `scale*N1*N2`, making every optimization comparison exact. Rational extrema are converted to floating point only to compare with the saved production results.

Across the full grid, this checks 32,500 feasible count-pair instances and 271 distinct optimization inputs. It also checks that the count pairs reported as attaining each extremum are feasible and give the stated value within tolerance. Reproduce with `python3 scripts/review_hct116_joint_bounds.py`; original cell records remain ignored local inputs, and the script rewrites only the aggregate review JSON.

## Verified empirical invariants

- All 300 unique planned baseline/offset/policy/horizon-pair/time cases are present. The fixed source-derived roster is retained within each baseline scenario.
- Per-cell path-survival intervals use the same `u` values at both horizons. Status labels match each horizon's saved mass and obey nested family inclusion.
- Every refined interval lies inside its primary interval within tolerance. Every time-zero interval equals zero within tolerance.
- The whole-episode ambiguity policy contains the corresponding first-issue interval. Code, plan, input, and source hashes match; the joint plan freeze precedes the joint result timestamp.
- The independent optimizer's maximum absolute disagreement is `1.8735013540549517e-16`. There are no missing cases, undefined results, or classification discrepancies.

## Width calculation

For each case, relative narrowing is `100*(primary_width-joint_width)/primary_width`. The summary uses all and only the **240 cases with evaluation time greater than zero**, with no selection by sign or width. The 60 time-zero intervals are `[0,0]` and are excluded because relative narrowing would divide by zero.

| Quantity | Independently calculated value |
|---|---:|
| Nonzero-time cases | 240 |
| Strictly narrower cases | 240 |
| Median relative narrowing | 51.56508439473909% |
| Minimum relative narrowing | 43.70982552800713% |
| Maximum relative narrowing | 65.5065149694056% |
| Contrasts including zero at `1e-12` | 300 of 300 |

## Interpretation limits

These remain outer ranges for a finite recorded roster, not confidence intervals or population null tests. The narrowing measures reduced looseness in a mathematical relaxation; it is not a treatment effect or a reduction in biological variability.

Zero lying between the optimized lower and upper endpoints does not certify an attainable zero-valued completion. Discrete selection choices can leave gaps, and the optimization still omits constraints needed for a complete biological lineage tree. The results therefore establish neither no effect nor fundamental nonidentifiability.

Original cohort eligibility, annotation accuracy, replicate mapping, shared ancestry, and treatment timing remain unresolved. Further numerical tightening cannot by itself resolve those source limitations. Any further claim about population dynamics needs a defined cohort and observation model as well as a separately specified analysis.
