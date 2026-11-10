# Open cancer-cell lineage data opportunity

Audit date: 2026-11-10. Status: **one acquired candidate for further validation; no fully certified prospective cohort yet**. This bounded search inspected three alternatives to the existing Oren/Chakrabarti sources. It did not calculate Q, covariance, hazards, treatment associations, or model fits. No author was contacted. Raw originals are preserved in the local source archive; public source URLs and hashes are in [acquisition.json](acquisition.json).

**Proceed with Kuchen2020 TET21N neuroblastoma source workbooks.** They contain explicit sister, mother, birth, division, death, and loss fields, and seven experiment-labeled sheets. The export is substantially closer to the required measurement than the previously audited matrix sources. The immediate task is a source dictionary and conservative observation graph. Original-founder inference and future-independent birth-cohort eligibility remain unverified.

## Access and eligibility decision

| Source | Actual access depth | Decision |
| --- | --- | --- |
| [Kuchen2020](https://doi.org/10.7554/eLife.51002) | Downloaded both original source XLSX files and experiment-overview PDF; inspected every workbook row structurally | Acquired candidate. Recorded-newborn analysis may become feasible; selection/censoring gates remain |
| [Korsnes2026](https://doi.org/10.3389/fcell.2026.1911886) | Read primary methods, availability, and linked Mendeley description; no complete tree file acquired | Strong prospective design, but underlying data are request-only |
| [ALFI2023](https://doi.org/10.1038/s41597-023-02540-1) | Read primary schema; downloaded author README and actual Figshare API metadata; 8.42GB archive not acquired | Open annotations do not establish a cohort with joint division/death/parent tracking |

## Kuchen source meaning

TET21N controls have ectopic MYCN. Perturbations use doxycycline-mediated MYCN inhibition (1µg/ml; 48–72h pretreatment) or rapamycin (20–40nM; 72h). This is a growth/cycle study, not a drug-persister experiment. Manual imaging tracks span up to seven days. The seven replicates combine biological and technical replication; per-sheet allocation is unspecified. The published cycle-correlation analysis truncates later generations using a 5% endpoint-alive rule. Early-leaving cells unable to yield deep trees were excluded; whether this exclusion precedes the raw export is unresolved. Migration and administrative censoring are conceptually distinguished, but the workbook loss field lacks that distinction. The authors already tested birth-time, spatial, and temporal confounds and resampled lineage clusters. These are prior analyses, not newly proposed discoveries. [Primary methods, censoring appendix and Figure 1 supplements](https://pmc.ncbi.nlm.nih.gov/articles/PMC7018508/).

The [experiment overview](https://cdn.elifesciences.org/articles/51002/elife-51002-fig1-data1-v2.pdf) assigns rap1=40nM,117h,8 generations and rap2=20nM,115h,7 generations. Actual export maxima below have the opposite duration/generation pairing. This discrepancy does **not** establish a label swap. Dose-specific comparison must wait.

The [control workbook](https://cdn.elifesciences.org/articles/51002/elife-51002-fig1-data2-v2.xlsx) has 19 columns and the [perturbation workbook](https://cdn.elifesciences.org/articles/51002/elife-51002-fig4-data1-v2.xlsx) 15. Both supply lineage ID; two sibling IDs; mother and grandmother IDs; shared birth time; separate cycle/death/loss durations; generation; and mother/grandmother cycle lengths. Controls also have sibling birth coordinates. Missing entries are literal `NaN` strings. IDs must remain opaque and namespaced by sheet. Negative durations remain source anomalies, not inferred events.

Independent read-only parsing reproduced the initial structural counts:

| Sheet | Pair rows | Children | Lineage IDs | Maximum generation | Maximum birth+duration (h) |
| --- | ---: | ---: | ---: | ---: | ---: |
| rep1 | 923 | 1,846 | 16 | 10 | 140.5000 |
| rep2 | 808 | 1,616 | 17 | 11 | 141.4667 |
| rep3 | 871 | 1,742 | 35 | 9 | 120.3000 |
| -myc1 | 492 | 984 | 40 | 9 | 166.6667 |
| -myc2 | 600 | 1,200 | 28 | 8 | 141.4667 |
| rap1 | 482 | 964 | 19 | 7 | 115.0000 |
| rap2 | 502 | 1,004 | 16 | 8 | 117.0000 |

These are exported-record counts, not an inferred prospective founder denominator. All sheets begin at generation 2. Across sheets there are 4,678 pair rows and 9,356 child records, with no duplicated child or pair-mother IDs within a sheet. Each child has exactly one finite fate-duration field: 4,508 division, 190 death, and 4,658 loss. These counts do not estimate a death probability. Every join to a recorded mother agrees in timing within 7.2×10⁻¹³h.

Five structural issues remain:

| Original file/sheet/cell | Source value or missing record | Required handling |
| --- | --- | --- |
| Control / rep2 / G548 | loss duration −96.5333333333333h | Unknown valid loss time; no repair inferred |
| Control / rep2 / G647 | loss duration −13.0666666666667h | Same |
| Perturbation / -myc1 / D423 | loss duration −16.3333333333333h | Same |
| Perturbation / -myc2 / G218 | loss duration −32.4h | Same |
| Control / rep3 / E170 | Cell 1018054 divides at 90.9+17.2h, but has no successor-pair row | Missing descendant mass, not a terminal death |

## Acquisition and analysis proposal

1. Preserve the acquired source files, names, hashes, source-cell locators, and CC BY attribution. Freeze a dictionary and graph construction before any Q/covariance calculations. Verify cycles, unique parents, simultaneous daughter birth, timing resolution, grandmother references, and all loss meanings. Keep unresolved timings and missing branches explicitly unknown.
2. Define a **recorded-at-birth sister cohort**, using birth and predeclared administrative support only. Absence of original founder rows need not defeat this estimand. However, later family success, completed cycles, survival, or complete-tree requirements cannot determine eligibility. The existing source statements do not yet certify that condition for these exports. If it cannot be certified, restrict conclusions to compatibility/bounds within the retained record.
3. Once admissible, test whether an age- and calendar/context-conditioned competing-risk baseline predicts held-out sheet sister-subtree outcomes. Compare a model carrying mother-history information under identical observation rules. Use family clusters and explicit experiment-level validation. Seven sheets are not seven certified independent biological experiments; conditions have only 3/2/2 sheets. Separate replication metadata and rapamycin mapping must be settled before condition-level inference.
4. Preserve disconfirming outcomes: independence may predict adequately; loss uncertainty may make tests uninformative; apparent dependence may track birth time or context. A residual family effect cannot uniquely identify inherited intracellular state because persistent shared environment gives an observational alternative. Low death counts, especially in perturbed sheets, may limit subtree-extinction measurements; no power calculation was performed.

This opportunity concerns predictive adequacy of competing lineage models with an explicit observation process. It is not a claim that cycle correlation, censoring bias, or birth-time adjustment is new, and it does not refute the original study. No treatment-target, clinical efficacy, or priority claim follows.

The [next graph and dictionary planning draft](graph-plan-draft.md) specifies source-cell provenance, namespaced identifiers, conservative unknown branches and structural checks. It is not frozen, and no graph-based outcome calculation has been performed under it.

## Other two sources

Korsnes2026 reports untreated MDA-MB-468 cells, 4,000 initial cells and descendants in 21 experiments, with 72h observation. Initial central-field cells are selected at recording start. Its healthy-pedigree analysis subsequently filters on normal divisions and absence of later death; that subset would be unsuitable for our prospective denominator. The full underlying data are available only upon author request. [Primary paper and availability statement](https://pmc.ncbi.nlm.nih.gov/articles/PMC13624361/). The linked [Mendeley deposit](https://data.mendeley.com/datasets/pt66xkf6p3/2) describes smoothed-distribution animations, not a full lineage export. Its dynamic file list was not exposed; a public API request returned 403. No request-only dataset was acquired.

ALFI contains HeLa, U2OS, and nonmalignant RPE-1 imaging. Its parent-linked Task 1 tracks interphase/mitosis; the death-rich Task 2 omits interphase and parent IDs. MI sequences have only mitotic phenotypes in Task 2. Thus death labels from CD/TP sequences cannot be joined to MI lineages as though they were the same cohort. Parent assignment also occurs after daughters enter interphase. [Primary data schema](https://pmc.ncbi.nlm.nih.gov/articles/PMC10551030/). The [author README](https://iris.cnr.it/retrieve/c56f0242-819e-4b07-89d4-292bb6721e8a/ALFI_dataset_Readme_2024.pdf) states CC-BY and contains an apparent contradictory filename statement for CD/TP; the acquired [Figshare metadata](https://api.figshare.com/v2/articles/23798451) instead labels CC0. Both statements are preserved. Archive contents and experiment independence have not been checked. ALFI remains useful for annotation-method validation, not the present prospective lineage-survival test.

## Provenance and scope

[opportunity-ledger.json](opportunity-ledger.json) records the bounded search, decisions, URLs, access depth and gates. [acquisition.json](acquisition.json) pins five exact acquisitions. `license-record.json` retains the observed rights basis and ALFI discrepancy. `kuchen-schema.json`, `kuchen-structural-audit.json`, and `kuchen-anomaly-locators.json` preserve first inspection. `audit_kuchen_structure.py` independently parses the untouched XLSX XML; its output is [structural-verification.json](structural-verification.json).

All source files are public established-cell-line records or metadata; no human participant records were acquired. Download permission is not blanket authority to publish raw originals. The initial audit was performed in ignored working storage before this public copy. Original source hashes, first structural findings and unresolved gates are preserved; no biological/model outcome was calculated.

## Reproduce the structural audit

Obtain the two unchanged XLSX originals from the links above and place them in `research/treatment-discovery/sources/lineage-2026-11-10/alternative-lineage-2026-11-10/`. This directory is excluded from public Git snapshots. The parser checks the pinned workbook and schema hashes before reading and preserves all source values. From the project root:

```sh
python scripts/audit_kuchen_structure.py --out tmp/kuchen-structural-reproduced.json
```

The seven per-sheet records should match [the preserved first parse](structural-verification-initial.json). The portable parser adds input paths and explicit no-overwrite handling; it does not repair anomalies or infer biological outcomes.
