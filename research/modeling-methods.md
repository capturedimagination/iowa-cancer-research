# Methods reference for Iowa cancer and environmental models

Verified October 22, 2026. **This is methodological guidance, not a fitted Iowa model or a finding that an industry causes a county's cancer rate.** `model-methods-sources.json` records primary methods papers and official implementation guidance, their applications, prerequisites and limits.

## Define the question before selecting a model

These objectives require different validation and interpretation:

| Objective | Suitable output | Interpretation |
| --- | --- | --- |
| Describe burden | Observed counts, age-specific/age-adjusted rates, intervals | What was diagnosed or recorded as a death in a defined population and period |
| Map unusual patterns | Standardized incidence/mortality ratios and uncertainty; optional spatial smoothing | Where recorded disease differs from a reference under defined assumptions |
| Predict future counts | Held-out predictive distributions | Forecast performance for a stated population/time horizon |
| Estimate an exposure effect | Prespecified epidemiologic estimand with an exposure history and confounding strategy | An association, with causal interpretation requiring additional assumptions |

Specify cancer site/histology, incidence versus mortality, primary-tumor rules, sex, age range, population, geography, period and exposure pathway before outcome-based searching. Combining unrelated cancers can dilute a site-specific effect. CDC's current framework defines clusters using the same or etiologically related cancers and warns that boundaries/time choices can create or obscure apparent clusters. [CDC cancer characteristics](https://www.cdc.gov/cancer-environment/php/guidelines/characteristics.html)

## Counts, denominators and age adjustment

Use age-adjusted rates for descriptive comparisons under the same standard population and age groups. They are weighted averages of age-specific rates, not raw event probabilities. **Do not multiply an age-adjusted rate by the county population to reconstruct observed cases**, and do not put an age-adjusted rate into a Poisson count likelihood. [NCI SEER definition and formula](https://seer.cancer.gov/seerstat/tutorials/aarates/definition.html)

For an outcome model, prefer actual nonnegative integer counts and corresponding person-time by county, year, cancer and relevant demographic stratum. The project's county 2019–2023 table currently contains an **Average Annual Count**, alongside age-adjusted rates. A rounded average times five is not guaranteed to recover the exact five-year total. Obtain underlying counts and annual denominators before treating that table as count-model input.

Two defensible starting structures are:

1. **Stratified count model:** `Y[i,g,t] ~ Poisson(PY[i,g,t] * rate[i,g,t])`; include `log(PY)` as a fixed offset and model age/sex/calendar-time effects explicitly.
2. **Expected-count disease map:** `E[i,t] = sum_g(PY[i,g,t] * reference_rate[g,t])`; then `Y[i,t] ~ Poisson(E[i,t] * RR[i,t])` with `log(E)` as an offset. The descriptive standardized ratio is `Y/E`.

Use rates per person-year in that formula, converting published “per 100,000” units. Match the reference cancer definition, strata and period. Do not double-apply age standardization. Document whether the reference is Iowa, the U.S. or another population; an Iowa reference is partly composed of the counties being compared. Treat uncertainty in estimated reference rates/denominators as an additional component when material. [CDC SIR/expected-count guidance](https://www.cdc.gov/cancer-environment/php/guidelines/statistical-considerations.html)

Suppressed, missing and genuine zero counts need different codes. USCS suppresses statistics based on fewer than 16 cases/deaths in the relevant period, with additional suppression possible. Never replace a suppressed cell with zero, infer confidential cells by subtraction, or pretend a suppressed rate has a known value. Any censored-count likelihood needs the actual release rule and permitted use. [CDC suppression rules](https://www.cdc.gov/united-states-cancer-statistics/technical-notes/suppression.html)

## Match exposure timing to disease development

Build time-indexed exposure histories before selecting a lag. Relevant fields include source opening/closing dates, process changes, emission years, medium, transport to people, residence/work histories, and exposure intensity/duration. A 2024 facility inventory is not an etiologic exposure history for cancers diagnosed during 2019–2023. It can support current-source description but cannot by itself reconstruct earlier exposure.

There is **no universal cancer lag**. Choose an agent/tumor-specific rationale and a small prespecified sensitivity set. Distinguish induction/latency, exposure averaging, time since first exposure, time since last exposure and cumulative dose. Migration and diagnosis-address geography can disconnect historical exposure from the county in which a cancer is recorded. CDC explicitly recommends considering cancer-specific latency and residence/mobility in study design. [CDC study-design guidance](https://www.cdc.gov/cancer-environment/php/guidelines/phase-3.html)

When sufficiently long repeated histories exist, exposure windows or distributed-lag models can represent timing and intensity jointly. Flexible lag functions consume information; correlated annual exposures and sparse outcomes can make them weakly identified. Do not search many lags and report only the strongest. Gasparrini's original framework includes a radon/lung-cancer cohort example; it supplies a modeling approach, not a lag to transplant into Iowa. [Original exposure-lag-response method](https://pubmed.ncbi.nlm.nih.gov/24027094/)

## Exposure variables and confounding

Use the strongest available pathway evidence: personal/workplace measurements or reconstructed dose, residential concentration models, monitored media with transport information, then clearly labeled proxies. A facility permit, TRI release mass, county facility count, distance buffer, monitoring-well concentration and finished-tap concentration represent different quantities. Keep their units and meanings intact.

An ecological model relates group-level exposures to group-level outcomes. It cannot show that the people with cancer were the people exposed. County adjustment for smoking, deprivation or age does not automatically repair that problem; ecological bias can persist after aggregate control. [Greenland and Morgenstern original methods paper](https://pubmed.ncbi.nlm.nih.gov/2656561/)

For an environmental association analysis, draw a causal diagram and prespecify confounders based on the exposure/cancer pair. Candidates may include smoking history, alcohol, radon, occupation, socioeconomic conditions, rurality, screening/access, demographic composition and calendar period. Their relevance differs by cancer. Avoid selecting all available variables or adjusting for mediators/colliders mechanically. Record measurement years, uncertainty and geographic mismatch. With 99 Iowa counties, hundreds of correlated chemicals/industry variables and lag choices cannot be supported simply by adding regression terms. Regularization reduces overfitting; it does not create missing exposure information.

Occupational studies additionally face healthy-hire and healthy-worker-survivor selection. A general-population SMR below one can coexist with a harmful workplace exposure. Internal comparisons help with some selection but do not automatically solve time-varying work/health feedback. Employment history, work status, exposure and health information over time are prerequisites for appropriate causal methods. Simple lagging or adjusting for current employment is not a general correction. [Naimi et al., causal diagrams and simulation](https://pmc.ncbi.nlm.nih.gov/articles/PMC3858107/)

## Candidate count and spatial models

Start with a parsimonious baseline and make added structure earn its place through diagnostics and relevant validation.

| Candidate | Use | Required checks and limitations |
| --- | --- | --- |
| Poisson with offset | Baseline count model conditional on population/expected count and covariates | Conditional variance equals mean; examine residual dispersion, zeros and influential counties |
| Negative binomial | Residual extra-Poisson variation remains | NB2 variance is `mu + mu^2/phi`; it does not directly model spatial dependence or confounding |
| Poisson with unstructured county effects | Persistent county heterogeneity | Partial pooling changes uncertainty/rankings; variance needs regularization |
| BYM2 | Structured neighbor dependence plus unstructured county heterogeneity | Correct county graph, scaling, constraints and priors; not proof that an exposure effect is causal |
| Space-time extension | Repeated periods with sufficient data | Separate temporal effects from exposure trends; avoid excessive interactions with short series |

Stan documents Poisson/NB parameterizations and log-link functions; confirm the exact parameterization before implementing a model. A Poisson-lognormal random effect can itself generate extra-Poisson variation. Do not automatically stack NB dispersion, several random effects and interactions on a small dataset. Numerous zero counts alone do not justify a zero-inflated model. [Official Stan count distributions](https://mc-stan.org/docs/functions-reference/unbounded_discrete_distributions.html)

BYM2 expresses a county effect as `sigma * (sqrt(1-rho)*v + sqrt(rho)*u_scaled)`, combining an independent effect and a scaled ICAR effect. Scaling makes variance/prior interpretation more consistent across graphs. Report both overall variability and the mixing parameter rather than equating the latter with the fraction of cancers “caused by geography.” [Original BYM2 paper](https://arxiv.org/abs/1601.01180)

Choose the neighbor definition before viewing exposure associations. Validate FIPS-to-node order, symmetry, duplicate edges, connected components and singleton handling. Use proper constraints and component-aware scaling; an unconstrained ICAR component is improper. Spatial smoothing can stabilize noisy areas while concealing sharp boundaries, and a smooth exposure may compete with the spatial effect. Compare exposure estimates under plausible spatial/nonspatial choices and priors. [Stan ICAR/BYM2 case study](https://mc-stan.org/learn-stan/case-studies/icar_stan.html), [official INLA BYM2 implementation note](https://inla.r-inla-download.org/r-inla.org/doc/latent/bym2.pdf)

## Multiple comparisons and honest validation

Define the family of searches: counties, cancer types, agents, buffers, lags and subgroups all count as analytical choices. Prespecify a few confirmatory tests and label broad screening exploratory. Report effect sizes and uncertainty even when a threshold is not crossed. FDR control can be suitable for screening, but the procedure must match the dependence structure; the original Benjamini–Hochberg proof assumes independent tests. Adjusted significance does not remove confounding or turn a discovered association into causation. [Original FDR paper](https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x)

For prediction, choose holdouts that reflect intended use. Forecasting needs forward-in-time validation. Predicting a new region needs spatially separated blocks; random county-year splits can leak neighboring information and county identity. If predicting a later period in the same counties, state that narrower target explicitly. Fit preprocessing, imputation, feature/lag selection and tuning inside training folds. Prevent overlap of five-year outcome windows between training and validation. The general blocked-validation paper demonstrates problems with random splits under dependence; it is not a cancer-specific validation study. [Roberts et al. original simulations and case studies](https://www.wsl.ch/lud/biodiversity_events/papers/Roberts_et_al-2017-Ecography.pdf)

Evaluate predictive calibration and interval coverage, not just fitted correlation or ranking. Compare with a population/age/time baseline and report where prediction extrapolates beyond training exposures. Posterior predictive checks should examine count distributions, overdispersion, rare-cancer zeros, extreme counties and spatial/temporal residual patterns. Good computation and good predictive fit are separate requirements. Neither establishes causal identification. [Stan prior/posterior predictive checks](https://mc-stan.org/docs/stan-users-guide/posterior-predictive-checks.html)

## Propagate uncertainty instead of hiding it

Keep analytical detection limits, nondetect flags, laboratory methods, spatial coverage, sample dates, detection frequency and measurement quality. A nondetect is not zero. A censoring model can use a known detection limit, but requires a defensible distribution and sampling mechanism. [Stan censored-data models](https://mc-stan.org/docs/stan-users-guide/censored-data.html)

Measurement-error models can treat true exposure as latent when calibration/replicate information or credible error assumptions exist. Distinguish uncertainty in measuring a concentration from the larger problem of converting a place-based concentration into a person's historical dose. Label model-derived exposure estimates and propagate their uncertainty/correlation rather than inserting predictions as error-free observations. Where inputs are inadequate, use transparent sensitivity analyses or leave the effect unidentified. [Stan measurement-error guidance](https://mc-stan.org/docs/stan-users-guide/measurement-error.html)

Separate sampling uncertainty from exposure reconstruction, population denominators, confounding, lag selection, missingness and structural model choices. A narrow conditional credible interval covers only the uncertainties included in that model. Model fit cannot fill decades with nonexistent measurements.

## Minimum reusable analysis package

Before fitting, save:

1. A versioned question/estimand and case definition; causal diagram if interpreting exposure effects.
2. Exact count and person-time tables with FIPS, strata, period, suppression and registry-release metadata.
3. An exposure table with source ID, agent, medium, units, coordinates, measurement/model distinction, dates, uncertainty and historical coverage.
4. Reference rates/expected-count calculation, graph file and node-order validation.
5. Prespecified covariates, lag rationale/sensitivities, candidate models and priors.
6. A held-out evaluation plan, multiple-comparison family, diagnostics and sensitivity analyses.
7. Reproducible code/environment, source snapshots, access restrictions and explicit unknowns.

The existing industry evidence tables supply source discovery and exposure hypotheses. They do not yet constitute a longitudinal individual-exposure dataset or a causal model-ready county panel.
