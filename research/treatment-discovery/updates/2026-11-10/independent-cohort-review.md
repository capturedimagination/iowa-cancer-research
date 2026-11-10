# Independent EGFR residual-state cohort review

Checked **November 10, 2026**. The strongest new candidate is **GSE292469**, released publicly on November 1. It supports an independent, cross-sectional expression comparison. Its stage, sampling and sequencing differences prevent that comparison from establishing a treatment-induced change. No independent paired pretreatment/residual cohort was verified in this targeted search. [Machine-readable review and metadata audit](independent-cohort-review.json)

## Newly available clinical data

The current [GEO submission](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292469) describes **73 patients/specimens**: 28 before osimertinib, 14 with residual disease on treatment after maximal shrinkage and before progression, and 31 at radiographic progression. MRD2 has two cores, producing **74 libraries**. This is a new MSK primary cohort, separate from the Maynard source study; it is not a reanalysis of Maynard cells. Participant identity linkage was neither necessary nor attempted.

Do not mix versions. The [2025 preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12248098/) described 62 unmatched patients, including six residual-disease patients. The November 2026 accession contains an expanded cohort. The [current author repository](https://github.com/shahcompbio/egfr_nucseq/tree/c4211458564c92b32c1276badaed2e6731ad1a68) also uses revised manuscript wording and the expanded deposit. Its Zenodo/CELLxGENE links remain placeholders in the checked README.

The [public file listing](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE292nnn/GSE292469/suppl/) supplies raw UMI counts and cell annotations. An anonymous HEAD request confirmed **12,553,420,880 bytes** for `GSE292469_counts.h5`. This review downloaded the **18,852,668-byte** annotation file, SHA-256 `9b16b89922bade9d1334ebaeb002763dcca9fd2652a3e9616befb98f04777012`, and GEO sample descriptions; it did not inspect expression scores. Full URLs, retrieval dates and source hashes are in the JSON ledger.

## What the metadata actually supports

Our direct audit found 457,724 unique cell identifiers, no duplicate identifiers, 73 sample IDs and 74 core IDs. Every row has a singlet label. `is_tumor_cell` identifies 166,112 tumor nuclei. Use this explicit annotation; epithelial identity alone is insufficient. `sample_id` is the patient unit under the submitted design, and `core_id` preserves MRD2's repeated sampling.

| Filter on delivered annotations | Pretreatment | Residual disease | Progression |
|---|---:|---:|---:|
| All source specimens | 28 | 14 | 31 |
| Any tumor nuclei, all histologies | 26 | 10 | 29 |
| LUAD histology and at least 20 tumor nuclei | 26 | 9 | 24 |
| LUAD histology and at least 100 tumor nuclei | 25 | 8 | 21 |

These are candidate sample counts, not expression-analysis results. Eight specimens have no annotated tumor nuclei. The JSON records them and all aggregate sensitivity counts.

The [individual GEO records](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE292469&targ=gsm&form=text&view=full) reveal several important constraints:

- At the LUAD/20-cell threshold, only **1/26 pretreatment** specimens is stage IV, compared with **8/9 residual** specimens. That sole stage-IV pretreatment specimen is a lymph node; no comparable stage-IV pretreatment lung specimen remains. A matched stage/site analysis cannot recover an adequate comparison from these data.
- Residual specimen **LX2019 is SCLC** by its histology field despite the generic LUAD title. Keep transformed histologies separate. LX1966 carries C797S and records 1,070 days on osimertinib; LX2000 records 847 days. “Residual” is not uniformly an early, resistance-mutation-free persister state.
- The Series describes legacy v3.1 and newer LX v4 libraries, but individual extraction paragraphs all say v3.1. Treat the kit mapping as unresolved source inconsistency. Using the Series-implied mapping, the LUAD/20-cell groups comprise pretreatment 24 legacy/2 newer patients versus residual 3 legacy/5 newer/1 mixed-core patient. This is strong state–batch imbalance.
- The newer records change the spelling of the age and days-on-osimertinib keys. Harmonize those keys explicitly. Preserve source labels, including the ambiguous procedure label “Fresh Frozen.”

The delivered H5 contains **raw UMI** counts. Author figure notebooks default to a SoupX-corrected `RNAsoup` assay in separate objects. A calculation from GEO counts must name its own normalization and cannot claim exact reproduction of those figures. [Author download/conversion specification](https://github.com/shahcompbio/egfr_nucseq/blob/c4211458564c92b32c1276badaed2e6731ad1a68/code/00_download_convert.qmd)

## Other candidates and exclusions

| Resource | What it contains | Role for this question |
|---|---|---|
| [GSE302284](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE302284) | Two post-treatment human tissue samples plus four PC9/DFCI282 model samples; H5 files available | The [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12374242/) describes one new patient undergoing scRNA-seq. No paired pretreatment comparator; cell annotation would need verification. Its Maynard reanalysis is not independent evidence. |
| [GSE243562](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243562) | Four scRNA-seq samples: untreated/residual YU-003 and YU-006 PDX models | Preclinical comparison, not four patients. Human cells growing in mice must retain model/donor grouping. |
| [GSE243564](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243564) | Bulk RNA-seq in related PDX models | Different assay and overlapping models; not independent clinical validation. |
| [GSE253742](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE253742) | Eight clinical bulk RNA-seq samples, four before/four after osimertinib | No malignant-cell resolution; donor pairing and residual-state definitions require further verification. |
| [GSE259387](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE259387) | 59 spatial regions from ten patients, focused on NSCLC/SCLC transformation | Regions are not patients; progression/transformation context differs from residual LUAD. |
| [GSE275199](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE275199) | Public cell-line persister experiment; separate human raw-data pointer to controlled dbGaP | Not an open independent patient validation set. No controlled-data application or acquisition was attempted. |

## Access and next analysis

[GEO policy](https://www.ncbi.nlm.nih.gov/geo/info/disclaimer.html) and [NCBI molecular-data policy](https://www.ncbi.nlm.nih.gov/home/about/policies/) permit public access and impose no provider restrictions on use/distribution, while preserving possible third-party rights. No record-specific access/use restriction appeared in the checked GSE292469 records. This permits ordinary open-data reanalysis; it is not a blanket license for every linked article, codebase or future controlled dataset. The author code is GPL-3.0; the old preprint's article license is a separate matter. This review publishes original findings and provenance, while retaining downloaded source bodies locally.

Freeze the exact published signature and scoring method before inspecting expression results. Verify barcode/gene correspondence, aggregate within each patient, combine MRD2's cores, separate progression and transformed histology, and report cell-count/site/batch sensitivities. Treat any score difference as a **descriptive cross-sectional association with major confounding**, not a treatment effect, causal resistance mechanism, drug target or patient-benefit result. No expression score was calculated by this cohort review.
