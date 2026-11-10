# Independent implementation review

Status: **static mathematical/protocol review passed; no remaining blocking finding**. No new scientific grid was executed or inspected by this reviewer. Review date: 2026-11-10. Initial and final reviewed implementation hashes are pinned in the companion JSON. Both recommended defensive checks and failure-value diagnostics were implemented before production outcomes. This review does not establish numerical convergence, independent simulator agreement, biological validity, or novelty.

The reviewed files are `scripts/age_calendar_calibration.py`, the frozen `protocol.json`, its formula-authority `theory.md`, and the hash-pinned prior `scripts/age_lineage_models.py`. Saved reports record 20 initial and 25 post-hardening non-grid checks. The final `primary-fixtures-pinned.json` records 25 passes for reviewed code `6f5d8279ca762bbd0ac6b4614806edd898bdbcf5c46b7ea7ec1a475a4b88a261`, also pinned before execution in `primary-code-pin.json`. I inspected those reports and fixture code, but did not rerun them or execute the model grid. Review findings were communicated before launch; this report was finalized after the root agent's launch notification without reading scientific outcomes.

## Mathematical checks

**Clock and selected paths.** Differentiating R gives the implemented r. Both transition/division and death clocks are multiplied, so stationary probabilities evaluated at R(t),R(T) are the intended common-clock model. The positive clock and R(4)=4 put every frozen query in the prior core's solved interval. The unconditional tag mean exp(−μR(t)) and endpoint identity Q_T(T)H(T)=exp(−μR(T)) use the same initial type/stage mixture. This reasoning would not justify a division-only modulation model.

**First qualifying division.** For initial stage j, r=k−j+1 stages remain. Its physical first-division density is the Erlang density at R(b), multiplied by the Jacobian R′(b), by exp(−μR(b)) for no earlier death, and by initial state mass π_zj. `born_density` includes every factor. Integrating after the substitution x=R(b) gives the incomplete-gamma expression in `eligibility_formula`. The uniform-stage law is used only for founders; daughters restart in stage 1. Fixed initial type weights cannot replace the birth-selected maternal weights.

**Sister joint probabilities.** Given maternal type z and physical birth b, the daughter mean is g_z=Σ_vK_zv h_v1(R(b+s)−R(b)). Conditional independence therefore gives the joint g_z². The implementation first averages over birth-selected maternal types and then over the actual qualifying density within each bin. It never substitutes a bin midpoint or uniform birth weights. The covariance decomposition is E_b Var_z(g_z|b)+Var_b E_z(g_z|b). `j=p²+c` is independently checked against the direct g² integral. In no-transmission cases the first term vanishes, while the second can remain.

**Partition and bound controls.** The partition identity uses eligibility masses, not equal bin weights. Its monotonicity check concerns the weighted remaining context variance under nested refinement. It does not assert monotonicity of individual-bin covariance. The no-transmission Lipschitz bound follows from |h′|≤μ and |r(b+s)−r(b)|≤2a|sin(πs/P)|: hence L≤2μa|sin(πs/P)| and Var(p|bin)≤min(1/4,L²w²/4). The bound is correctly withheld for transmitted mixtures. Full-period alias, zero-death, stationary recovery, and homogeneous exponential horizon controls are retained.

**Finite calibration moments.** The four categories are ordered 00,01,10,11, with probabilities 1−2p+j,p−j,p−j,j. At fixed calibration q, the product scores are q²,−q(1−q),−q(1−q),(1−q)². Averaging their conditional variance divided by n, plus variance of their conditional mean across the Binomial(m,p) calibration, is the correct total-variance calculation when one fitted q is shared by all target pairs. Subtracting q(1−q)/(m−1) gives unconditional mean c across both training and test samples. It does not remove fixed-fit squared prediction error or within-bin context covariance. The finite sum leaves raw values unprojected.

**Ordinary covariance benchmark.** For centered binary daughters, E[X²Y²]=v²+c(1−2p)², where v=p(1−p). The standard unbiased sample-covariance variance is therefore

`[v²−c²+c(1−2p)²]/n + [v²+c²]/[n(n−1)]`,

matching the code. As a hand-algebra control, independent fair daughters give variance 1/[16(n−1)]. The corrected shared-fit estimator instead has variance (1+2/m)/(16n)+1/[8m(m−1)]. These symbolic checks use no model-grid probabilities and illustrate the fixed-m calibration variance floor. The code's enumerated small-n fixtures provide a separate finite-count check recorded by the root agent.

## Protocol and failure handling

The loop structure retains all 20 cases, 17 selected-path checks per case, 15 birth bins, 45 bin/lag pair records, and 270 calibration designs per case. The four estimators, six m/n combinations, two solver tolerances, and 64/96-point quadrature match the frozen plan. Calibration sizes repeated for the ordinary covariance benchmark do not create independent biological replications. Primary/strict comparison enforces 1e−10 for calibration fields and 1e−8 elsewhere. The protocol and old core hashes are checked before execution.

Partial primary and strict current-case dictionaries are shared with the exception handler. Completed cases, convergence records, and the current partial case survive ordinary exceptions and interruptions. Nonfinite diagnostic values are labeled rather than converted to probabilities. Both result payloads are checked for valid JSON before the first write; exclusive creation protects existing outputs. An error writing the second output can leave a first output plus a failure diagnostic, which must be treated as an incomplete paired write. This is preservation rather than transactional atomicity.

Two pre-run hardening items were raised and resolved:

1. Identical resolved primary and strict output paths are now rejected before computation. Exclusive creation already prevented overwriting, but the initial implementation discovered this mistake only after a full run.
2. Explicit finite/domain checks now cover H, Q, positive loss, U, total/bin eligibility, and unconditional removed-stratum loss. Together with the p/j category constraints and endpoint/complement checks, these protect the intended probability references. Raw values are retained with the frozen 1e−8 domain slack, without silent clipping. Diagnostic messages now retain rejected values, including nonfinite p/j/category inputs that fail before a row is appended.

These are defensive checks, not changes to model formulas or scientific parameters. Run without Python optimization because the implementation uses assertions for scientific gates. The independent verifier and complete-tree/calibration simulators remain separate required checks. This review cannot clear their outcomes in advance.

## Reporting limits

Exact statistical identities are evaluated with numerical model probabilities. They do not turn floating-point ODE solutions into exact arithmetic. Oracle bin means, fitted bin means, and exact-birth conditioning are different targets. Calibration/test distribution shift, shared random well effects, general regression error, incomplete observation, and biological time calibration remain outside the stipulated simulator. Persistent family environment can imitate transmitted type. The files contain no clinical or first-ever claim, and the prior study's two flagged comparisons and 168 unresolved checks remain untouched.
