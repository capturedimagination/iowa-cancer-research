# Cell-cycle timing, family selection, and paired subtrees

These equations describe the hypothetical models in the [frozen protocol](protocol.json), SHA256 `e7fe08e71d614f27f7d312a6afa7cf64d8022cba2af908cc92c7965d7d6caeb5`. The derivations and small-time prediction were recorded before new numerical outcomes. This document is a mathematical model specification, not a claim of theorem priority, a cancer mechanism, or empirical validation.

The prior [calendar-rate proof](../horizon-invariance/proof.md) establishes that horizon invariance survives shared deterministic calendar rates. The present calculation asks how age dependence, transmitted types, and founder initialization change its specificity. These are established model ingredients; the study does not claim to introduce age-structured branching or sister correlation.

## States, clocks, and observation

A living cell has type `z` and stage `j=1,...,k`. It advances a stage at rate `alpha_z=k/m_z`; its last stage divides into two newborn stage-1 daughters at that rate. Each cell independently dies at rate `mu`, competing with division and stage advancement. Type is fixed during a cell's lifetime. Conditional on maternal type, daughter types are independently drawn from

`K(z,v)=rho*1[z=v]+(1-rho)/2`.

For two types, diagonal entries are `(1+rho)/2` and off-diagonal entries are `(1-rho)/2`. The homogeneous model has one type and K=1. Daughter clocks and subtrees are independent conditional on their types. Jointly drawing one type for both daughters would be a different model.

Initial type weights are `p_z`; initial stage probabilities within type are `a_zj`. Write `pi_zj=p_z*a_zj`. Newborn founders have `a_z1=1`; uniform-stage founders have `a_zj=1/k`. The latter gives a mixture of residual Erlang shapes `k-j+1`, not a newborn timer or a claimed stable population age distribution. Every daughter starts at stage 1 under both founder initializations.

At every division, a chronological tag chooses a daughter fairly and independently of future fate. Its death is absorbing. Equivalently, `U(t)` is the sum of `2^(-generation)` over living descendants. Every prospective founder is retained in the initial cohort, including extinct and never-dividing founders. With `F_T=1[N(T)>0]`,

`Q_T(t)=E[F_T*U(t)]/P(F_T)`, for `0<=t<=T`.

The comparison is `Q_T2(t)-Q_T1(t)` at the same t. This is not an endpoint-survivor ancestry. Constant common death implies `E[U(t)]=exp(-mu*t)` regardless of division timing and transmitted types.

## Family survival and a positive marked system

Let `h_zj(x)` be the probability that a cell initially in state `(z,j)` has living descendants after duration x. Let `H_z(x)=sum_v K(z,v)*h_v1(x)`. Independent daughters give

```text
h_zj(0)=1
h_zj' = -(mu+alpha_z)*h_zj + alpha_z*h_z,j+1                 (j<k)
h_zk' = -(mu+alpha_z)*h_zk + alpha_z*(2*H_z-H_z^2).
```

Founder-family survival is `h_pi(T)=sum_zj pi_zj*h_zj(T)`. Initial types and stages must be mixed before taking a ratio; their selected weights depend on T.

For fixed `(t,T)`, put `r=T-t`. Define `J_zj(x;r)` as the probability of tag survival through duration `x-r` together with family survival through duration x. Integrate from x=r to T, using the previously solved h. Set `Jbar_z=sum_v K(z,v)*J_v1` and `y=exp[-mu*(x-r)]`:

```text
J_zj(r;r)=h_zj(r)
J_zj' = -(mu+alpha_z)*J_zj + alpha_z*J_z,j+1                 (j<k)
J_zk' = -(mu+alpha_z)*J_zk
         + alpha_z*((1-H_z)*Jbar_z + y*H_z).
Q_T(t) = [sum_zj pi_zj*J_zj(T;T-t)]/h_pi(T).
```

At division, either the discarded sister fails and the tagged subtree supplies the marked joint event, or that sister survives and only tag survival through the required duration is needed. These are disjoint cases. The formula does not assume independence between tag survival and the tagged subtree's eventual survival. Common constant mu makes y independent of tag type and stage.

The system gives `Q_T(0)=1` and `Q_T(T)*h_pi(T)=exp(-mu*T)`. Zero division and zero death give Q=1 when defined. In the proposed factorial grid, the nonlinear system has at most eight states; its size does not grow with tree size.

## Independent extinction and forward-spine calculation

Extinction `e=1-h` can instead be solved directly from e(0)=0:

```text
e_zj' = mu*(1-e_zj) + alpha_z*(e_z,j+1-e_zj)                (j<k)
e_zk' = mu*(1-e_zk) + alpha_z*((sum_v K(z,v)*e_v1)^2-e_zk).
```

For a fixed T, a row vector `p_spine(u)` starts at pi and follows the tagged cell, weighted by extinction at T of every discarded sister. Its matrix has loss `-(alpha_z+mu)` on each diagonal, internal-stage transition alpha_z, and last-stage reset entry

`alpha_z*K(z,v)*sum_w K(z,w)*e_w1(T-u)`

to state `(v,1)`. Add self-reset contributions to the diagonal when k=1; do not replace its loss. There is no factor two for this one fair tag. Then

```text
R(t,T)=exp(-mu*t)-dot(p_spine(t),e(T-t))
Q_T(t)=R(t,T)/[1-dot(pi,e(T))].
```

This provides a reference independent of the positive-J formulation. It uses subtraction, so numerical checks retain numerator and denominator errors and employ stricter integration tolerances. It is not an expected-population equation. [The reference implementation](../../../../scripts/verify_age_lineage_models.py) does not import the production solver.

## Qualification and sister-subtree covariance

A founder contributes at most one sister pair: its first future division must occur by B=2 before its own death. Both daughters are then followed at the same lag s after birth. Qualification depends on the past at division, never subsequent survival or future recording completeness. B plus the largest lag is the fixed administrative horizon 4.

Given initial type z and stage j, the remaining potential timer has Erlang shape `r_j=k-j+1` and rate alpha_z. The probability of qualifying is

```text
L_z(B)=sum_j a_zj*integral_0^B exp(-mu*b)*f_Erlang(r_j,alpha_z)(b) db
      =sum_j a_zj*(alpha_z/(alpha_z+mu))^r_j*P(r_j,(alpha_z+mu)*B),
```

where P is the regularized lower incomplete gamma function. This is a competing-risk probability, not a timer conditioned on eventual division. Qualification probability is `p_qual=sum_z p_z*L_z`; maternal weights among qualifying pairs are `w_z=p_z*L_z/p_qual`. Initial one-half type weights cannot be substituted for w.

Let `A_l(s)` indicate survival of daughter l's subtree to lag s. With `g_z(s)=sum_v K(z,v)*h_v1(s)`, conditional daughter independence gives

```text
E[A1]=E[A2]=sum_z w_z*g_z
E[A1*A2]=sum_z w_z*g_z^2
C(s)=sum_z w_z*g_z^2-(sum_z w_z*g_z)^2.
```

For two types this simplifies to

`C(s)=rho^2*w_0*w_1*(h_01(s)-h_11(s))^2`.

Homogeneous renewal and rho=0 have zero covariance. Equal newborn subtree survival also gives zero at any rho. The explicit rho-squared factor does not prove monotonicity in rho because h itself depends on rho. A permanent unobserved family environment with the same rate multipliers is observationally equivalent to perfectly inherited type; covariance is not a universal inheritance diagnostic.

No-division controls have no qualifying pairs: their covariance is undefined, not zero. Zero death gives covariance zero among existing pairs. Calendar controls require a separate distinction below.

## Exact control routes

For deterministic division age d and newborn founders,

```text
h(T)=exp(-mu*T)                                      (T<d)
h(T)=exp(-mu*d)*(2*h(T-d)-h(T-d)^2)                  (T>=d).
```

A positive marked recursion has `G(t,T)=h(T)` for `t<=min(d,T)` and

`G(t,T)=exp(-mu*d)*[(1-h(T-d))*G(t-d,T-d)+exp(-mu*(t-d))*h(T-d)]`

for t>d; Q=G/h(T). This is exact, not a large-k approximation.

An independent reference uses the discarded-sister product. At t, let `n=floor(t/d)` and age `a=t-n*d`, with the post-division convention at exact boundaries. The current cell's family survival over x is exp(-mu*x) before its residual division time `d-a`, and afterward is `exp[-mu*(d-a)]*(2*h(x-d+a)-h(x-d+a)^2)`. Call this `h_age(a,x)`. Then

`Q_T(t)=exp(-mu*t)*[1-(1-h_age(a,T-t))*product_{j=1}^n(1-h(T-j*d))]/h(T)`.

For `d<t<=T<2d`, this becomes `(1+x-y)/(2-y)`, where `x=exp[-mu*(t-d)]` and `y=exp[-mu*(T-d)]`. It depends on T despite independent renewal clocks. Deterministic newborn Q is exactly one before its first division age.

For the shared calendar schedule lambda and constant mu, an independent positive quadrature is

`h(b,T)=1/[1+mu*integral_b^T exp(-integral_b^u(lambda(v)-mu)dv)du]`.

The forward-spine expression is

`Q_T(t)=exp(-mu*t)*[1-(1-h(t,T))*exp(-integral_0^t lambda(u)*h(u,T)du)]/h(0,T)`.

It agrees with the horizon-independent expression in the earlier proof. For `lambda(u)=1+0.5*sin(pi*u)`, its integrated rate is `L(u)=u+(0.5/pi)*(1-cos(pi*u))`.

Qualifying division times in this control have density proportional to `lambda(b)*exp(-L(b)-mu*b)` on `[0,B]`. Conditional on b, sisters are independent with survival `g(b,s)=h(b,b+s)`. Raw covariance is `Var[g(b,s)|eligible]` and can be positive from pooling birth times. The pooled, birth-time-adjusted residual product has expectation

`E[(A1-g(b,s))*(A2-g(b,s))|eligible]=0`.

This uses known model probabilities; finite empirical birth-time bins are not exact conditioning.

## Small-time prediction and its sampling dependence

Fix T>0 and let t approach zero with t<T. Define `g_z(T)=sum_v K(z,v)*h_v1(T)` and newborn founder inclusion `H_0(T)=sum_z p_z*h_z1(T)`. For positive finite rates and common integer k,

```text
1-Q_T(t) = [mu*sum_z p_z*alpha_z^k*g_z(T)]
           /[(k+1)!*H_0(T)] * t^(k+1) + O(t^(k+2)).
```

The first division must occur before tag death: tag death without any division leaves no family. Its density is `alpha_z^k*s^(k-1)/(k-1)!+O(s^k)`, including the competing founder death factor. After division, tagged-daughter death by t contributes `mu*(t-s)+O((t-s)^2)`; sister survival contributes `g_z(T)+O(s)`. Their leading integral is `mu*alpha_z^k*g_z(T)*t^(k+1)/(k+1)!`. Paths with another tagged division before death contribute only `O(t^(2k+1))`, which is covered by `O(t^(k+2))`. Divide by fixed positive H_0(T).

In homogeneous newborn renewal, g equals H_0 and the coefficient is `mu*alpha^k/(k+1)!`, independent of T. At rho=0 it similarly becomes `mu*mean(alpha_z^k)/(k+1)!` **only when initial types follow the same distribution as daughter redraws**, as in this grid. For arbitrary initial type weights the cancellation need not hold. At rho=1, the coefficient weights alpha_z^k by horizon-selected founder types and can vary with T. Leading-coefficient agreement does not imply full-curve invariance.

For uniform-stage founders with `H_initial(T)=sum_zj pi_zj*h_zj(T)`, the last initial stage dominates:

`1-Q_T(t)=[mu*sum_z p_z*(alpha_z/k)*g_z(T)]/[2*H_initial(T)]*t^2+O(t^3)`.

This coefficient can depend on T even in homogeneous independent renewal. More generally the smallest remaining-stage count with positive founder weight determines the leading exponent, that count plus one. An arbitrarily small proportion of near-division founders changes the strict exponent to two. Unknown age, measurement delays, early-event scarcity and time resolution therefore limit any interpretation as a multistep killing signal.

These are fixed-T asymptotics. They are not a uniform claim as T shrinks with t or rates diverge. At zero death the decline vanishes identically. Deterministic newborn division instead has a flat interval at the origin. No finite observed slope uniquely identifies biochemical death stages.

## Stable defect calculation and independent Volterra reference

Let D=h-J be the probability of tag death by x-r with family survival at x. Its initial value at x=r is zero. Internal-stage equations are the same linear equations as J; the last-stage source becomes `(1-exp[-mu*(x-r)])*H_z`:

`D_zk'=-(mu+alpha_z)*D_zk+alpha_z*((1-H_z)*Dbar_z+(1-exp[-mu*(x-r)])*H_z)`.

There is no separate death forcing. J+D=h follows directly. To avoid small probabilities and cancellation, set x=T-t+t*v and, for one-based j, `D_zj=t^(k-j+2)*X_zj(v)`. Then

```text
X_zj(0)=0
X_zj' = -(alpha_z+mu)*t*X_zj+alpha_z*X_z,j+1                 (j<k)
X_zk' = -(alpha_z+mu)*t*X_zk
         +alpha_z*[t^k*(1-H_z)*Xbar_z,newborn
                    +{-expm1(-mu*t*v)/t}*H_z].
```

Here H is evaluated at T-t+t*v. At t=0 the braced quotient has limit mu*v, and the triangular solution is

`X_zj(v;0)=mu*alpha_z^(k-j+1)*g_z(T)*v^(k-j+2)/(k-j+2)!`.

For an independent reference, first-division decomposition gives, with `r_j=k-j+1`,

```text
X_zj(u)=alpha_z^r_j/(r_j-1)!
 * integral_0^u (u-w)^(r_j-1)*exp[-(alpha_z+mu)*t*(u-w)]
 * [t^k*(1-g_z(T-t+t*w))*Xbar_z,newborn(w)
    +{-expm1(-mu*t*w)/t}*g_z(T-t+t*w)]dw.
```

Only newborn components are coupled. The feedback operator has sup-norm at most `(alpha_max*t)^k/k!`, so it is a contraction on the frozen epsilon grid. The reference uses Chebyshev-Lobatto collocation at orders 24 and40 with mapped Gauss-Legendre quadrature at48 and80, rather than the production differential equation. Order agreement is a numerical check, not a rigorous quadrature error certificate. Zero-death cases check D=0 directly; their positive-leading-term ratio is undefined.

## A conservative finite-epsilon envelope

Let R be exact D divided by its positive leading term; the same R applies to `1-Q` because the common founder denominator cancels. Put

`beta=max_z[(K*diag(alpha^k)*g(T))_z/g_z(T)]`, `b=beta^(1/k)`.

For newborn and uniform-stage founders,

`exp[-(mu+alpha_max)*t] <= R <= exp[(mu+b)*t]`.

The bound can be established without assuming monotone convergence:

1. Family extinction occurs only when its sole remaining cell dies. Thus `h_a'=-mu*P_a(N=1)`, so `-mu*h_a<=h_a'<=0`; this gives `g_z(T)<=g_z(T-u)<=exp(mu*t)*g_z(T)` for u<=t.
2. Couple tag death to an independent exponential clock. Given that death, family survival is a union of discarded-sister survival events. The first sister is a lower bound; the sum over all sisters is an upper bound. This upper bound does not require independence among the union events.
3. The first newborn division density has its leading polynomial times exp(-alpha_z*s). For uniform stages, summing all residual-stage densities gives exactly `(alpha_z/k)*P(Erlang(k,alpha_z)>s)`, between `(alpha_z/k)*exp(-alpha_z*s)` and alpha_z/k. This accounts for the entire initial residual-stage mixture.
4. Write M=K*diag(alpha^k). Since M*g<=beta*g componentwise, each additional tagged generation contributes at most beta to the polynomial density coefficient. Convolution and the death-time integral give upper ratio series

   `exp(mu*t)*sum_{q>=0} beta^q*t^(q*k)*(k+1)!/((q+1)*k+1)!`

   for newborns, and `exp(mu*t)*sum_{q>=0} beta^q*t^(q*k)*2/(q*k+2)!` for uniform stages. Factorial inequalities bound either series by exp[(mu+b)*t]. The first-sister lower bound retains exp[-(mu+alpha_max)*t].

For homogeneous models and rho in{0,1}, beta<=alpha_max^k. At rho0.5, the two g entries differ by at most a factor3, so beta<=3*alpha_max^k. The grid also has mu/alpha_max<=2. With t=epsilon/alpha_max, the deliberately conservative frozen envelope is therefore

**`exp(-3*epsilon) <= R <= exp(6*epsilon)`**.

The sixth rather than fifth unit in the upper exponent is conservative; it also permits a looser initial-stage bound. At epsilon1e-4 the exact relative error is below0.001, so the frozen1% smallest-epsilon diagnostic is loose but justified. Numerical verification separately permits the specified1e-7 envelope slack. Nothing here requires error to decrease monotonically across the three epsilon values.

All parameter values and times are dimensionless. Numerical agreement and synthetic discrimination do not resolve empirical founder eligibility, source annotation problems, inheritance versus shared environment, or any clinical treatment question.
