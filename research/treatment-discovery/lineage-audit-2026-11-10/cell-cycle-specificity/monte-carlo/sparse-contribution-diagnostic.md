# Sparse contributions in the horizon contrasts

This **post-results, read-only diagnostic retains both original flags**. It examines all 864 declared contrasts, including the unflagged and structurally constant cases. No trees, seeds, model parameters, primary outcomes, thresholds or comparison classifications changed. The two flagged cases had already been inspected before this wider diagnostic was designed; this is not a preregistered explanation or an independent confirmation of a sampling explanation.

All 2,880 saved synthetic checkpoint hashes were verified. Independent arithmetic using tag-weight **loss**, `D=1-U(t)`, reproduced every contrast within `1.11e-16` and every reported standard error within `6.94e-18`. A separate nonnegative stratum decomposition reproduced the standard errors within `1.39e-17`. These checks establish agreement with the saved records and estimator formulas; they do not prove that a Gaussian approximation is accurate.

## What happens across the full grid

The 864 frozen contrast classifications remain: 670 with no six-SE flag, 102 unresolved for low counts, two flagged, and 90 structural agreements. There are 36 contrasts with identical observed selection sets. Of the remaining contrasts, 62 have a nonempty cohort that survives the earlier horizon but not the later horizon and **zero observed early-loss contributors in that cohort**. Fifty-four are known structural constants. The other eight include both flags and six unflagged contrasts; all eight satisfy the original selected-denominator requirement of at least 100.

| Case | Evaluation t | Horizons | Removed families | Later-selected families with early loss | Reference expected removed weighted loss per 10,000 roots | Frozen result |
|---|---:|---|---:|---:|---:|---|
| C07 | 0.5 | 3 → 4 | 112 | 175 | 1.28020 | Flagged |
| C13 | 0.5 | 3 → 4 | 74 | 63 | 0.44547 | Flagged |
| C19 | 0.5 | 2 → 3 | 180 | 11 | 0.24855 | No flag |
| C19 | 0.5 | 2 → 4 | 256 | 11 | 0.34720 | No flag |
| C19 | 0.5 | 3 → 4 | 76 | 11 | 0.09865 | No flag |
| C55 | 0.5 | 2 → 3 | 253 | 207 | 0.48981 | No flag |
| C55 | 0.5 | 2 → 4 | 387 | 207 | 0.70069 | No flag |
| C55 | 0.5 | 3 → 4 | 134 | 207 | 0.21089 | No flag |

Every row in this table has **zero** observed early-loss contributors among the removed families. The full [diagnostic JSON](sparse-contribution-diagnostic.json) retains all 864 rows, not just this subset. The pattern is therefore not unique to failed checks and is not sufficient to predict a failure.

The reference column is expected **weighted tag-loss mass**, calculated from saved first moments, `N[h1(1-q1)-h2(1-q2)]`, using saved positive-defect fields when available to avoid unnecessary subtraction. It is **not** an expected count of founders with any loss. Individual losses are fractional dyadic weights, and their sizes vary. These first moments do not supply the probability that the binary count of contributors is zero.

## Why a large selected denominator is insufficient

Let `F1` and `F2` indicate family survival at the earlier and later horizons, with `F2 ⊆ F1`. Let R contain families in `F1` but not `F2`. For observed counts n1, n2 and nR, whenever both Q estimates are defined,

`Qhat2-Qhat1 = (nR/n1) * (mean(D | R) - mean(D | F2))`.

If nR is zero, the empirical contrast is zero. Otherwise this identity separates the small cohort whose membership changes from the large later-selected cohort. In both flagged cases, the observed removed-cohort mean loss is zero while the later-selected mean is positive, forcing the empirical contrast negative. The independent model reference is small and positive.

The frozen standard error uses the paired founder influence

`g_i = F1_i(D_i-d1)/hhat1 - F2_i(D_i-d2)/hhat2`,

where dj is the observed conditional mean loss and hhatj=nj/N. Its SE is `sample_sd(g)/sqrt(N)`. The same empirical variance can be written with nonnegative terms. For empirical conditional variances v2 and vR using denominator n2 or nR, put hR=nR/N. Then

`mean(g²) = hR²*v2/(h1²*h2) + hR*vR/h1² + h2*hR*(d2-dR)²/h1³`.

The reported sample-SE correction gives `SE²=mean(g²)/(N-1)`. The diagnostic checks this identity for every defined contrast. Zero observed loss among removed families makes its observed within-stratum variance term zero, even though the stipulated model can assign positive probability to rare losses there.

Thus the frozen selected-denominator rule is a coarse precision screen. It does not guarantee adequate sampling of every influential nested-selection stratum or its rare contributions. Even requiring 100 removed families would not address C07, which has 112 removed families and no observed early-loss contributors. This is a concrete limitation of that screen, **not a replacement threshold**. The two failed checks remain failures, and the full comparison's 168 low-precision quantity checks remain unresolved. The saved data support investigating sparse-event Gaussian approximation error; they do not establish it as the sole explanation or automatically validate the simulator.

## An analytic variance oracle is feasible but was not computed

The following is a derivation for a possible separate follow-up, independently checked symbolically. No additional moment system was solved for this diagnostic.

For a fixed evaluation time t, define population quantities `hj=P(Fj)`, `Mj=E[U(t)Fj]=hj*qj`, and `Sj=E[U(t)² Fj]`. With `v2=S2/h2-q2²` and `v1=S1/h1-q1²`, the paired ratio influence has variance

`V = v1/h1 + v2/h2 - 2*v2/h1`.

The cross term uses nesting: `E[F2(U-q2)(U-q1)]=h2*v2`. A nonnegative equivalent, for hR=h1-h2>0, is

`V = hR²*v2/(h1²*h2) + hR*vR/h1² + h2*hR*(q2-qR)²/h1³`,

where `qR=(M1-M2)/hR` and `vR=(S1-S2)/hR-qR²`. When hR=0, the two selection events agree almost surely and the contrast/influence difference is zero. Positive h1 and h2 are required. The proposed oracle asymptotic MCSE is `sqrt(V/N)`. Existing aggregate first moments alone do not determine S1 and S2.

A finite-state second-moment construction is available for the declared stationary Erlang/type models. Let H_zj(x) be family survival from type z and stage j over duration x, with stage rate αz and common death rate μ. Fix gap r=T-t. Let

- `m(v)=exp(-μv)`;
- `B_zj(v)=E[U(v)²]`, initialized at B(0)=1;
- `J_zj(x;r)=E[U(x-r)F_x]`, the marked first moment;
- `S_zj(x;r)=E[U(x-r)² F_x]`, initialized with `S(r;r)=H(r)`.

For internal stages, any of B, J or S follows the corresponding linear stage transition `Y'=αz(Y_next-Y)-μY`. At the division stage, let K be the frozen daughter-type transition kernel. Bars denote K-weighted newborn values; `g=K H_newborn(x)`, `Bbar=K B_newborn(x-r)`, and m is evaluated at x-r. Then

`B' = -(αz+μ)B + (αz/2)*(Bbar + m²)`

and

`S' = -(αz+μ)S + (αz/2)*[(1-g)Sbar + g*Bbar + 2*m*Jbar - Jbar²]`.

For B alone its running argument is v. The second formula follows from `U=(U1+U2)/2` and `F=F1 OR F2`, using daughter independence conditional on maternal type. The squared-daughter terms give `[(1-g)Sbar+g*Bbar]/2`; the cross term gives `[2*m*Jbar-Jbar²]/2`. Founder-stage/type mixtures are averaged only after their state-specific moments are propagated. At gap zero S=B, supplying an endpoint check; zero death gives B=S=1; no division gives B(v)=exp(-μv) and S(x;r)=exp(-μx). These are symbolic consistency controls, not additional numerical results.

This route could provide model-based second moments without another random tree sample. It still supplies a **delta-method asymptotic variance**, not the exact finite-N distribution of random-denominator ratios or guaranteed Gaussian tail coverage. A separate frozen implementation and validation would be needed, and it must not retroactively erase the current flags.

## Reproduction and provenance

The diagnostic requires only generated synthetic checkpoints and saved model aggregates. It never reads empirical source workbooks or imports either model implementation. From the repository root, after the published simulator has regenerated its checkpoints, an explicit invocation is:

```sh
python scripts/diagnose_age_lineage_contrasts.py \
  --mc tmp/age-reproduction/monte-carlo.json \
  --primary tmp/age-reproduction/results.json \
  --comparison research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/monte-carlo/comparison.json \
  --checkpoint-root . \
  --output tmp/age-reproduction/sparse-contribution-diagnostic.json
```

Checkpoint paths resolve relative to `--checkpoint-root`. All stored checkpoint hashes, root order, code/protocol metadata and comparison estimate/SE joins are verified before labels are reused. Regenerated results must reproduce the supplied comparison's estimates and SEs; otherwise the diagnostic stops instead of attaching old classifications to different outcomes. Existing output files are never overwritten. Six fixed arithmetic fixtures are included.

Adding these explicit path options changed packaging only; all 864 diagnostic rows and summary values matched the first diagnostic exactly. That first JSON is preserved locally at `tmp/age-lineage-2026-11-10/contrast-diagnostics-initial.json`. The current script and input hashes are recorded in the public JSON. The [run-freeze publication note](run-freeze-publication-note.json) separately records the public executable-path redaction; no scientific freeze fields changed.
