# What sampling information separates death from family selection?

**One additional population-level quantity is sufficient under the stated model:** the proportion of all eligible founders whose families survive to the observation endpoint. Together with selected-tag survival, it identifies the constant death rate. Without that quantity or another source of information, selected-tag death observations alone cannot distinguish a birth/death rate pair from the swapped pair, even when the implied population growth signs are opposite.

This is an independent mathematical reviewer note, not an estimate from Oren's workbook or a claim of a new cancer mechanism. The [structured review](sampling-information-review.json) records assumptions, numerical checks and limitations. Novelty is unestablished; the main identity follows directly from conditional probability.

## Define the population and the tag before conditioning

Start one founder at time zero in a homogeneous binary birth–death branching process. Each living cell divides at constant rate \(\lambda\), replacing itself with two daughters, and dies at constant rate \(\mu\). Descendant processes are independent. There are no cell types, density effects or changes in exposure. Time units are arbitrary model units.

A forward tag follows one daughter at each division, chosen without information about future outcomes. Its death ends the tagged path: it cannot jump to a different branch afterward. Define, at a fixed known \(T>0\),

\[
A_T=\{N(T)>0\},\qquad B_T=\{\text{tag alive at }T\},
\]

\[
h(T)=P(A_T),\qquad Q(T)=P(B_T\mid A_T).
\]

Families are sampled equally by founder, or known inclusion weights recover that target population. The tag, selection probability and endpoint must all refer to this same population. Selecting a founder because some descendant survives is different from choosing a path guaranteed to reach a terminal survivor.

## The identity and its short proof

A living tag is a living member of its founder's family, so \(B_T\subseteq A_T\). Therefore

\[
Q(T)h(T)=P(B_T\mid A_T)P(A_T)=P(B_T).
\]

Along the forward tag, division changes its tracked daughter but does not change the homogeneous death hazard. Thus

\[
\boxed{Q(T)h(T)=e^{-\mu T}},\qquad
\boxed{\mu=-\frac{\log[Q(T)h(T)]}{T}}.
\]

The set identity does not need knowledge of \(\lambda\). Interpreting its right-hand side as a single exponential does require the constant homogeneous tagged-cell death model. This provides one sufficient additional scalar, not a claim that measuring \(h\) is the only possible way to resolve the ambiguity.

For a complete matched cohort, let \(n_0\) be initially eligible founders, \(n_A\) families surviving to \(T\), and \(n_B\) living forward tags. Then

\[
\widehat Q\widehat h=\frac{n_B}{n_A}\frac{n_A}{n_0}=\frac{n_B}{n_0}.
\]

This cancellation requires correct ascertainment and the same cohort; it does not license multiplying unrelated table fractions. Shared-cohort estimates are dependent. A separate prospective cohort can also estimate \(h\), provided the target population and conditions match; its sampling uncertainty must be propagated.

## Why the missing denominator matters

For \(\lambda\ne\mu\), the prospective family-survival probability is

\[
h(T)=\frac{\lambda-\mu}{\lambda-\mu e^{-(\lambda-\mu)T}}.
\]

The selected tag's death density before the endpoint and survival probability at that endpoint are

\[
f(t\mid A_T)=\frac{\lambda\mu}{\lambda-\mu}
\left(e^{-\mu t}-e^{-\lambda t}\right),\quad 0\le t<T,
\]

\[
Q(T)=\frac{\lambda e^{-\mu T}-\mu e^{-\lambda T}}{\lambda-\mu}.
\]

One independent derivation conditions on tag death at \(t\). Sibling branches arise along its history at rate \(\lambda\); each independently survives to \(T\) with probability \(h(T-s)\). Hence

\[
f(t\mid A_T)=\mu e^{-\mu t}
\frac{1-\exp[-\lambda\int_0^t h(T-s)\,ds]}{h(T)},
\]

which simplifies to the density above. For \(\lambda=\mu=r\), the limits are \(h(T)=1/(1+rT)\), \(f(t\mid A_T)=r^2te^{-rt}\), and \(Q(T)=(1+rT)e^{-rT}\).

For positive rates, the full selected-tag death law equals the sum of independent exponential waiting times with rates \(\lambda\) and \(\mu\), right-censored at \(T\). Both its density and survival atom are unchanged when the rates swap. This is an exact finite-horizon result. It does not rely on a large-time approximation. Zero-rate cases follow by limits.

An illustrative pair at \(T=3\) shows the distinction:

| Division rate \(\lambda\) | Death rate \(\mu\) | Selected-tag survival \(Q\) | Prospective family survival \(h\) | Net population growth \(\lambda-\mu\) |
|---:|---:|---:|---:|---:|
| 0.8 | 0.2 | 0.701510 | 0.782330 | +0.6 |
| 0.2 | 0.8 | 0.701510 | 0.129318 | −0.6 |

The conditional death-time distributions are identical, not merely their endpoint survival probabilities. Yet multiplying the common \(Q\) by each correct \(h\) recovers death rates 0.2 and 0.8. These are synthetic parameters, with no mapping to patients or measured cell lines.

**The ambiguity applies to selected-tag death observations alone.** Division histories, clone sizes, complete family trees, known rates or other selection information can add information. The result does not show that all lineage data are uninformative. Nor do \(Q\) and \(h\) automatically identify every parameter of a more general model.

## Conditions that cannot be skipped

- A required terminal-survivor path or replacement of a dead tag violates the forward-tag model. Such paths cannot be substituted for a prospectively defined tag.
- The denominator for \(h\) must include initially eligible founders whose families later become extinct. Endpoint-cell counts, a selected-row fraction or unknown clone-size weights cannot supply it.
- Observation, death and censoring labels must be distinguished. Tracking loss cannot be silently counted as death or survival; administrative follow-up must correspond to the same known \(T\).
- With a common time-varying death rate, the product gives \(\exp[-\int_0^T\mu(s)ds]\), identifying cumulative hazard rather than the complete rate trajectory. With heterogeneous founder-specific constant rates, it gives a mixture of survival probabilities; the transformed value is an effective rate, not a shared individual rate.
- The population formula assumes \(h>0\). A finite-sample estimate of zero tag survival requires appropriate uncertainty or bounds; it does not establish an infinite biological death rate.

## Independent numerical check and present data boundary

An independent calculation solved the branching survival equation \(h'=(\lambda-\mu)h-\lambda h^2\), \(h(0)=1\), and evaluated the sibling-survival integral. It checked the closed forms, normalization, rate swapping, product identity and recovered death rate in **108 settings**, including critical, near-critical and zero-rate cases. Every absolute discrepancy was below \(5.43\times10^{-10}\), against a fixed \(10^{-8}\) acceptance tolerance. This checks the mathematics; it is not empirical validation or a review of the root simulation's implementation. That simulation was not modified. The 108 checks are documented reviewer calculations; a standalone public checker script is not supplied.

The [Oren source dictionary](source-dictionary.md) still lacks the verified founder denominator, selected-path rule, observation mask, row joins and column times. The [paper's methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC9209846/) describe both prospective forward tracking and endpoint-based founder ascertainment, without resolving the full workbook sampling dictionary. Neither 80/1,135 nor 77/1,135 is currently a certified \(h\) or \(Q\). The immediate empirical requirement is an eligible-founder roster linked to family endpoint survival and a documented forward tag, with exact timing and censoring. Until that is available, this identity is a design requirement and sensitivity tool, not a biological rate estimate.
