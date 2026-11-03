# Preclinical data: a feasible starting point

Verified **October 29, 2026**. This is a data-feasibility review for treatment discovery, not an efficacy result. No response model was fitted and no target was validated. The existing Iowa county/environmental corpus supplies neither drug-response measurements nor patient treatment outcomes.

## Versions and access actually verified

| Resource | Verified version and contents | Access and local status |
| --- | --- | --- |
| Current Broad DepMap | **26Q3**, announced October 5, 2026; integrates 150 NextGen models and changes CRISPR/omics processing | Official release notes archived. Downloads, terms, and catalogue endpoint returned human-verification HTML, including in Brave Personal. Current matrix inventory and licence were **not verified**. |
| Reproducible DepMap archive | **24Q4 v1**, DOI `10.25452/figshare.plus.27993248.v1` | Public Figshare API/downloads, CC BY 4.0 verified in article metadata. Manifest, README, model/condition/profile/screen mapping files and control lists archived; large matrices not acquired. |
| PRISM extended primary | **Repurposing Public 24Q2 v1**, DOI `10.6084/m9.figshare.25917643.v1` | Public archive, CC BY 4.0; both readmes and cell/compound/treatment metadata saved. Large response matrices not acquired. Newest PRISM archive located here; complete latest portal inventory remains unverified. |
| PRISM dose response | **PRISM Repurposing 19Q4 v4**, DOI `10.6084/m9.figshare.9393293.v4` | Public archive, CC BY 4.0; readmes and selected metadata saved. This is an older, separate screen, not the dose-response version of every 24Q2 compound. |
| GDSC | Official **release 8.5** file `GDSC2_fitted_dose_response_27Oct23.xlsx` | Official object URL returned HEAD 200, 21,330,376 bytes; workbook not acquired. Old CancerRxGene homepage/download page returned HTTP 410. Latest complete release inventory not confirmed. |
| Sanger Cell Model Passports | Mutable `model_list_latest.csv.gz`, snapshotted October 29, 2026; **1,984 model rows** | Model list and official methods/usage pages saved. Custom Sanger terms apply; do not label these files CC BY. |

Sources: [26Q3 staff release notes](https://forum.depmap.org/t/announcing-the-26q3-release/4692), [24Q4 archive](https://plus.figshare.com/articles/dataset/DepMap_24Q4_Public/27993248/1), [24Q2 PRISM metadata API](https://api.figshare.com/v2/articles/25917643/versions/1), [19Q4 PRISM metadata API](https://api.figshare.com/v2/articles/9393293/versions/4), [GDSC2 workbook](https://cog.sanger.ac.uk/cancerrxgene/GDSC_release8.5/GDSC2_fitted_dose_response_27Oct23.xlsx), [Sanger usage policy](https://depmap.sanger.ac.uk/documentation/data-usage-policy/).

26Q3 fixes previously undercorrected library effects and removes 96 genes found only in TKOv3/Brunello from specified CRISPR files. An old archive is useful for reproduction, but results must be checked against the corrected release before promoting a target. Do not append different releases as if they were independent experiments. [Release notes](https://forum.depmap.org/t/announcing-the-26q3-release/4692)

## Files, measurement meaning and joins

| Data | Source filename | Grain, unit and key |
| --- | --- | --- |
| Knockout fitness | `CRISPRGeneEffect.csv` | `ModelID` × gene; corrected/scaled Chronos effect. More negative indicates greater fitness loss. Approximately 0 and −1 anchor reference nonessential and common-essential distributions; −1 does not mean 100% death. |
| Dependency probability | `CRISPRGeneDependency.csv` | `ModelID` × gene; inferred dependency probability, **not** probability of a patient responding. |
| Baseline expression | `OmicsExpressionProteinCodingGenesTPMLogp1.csv` | Model × gene, `log2(TPM+1)`; not counts. Profile-level alternatives require `OmicsProfiles.csv` and default-profile mapping; do not treat repeated sequencing profiles as independent models. |
| Mutations | `OmicsSomaticMutations.csv`; `OmicsSomaticMutationsMatrixHotspot.csv`; `OmicsSomaticMutationsMatrixDamaging.csv` | Variant/model records versus model × gene categories. In 24Q4, matrix values 0/1/2 represent no called qualifying mutation and allele-frequency-sum categories, with 2 assigned above 0.95. This is not proof of biallelic loss or a universal oncogenic-variant classification. |
| Model provenance | `Model.csv`, `ModelCondition.csv`, `CRISPRScreenMap.csv`, `ScreenSequenceMap.csv` | Model, condition, screen, sequence, source-patient and alias keys are different levels. Preserve QC, culture format, drug treatment, growth medium and parent/derived relationships. |
| PRISM24Q2 | `Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv`; `Repurposing_Public_24Q2_LFC_COLLAPSED.csv` | Extended matrix: treatments × `depmap_id`; lower-level table retains culture/screen/dose. Log2 barcode viability versus DMSO after five days; new screens used 2.5 µM. More negative means lower relative viability; a negative value alone does not establish cell death. |
| PRISM19Q4 | `secondary-screen-dose-response-curve-parameters.csv` | Compound-batch × model × screen; fitted `auc`, `ec50`, `ic50`, convergence and `r2`; eight fourfold dilutions beginning at 10 µM. Source recommends technical redo `MTS010` when available; redos are not independent validation. |
| GDSC2 | `GDSC2_fitted_dose_response_27Oct23.xlsx` | Fitted model × compound curve; `SANGER_MODEL_ID`, `DRUG_ID`, curve/result IDs; `LN_IC50` is natural log of micromolar IC50. `AUC` is normalized to the screened concentration interval; retain `MIN_CONC`, `MAX_CONC` and `RMSE`. |

Definitions are from saved source readmes, [Chronos primary methods](https://doi.org/10.1186/s13059-021-02540-7) and the [official GDSC dictionary](https://depmap.sanger.ac.uk/documentation/datasets/drug-sensitivity/). PRISM24Q2 single-dose LFC, PRISM19Q4 AUC and GDSC AUC are different outcomes. Do not pool their numbers. Drug name/nominal target is insufficient for compound matching: retain full batch identifiers, structure/salt information and a reviewed compound crosswalk. In particular, 24Q2 `IDs` can include the `BRD:` prefix absent from older `broad_id` values.

Preserve a source inconsistency: the PRISM24Q2 article and `README.txt` describe 1,514 new compounds, while `Repurposing_Public_24Q2_Readme.txt` says 1,522. The actual extended compound list has **6,790 rows**, including earlier primary screens. Its 1,898 cell metadata rows represent **915 unique model IDs**, with repeated pools/cultures/screens; they are not 915 complete passing response profiles.

## Observed coverage and duplicate warnings

These are intersections of **saved metadata**, not evaluable drug-response sample sizes. The 24Q4 CRISPR screen map contains 1,178 unique models; the full model catalogue contains 2,105. Neither catalogue size is the denominator for an individual gene/drug analysis.

| Cohort, exact OncoTree codes | Model catalogue | CRISPR screen map | PRISM24Q2 metadata | Both metadata sets |
| --- | ---: | ---: | ---: | ---: |
| LUAD | 91 | 53 | 52 | 39 |
| Selected NSCLC: LUAD, LUSC, LCLC, NSCLC, LUAS, GCLC, NSCLCPD | 161 | 96 | 92 | 70 |
| Colorectal adenocarcinoma: COAD, READ, COADREAD, MACR | 96 | 63 | 43 | 35 |
| Pancreatic adenocarcinoma: PAAD | 64 | 45 | 39 | 36 |

The broader NSCLC grouping is an explicit convenience definition, not all Lung models. Keep SCLC and unresolved classifications separate. Histology-specific and variant-specific counts will be smaller after response/QC joins. Computation and exact duplicate groups are in [preclinical-metadata-audit.json](preclinical-metadata-audit.json).

The archived DepMap table has 163 shared `PatientID` groups covering 359 rows, one repeated populated `SangerModelID`, and four repeated RRIDs. **NCI-H322 (`ACH-000837`) and NCI-H322M (`ACH-002172`) share `SIDM00117` and `PatientID`**. These can leak across apparent Broad/Sanger validation sets. The Sanger snapshot has 234 shared patient-ID groups and two repeated RRIDs. There are 1,680 literal Sanger `BROAD_ID` matches to the older DepMap table, with no disagreement among corresponding populated Sanger IDs. Missing IDs and related/subclone models still require review; do not fuzzy-match names automatically or silently delete possible duplicates.

## Pilot that these data can support

Start with a **reproduction and coverage audit in LUAD**: verify that curated activating-EGFR mutation status distinguishes basal EGFR knockout fitness and response to an EGFR inhibitor already represented in PRISM. Erlotinib, gefitinib and osimertinib appear in the saved PRISM compound metadata; presence does not establish response coverage. Freeze mutation definitions, assay-specific endpoint/QC rules and a single compound before looking at responses. This is a positive control for the pipeline, not a novel discovery.

For the proposed **EGFR residual-state robustness** question, these basal screens only supply background and candidate triage. A test requires paired baseline/on-treatment state measurements, defined EGFR inhibitor/exposure duration, residual viable-cell measurements, and genetic or pharmacologic perturbations **in the residual state**, followed by a separate cohort or independently conducted experiment. Single-agent basal dependencies do not establish combination synergy, drug-tolerant persister dependencies or resistance prevention.

Before fitting anything:

1. Obtain permitted, version-pinned response/mutation/expression matrices and verify exact headers, nonmissing overlap and QC for each chosen inhibitor. Refresh the 26Q3 manifest/terms through ordinary authorized access; do not assume older licence or schema.
2. Reconcile ACH/SIDM/RRID/COSMIC identifiers and parent/source-patient relationships. Keep all profiles, conditions, compounds' replicate wells and related models together in the split appropriate to the intended generalization. Perform all learned feature selection, scaling and imputation within development folds.
3. Separate reproducibility in the **same lines with another assay** from generalization to **new biological models**. Reserve unseen source-patient/model groups for the latter. GDSC1/GDSC2 overlap and the Sanger screens integrated into DepMap can defeat a superficial “external dataset” split.
4. Compare within histology/biomarker strata and report uncertainty and group sizes. Pan-cancer associations can mainly encode tissue lineage, media or growth rate; they do not demonstrate a within-LUAD mechanism.

## Limits that remain after a successful analysis

- **Pan-essentiality and selectivity:** broadly essential genes are not automatically selective targets. Show full within- and across-lineage effect distributions, common-essential controls and measurement quality; a mean effect or arbitrary cutoff is insufficient. Selectivity among cancer models does not measure a therapeutic window in normal tissues.
- **Assay dependence:** GDSC2 uses a 72-hour ATP assay and PRISM uses five-day pooled barcode measurements. Different dose ranges, media, proliferation and readouts can change response. AUC is dose-range dependent. Growth-rate correction needs baseline/control growth measurements; it cannot be reconstructed honestly from AUC alone. [Primary GR methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC4887336/)
- **Translation:** knockout removes gene function differently from an inhibitor's concentration, target engagement and off-target activity. These screens do not measure human pharmacokinetics, organ toxicity, immune effects, stromal interactions, durable tumor control or patient survival. Even 3D models preserve some states missed by conventional cultures, demonstrating why model context matters. [Primary NextGen study](https://doi.org/10.1038/s41586-026-10843-7), [primary PRISM study](https://doi.org/10.1038/s43018-019-0018-6)

An eventual claim of benefit requires the relevant normal-tissue and mechanistic experiments, independent model validation, exposure/target-engagement evidence and appropriate patient studies. The present output is a reproducible route to hypotheses and explicit missing inputs.

## Saved provenance

[Source catalogue](preclinical-data-sources.json) records versions, access depth, file URLs, source MD5 values and whether each file was actually acquired. The [archive manifest](sources/preclinical/2026-10-29/archive-manifest.json) records local SHA-256 values and verified source MD5s. Thirty public source snapshots were saved, plus one small derived HTTP-availability record; every file is below 5 MB. Large matrices and credentials were not acquired. Originals were preserved; no existing research source was replaced.
