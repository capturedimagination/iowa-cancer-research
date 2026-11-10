# Implementation choices before the empirical calculation

The [frozen protocol](protocol.json) fixes the recorded rosters, time grid, annotation sensitivities and descriptive estimand. These implementation notes were written before inspecting empirical ratio or contrast bounds.

- The generic mass API checks whether a baseline cell is alive using the chosen death-frame offset. A synthetic founder with an apoptosis annotation at frame zero and death offset one is alive at baseline and dies at frame one. The empirical caller independently applies the protocol's stricter common eligibility rule: no apoptosis annotation at or before baseline. The source review found no same-frame baseline apoptosis flags, so this API correction does not change the empirical roster. Both boundary cases have fixtures.
- One source episode has a simultaneous division/apoptosis flag. Neither annotation receives priority. Its unresolved fate becomes unknown path mass under both prespecified ambiguity policies.
- Missing daughters retain their original half-weight. The calculation does not renormalize onto the recorded sister or exclude the baseline family because later recording is incomplete.
- A source baseline cell is a recorded observational unit, not automatically an independent experimental replicate. Resetting its path mass to one does not validate the original cohort selection or erase shared ancestry.
- The current graph is hash-pinned and its complete event-to-episode mapping was independently checked against the original workbook. The generic constructor is not a replacement for those source checks when other graphs are supplied.
- Numerical endpoints are floating-point approximations to the mathematical outer bounds. The production arithmetic was checked against exact rational controls. Use a `1e-12` tolerance for implementation agreement and any descriptive zero-separation count; this is not an interval-arithmetic certificate or a statistical significance threshold.
- The simulated-forest check tests deterministic containment of known complete-tree truth after branch removal. It does not estimate confidence-interval coverage or validate the cancer model. No rate was fitted to HCT116 observations.

All planned cases will be retained. Neither a separated finite-record interval nor an interval containing zero establishes the population horizon-invariance hypothesis. Unknown original eligibility, sampling variability and the looseness of the relaxation remain distinct limitations.
