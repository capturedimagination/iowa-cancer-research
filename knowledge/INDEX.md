# Iowa cancer reference library

Library extended **November 10, 2026** with verified malignant-cell expression data and an independent lung-cancer signature comparison. The clinical benchmark remains the October 29 analysis; the Iowa surveillance/environmental compilation remains the **October 22, 2026** snapshot. Individual sources retain their own dates. This folder is the starting point for future research, data work and model design. Rebuilding its index does not refresh the underlying sources.

## Find evidence for a question

| Question | Start here |
|---|---|
| Statewide rates, national comparisons, apparent rankings or trends | [Epidemiology](../research/epidemiology.md), [data dictionary](../research/data-dictionary.md), original NCI downloads in `research/sources/` |
| County differences | [99-county summary](../research/iowa-99-counties-comparison.csv), then exact population, cancer site and observation window in the original export |
| Nitrate, pesticides, radon, PFAS, farms, water or outdoor air | [Environmental research](../research/environment.md) and [dataset catalog](../research/data-source-catalog.md) |
| Foundries, metalworking, rubber, wood products, vehicles, electronics or sterilization | [Manufacturing](../research/industries-manufacturing.md) and [25 evidence records](../research/industry-manufacturing-evidence.csv) |
| Ethanol, grain, soy, fertilizer, meat or poultry | [Food and agricultural processing](../research/industries-food-agprocessing.md) and [32 evidence records](../research/industry-food-agprocessing-evidence.csv) |
| Fuel, power, rail, coal ash, mining, nuclear work, dry cleaning or legacy sites | [Energy and legacy industries](../research/industries-energy-legacy.md) and [25 evidence records](../research/industry-energy-legacy-evidence.csv) |
| Healthcare, pharmacy, funeral work, salons, cleaning, night shifts or product consumption | [Services](../research/industries-services.md) and [11 evidence records](../research/industry-services-evidence.csv) |
| Facility inventories or modeled air risks | [Statewide industry data](../research/industries-statewide-data.md), original snapshots and the SQL tables below |
| Screening, care, prevention, policy or disparities | [Prevention and care](../research/prevention-care.md) |
| Choosing or fitting a statistical model | [Methods](../research/modeling-methods.md), [readiness checklist](../research/model-readiness-checklist.md), [dataset catalog](../research/data-source-catalog.md) |
| Treatment discovery, response or resistance | [Latest molecular findings](../research/treatment-discovery/updates/2026-11-10/README.md), then [lung cancer research program](../research/treatment-discovery/README.md). Keep the clinical TMB benchmark and EGFR residual-state analysis separate. |
| Individual exposure histories, cohort data or occupational coding | [Cohort access](../research/cohort-data-access.md), [occupational data systems](../research/manufacturing-input-datasets.csv); access metadata do not imply individual records are held here |
| Narrative orientation | [Original research report](../Iowa-Cancer-Research.md); the later industry and modeling work is in this library |

## What is actually saved

| Material | Coverage | Important boundary |
|---|---|---|
| Cancer surveillance | All 99 Iowa counties, state comparisons, selected sites and demographic groups | Incidence 2019–2023 and mortality 2020–2024 are different windows. Rounded average annual counts are not exact period counts. |
| EPA TRI originals | **60,040 chemical forms, 1987–2024**, all 38 annual Iowa files; 2024 has **463 facilities across 22 reported sectors** | Reporting history is not a harmonized exposure panel. Missing facility-year is not zero. |
| DNR Title V inventory | **283 facilities**, 2024 emissions published February 2026 | PDF says “tons”; ton basis is unconfirmed. Pollutant columns overlap. |
| EPA AirToxScreen | 2020 modeled cancer-risk components for all 99 counties and Iowa | Excess lifetime risk per million, not annual cancer incidence, personal dose or current measurement. |
| Industry evidence | **93 records** in four sector families | Multiple records may refer to the same study, cohort or site; record count is not independent-study count. |
| Historical workplace measurements | 19 selected values/summaries plus a complete 17-sample Winnebago table | Seven samples overlap between files; summary endpoints and means are not independent samples. |
| AHS public materials | Blank coded enrollment instrument, collaboration policy and 46 cancer-summary rows through 2021 | Tables combine Iowa and North Carolina; follow-up/sample subsets overlap. No participant records or Iowa-only denominator. |
| Treatment research extension | Public 240-person NSCLC clinical benchmark; versioned preclinical metadata; verified original 3,754-malignant-cell object; independent 457,724-nucleus cohort and fixed 26-untreated/9-residual-patient expression comparison | Molecular originals remain local with public provenance. Direction reverses by small kit stratum, with major stage/site/batch imbalance. Separate non-Iowa data, endpoints and patient/model units. No causal treatment effect, target validation or cure result. |
| Source corpus | Memos, references, dataset metadata, archived PDFs and raw federal/regulatory files | Access and extraction limits remain visible; not every cited web page is archived in full. |

The verified catalog records access requirements and whether data are actually saved locally. A catalog entry is not proof that its observations are available locally.

## Search and retrieve

The rebuildable SQLite database is generated locally at `knowledge/research.sqlite` and is not committed to the public repository. [Publication instructions](../PUBLICATION.md) explain how to build the public subset. [Build manifest](build-manifest.json) records integrity checks, source counts and the database hash for its stated snapshot. [PDF extraction log](pdf-text-extraction-log.json) distinguishes native extraction, partial/empty text, OCR sidecars and failures in the original local archive. Extracted text is a search aid; check the original page for numeric tables and methods.

Run from the project folder with Python 3:

```sh
python3 scripts/query_research.py search "formaldehyde"
python3 scripts/query_research.py search "healthy worker"
python3 scripts/query_research.py record "energy_legacy:EL001"
python3 scripts/query_research.py tables
python3 scripts/query_research.py sql "SELECT reporting_year, unit_of_measure, form_type, forms, reporting_facilities FROM tri_reporting_coverage WHERE reporting_year=2024"
python3 scripts/query_research.py sql "SELECT trifd, facility_name, chemical_name, reported_air, unit_of_measure, source_file, source_row FROM tri_forms WHERE reporting_year=2024 AND chemical_name LIKE '%ethylene oxide%'"
```

Search terms are matched together. The CLI opens the database read-only and returns JSON. Search includes historical TRI facility names, aliases and reported chemicals; inventory matches are lookup pointers, not health findings. Database filenames and CSV record numbers point back to saved originals. `source_row` counts logical CSV records including the header; an embedded newline can make physical line numbers differ.

## Database tables

| Table | Grain and use |
|---|---|
| `tri_forms` | All 60,040 raw forms with selected numeric convenience fields and **every original field retained in `raw_record_json`**. Original Form A zero placeholders map to SQL `NULL`. |
| `tri_reporting_coverage` | Form and reporting-facility counts by year, unit and form type. Coverage check, not an emissions trend. |
| `county_cancer_summary` | 99 descriptive county rows; original columns imported as text. |
| `title_v_facilities` | 283 DNR facility records; original units and IDs retained. |
| `airtox_risk_values` | Long-format source-group and pollutant risk components, plus displayed totals, for counties/state. `poll` and `srcgrp` are alternative decompositions; do not sum across them. |
| `manufacturing_measurements`, `winnebago_dust_samples` | Selected historical measurements and complete sample table, kept separate because samples overlap. |
| `ahs_public_cancer_summary` | Public AHS site/group counts, with overlapping subset columns and original qualifiers; not a participant or Iowa-only data file. |
| `cancer_site_summary`, `demographic_summary` | Source-defined comparisons and quality flags. |
| `evidence` | Normalized lookup fields plus the complete original evidence record in JSON; no invented certainty score. |
| `datasets`, `references_catalog` | Core catalog, occupational/cohort supplements and source references; overlapping resources are retained with their provenance. |
| `documents`, `search_index` | Searchable memos, archived PDF text, PubMed abstracts, evidence metadata and historical inventory-facility aliases; source paths and extraction status. |
| `files`, `table_notes`, `metadata` | Input hashes, table-specific units/keys/limits, source cutoff and build version. |

SQLite `REAL` values are convenient for exploration, not lossless decimal storage. Retrieve exact strings from `raw_record_json` or source CSV when exact arithmetic matters. Imported comparison and measurement CSV fields remain text to preserve suppression flags, qualifiers and original formatting. Parse those flags explicitly before numeric analysis: SQLite can silently cast a nonnumeric string to zero.

## Rules for future analysis

1. Specify cancer site, population, geography, period, exposure route and target question before selecting a model. An all-cancer county ranking cannot identify a facility or chemical cause.
2. Keep **hazard classification, inventory mass, measured concentration, modeled dose/risk, observed cancer, and causal inference** separate. A carcinogen flag is not a potency weight.
3. Preserve identifiers as text: five-digit county FIPS, TRIFD, FRS ID and DNR facility ID are different keys. Facility names and present-day owners are not reliable historical crosswalks. Offsite waste destinations are not automatically the originating county.
4. Use exact cancer counts, matching person-time/expected counts, strata and uncertainty for count models. Do not reverse-engineer population from age-adjusted rates or multiply rounded average annual counts into exact observations.
5. Resolve suppression, reporting eligibility, chemical-list/threshold changes, absent years, unit differences and duplicate samples before making an analysis panel. Never silently impute missing releases to zero.
6. Choose exposure lags and covariates from cancer biology and study design. The current county rates cannot establish the effect of current emissions; residential county does not identify workplace or lifetime residence.
7. Plan confounding control, spatial dependence, uncertainty, multiplicity and geographic/time validation before choosing associations to highlight. PLACES modeled estimates require their own dependence and trend cautions.
8. Cite the source and its actual observation dates. Refresh drift-prone releases, classifications, facility status and policy before answering a current-status question. Preserve dated snapshots rather than overwriting originals.
9. Report what was observed, estimated or unavailable. A non-detect has a detection limit; it is not automatically zero. A completed cleanup, compensation designation or closure notice has a specific evidentiary scope.

No causal environmental model or clinical treatment-selection model has been fitted. A separate [retrospective clinical biomarker benchmark](../research/treatment-discovery/results/nsclc-tmb-dcb-2026-10-29/RESULTS.md) calculates rank discrimination without training a model. The [readiness checklist](../research/model-readiness-checklist.md) identifies missing inputs for environmental models; treatment work has its own protocols and timing/unit requirements.

## Rebuild

`scripts/build_knowledge_base.py` imports saved inputs, checks hashes and counts, indexes available research text, validates SQLite integrity and replaces the derived database only after those checks pass. Use the Python setup in [PUBLICATION.md](../PUBLICATION.md); ordinary Python 3 can run the read-only query tool. Original-PDF indexing applies only when those files are available locally. The build does not download updates, alter originals, fit a model or publish anything.

For data updates, retain a dated source snapshot, record the query, retrieval date, original units and hash, rerun the relevant extraction script, update the catalog and methodological notes, then rebuild. The original PDF report remains a dated overview rather than an automatically updated representation of this entire corpus.
