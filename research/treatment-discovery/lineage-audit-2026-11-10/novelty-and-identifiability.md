# Lineage ascertainment: novelty and identifiability audit

November 10, 2026. **A useful candidate contribution is an exact observation-model counterexample, not a new cancer mechanism.** Under a homogeneous binary birth–death model, selecting a founder because *any descendant* survives and then following an independent random sister path produces a censored death-time distribution identical to a two-stage process. The broad phenomenon of lineage selection bias is established. A targeted follow-up also connects the limiting two-exponential law directly to known spine constructions: **no new-theorem claim is warranted**. This bounded search did not locate this application to Oren's PC9 experiment; priority and the actual selected-path rule remain unverified.

The [frozen simulation plan](sampling-simulation-plan.json) was written before simulation outcomes. Its SHA-256 is `424705a8c9dac1d199285eddda49b19a4050aa82f235102f731046c62a78ee8e`. This memo supplies a literature and mathematical audit; it does not fit an empirical hazard or adjudicate the source paper's biological conclusions.

## What the source establishes

Oren and colleagues followed PC9 cells under osimertinib. Their methods describe prospective tracking for nonpersisters, retaining one representative and choosing a sister randomly at division. For persisters, they traced final-frame cells backward to identify founders, then retained one forward path per founder/timepoint to avoid overrepresenting large progenies. Deaths were manually recorded. Extended Data Figure 1b points back to the forward-tracking schematic, but does not fully specify future-fate dependence of sister selection in this subset. Figure 1b reports 1,135 total and 77 persister lineages. The paper separately corrects barcode-sampling comparisons; that does not specify the live-imaging observation model. [Primary manuscript: methods, Figure 1, Extended Data Figures 1 and 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC9209846/).

This supports endpoint-based **founder ascertainment**. It does not prove that every selected forward path was required to survive, or that an independently chosen path that died would remain in the export. Generic tracking-software capabilities cannot resolve which export options were used. The [source dictionary audit](source-dictionary.md) remains **partial and not ready for hazard estimation**: timing, event codes, loss-to-follow-up, row identities and the reconciliation of counts remain unresolved.

Calling the entire study an “immortal-time bias” would overstate the evidence. A correctly described retrospective estimand is legitimate. The problem arises if it is interpreted as an unconditional per-cell rate or as evidence for latent stages without accounting for ascertainment.

## Prior art and remaining scope

| Primary source | Established overlap | What this audit still needs |
|---|---|---|
| [Nakashima, Sughiyama & Kobayashi, Bioinformatics 2020, DOI 10.1093/bioinformatics/btaa040](https://arxiv.org/html/1806.00215v4) | Explicit chronological/random-daughter, retrospective/terminal-cell and whole-tree sampling; survivorship corrections for latent-state inference. | It precludes claiming that contrasting these observation schemes is new. |
| [Genthon et al., PRX Life 2023, DOI 10.1103/PRXLife.1.013014](https://arxiv.org/html/2305.05406v2) | Separates survival from reproductive selection and retains incomplete/dead lineages. Demonstration uses isoniazid-treated bacteria. | It is not an Oren PC9 reanalysis; a different biological system does not make the statistical principle novel. |
| [Cheek & Johnston, Journal of Mathematical Biology 2023, DOI 10.1007/s00285-023-01907-7](https://link.springer.com/article/10.1007/s00285-023-01907-7) | Homogeneous branching can yield time-varying ancestral reproduction after uniform terminal-cell sampling. | Terminal-cell ancestry is a different random object from a forward tag that can die. Publisher abstract and author-preprint metadata were checked; the later paper below supplies the directly inspected extension. |
| [Igelbrink & Ischebeck, Journal of Mathematical Biology 2024, DOI 10.1007/s00285-024-02105-9](https://link.springer.com/article/10.1007/s00285-024-02105-9) | Explicitly compares surviving-founder/terminal-cell sampling, population size weighting, marker selection and a surviving spine. Rates depend on the rule. | Sections 2, 6 and 7 are close mathematical prior art. They do not justify substituting a guaranteed surviving spine for an independently chosen mortal path. |
| [Iyer et al., PLoS Computational Biology 2025, DOI 10.1371/journal.pcbi.1013446](https://pmc.ncbi.nlm.nih.gov/articles/PMC12469175/) | Cancer DTP models explicitly address competing division/death risks, full-tree HCT116 versus single-sister U2OS tracking, and inherited-state alternatives. | The analyzed datasets are not PC9/Oren. Competing-risk bias and inheritance modeling are already established; neither is this project's discovery. |
| [A lineage tree-based hidden Markov model quantifies cellular heterogeneity and plasticity, Communications Biology 2022, DOI 10.1038/s42003-022-04208-9](https://pmc.ncbi.nlm.nih.gov/articles/PMC9671968/) | Handles finite-window cell-lifetime censoring and illustrates how dropping incomplete observations biases duration inference. | Censoring correction alone does not specify endpoint-conditioned founder inclusion. |

No exact finite-horizon statement was found for the **family-selected, independently random chronological path's hypoexponential death law** in the initial recorded focused searches. The priority addendum below substantially narrows that observation: the corresponding limiting law is an immediate specialization of known spine constructions. The absence of an exact phrase or application in a search does not establish mathematical originality. Nearby population-size, terminal-ancestry and multistep cell-cycle results concern different observables and must still be distinguished.

## Exact counterexample and proof

Let a single founder start at time zero. Every cell independently divides into two at rate λ and dies at rate μ. Daughters have identical independent clocks. A tag follows one uniformly random daughter at each division, independently of future fate, and stops when that chosen branch dies. Let D denote its stopping time, Z(T) the full family's size at the prespecified horizon T, and F the event Z(T)>0.

For positive rates, set r=λ−μ. The ordinary one-founder survival probability over duration u is

\[
h(u)=\begin{cases}
\dfrac{r}{\lambda-\mu e^{-ru}},&\lambda\ne\mu,\\[4pt]
\dfrac{1}{1+\lambda u},&\lambda=\mu,
\end{cases}\qquad q(u)=1-h(u).
\]

Conditional on the tag being alive at t, its earlier divisions form a rate-λ Poisson process. Each discarded sister starts an independent subtree. All those discarded subtrees being extinct by T has probability

\[
A(t)=\exp\left[-\lambda\int_0^t h(T-u)\,du\right].
\]

The active tag's future subtree becomes extinct with probability q(T−t), independently of those sisters. Hence

\[
\Pr(D>t,F)=e^{-\mu t}\{1-q(T-t)A(t)\}.
\]

Dividing by h(T) and simplifying gives, **only for 0≤t≤T**,

\[
S_F(t)=\Pr(D>t\mid F)=
\begin{cases}
\dfrac{\lambda e^{-\mu t}-\mu e^{-\lambda t}}{\lambda-\mu},&\lambda\ne\mu,\\[6pt]
e^{-kt}(1+kt),&\lambda=\mu=k.
\end{cases}
\]

This is exactly the survival function of a sum of independent Exp(λ) and Exp(μ) waiting times, observed with right censoring at T. No intrinsic two-stage death mechanism exists in the generating model. The equality is an observational equivalence, not merely an approximate fitted curve. It is symmetric under exchange of λ and μ: these selected death times alone cannot determine which inferred rate was division and which was mortality.

The selected death hazard is −S′_F(t)/S_F(t). It starts at zero and increases despite constant intrinsic μ; in the critical case it is k²t/(1+kt). The result is independent of the chosen horizon wherever t≤T. It must **not** be extrapolated past T: after that selection horizon, the original random path's subsequent death hazard is again μ, so the full uncensored lifetime need not be hypoexponential.

The corresponding selected-tag event intensities, averaged over its at-risk histories, are

\[
b_F(t)=\lambda\frac{1-q(T-t)^2 A(t)}{1-q(T-t)A(t)},\qquad
d_F(t)=\mu\frac{1-A(t)}{1-q(T-t)A(t)}.
\]

At t=0 these are λ[1+q(T)] and zero. As t approaches T, division tends to λ, while death tends to μ[1−A(T)], generally below μ. These are marginal conditional intensities; the observed tag alone need not form a Markov process with these rates for every individual history.

The proof is a project derivation using established branching and Poisson-process principles. Independent numerical verification compared the Poisson-functional integral with the closed form and a two-transient-state matrix exponential over 500 rate/horizon/time combinations. Maximum absolute discrepancies were 1.01×10⁻¹⁰ and 9.36×10⁻¹⁵, respectively. This algebra check is separate from the frozen Monte Carlo study and supplies no biological evidence.

The [public checker](../../../scripts/check_lineage_sampling_identity.py) reproduces [all 500 case results](identity-check-results.json). It was packaged after the scratch calculation and root simulator results had been inspected; the original cases, quadrature tolerances and methods are unchanged, and every case output was compared with the scratch record. It uses no random draws, so its seed is null. The ledger records Python/NumPy/SciPy versions and script/result hashes. From the repository root, run `python3 scripts/check_lineage_sampling_identity.py` in an environment with NumPy and SciPy. This packaging is not a new prospectively frozen test.

## Controls that prevent the wrong conclusion

| Observation rule | Exact expectation under constant independent rates |
|---|---|
| Prospective random sister path, no terminal selection | Survival e^(−μt); division hazard λ; death hazard μ. Expected exposure by T is (1−e^(−μT))/μ. Expected division count is λ times that exposure. |
| Keep only tags alive at T | No observed deaths before T. Division intensity stays λ. Survivor filtering does **not** universally create changing division rates. |
| Keep founders with any descendant alive at T, retain independent random tag even if it dies | Hypoexponential/Erlang-2 selected death law above; division and death intensities differ from unconditional rates. |
| Keep tags that die by T | Death hazard μ/[1−e^(−μ(T−t))] before T; division intensity stays λ. This differs from family selection. |
| Choose a terminal cell and trace backward | The path necessarily survives; reproduction weighting depends on terminal-cell versus founder sampling. Use the cited ancestry theory, not the mortal-tag formula. |
| Pure death, λ=0 | A selected family has no branching alternative, so its tag must survive to T. |
| Pure birth, μ=0, or no events | Selection is trivial and no death curve is estimable; these are essential implementation controls. |

Counts divided by plotted rows are not hazards. Use event counts divided by actual at-risk time, preserve right censoring and entry, and distinguish clock time from cell age. A completed-interval histogram omits competing events and censored cells; the cancer methods above already explain why it cannot simply identify the intrinsic waiting-time law.

## Frozen test and falsifiable implications

The adopted [plan](sampling-simulation-plan.json) uses T=1 in arbitrary units, all nine pairs from λ,μ∈{0.5,2,5}, plus (0,2), (2,0), (0,0), 200,000 prospective tags per case, seed 2026111004, and ten equal observation bins. Discarded-sister subtree survival is sampled using its exact probability. An independent reviewer uses full trees on a fixed subset, avoiding the shortcut's implementation. All cases, exclusions and discrepancies must be retained. The rates are not fitted to PC9 and the time units are not movie frames, days or treatment schedules.

1. **Simulation falsifier:** selected risk curves and integrated event/exposure quantities must match the exact formulas within Monte Carlo error. A failed check challenges the implementation or assumptions; it is not evidence for a cancer mechanism.
2. **Observation-rule falsifier:** if the exported selected paths were guaranteed to survive, the mortal-tag identity is inapplicable. If dead selected paths were retained after random sister choice, it becomes a relevant null. Founder deduplication removes clone-size weighting but does not itself settle this issue.
3. **Biological test after the dictionary gate:** a newly specified prospective experiment can retain a randomly chosen path from every founder and separately record whole-family endpoint survival. The unselected and selected hazards can then be compared against the same observation model. Full sibling tracking and independent division counts can help break the rate-exchange ambiguity. Survival-curve shape alone cannot prove two death stages.

This counterexample could change **how a reused export is modeled and which measurements are needed next**. It does not explain all persister behavior, test inherited molecular programs, refute perturbation results, infer drug benefit, or establish an Iowa-specific biological finding. If the exact source observation rule cannot be established, publish the theoretical sensitivity and unresolved dictionary rather than a fitted reinterpretation of the experiment.

## Claim and search ledger

- **Established prior art:** sampling, survival, incomplete-tree and competing-risk effects; time-varying ancestral rates from homogeneous branching.
- **Exact model result:** the finite-window family-selected mortal-tag death law above, with explicitly stated assumptions and independent algebra checks.
- **Potential useful contribution:** an explicit finite-horizon derivation and reproducible observation-model benchmark grounded in known branching constructions, plus a dataset-specific identifiability audit. No new theorem is claimed.
- **Unresolved:** exact mathematical priority, Oren export's selected-sister rule, empirical event-time/at-risk dictionary and biological applicability.
- **Unsupported:** a new cancer mechanism, a validated therapeutic target, a treatment or cure, or the claim that the original authors ignored sampling.

The [machine-readable ledger](novelty-and-identifiability.json) records primary URLs, review scope, search phrases, source hashes, mathematical checks and claim status. Searches were bounded web and primary-paper reference checks, not an exhaustive systematic review. Original downloaded text remains in the ignored local source cache; this report is an original synthesis.

## Priority addendum: the standard spine connection

Five additional targeted searches were completed before publication. They support a stronger originality downgrade than the initial exact-phrase search. The arguments below are **our specializations of published constructions**, not claims that the cited papers state the exact finite-T identity in this notation.

**Subcritical limit.** Hautphenne and Horton's 2025 primary preprint explicitly describes a Q-process with a spine that branches at rate mλ, one uniformly chosen child continuing the spine, and ordinary independent non-spine subtrees. For binary splitting, m=2. An independently tagged random daughter leaves the spine with probability 1/2 at each spine division, so its exit time is Exp(λ). After exit, the ordinary tagged path dies after an independent Exp(μ) time. The sum follows immediately. [Section 3, equations 8–9](https://arxiv.org/html/2511.01153v1).

**Critical limit.** The standard size-biased spine construction is longstanding; Lambert reviews it and distinguishes distant-future conditioning from finite-horizon conditioning. Specializing the h(n)=n transform to λ=μ=k gives total upward and downward rates k(n+1) and k(n−1). These equal n−1 ordinary cells plus one immortal spine splitting at rate 2k. A random tag exits that spine at rate k, then dies at rate k, giving Erlang-2. This rate calculation is our elementary specialization, not a quotation of Lambert's continuous-state results. [Lambert 2007, Section 2.1 and introduction](https://www.maths.tcd.ie/EMIS/journals/EJP-ECP/article/download/402/402-1261-1-PB.pdf).

**Supercritical limit.** Jagers and Lagerås establish extinction conditioning and give the single-type offspring tilt q^(offspring−1). For binary birth–death with λ>μ, q=μ/λ; the doomed subtree therefore has division rate λq=μ and death rate μ/q=λ. Conditional on an immortal parent's survival, a split with one immortal and one doomed daughter occurs at rate λ·2q=2μ. An independent uniform tag enters the doomed daughter at rate μ and subsequently dies at rate λ. Again the sum is Exp(μ)+Exp(λ). This is a short conditional-branching calculation using established extinction tilting. [Jagers & Lagerås 2008, Theorem 1, Remark 1 and Example 1](https://staff.math.su.se/andreas/ECP-2008-2048.pdf).

These limiting constructions explain why a two-exponential law is unsurprising here. **An infinite-horizon argument does not prove the exact finite-horizon identity.** The separate Poisson-functional derivation above establishes that statement on 0≤t≤T and preserves its post-T boundary. The defensible contribution is the explicit finite-window benchmark, the observation-rule audit and the practical identifiability warning; mathematical priority is unestablished and the underlying spine principle is known.
