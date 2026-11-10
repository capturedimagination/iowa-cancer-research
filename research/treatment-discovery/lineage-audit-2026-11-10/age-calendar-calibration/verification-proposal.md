# Independent verification proposal: age, calendar context and calibration

Planning only, 2026-11-10. No new scientific outcomes, random draws or model fits have been generated. This proposal incorporates the parent's 20-model design and the mechanistic agent's time-change derivation. The parent must freeze the exact case list, seeds, estimators, multiplicity and numerical gates before execution. Earlier study outputs and its two unresolved simulation flags remain unchanged.

## Scope and useful question

The primary controls multiply **both** division-stage and death rates by a known positive common calendar factor. This is an ordinary deterministic time change, not a new mechanism or a novel construction. The practical question is whether estimating or coarsening the shared context can manufacture a positive sister residual even when the daughters' futures are independent at fixed context. A simple unbiased sample covariance must remain a benchmark; the calibration correction is not proposed as a superior new covariance estimator.

Use the parent's six positive-death bases at mu=1: homogeneous k=1 newborn; homogeneous k=4 newborn or uniform initial stage; two-type k=4 newborn with rho=0,.5,1 and the previous means .5,1.5. Combine each with constant clock, amplitude .75/period2, and amplitude .75/period4, then add the proposed homogeneous-k4 and rho1 two-type zero-death/period4 controls: 20 records. Retain physical T=2,3,4, evaluation t=.5,1,1.5,2, first-division cutoff2 and sister lags .5,1,2. All details remain provisional until the parent's freeze.

## Independent complete-tree generator

Let `r(c)=1+a*sin(2*pi*c/P)` and `R(c)=c+a*P/(2*pi)*(1-cos(2*pi*c/P))`. Constant clock uses R(c)=c. The operational-time stage clock is ordinary Erlang; a cell born at operational time s gets an independent Gamma remaining-stage division duration and exponential death duration. Both daughters start stage1 and use independent type-transition draws. Draw the entire branching tree through R(4), even if a chronological tag would die. This implementation uses event draws and inverse integrated hazards, not the primary moment solver.

Use 10,000 prospective roots per model, fixed batches250 and a new case-indexed PCG64 stream, provisionally SeedSequence([2026111017,case_index]). Freeze the exact draw order, environment and code as before. Preserve both daughter subtrees, extinct roots, failed cases and all planned queries. Use the prior explicit 50M generated-cells/case and5M-frontier guards, immutable per-batch checkpoints, and no replacement of large trees or seeds.

Record chronological weights `U_i(t)=sum_alive 2^(-generation)` at operational queries R(t), and family indicators at R(T). Eligibility is first division at s<=R(2). Invert R to get its physical birth time b; the sister query is **R(b+lag)**, not s+lag. Inversion to absolute physical-time error1e-12 can use monotone bisection, since r>=.25. Include exact endpoint births and preserve the `[birth,event)` convention. Fixed support b<=2 and lag<=2 ensures no incomplete administrative follow-up.

At lag2 with period2, `R(b+2)-R(b)=2`. This removes birth-time variation in the homogeneous/no-transmission newborn subtree law. It is not a general zero-covariance statement for inherited types: eligible maternal-type weights can still vary with birth time. Store mother type as a diagnostic, but residualize against the declared **birth-context marginal** survival probability, not the latent maternal type, unless a separate estimand is explicitly defined.

A model that changes division-stage rates while leaving death fixed in physical time requires a distinct generator: invert R for division only and draw physical exponential death, then compare physical event times. It is a tractable future control, but is outside this 20-model time-change proposal. Do not silently equate the two models or call operational Erlang timing an unchanged physical-age Gamma law.

## Finite-sample tree validation

Retain first-event, inverse-clock, endpoint, zero-death, random-tag, residual-stage and daughter-type fixtures. Compare both first and second moments only when independently supplied and reviewed; the previous asymptotic variance-oracle proposal remains uncomputed until separately implemented.

Use exact binomial probability checks for family inclusion and eligibility. For each Q, conditional on M selected iid founders, their U values lie in[0,1], so a two-sided Hoeffding radius `sqrt(log(2K/alpha)/(2M))` gives a conservative finite-sample interval. M=0 remains undefined. Difference intervals obtained from simultaneous Q intervals are safe outer bounds for paired contrasts; they may be wide. Freeze K over the complete planned set. Known structural constants can be checked directly. Do not use selected M>=100 alone as evidence that a Gaussian SE approximation is adequate, and do not reinterpret the older two flags under the new rule.

For known exact birth probabilities p_i, the residual product `(A1_i-p_i)*(A2_i-p_i)` has null mean0 under conditional daughter independence. Conditional on the recorded birth contexts, it is an independent bounded variable across roots; its range width is at most max(p_i,1-p_i). A finite concentration check can use these known ranges. A separate exact conditional-randomization check is possible by conditioning on A1 and birth contexts and resampling A2_i independently from Bernoulli(p_i). The conservative Monte Carlo rank p-value `(1+number of resampled statistics >= observed)/(B+1)` is finite-sample calibrated for a prespecified statistic under the **known conditional law**, including ties. It is not exact after replacing p_i with a fitted function. This is established CRT methodology, not a new test; leave it optional unless the parent freezes its statistic, resampling count and multiplicity. [Candès et al.](https://doi.org/10.1111/rssb.12265), [Berrett et al.](https://arxiv.org/abs/1807.05405).

## Shared calibration error and coarse context

For fixed context B, write `p=p(B)` and let the training data be independent of the target sister pairs. Under conditional independence,

`E[(A1-phat(B))*(A2-phat(B)) | B,training]=(p(B)-phat(B))²`.

Thus cross-fitting alone does not remove shared prediction error. With two different fits the term is the product of their errors, not automatically zero. The product-of-errors phenomenon is explicit in the established GCM analysis; its asymptotic validity requires nuisance-error and moment conditions. [Shah & Peters, Eq.5 and Theorem6](https://arxiv.org/html/1804.07203).

For independent exact-context calibration `X~Binomial(m,p)`, phat=X/m, the naive residual's expectation is `c+p(1-p)/m`, where c is the true sister covariance. Subtracting `phat*(1-phat)/(m-1)` removes that calibration bias for m>=2. This is the elementary unbiased factorial-moment identity: the adjusted squared term is `X*(X-1)/(m*(m-1))`. It is not a general correction for a biased/nonparametric probability estimator.

Within a birth bin, p denotes the bin marginal and s=E[A1*A2|bin]. Corrected residuals recover `c_bin=s-p²`. Even without inheritance, this includes `Var[p(B)|bin]`. Independent calibration variance and context-coarsening variance are separate effects. Neither cross-fitting nor this finite-binomial correction recovers exact-birth conditional covariance from a coarse bin.

## Independent finite-calibration verifier

For each model/lag/bin, take primary integrated probabilities p and s as inputs, explicitly checking `max(0,2p-1)<=s<=p`. Target pairs have four-category probabilities `(1-2p+s, p-s, p-s, s)`. Draw their totals from Multinomial(n, probabilities), independently of X~Binomial(m,p). This exactly simulates a **whole calibration-and-target experiment** without generating n individual arrays. A common calibration draw is shared by every target pair in that experiment. Treating the pairs as independent unconditional calibration replicates would be wrong.

Let Zbar=N11/n and Wbar=(N10+N01+2*N11)/n. Calculate:

- Naive shared-fit residual: `T0=Zbar-f*Wbar+f²`, f=X/m.
- Corrected residual: `T1=T0-f*(1-f)/(m-1)`.
- Ordinary unbiased sample covariance: `S=n/(n-1)*(Zbar-Abar*Bbar)`; it uses no calibration data and estimates the same coarse-bin covariance.

Given f, either residual has conditional variance

`V(f)=[s(1-s)+f²*(2p+2s-4p²)-4*f*s*(1-p)]/n`.

Its conditional mean is `a+b*f+d*f²`, with a=s, b=-2p-kappa, d=1+kappa and kappa=0 or1/(m-1). Primary verification may sum over all m+1 binomial outcomes. The independent verifier should instead use factorial moments:

`E[f]=p`, `E[f²]=[(m)_2*p²+m*p]/m²`,

`E[f³]=[(m)_3*p³+3*(m)_2*p²+m*p]/m³`,

`E[f⁴]=[(m)_4*p⁴+6*(m)_3*p³+7*(m)_2*p²+m*p]/m⁴`.

Then compute `E[T]=a+b*M1+d*M2` and `Var(T)=E[V(f)]+E[(a+b*f+d*f²)²]-E[T]²`. Use high-precision arithmetic for the independent polynomial calculation and explicit p0/p1 controls to avoid cancellation being mislabeled negative variance. This calculation verifies the estimator distribution conditional on the supplied p,s; it is not independent evidence that the biological p,s are correct.

For the unbiased covariance benchmark put v=p(1-p), c=s-p². Its variance is

`Var(S)=[v²-c²+c*(1-2p)²]/n + [v²+c²]/[n*(n-1)]`.

This follows from `E[(A1-p)²*(A2-p)²]=v²+c*(1-2p)²`. At c=0 it reduces to v²/(n-1). Retain this simple benchmark, including duplicate comparisons across calibration m if the grid repeats them; do not treat repeated outputs as independent evidence. External calibration m is an added data cost, so no equal-cost efficiency claim is justified without a separate matched-budget design.

## Calibration simulation budget and rigorous precision

The proposed deterministic grid covers all15 bins from widths2,1,.5,.25 over[0,2], all20 models, three lags, m=5,20,100 and n=100,1000:5,400 settings. For Monte Carlo use only the prospectively specified whole interval[0,2] and first half[0,1]:720 settings, each50,000 independent **whole experiments**, or36M experiments total. Draw in fixed chunks, with separate case/lag/bin/m/n indexed streams (provisionally base seed2026111018). All other bin results remain deterministic. This subset is chosen before outcomes, not to favor agreement. The covariance benchmark uses the same target counts, not a fresh target cohort.

Validate mean and variance with finite bounds based on independently checked analytic variance, not a plug-in SE. If each experiment score Y lies in[a,b], B=b-a, analytic mean eta and variance sigma², and L=log(2K/alpha), a conservative Bernstein radius for the R-experiment mean is

`sqrt(2*sigma²*L/R)+2*B*L/(3R)`.

For the variance check average `(Y-eta)²`; its expectation is sigma², its range is at most B², and its variance is at most B²*sigma². The same bound with those quantities avoids assuming a fourth-moment oracle. Use the true analytic eta, not a fitted sample mean, in this check. Freeze the complete K before outputs. These are classical bounded-sum inequalities, not Gaussian-tail approximations. [Bennett, 1962](https://doi.org/10.1080/01621459.1962.10482149), [Hoeffding, 1963](https://doi.org/10.1080/01621459.1963.10500830).

Safe score ranges are T0 in[-1/4,1], T1 in[-m/(4*(m-1)),1], and S in[-n/(4*(n-1)),n/(4*(n-1))]. Loose finite bounds may leave questions unresolved; report their widths. Keep exact p0/p1 outcomes and m1/n1 undefined cases in fixtures. No sample-size extensions, replacements or threshold changes after results.

## Experimental application and stopping point

The useful deliverable would be a source-linked warning and design calculator for **estimated context adjustment in lineage assays**: record birth time, treatment/medium clock, stage, field/well and missing outcomes; keep training and target founders separate; and show calibration bias, binning bias and their uncertainty separately. A prospective time-lapse experiment with independently randomized treatment timing across wells and separate calibration movies could test this observation rule. Distinct biological experiments, not daughters or repeated lags, are the relevant units for generalization. Sister separation across measured environments could constrain particular shared-environment explanations but does not universally identify inheritance.

NCBS's current Chakrabarti research page explicitly connects time-lapse cancer-cell fate, age-structured models and circadian context, making it a concrete scientific-validation destination for a reviewed packet. Its published lineage work already includes age-dependent alternatives; this proposal does not refute that work. [Official research page](https://www.ncbs.res.in/node/80022), [Iyer et al.](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013446). No contact or submission is planned here. The current HCT116 source-encoding/readiness gates remain in force; no empirical fitting or clinical claim follows from this proposal.
