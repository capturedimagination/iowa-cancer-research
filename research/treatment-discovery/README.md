# Lung cancer treatment research

Started October 29, 2026. The first research direction is **durable response and treatment resistance in non-small-cell lung cancer**. The immediate work combines a reproducibility benchmark with a separate, testable question about residual malignant cells. No treatment candidate or cancer cure has been discovered or validated by this project.

**November 10 update:** the exact published 17-gene alveolar signature and malignant expression object are verified. An independent public cohort supports a completed descriptive comparison of 26 untreated and 9 residual-disease patients. The pooled residual score is lower, but the small newer-kit subset reverses direction; strong stage/site/batch confounding leaves the biological interpretation unresolved. [Findings and reproducible analysis](updates/2026-11-10/README.md).

## Why start here

Lung cancer has substantial Iowa burden, and usable public clinical records and experimental-model metadata are available. The archived Iowa surveillance table reports an average 1,477 lung/bronchus deaths per year during 2020–2024, compared with 556 colorectal and 484 pancreatic deaths in the same window. These are rounded historical averages across all stages/histologies, not NSCLC-only counts or 2026 deaths. They motivate prioritization, not a claim that one disease is scientifically easiest to cure. [Saved surveillance comparison](../iowa-cancer-types-comparison.csv), [original NCI mortality query](https://statecancerprofiles.cancer.gov/deathrates/index.php?stateFIPS=00&areatype=state&cancer=047&race=00&sex=0&age=001&type=death&year=0&output=1).

The [therapeutic comparison](therapeutic-questions.md) evaluates lung, colorectal and pancreatic research questions using original trials and current regulatory sources. Clinical response, progression-free survival, overall survival and cure remain different outcomes. An environmental county association cannot establish a treatment mechanism, and a cancer-cell-line dependency cannot establish human benefit or normal-tissue safety.

## First analysis completed

A public MSK checkpoint-immunotherapy cohort provides a small reproducible benchmark. Its original tumor mutation-rate score separated recorded durable-benefit and no-benefit groups with an empirical rank **AUC of 0.614**, with a conditional 95% stratified-bootstrap interval of **0.531–0.695**. The analysis includes 227 evaluable patients and explicitly excludes 13 recorded non-evaluable outcomes from 240 original patients.

This is a reproduction of a known retrospective association. An AUC of 0.614 is a ranking statistic, not 61.4% treatment accuracy, cure probability or treatment benefit. The public columns cannot identify the 36 specimens the original paper says were sampled after immunotherapy began. Consequently, this analysis cannot establish a pretreatment predictor. There is no randomized treatment comparator or independent validation cohort.

The [results](results/nsclc-tmb-dcb-2026-10-29/RESULTS.md), [frozen specification](clinical-pilot-analysis-spec.md), [clinical-data audit](clinical-pilot-data.md) and [independent arithmetic review](results/nsclc-tmb-dcb-2026-10-29/independent-review.md) preserve the endpoint, measurement-vintage, inclusion and timing decisions. The protocol was fixed before this benchmark calculation but after inspection of the published study and descriptive statistics. It is not a blinded or prospectively registered analysis. No biomarker threshold or predictive model was fitted.

The original clinical tables are a separate, pinned public ODbL dataset under `data/nsclc_pd1_msk_2018/2026-10-29/`, with license, source URLs, dates and hashes. They are not Iowa patient records. Reproduce the calculation with the bundled NumPy runtime and `scripts/run_nsclc_benchmark.py`; its inclusion log retains all 240 source records and references without changing the originals.

## Mechanism question selected

**In EGFR-mutant lung adenocarcinoma, does the published alveolar-regenerative expression signature remain enriched in residual malignant cells after targeted therapy across independent patient cohorts?**

The [Maynard study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/) supplies an existing biological hypothesis and source/code pointers. Reproducing its signature in the same discovery data would test the pipeline. Independent eligible patients are needed to test whether the state is reproducible beyond that source. EGFR-targeted therapy and checkpoint immunotherapy are separate research tracks; the clinical TMB benchmark does not test this mechanism.

The completed molecular analysis verifies processed expression, the published gene set, malignant-cell annotations and patient/sample joins. Patient and sample counts govern the evidence; thousands of cells cannot substitute for independent patients. The independent cohort is cross-sectional and cannot demonstrate causal drug tolerance. [Fixed plan](updates/2026-11-10/analysis-plan.md), [full results and sensitivities](results/gse292469-alveolar-2026-11-10/RESULTS.md).

The [October preflight](egfr-mechanism-feasibility.md) identified three candidate main-cohort pairs before malignant-cell QC. The [November audit](updates/2026-11-10/malignant-membership-review.md) reduces this to two pairs with any cancer cells and only one with at least 10 per state. The [supplement cross-check](updates/2026-11-10/signature-verification.md) confirms that all 17 author-code genes match the paper's alveolar signature. Original-cohort scoring would still be reproduction, not independent validation.

If the state reproduces, the next question is whether perturbing a specified dependency reduces persistence in relevant treated models. That would require direct perturbation evidence and orthogonal validation, then suitable normal-tissue, exposure and toxicity work before clinical evaluation. This project has not run those experiments.

## Data feasibility and next decisions

| Component | Present evidence | Next requirement |
|---|---|---|
| Clinical association benchmark | Pinned 240-person public cohort; reproducible calculation and independent audit | Timing-resolved, independent pretreatment cohort with harmonized treatment and outcome definitions |
| EGFR residual-state hypothesis | Exact signature, original malignant expression/QC, and independent patient-level descriptive comparison completed | Independent paired or suitably balanced data; resolve assay/ambient-RNA and stage/site/batch differences before biological inference |
| Basal dependency and drug-response resources | Versioned DepMap/PRISM/Sanger metadata, documented GDSC file access, model/alias audit | Permitted response/omics matrices, drug-specific nonmissing overlap and assay QC; treated-state experiments for persistence |
| Clinical translation | Published trial evidence provides context | Mechanistic intervention, normal-tissue and exposure evidence, then appropriate prospective patient studies |

The [preclinical audit](preclinical-data.md) identifies duplicate/related models that could leak across apparent validation sets. Archived baseline screens do not measure residual-state vulnerabilities. The current DepMap release announcement was verified, but its matrix downloads/terms returned human verification. Older open archives are recorded separately; their licensing and processing cannot be assumed to apply to the current release.

Proceed with the mechanism calculation only after its identifiers, timing, signature and patient units are supportable. If a processed matrix or independent cohort is unavailable, retain that gap explicitly rather than substituting unrelated untreated tumors or calling an internal split external validation. The [data catalog](data-access-catalog.json) and source ledgers distinguish downloaded observations, metadata and unresolved access.

## Research files

- [Clinical cohort and endpoint dictionary](clinical-pilot-data.md)
- [Clinical analysis specification](clinical-pilot-analysis-spec.md)
- [Benchmark results](results/nsclc-tmb-dcb-2026-10-29/RESULTS.md)
- [Treatment questions and trial evidence](therapeutic-questions.md)
- [Preclinical resource feasibility](preclinical-data.md) and [model-overlap audit](preclinical-metadata-audit.json)
- [EGFR mechanism data preflight](egfr-mechanism-feasibility.md)
- Source ledgers: [therapeutic](sources.json), [clinical](clinical-pilot-sources.json), [preclinical](preclinical-data-sources.json)

The broader Iowa prevention, occupational and environmental library remains at [knowledge/INDEX.md](../../knowledge/INDEX.md). Its observed population data retain their original dates and scope.
