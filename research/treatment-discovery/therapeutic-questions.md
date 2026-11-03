# Therapeutic research questions

Evidence checked **October 29, 2026**. This is a scoped research comparison, not a treatment recommendation or a claim of a cancer cure. The existing Iowa surveillance/environmental corpus does not contain the molecular, treatment, longitudinal biopsy or trial records needed for these questions. The machine-readable [source ledger](sources.json) preserves publication dates, available observation dates and access limits.

## What would count as progress

| Endpoint | What it measures | Boundary |
|---|---|---|
| Overall survival (OS) | Time to death from any cause, from the trial's defined starting point | Longer survival does not establish eradication of cancer. |
| Progression-free survival (PFS) | Time to progression or death under the trial's assessment/censoring rules | Disease can remain present; imaging schedules and subsequent treatment matter. |
| Disease-free / recurrence-free survival (DFS/RFS) | Time without a protocol-defined recurrence/event after treatment intended to clear disease | Definitions differ across trials; some include death or new primary cancers. |
| Objective response / complete response | Prespecified tumor shrinkage / disappearance of detectable disease | Response rate omits duration. Clinical and pathological complete responses use different assessments. |
| Durable control | A response or absence of progression/recurrence maintained for a stated interval | Report time, treatment exposure and patients still at risk; avoid an undefined “durable.” |
| Cure | Permanent elimination of cancer and recurrence | Curative intent, complete response and five-year survival are not interchangeable proof of cure. |

These distinctions follow [NCI's complete-response definition](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/complete-response), [OS](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/overall-survival), [PFS](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/progression-free-survival), [DFS](https://www.cancer.gov/publications/dictionaries/cancer-terms/def/disease-free-survival) and [prognosis explanation](https://www.cancer.gov/about-cancer/diagnosis-staging/prognosis). Apply each trial's protocol definition when extracting results. A hazard ratio is not a cure fraction or an individual's probability of benefit.

## Three tractable directions

### EGFR-mutant non-small-cell lung cancer

**Observed clinical progress.** In completely resected stage IB–IIIA EGFR-mutant NSCLC, ADAURA reported five-year OS of 88% with adjuvant osimertinib versus 78% with placebo (HR 0.49; 95.03% CI 0.34–0.70). This is evidence in a curative-intent setting, with finite follow-up. It is not evidence for the same benefit in metastatic disease. [Original ADAURA OS paper](https://pubmed.ncbi.nlm.nih.gov/37272535/)

In previously untreated advanced EGFR exon 19 deletion/L858R disease, FLAURA2 now has an OS result: median 47.5 months with osimertinib plus chemotherapy versus 37.6 with osimertinib (HR 0.77; 95% CI 0.61–0.96). Grade ≥3 adverse events of any cause occurred in 70% versus 34%. MARIPOSA's final OS comparison also favored amivantamab–lazertinib over osimertinib (HR 0.75; 95% CI 0.61–0.92; three-year OS 60% versus 51%), with grade ≥3 events in 80% versus 52%. These are separate trials; their arms cannot be ranked by comparing published percentages. [FLAURA2 OS](https://pubmed.ncbi.nlm.nih.gov/41104938/), [MARIPOSA OS](https://pubmed.ncbi.nlm.nih.gov/40923797/)

**Unmet question.** What allows surviving malignant cells to persist through an initial response and later support progression? Maynard et al. profiled 49 biopsies from 30 patients during targeted therapy and described an alveolar-regenerative program in residual malignant cells. The cohort mixes oncogenic drivers and therapies; its 20,000-plus cellular profiles are not 20,000 independent patients. [Original single-cell study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/)

**Computational opportunity (inference).** Replicate a frozen residual-state signature at the patient/sample level, then test it externally. This offers a bounded biological reproducibility task. It does not by itself identify a drug target, demonstrate causal resistance or predict survival.

### Colorectal cancer

**Observed clinical progress.** Biological subtypes require separate questions. CheckMate 8HW's 2025 nivolumab–ipilimumab versus nivolumab comparison in MSI-H/dMMR metastatic CRC reported PFS HR 0.62 (95% CI 0.48–0.81) at median follow-up 47 months; it does not supply an OS or cure conclusion from that endpoint. Grade 3–4 treatment-related adverse events occurred in 22% versus 14%. [Original randomized trial](https://pubmed.ncbi.nlm.nih.gov/39874977/)

In a separate single-arm phase 2 early-stage dMMR study, all 49 rectal-cancer patients completing dostarlimab had a clinical complete response; 37 had a response sustained at least 12 months. Two-year RFS was 92% (95% CI 86–99) across **all 117 rectal and nonrectal patients**, with median recurrence follow-up 20 months. The 92% is neither a rectal-only cure fraction nor evidence for mismatch-repair-proficient CRC. [Original nonoperative study](https://pubmed.ncbi.nlm.nih.gov/40293177/)

BREAKWATER provides a different subtype example: in untreated BRAF V600E metastatic CRC, encorafenib–cetuximab–mFOLFOX6 improved median PFS to 12.8 versus 7.1 months and interim median OS to 30.3 versus 15.1 months (OS HR 0.49; 95% CI 0.38–0.63). This finite PFS despite improved survival motivates resistance research; it does not identify its mechanism. [Original BREAKWATER survival paper](https://pubmed.ncbi.nlm.nih.gov/40444708/)

**Computational opportunity (proposed hypothesis).** Within a molecularly defined CRC subtype, test whether a prespecified baseline immune program reproducibly separates later response categories. Treatment, stage, response definition and biopsy timing must be matched. Combining the dMMR organ-preservation cohort with BRAF metastatic survival data would produce an uninterpretable target. The selected papers do not establish a ready, open patient-level dataset for this task.

### Pancreatic ductal adenocarcinoma (PDAC)

**Observed clinical progress.** After macroscopic resection in PRODIGE 24, adjuvant modified FOLFIRINOX improved five-year OS to 43.2% versus 31.4% with gemcitabine; five-year DFS was 26.1% versus 19.0%. These distinct endpoints show why survival cannot be relabeled recurrence-free survival. Participants were selected postoperative trial patients, not the whole PDAC population. [Original five-year trial analysis](https://jamanetwork.com/journals/jamaoncology/fullarticle/2795978)

The current metastatic context has changed: RASolute 302 reported median OS 13.2 versus 6.7 months and PFS 7.2 versus 3.6 months with daraxonrasib versus chemotherapy in its overall previously treated population (OS HR 0.40; PFS HR 0.49). This randomized benefit remains disease control evidence. The [original 2026 trial paper](https://pubmed.ncbi.nlm.nih.gov/42223072/) supplies efficacy; the [FDA's August 26, 2026 notice](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma) supplies the current U.S. approval status.

**Unmet question.** A 2026 translational study examined paired ctDNA from 44 patients selected for initial disease control followed by progression on daraxonrasib. Acquired RAS-pathway alterations were found in 26, including mutant KRAS amplification in 16; alterations could overlap. Preclinical combination results suggest hypotheses, not established human combination efficacy. These selected denominators do not estimate resistance frequency among every treated patient. [Original resistance study](https://www.nature.com/articles/s41591-026-04537-w)

**Computational opportunity (inference).** Test whether a defined RAS-reactivation signal tracks acquired resistance in paired samples. This is clinically timely, but copy-number calling from ctDNA depends on tumor fraction and assay properties; selected progressors, limited sample size and access to usable paired records make it a more difficult first project.

## Recommended mechanism question

**In EGFR-mutant lung adenocarcinoma, is the published Maynard alveolar-regenerative signature enriched in residual-disease malignant cells relative to pretreatment, and does the direction reproduce in an independent osimertinib-treated cohort when patients, rather than cells, are the analysis unit?**

This is a conditional recommendation for the first mechanism study. It is a replication and robustness test, not a novel cure claim. Its advantage is a specific biological state, published methods and public source/code pointers. Its costs are sampling bias, a small effective patient count, mixed therapy in the discovery source and uncertain availability of an independent cohort with suitable labels. A negative or non-identifiable result is useful.

The subsequent [public-data preflight](egfr-mechanism-feasibility.md) retrieved the full main metadata and a separate small osimertinib metadata subset. It also retrieved an author-code 17-gene AT2 vector, whose equivalence to the exact paper alveolar-regenerative signature remains unverified. Matching malignant-cell expression/QC, exact signature mapping and independent validation remain outstanding.

Before execution:

1. Verify permitted public processed-data access, source version and hashes. The paper points to BioProject **PRJNA591860** and `czbiohub/scell_lung_adenocarcinoma`; pointers do not prove that a suitable processed matrix and all necessary metadata have been obtained.
2. Obtain patient, sample, lesion/site, EGFR variant, treatment/line, biopsy timing and source-defined pretreatment/residual/progression labels. Count eligible patients and genuinely paired samples before making a power or feasibility claim. Missing timing is not “baseline.”
3. Freeze the published gene set and scoring rule. The signature was partly derived from the original state comparison, so separating those states in that source is a reproduction check, not independent validation.
4. Confirm malignant-cell annotation and check normal alveolar contamination, tumor fraction, cell-cycle effects, lesion/site and treatment differences. Use donor/sample aggregation and donor-level uncertainty; do not use cells as independent replicates or split one patient's cells across training/test sets.
5. Reserve an independent eligible cohort and hold all preprocessing choices fixed for that evaluation. If one is unavailable, report **reproduction only**. Do not replace it with unrelated untreated TCGA samples or a different treatment class.

The immediate endpoint is a prespecified patient-level score difference with uncertainty and external directional replication. Subsequent perturbation evidence would be needed to call a causal dependency, and a separate clinical study would need PFS/OS or recurrence endpoints plus toxicity and quality of life. An expression score is not a validated surrogate for any of them.

The separate workspace TMB–durable-clinical-benefit immunotherapy benchmark is a data-validation foundation. It does not test this EGFR targeted-therapy mechanism, and the treatment classes, labels and signatures must not be pooled.

## Evidence and execution limits

This is a targeted comparison, not a systematic review or an exhaustive treatment inventory. Original trial abstracts were inspected through PubMed/Europe PMC; relevant methods/results sections were also checked for the open Maynard, nonoperative dMMR, BREAKWATER and daraxonrasib-resistance papers. Some publisher pages blocked direct full-text retrieval. The ledger identifies unverified cutoff dates rather than substituting publication dates. No model was fitted, no trial data were requested, and no clinical efficacy conclusion was generated from the Iowa ecological corpus.
