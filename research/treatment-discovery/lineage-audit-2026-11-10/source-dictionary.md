# Oren Figure 1: a partial dictionary, not a certified hazard dataset

The source establishes the experiment and its mixed tracking design, but **does not yet establish the exact 2,025-column time map, spreadsheet event-code transformation, observation mask or row-level selection/replicate dictionary**. Those are required before estimating division, death or state-exit hazards. This audit separates primary-source interpretation from independently checked numeric patterns; it does not fit biological event rates or change the earlier published simulations.

The [structured dictionary](source-dictionary.json) distinguishes affirmative source statements, generic software conventions, independent structural observations and unresolved fields. The input is the [publisher's Figure 1 workbook](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-03796-6/MediaObjects/41586_2021_3796_MOESM8_ESM.xlsx), SHA-256 `a53fe57483b0e55a3b2545f611ff2cf2a31338b8c9dffad0f9af1522222d8f7c`. Root's separate [structural audit](workbook-structure.json) and [encoding checks](encoding-checks.json) verify the numeric arrays.

| Field needed | Source-supported status | What remains unresolved |
|---|---|---|
| Observation time | Imaging intervals change from 10 to 20 to 60 minutes; Figure 1b spans 14 treatment days | Mapping each spreadsheet column to elapsed time, resampling and actual start/stop times |
| Division values | Values 0–7; 1,668 nondecreasing unit increments; five initial ones | Study-specific cumulative transformation, initial-state meaning and missing-observation handling |
| Death values | Manual death annotation is reported; numeric rows start at zero and either stay zero or switch once to persistent one | Biological/missing-observation semantics, coverage and exact transition times in this export |
| Row population | Figure legend reports 1,135 lineage paths and a 77-lineage persister subset | Original eligible-founder denominator, merge/deduplication and inclusion probabilities |
| Cycle times | Different untreated/persister interval rules; displayed unit is hours | Censoring-code meaning and row-to-lineage join |
| Independence | Cells belong to tracked lineages; broader experiment replication is reported | Movie/field/well/date identifiers for every row |

## Time cannot be reconstructed from column count alone

The [author manuscript's imaging methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC9209846/) specify 10-minute acquisition during the first 24 hours, 20-minute acquisition during hours 24–120, and hourly acquisition afterward. Nonpersister tracking starts at the movie beginning. Persisters are first traced backward from the final frame to their founders, then one path is followed forward. The untreated cycle interval is first-to-second mitosis; persister intervals begin with the first mitosis after 72 treatment hours and subsequent mitoses are averaged.

**Our consistency calculation**, assuming exact observation from 0 through 336 hours with a single copy of each boundary, gives `1 + 24×6 + 96×3 + 216 = 649` frames. It does not give 2,025. Conversely, 2,025 uniformly spaced ten-minute points span 337⅓ hours. Neither calculation proves the export uses that grid. A resampled matrix, padded timeline or different actual movie limits could explain the discrepancy; none is established by the inspected sources.

The ten-page [Supplementary Information](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-03796-6/MediaObjects/41586_2021_3796_MOESM1_ESM.pdf) was searched directly. It contains additional methods and transcriptomic lineage analyses, but no identified Figure 1b time-vector/export dictionary. The transcriptional time course at days 0/3/7/14 is a separate experiment and cannot supply microscopy frame times.

## Selection is documented, but the sampling denominator is not

Methods explicitly describe random sister choice for forward-tracked nonpersisters. For persisters, final-frame cells identify founders retrospectively; only one forward path per lineage/timepoint is then retained. Extended Data Figure 1b says the founder is tracked forward “as in a.” This supports forward re-tracking, but does not certify its exact sister-selection algorithm or whether retained paths were required to survive.

The crucial distinction is between selecting a founder because **some descendant survives**, selecting a **surviving ancestral path**, and selecting a **new random forward path** from that founder. These designs have different conditional distributions. The paper's effort to avoid overrepresenting large progenies does not itself supply the inclusion probability of each founder or branch. A generic software sampler also does not establish which study-specific rule was used.

The Figure 1b legend reports 77 persister lineages. The workbook's Figure 1d table has the explicit header `viability(0_persister)` and 80 zero entries. Independently, the death matrix ends with 80 zeros. These counts require reconciliation with the figure subset; the table's label does not certify death-matrix semantics or a row join. No intended correction, source error or biological explanation is inferred.

## Numeric patterns narrow the encoding possibilities

The [pinned encoding checks](encoding-checks.json) establish that the division matrix never decreases and contains exactly 1,668 unit increments between adjacent columns, with no larger positive step. Five rows already contain one in the first column. Those values are consistent with cumulative counts; raw isolated binary event spikes cannot explain the 0–7 monotone array. However, the study-specific transformation, ancestral-history handling and meaning of the five initial ones remain unresolved. **The 1,668 increments are a structural count, not a certified biological event total.**

Every death row begins at zero. Exactly 1,055 rows switch once from zero to one and retain one; 80 remain zero. This proves a persistent numerical step pattern, but not that all zeros represent observed living cells or that the transition column gives a source-certified event time. There are no division increments after a prior-column death code of one; that compatibility does not establish the biological codebook or an at-risk mask.

The Figure 1d table has the same 1,135 rows and 80/1,055 zero/one counts as the terminal death column, yet **146 values differ when compared by position**. All mismatch positions are retained in the [structured dictionary](source-dictionary.json) and root's check file. This is direct evidence that matching table dimensions and aggregate counts cannot authorize a positional join. It does not identify a permutation, mislabeled record or correction. Explicit source row identities and selection/export rules are still needed.

## What the official tracking code establishes—and what it does not

The paper links [p53CinemaManual](https://github.com/balvahal/p53CinemaManual). We inspected its official code and recorded individual Git blob hashes in the JSON. The Oren-specific code version and plotting/export calls were not located.

- [getDivisionMatrix](https://github.com/balvahal/p53CinemaManual/blob/master/quantificationScripts/getDivisionMatrix.m) creates a zero-filled array and marks recorded event centroids with one. A zero is consequently an absence of an event annotation in that generic array, **not an observation or alive-at-risk flag**.
- [accumulatedDivisionMatrix](https://github.com/balvahal/p53CinemaManual/blob/master/analysisScripts/accumulatedDivisionMatrix.m) converts event indicators into stepwise cumulative counts. This matches the verified monotone 0–7 pattern in form, but matching a pattern does not prove the study used that function or establish initial-state handling.
- [The lineage-aware export](https://github.com/balvahal/p53CinemaManual/blob/master/quantificationScripts/getDatasetTraces_fillLineageInformation.m) separately retains raw/filled division and death arrays, traces, coordinates, `lineageTree` and `cellAnnotation` containing group, position and cell ID. Its generic death-event array uses the same event builder as divisions.
- [Lineage filling](https://github.com/balvahal/p53CinemaManual/blob/master/quantificationScripts/fillLineageInformation.m) can copy ancestral trace history between branches. Filled arrays must not automatically be treated as independent event histories.
- [A tabular export](https://github.com/balvahal/p53CinemaManual/blob/master/quantificationScripts/centroids2table_withCellFates.m) can retain `cell_id`, position, `timepoint`, division and death indicators. [Image-database construction](https://github.com/balvahal/p53CinemaManual/blob/master/fileManaging/createDatabaseFile.m) parses a frame identifier from filenames; it does not turn that identifier into a documented elapsed-time vector.

These functions identify the useful missing companion files: original annotation objects, the image/timestamp database, lineage/identity arrays, row-selection indices and the study-specific export script. The [Watermelon repository](https://github.com/yaaraore/Watermelon) instead exposes barcode-processing scripts and transcriptomic RDS pointers; its inspected inventory and public issues did not resolve the microscopy export. No large RDS was downloaded.

## Censoring and replication remain separate gaps

The [publisher's Figure 1c](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-021-03796-6/MediaObjects/41586_2021_3796_Fig1_HTML.png) was visually checked: mean cell-cycle time is measured in hours, and the ordinate is non-division probability. That verifies the displayed unit, not the meaning of numeric `censoring_status` values in the workbook. The source does not establish here whether 0 or 1 denotes censoring, how an incomplete cycle is timed, or how tracking loss is distinguished from administrative follow-up.

The image-based [Reporting Summary](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-03796-6/MediaObjects/41586_2021_3796_MOESM2_ESM.pdf) was checked using OCR. Its broad replication statements cannot assign 1,135 microscopy paths to independent biological experiments. In particular, single-cell sequencing replicate counts must not be transferred to these movie rows. The workbook lacks a verified movie/field/well/date join.

The next gate is a **jointly consistent dictionary**: timestamps, event transformations, observation masks, chosen-path sampling, row identities, replicate membership and censoring. Until then, structural checks and explicitly synthetic selection demonstrations are justified; an unconditional population hazard or post-withdrawal state-exit estimate is not supplied by this audit. Public source access and the generic repository's lack of a verified licence also do not authorize mirroring their raw files or code.
