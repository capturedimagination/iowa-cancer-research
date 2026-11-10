# Independent Monte Carlo implementation review

Date: 2026-11-10. **Static mathematical review passed after a pre-run clock-boundary correction and verification-gate hardening.** The reviewer did not execute either scientific grid, import the primary model, or read new primary/reference numerical outputs. Final reviewed hashes and inspected fixture reports are recorded in the companion JSON. Numerical agreement remains a separate outcome.

## Complete trees

`simulate_age_calendar_trees.py` generates complete branching trees in operational time. A founder at stage j draws an Erlang residual timer with shape k−j+1 and scale mean_z/k, independently of its exponential death timer. Daughters restart at stage 1. Two-type daughter uniforms are independent conditional on maternal type and give transition probability (1+ρ)/2 to remain the same type. Initial types are equally weighted. The documented draw order includes endpoint-born daughters and consumes daughter uniforms even for ρ=1; this makes reproduction explicit.

Every fixed physical query uses R(t). Pair eligibility uses the first founder division before its death and by R(2), without later selection. Both daughter subtrees are queried at R(b+s), not R(b)+R(s). Birth-bin membership compares original operational birth times with transformed boundaries, avoiding inverse-roundoff changes of bin assignment. No observed qualifying birth is replaced with an imputed zero; absent births and absent pair-query times remain NaN in checkpoints, and ineligible roots are excluded from pair counts.

Generation-g cells carry chronological mass 2⁻ᵍ. Summing all live descendants at each query correctly integrates a future-blind fair daughter choice. Subtree side labels propagate from the first founder division. Death and division use half-open lifetimes; tied potential death wins. Empty selected cohorts retain undefined Q. Empty/one-pair bins retain undefined covariance. Empty removed strata have zero unconditional removed-loss mean and undefined conditional mean. Resource failures preserve completed checkpoints and incomplete status instead of replacing founders.

**Resolved finding:** the initial inverse bisection treated an exact midpoint equality as an upper bound, producing a slightly early reconstructed birth. Under the nonlinear clock, birth b=.5 and lag .5 could consequently query before a daughter death exactly at R(1). The corrected inverse sets both bracket endpoints to an exact matching midpoint. The added deterministic fixture preserves b=.5 and excludes the daughters at the death boundary. This correction preceded scientific execution. The inspected fixture report increased from 29 to 30 checks.

## Shared calibration experiments

`simulate_shared_calibration.py` keeps target counts in category order 00,01,10,11, preserving both discordant orientations for ordinary sample covariance. Each independent whole experiment draws one Binomial(m,p) calibration fit and reuses it across n target pairs. All four estimators use the same target counts. The random unit is the whole experiment, not individual pairs sharing a fitted mean.

The code uses every frozen tuple [seed,case,lag,bin,m,n] in protocol order: 720 settings, 50,000 experiments per setting, fixed batches of 5,000. Each batch draws calibration values before target multinomial counts. The four-category score formulas reproduce the oracle product, shared-fit product, binomial correction, and unbiased target sample covariance. Seed, environment, source hashes, checkpoints, moments and failure records are retained.

For each estimator, the mean check uses its reference variance and bounded score range. The squared-deviation variable W=(Y−EY)² has range at most L² and variance at most L²Var(Y), which is the implemented conservative bound. The threshold sqrt(2v log(2K/α)/N)+2L log(2K/α)/(3N) is sufficient for the stated two-sided Bernstein bound. K=5,760 covers 720×4×2 checks. The union bound does not require independence among estimators or overlapping design settings. Zero-variance diagnostics retain the numerical slack and record exact floating-point agreement separately. Inspected deterministic fixture reports contain 20 initial and 27 final checks; these are not simulation outcomes.

**Resolved finding:** the first runner accepted any nonempty verification JSON. It now requires the known independent report schema to show PASS, 20 cases, no failures, the complete field count, the frozen protocol hash, and the byte hash of the supplied primary result. These validation checks execute before generating calibration draws. This static review verifies the gate's implementation, not the numerical comparison result that will be supplied to it.

## Operational conditions and limits

- Before calibration execution, the saved independent verification evidence must pass the implemented full-report and input-hash gate. External authorization to start the run remains a separate operational decision.
- Tiny probability projections are bounded and explicitly recorded. Sampling then uses the projected law while statistical comparisons retain raw numerical references. The concentration statements are exact for exact reference probabilities; the declared numerical slack is not an interval-arithmetic guarantee for ODE integration or projection error.
- Writes use exclusive/atomic publication of individual files, with provenance-checked resume. An incomplete case/setting is reported rather than dropped. The scripts can return process status zero with incomplete records, so completion must be determined from the aggregate counts, not exit status alone.
- A keyboard interruption retains completed checkpoints but does not guarantee a custom interrupted-batch diagnostic. Unexpected raw tracebacks may contain local paths; preserve these privately and review any failure-containing public report before release.
- The tree script imports no primary branching solver. The calibration script uses saved p/j/moment references and imports no numerical branching model. Their independent implementation checks do not establish biological replication, clinical relevance, or a new estimator.

No further blocking formula or generator issue was found in the reviewed source versions. A changed script requires a new hash and review of the changed contracts before relying on this report.
