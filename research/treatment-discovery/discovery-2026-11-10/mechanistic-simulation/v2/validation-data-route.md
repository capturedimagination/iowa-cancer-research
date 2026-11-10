# A concrete validation route, with an unresolved data gap

**None of the three audited resources is ready to identify tolerant-state exit after withdrawal.** The strongest partial resource is better than a movie: Oren et al. publish machine-readable PC9 division/death matrices. These could help test the growth/death part of a model after resolving their time and identity dictionary. They do not supply the joint functional state-transition histories needed to distinguish exit from changing proliferation, death or marker retention.

This bounded audit was performed on 2026-11-10. It does not establish that no suitable dataset exists elsewhere. [The structured audit](validation-data-route.json) records verified resources, field inventories, access terms, file hashes, missing fields and decisions. No authors were contacted and no raw source data were added to this repository.

| Candidate | What is actually available or verified | Decision for this question |
|---|---|---|
| Oren et al., 2021, Watermelon/PC9 | Numeric division/death matrices and cycle-time/censoring fields; separate lineage-linked transcriptomes | **Conditional go** for a growth/death benchmark; **no-go** for withdrawal exit hazard |
| Berger et al., 2021, IRS1/PC9 | Three listed long-term WMV movies, figure source data and a small simulation-code deposit | **No-go** for direct event-level withdrawal validation |
| May/Martin/Houseley, 2026, GSE335847/335848 | Public RNA-seq/TrAEL-seq metadata and sequencing deposits; no track/event table listed | **No-go**: assay mismatch |

## 1. Oren: the most useful partial resource

The [primary paper](https://www.nature.com/articles/s41586-021-03796-6) describes 1,135 PC9 lineages tracked during continued osimertinib treatment, including 77 persister lineages. Divisions and deaths were recorded. The tracking design follows one path through a dividing lineage, choosing one sister; persister identification also includes retrospective tracing from endpoint survivors. These selection rules matter for event-rate inference. Methods are available in the [author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC9209846/).

We inspected the [Figure 1 source workbook](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-03796-6/MediaObjects/41586_2021_3796_MOESM8_ESM.xlsx) in memory: 13,180,157 bytes; SHA-256 `a53fe57483b0e55a3b2545f611ff2cf2a31338b8c9dffad0f9af1522222d8f7c`. Its actual contents include:

- `Figure 1b-divison` and `Figure 1b-death`: each 1,135 × 2,025 numeric cells. The source spelling “divison” is preserved here. First rows and columns are numeric, not an explicit timestamp/lineage-ID header.
- `Figure 1c`: `type`, `cell_cycle_time`, `censoring_status`, with 306 data rows.
- `Figure 1d`: `viability(0_persister)` and `Progeny_size`, with 1,135 data rows.
- Figures 1g/1h: population resensitization/growth summaries, not a longitudinal functional-state label for every tracked cell.

The [official GitHub repository](https://github.com/yaaraore/Watermelon) contains lineage-barcode processing code and Seurat transcriptomic objects. Its PC9 object points to a 581,991,189-byte Git LFS object; it was **not downloaded**. These transcriptomes are not microscopy event logs. No raw movie deposit was identified in the inspected supplementary listing or repository.

The immediate missing pieces are the matrix-column time map, row-to-lineage/replicate dictionary, event/censoring code definitions, and the sampled-path selection record. More fundamentally, the public matrices do not provide verified post-withdrawal sensitive/tolerant transitions linked to those events. Endpoint survival, cycling history and an expression signature are not interchangeable state labels.

**Access and terms:** the workbook is publicly retrievable. The article lists an exclusive publisher licence, and the GitHub repository reports no licence. No explicit open-data licence for redistributing this workbook was verified. The repository therefore records its link, hash and field inventory, rather than copying its raw data. Public access alone is not recorded as permission to train on or republish the files.

## 2. Berger: movies are available, annotated tracks are not established

The [primary paper](https://www.nature.com/articles/s43018-021-00261-1) lists three supplementary time-lapse movies of PC9 under gefitinib over 80 days. [Video 1](https://static-content.springer.com/esm/art%3A10.1038%2Fs43018-021-00261-1/MediaObjects/43018_2021_261_MOESM2_ESM.wmv) returned HTTP 200 with a size of 18,350,764 bytes on a header-only check; its contents were not downloaded or visually validated. A movie link does not establish full lineage trees, division/death timestamps, image quality sufficient for reannotation, or censoring information.

The linked [Zenodo record](https://zenodo.org/records/5036166) is open and explicitly CC BY 4.0, but its only listed file is `panel1v2.m`, 392 bytes, for the paper's chance-to-persist simulation. That is not an imaging track dataset. We also inspected the Figure 1 and Figure 3 source-workbook structures: they contain population drug-release/growth summaries and clone/plate/timepoint object counts. Their headers did not establish a full per-cell parent/event table or repeated functional-state labels. File hashes and observed fields are in the structured audit. No same-lineage withdrawal-state event table was identified.

**Access and terms:** the publisher identifies an exclusive licence and no Creative Commons link for these supplements was verified. The Zenodo code's CC BY licence does not extend to the publisher's movies. A future movie reannotation project would need original time metadata, cell-tree/event annotations, follow-up/censoring definitions and reuse terms. Even complete tracks during continued treatment would not by themselves validate post-withdrawal exit.

## 3. The recent PC9 sequencing deposit: relevant biology, wrong observation type

[GSE335847](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE335847) is public as of 2026-06-22 and is part of [GSE335848](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE335848). Its submitter description reports cell cycling and death balancing population size under osimertinib. That motivates the growth-versus-exit ambiguity, but it is not an analysis performed here. The inspected GEO record has no linked publication citation.

The deposited observations are TrAEL-seq and RNA-seq, including treatment-day samples and resistant derivatives. The 13 TrAEL-seq samples are sequencing samples, not patients or imaging lineages. No movie, individual-cell event table, functional transition labels or withdrawal trajectory is listed. Only public metadata were retrieved; sequencing matrices were not downloaded.

**Access and terms:** [GEO's official download page](https://www.ncbi.nlm.nih.gov/geo/info/download.html) describes free access to its records and raw files. No controlled-access application or file-specific licence appears in the inspected series metadata. These access facts do not supply rights or availability for an unlocated imaging dataset. The decision is no-go because the required observations are absent from the inspected deposit.

## The focused empirical test

A qualified laboratory could test a narrower question: **after stress removal, does changing state abundance require changing exit once division, death, entry and marker drift are separately observed?** This is a measurement specification, not a wet-lab procedure or treatment regimen.

The minimum record needs persistent cell, parent, lineage and independent-experiment IDs; exact observation and exposure-change times; both-daughter division and death events; tracking loss distinguished from death; repeated functional-state labels; and independent marker-retention/error measurements. Functional resensitization must be tied to the tracked lineage. If establishing state requires destroying a cell or testing a matched sister population, that limitation must remain explicit. Absolute abundance of both states and re-entry events are needed to test the restricted model used in v2.

Use an independent pilot to define the state and observation window, then freeze the comparison of constant exit, changing exit, changing growth/death, marker drift and re-entry models. Evaluate joint event predictions on held-out independent experiments, preserving lineage dependence. Exit hazards require observed transitions and time spent at risk in the state; they cannot be recovered simply by labeling endpoint survivors or using transcriptomic pseudotime.

If measured growth/death or marker drift explains the curvature, changing exit is unsupported. If a changing-exit model fails to improve held-out joint predictions, its additional complexity has not earned a mechanistic interpretation. Until those observations exist, v2 remains a synthetic precision calculation with documented ambiguity.
