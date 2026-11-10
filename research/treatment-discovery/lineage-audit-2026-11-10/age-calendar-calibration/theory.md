# Proposal: cell-cycle age, shared calendar context, and calibrated sister measurements

Status: mathematical design recorded before new numerical outcomes; **not a frozen protocol**. The published cell-cycle specificity study remains unchanged. This proposal introduces no empirical biological fit, new mechanism, treatment claim, or theorem-priority claim. It uses the prior study's prospective founder and random-daughter definitions. All times and rates below are dimensionless.

## 1. Bounded scientific question

Can non-exponential independent division timers and a shared deterministic calendar environment jointly generate both a selection-horizon contrast and pooled sister-subtree covariance without transmitted type? If so, what measurement conditioning removes the specified context contribution, and what finite-sample artifacts remain when the needed context probability is estimated?

The common-clock construction below is deliberately tractable: it is an exact deterministic time change of an established age-structured branching model. Its value is a falsification/control and measurement-calibration exercise, not a new biological mechanism. Both clocks changing proportionally is a substantive restriction. The optional separate-clock extension in section 9 is not needed for the proposed primary grid.

Two statistics are different throughout:

- `Q_T(t) = E[U(t) F_T]/P(F_T)`, where `U(t)` is chronological random-daughter survival mass and `F_T` means any founder-family descendant survives at T.
- Covariance of two prospective daughter-subtree survival indicators, observed at equal elapsed lag after the mother's first qualifying division. Qualification uses only events through that division.

No future-success filtering, endpoint-survivor ancestry, or treating an unobserved daughter as dead is allowed. This is a hypothetical complete-observation study, separate from the unresolved HCT116 source cohort.

## 2. Exact common-clock model

A cell of type z has k stages and stage-advancement rate `alpha_z`; the last stage splits into two stage-1 daughters. Daughter types are conditionally independent given maternal type, with

`K(z,v) = rho * 1[z=v] + (1-rho)/2`

for two types. A homogeneous model has K=1. Death rate is the common `mu`. The initial type distribution is `p_z`; initial stage probabilities are `a_zj`, and `pi_zj=p_z*a_zj`. Newborn founders occupy stage 1; uniform-stage founders assign probability 1/k to each stage. Uniform stages are not asserted to represent an equilibrium or stable population age distribution. Every daughter starts at stage 1.

Let `r(c)>0` be a deterministic shared calendar multiplier and `R(c)=integral_0^c r(u) du`. In physical/calendar time c, **both** stage advancement and death rates become `alpha_z*r(c)` and `mu*r(c)`. Operational time is R(c). All clocks remain independent conditional on types and the deterministic schedule.

Write `h^0_zj(x)` for the stationary operational-time family survival solution, with `g_z(x)=sum_v K(z,v) h^0_v1(x)`:

```text
h^0_zj(0)=1
(h^0_zj)'=-(alpha_z+mu)h^0_zj+alpha_z h^0_z,j+1          (j<k)
(h^0_zk)'=-(alpha_z+mu)h^0_zk+alpha_z(2g_z-g_z^2).
```

Then the exact two-time family survival is

`h_zj(b,T)=h^0_zj(R(T)-R(b))`.

With founders at calendar zero, the stationary marked solution gives

```text
H(T) = sum_zj pi_zj h^0_zj(R(T))
Q_T(t) = Q^0_{R(T)}(R(t))
E[U(t)] = exp[-mu R(t)]
Q_T(T) H(T) = exp[-mu R(T)].
```

The same founder mixture is used before taking every ratio. A homogeneous exponential model remains horizon-invariant. Non-exponential age effects carry through the monotone time change. A no-transmission mixed model at rho=0 redraws daughter types independently; the founder distribution proposed below matches the daughter redraw distribution.

The independent verification route can solve extinction and the forward weighted spine at mapped times, rather than import a production marked solver. Complete-tree verification can generate stationary operational-time trees, query them at R(t), and invert R to recover a qualifying physical birth time. This is a model identity, not an empirical time rescaling justified by observed data.

## 3. Proposed 20-model grid and exact controls

Six positive-death base configurations, all mu=1:

1. Homogeneous mean division timer 1, k=1, newborn founders.
2. Homogeneous mean 1, k=4, newborn founders.
3. Homogeneous mean 1, k=4, uniform-stage founders.
4. Two means `[0.5,1.5]`, k=4, newborn founders, rho=0.
5. The same mixture with rho=0.5.
6. The same mixture with rho=1.

Two-type founders have weights `[0.5,0.5]`, and `alpha_z=k/mean_z`. Cross each base configuration with these three shared clock contexts:

```text
r(c)=1
r(c)=1+0.75 sin(2*pi*c/2)
r(c)=1+0.75 sin(2*pi*c/4).
```

Add two mu=0 controls under the period-4 clock: homogeneous k=4 newborn and mixed k=4 newborn rho=1. This gives 20 cases. The homogeneous means and founder weights above must be explicit in the final freeze.

For amplitude A and period P,

`R(c)=c+(A*P/(2*pi)) [1-cos(2*pi*c/P)]`.

Both proposed periodic schedules have R(4)=4; r is at least 0.25, so R is increasing and all required mapped times lie within [0,4]. No simulation is needed to establish this coverage.

Proposed observations: `T in [2,3,4]`, common `t in [0.5,1,1.5,2]`; all three ordered horizon pairs at each t; first-division cutoff B=2; sister lags `[0.5,1,2]`. The declared grid has 240 selected-survival values, 240 contrasts, 60 family-inclusion values and 60 pooled pair targets, before endpoint/zero-time accounting controls. Any extra zero-time or endpoint checks should be explicitly frozen as controls rather than silently enlarging the scientific grid.

Birth partitions of widths `[2,1,0.5,0.25]` cover [0,2], with 1+2+4+8=15 bins per case and lag. Use a fixed boundary convention, such as left-closed/right-open except the final right endpoint; continuous distributions put zero probability on boundaries. This gives 900 bin records. Crossing every bin with m in `[5,20,100]` and n in `[100,1000]` gives 5,400 calibration designs. The sample-covariance benchmark depends on n, not m; its repeated appearances across m are not independent scientific targets.

Required analytic controls:

- Constant r recovers the stationary model exactly.
- Homogeneous k=1 has zero horizon contrasts under every clock.
- Mu=0 gives Q=1 and sister indicators identically one; all covariance and estimator variances are zero, not undefined ratios.
- At rho=0 or in homogeneous cases, exact birth-conditioned sister covariance is zero.
- For the period-2 schedule and physical lag 2, `R(b+2)-R(b)=2` for every b. Thus no-transmission newborn-daughter survival is independent of birth time; raw and every bin covariance are exactly zero. This alias does **not** imply zero covariance for inherited-type models, whose qualifying maternal-type distribution can vary with b.
- The weighted within-partition context contribution must be nonincreasing along the nested refinements; this is not a monotonicity claim for individual bins or total inherited-type covariance across unrelated cases.

Do not select a clock or lag after seeing which gives the largest contrast. Preserve null/alias controls and all 20 cases.

## 4. Correct qualifying births and pair decomposition

Let b be the founder's first future division time. A founder qualifies only if b<=B and division precedes its own death. Given initial state (z,j), its residual potential division time in operational units is Erlang with shape `k-j+1` and rate alpha_z. The unnormalized physical birth density for qualifying maternal type z is

`f_z(b)=p_z*r(b)*exp[-mu*R(b)]*sum_j a_zj*f_Erlang(k-j+1,alpha_z;R(b))`, for 0<b<=B.

Define `f(b)=sum_z f_z(b)` and `P_qual=integral_0^B f(b)db`. The conditional birth density is f/P_qual. At each b with f(b)>0,

`w_z(b)=f_z(b)/f(b)`.

The total eligibility probability has an independent incomplete-gamma reference after substituting u=R(b):

`P_qual=sum_zj pi_zj [alpha_z/(alpha_z+mu)]^(k-j+1) P(k-j+1,(alpha_z+mu)*R(B))`.

Here P is the regularized lower incomplete gamma function. Initial one-half maternal weights cannot replace w(b). At b=0 both numerator and denominator may vanish; integrate the unnormalized densities or use a derived limiting value, rather than form 0/0 or silently omit endpoint contributions.

For physical lag s, set `delta(b,s)=R(b+s)-R(b)` and

```text
g_z(b,s) = sum_v K(z,v) h^0_v1(delta(b,s))
p(b,s) = sum_z w_z(b) g_z(b,s)
j(b,s) = sum_z w_z(b) g_z(b,s)^2
c(b,s) = j(b,s)-p(b,s)^2 = Var_{w(b)}[g_z(b,s)].
```

These are the conditional daughter survival mean, joint survival probability and covariance given birth time b. Sisters are independent given maternal type; they need not be independent given birth alone. At rho=0 g_z is independent of maternal type, so c(b,s)=0. Homogeneous models also have c=0.

Pooling all qualifying births gives the exact law-of-total-covariance decomposition

`C_pool(s)=E_b[c(b,s)]+Var_b[p(b,s)]`.

Using the true birth-specific mean, the residual product has expectation

`E[(A1-p(b,s))(A2-p(b,s)) | qualifying] = E_b[c(b,s)]`.

Thus the combined no-transmission model can have an age-driven horizon contrast and a context-driven raw covariance, while its known-context residual remains zero. Whether each declared noncontrol case has numerically nonzero targets is an outcome to calculate only after freeze; the proposal does not claim a result before running it.

For a birth bin G, use its actual qualifying probability weight `omega_G=integral_G f/P_qual`, not equal bin weights:

```text
p_G = E[p(b,s)|G]
j_G = E[j(b,s)|G]
c_G = j_G-p_G^2 = E[c(b,s)|G]+Var[p(b,s)|G]
C_pool = sum_G omega_G*c_G + Var_omega(p_G).
```

Weighted within-bin covariance is `sum_G omega_G*c_G = E[c(b,s)] + E[Var(p(b,s)|partition)]`. The context remainder decreases under nested partition refinement by the conditional-variance identity. Report both terms; fine bins are not exact conditioning.

## 5. Estimated residuals: correction and its limits

At one exact context or one specified bin, write `p=E[A1]=E[A2]`, `j=P(A1=A2=1)` and `c=j-p^2`. In a bin, p and j are its marginal moments under the same within-bin birth distribution, not moments at its midpoint.

Use m independent calibration singles from separate families with `X~Binomial(m,p)` and `q=X/m`, independent of n independent test pairs. Reuse this same q for all n pairs. Both members of a correlated sister pair cannot be counted as independent calibration singles. Matching the training and test within-bin context distributions is a requirement.

Conditionally on the realized calibration q,

`E[(A1-q)(A2-q)|q]=c+(p-q)^2`.

An independent training set alone therefore leaves squared prediction error. With m>=2, define

`S=(1/n)sum_i (Ai1-q)(Ai2-q)-q*(1-q)/(m-1)`.

Then `E[S]=c`, averaging over **both** calibration and test sampling, because `E[q(1-q)/(m-1)]=p(1-p)/m`. It is not conditionally unbiased for a fixed realized training set. If calibration mean is p_train and test mean p_test, the same correction leaves `(p_test-p_train)^2` in addition to test covariance. Arbitrary fitted regression is not binomial calibration; no blanket correction for arbitrary prediction error follows.

Even with correct bin calibration, E[S]=c_G retains the within-bin context variance. It does not equal biological inheritance or its absence. Unobserved permanent family environment can be observationally equivalent to transmitted type. An empirical rejection can reject a specified conditional-independence/observation model without identifying the cause.

### Exact finite-sample variance

Put `v=p(1-p)` and `A=v^2-c^2+c(1-2p)^2`. For iid exchangeable test pairs independent of calibration,

`Var(S)=[A+2v(v+c)/m]/n + 2v^2/[m(m-1)]`.

The final term is a shared-calibration variance floor. Increasing n at fixed m does not remove it. Under c=0 this becomes

`Var(S)=v^2[(1+2/m)/n+2/(m(m-1))]`.

Proof: with d=p-q, the variance of one pair product conditional on q is

`Var[(A1-q)(A2-q)|q]=v^2-c^2+2(v-c)d^2+c(1-2q)^2`.

Averaging it over the binomial q gives `A+2v(v+c)/m`. The conditional-mean departure from c is `F(q)=(p-q)^2-q(1-q)/(m-1)`. Writing e=q-p gives

`F=[m*e^2-(1-2p)*e-v]/(m-1)`.

The binomial central moments imply `E F=0` and `Var F=2v^2/[m(m-1)]`; the law of total variance gives the result. This is a finite-sample identity, not an asymptotic standard error or a coverage guarantee.

Independent finite-sum reference: for each x=0,...,m, put q=x/m and weight `w_x=BinomialPMF(x;m,p)`. The pair product has three values/probabilities:

```text
(1-q)^2       with probability j
-q(1-q)       with probability 2(p-j)
q^2          with probability 1-2p+j.
```

Compute its mean z_x and variance v_x directly, and `s_x=z_x-q(1-q)/(m-1)`. Then `E S=sum w_x*s_x` and `Var S=sum w_x*(v_x/n+s_x^2)-(E S)^2`. This reference does not require enumerating all n-pair count outcomes. Enforce the Bernoulli joint-probability constraints; never silently clip a materially invalid p or j.

For the proposed four-method comparison, also retain the uncorrected shared-fit statistic `F=(1/n)sum_i(Ai1-q)(Ai2-q)` and the oracle bin-mean statistic `O=(1/n)sum_i(Ai1-p)(Ai2-p)`. Their exact moments are

```text
E O=c
Var(O)=A/n
E F=c+v/m
Var(F)=[A+2v(v+c)/m]/n + 2v^2/m^2 + v*(1-6v)/m^3.
```

The last two terms of Var(F) equal `Var((p-q)^2)` from the binomial fourth central moment. Both F and O lie in the universal range [-1/4,1]. The oracle is an unavailable known-p benchmark, not a data-derived estimator. The uncorrected fit's positive expectation shift is a mathematical calibration artifact even when c=0.

## 6. Essential benchmark: ordinary unbiased sample covariance

Estimating a single bin's covariance does not require external calibration. On exactly the same n test pairs, let

`C=(1/(n-1))sum_i (Ai1-Abar1)(Ai2-Abar2)`, for n>=2.

Then `E C=c`. With `mu22=E[(A1-p)^2(A2-p)^2]=v^2+c(1-2p)^2`, the standard sample-covariance moment expansion gives

`Var(C)=[v^2-c^2+c(1-2p)^2]/n+(v^2+c^2)/[n(n-1)]`.

At c=0, `Var(C)=v^2/(n-1)`. It has no calibration cost or fixed-m variance floor. This benchmark prevents presenting S as a superior general bin-level assay. A comparison at the same n is an estimator comparison, not equal total sampling effort: S additionally uses m calibration singles. No recommended sample allocation follows without a stated cost and sampling model. Continuous-context regression remains a different problem from estimating a single bin covariance.

For a paired Monte Carlo comparison using the same n test pairs and independent q,

```text
Cov(S,C)=A/n
Var(S-C)=2v(v+c)/(m*n)+2v^2/[m(m-1)]+(v^2+c^2)/[n(n-1)].
```

To see the cross-covariance, center each pair at p, put `W_i=(Ai1-p)(Ai2-p)`, and write `C=n/(n-1)*(Wbar-Xbar_centered*Ybar_centered)`. Then `Var(Wbar)=A/n` and `Cov(Wbar,Xbar_centered*Ybar_centered)=A/n^2`; averaging the terms linear in q-p gives zero. These identities can be checked independently by finite count sums. They are optional exact validation targets to freeze, not a reason to enlarge the biology grid.

## 7. A usable bound for unresolved context within a bin

In the homogeneous or rho=0 common-clock model, the reset survival probability depends on b only through delta(b,s): `p(b,s)=h_reset^0(delta(b,s))`. Family survival can decrease only when the sole remaining cell dies, so

`(h_reset^0)'(u)=-mu*P(N(u)=1)`, and `|(h_reset^0)'|<=mu`.

Consequently

```text
partial_b p(b,s) = (h_reset^0)'(delta) [r(b+s)-r(b)]
L_s <= mu * sup_{b in [0,B]} |r(b+s)-r(b)|.
```

For the sine schedule, the global safe bound is `L_s<=2*mu*A*|sin(pi*s/P)|`. For a bin of width w,

`Var[p(b,s)|G] <= min(1/4, L_s^2*w^2/4)`.

If the true qualifying birth variance in the bin is known, the potentially sharper bound is `L_s^2*Var(b|G)`. Do not substitute w^2/12 unless births really are uniform in that bin. The observed qualifying birth density is generally not uniform.

The full-period alias makes L_s=0. In transmitted-type models the maternal weights w_z(b) also vary; the displayed derivative and no-transmission bound do not apply to their marginal p without extra terms. A measured covariance beyond this bound, with valid uncertainty accounting, could reject this specified no-transmission clock model. It cannot distinguish all shared environments, measurement errors, or inherited mechanisms.

## 8. Exact means/variances and nonasymptotic Monte Carlo checks

The p,j moments require controlled ODE/quadrature calculations; calling the statistical formulas exact does not turn floating-point integration into exact arithmetic. Independently compare primary and strict calculations, probability constraints, decompositions, eligibility weights and the analytic controls before generating calibration experiments.

Each calibration experiment can draw X binomial and pair counts multinomial with probabilities `[j,2(p-j),1-2p+j]`. To compute C on the same data, retain the two discordant orientations separately, for example draw four counts with probabilities `[j,p-j,p-j,1-2p+j]`; the aggregate discordant count alone does not determine the two sample means. This detail is essential for the benchmark, though S depends only on the aggregate count.

With m>=2, `S in [-m/(4(m-1)),1]`; its range width is `L_m=1+m/(4(m-1))`. If R independent complete calibration experiments have exact variance sigma^2, then Bernstein gives

`P(|mean(S)-c|>=e) <= 2 exp[-R*e^2/{2*(sigma^2+L_m*e/3)}]`.

This is a check of repeated-experiment simulation means, not a confidence interval for one biological dataset. Freeze R, seeds, batching, familywise error budget and number of checked targets before outcomes. A union bound does not require independence between cases or between m/n comparisons, but each repeated experiment must have the declared within-case independence. Use the same outcomes for S/C comparison, not an independence assumption between the estimators.

For C, bounded binary covariance implies `|C|<=n/[4(n-1)]`, so a safe range width is `n/[2(n-1)]`. For S-C one may conservatively add the two ranges. Known exact variances above then supply analogous Bernstein checks. Zero-variance controls require exact deterministic agreement rather than a division by zero. A variance diagnostic can instead check `W=(S-c)^2`, with `E W=sigma^2`, `0<=W<=L_m^2`, and `Var W<=L_m^2*sigma^2`; this is conservative and needs its own frozen multiplicity allocation.

An optional exact fixed-context test is also possible without estimating p: under the iid no-transmission null, condition on total successes M among m calibration singles and 2n test daughters. If X=x, J=j11 both-success pairs and K=k discordant pairs, then k=M-x-2*j11 and

`P(X=x,J=j11,K=k|M)=choose(m,x)*choose(n,j11)*choose(n-j11,k)*2^k / choose(m+2n,M)`.

Finite sums give an exact conditional tail for a prespecified statistic and tail convention. This conditional law is not valid under unresolved within-bin shared context, where the two test daughters are not independent Bernoulli draws. It is optional future statistical work, not necessary for the proposed mean/variance validation. Do not expand the primary study to add it without an explicit freeze.

## 9. Richer separate-clock extension, explicitly deferred

If only stage progression changes with calendar context while death remains physical-time constant, the exact time-change reduction fails. It remains tractable with a two-time backward system. Let `a_z(b)=alpha_z*r(b)` and death d(b), and write H_zj(b,T) for family survival. With H(T,T)=1 and Hbar_z=sum_v K(z,v)H_v1,

```text
-partial_b H_zj=-(a_z(b)+d(b))*H_zj+a_z(b)*H_z,j+1       (j<k)
-partial_b H_zk=-(a_z(b)+d(b))*H_zk+a_z(b)*(2Hbar_z-Hbar_z^2).
```

For the marked joint J_zj(b;t,T), J(t;t,T)=H(t,T), and `m(b,t)=exp[-integral_b^t d(u)du]`. Its last-stage source is

`-partial_b J_zk=-(a_z+d)J_zk+a_z[(1-Hbar_z)Jbar_z+m(b,t)*Hbar_z]`,

with the same internal-stage linear transitions. The forward extinction/spine formulation supplies an independent route. Qualification density uses `r(b)*exp[-integral_0^b d(u)du]*f_residual(R(b))`. Pair survival uses H_v1(b,b+s), and the conditional-independence and total-covariance identities remain valid.

The simple derivative bound in section 7 cannot be carried over without a separate sensitivity calculation. This richer model may be scientifically useful after the primary common-clock study, but adding it now would obscure the clean exact control and double implementation work. No numerical outcomes or expanded grid are proposed here.

## 10. Freeze requirements and interpretation limits

Before runs, root should freeze the complete grid, founder law, clock applying to both hazards, pair selection/birth weights, bin boundaries, quadrature and solver tolerances, comparison field schema, shared-calibration design, sample-covariance benchmark, seeds, Monte Carlo experiment count, bounded-error gates and failure preservation. Every numerical output must retain code/protocol hashes and its first-run status. Independent code should be pinned before viewing production numerical outputs.

The primary scientific deliverable is a bounded observation-model counterexample and an estimator-calibration caution with a simpler benchmark. Simultaneous nonzero horizon contrast and pooled sister covariance do not identify inheritance in the combined no-transmission model. Known context, finite context bins, learned probabilities and exact conditioning are different measurements. Unknown context, source selection, observation error, family dependence and physical time calibration remain empirical requirements. The prior study's flags remain unchanged; this new design neither retroactively resolves them nor validates a cancer mechanism.

Primary-literature and novelty review is assigned separately. These formulas are independently derived here but are not claimed to be previously unknown. No new numerical outcome was computed in preparing this proposal.
