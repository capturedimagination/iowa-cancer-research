# Iowa cancer research

Public research snapshot prepared November 3, 2026. [Publication scope and reproduction](PUBLICATION.md) explains source availability, dependencies and licensing. All original findings and analyses are included; cached originals with unclear redistribution rights are represented by their citations and provenance.

Core compilation October 22, 2026. Treatment research added October 29, 2026. **Start with the [reference-library guide](knowledge/INDEX.md)** for future questions, data work and model design. The original report is a dated narrative overview; later research extends beyond it.

- [Lung cancer treatment research](research/treatment-discovery/README.md): completed retrospective clinical benchmark, molecular data feasibility and a defined resistance question

- [Searchable research database and usage](knowledge/INDEX.md#search-and-retrieve)
- [Dataset catalog and access status](research/data-source-catalog.md)
- [Cohort data and access routes](research/cohort-data-access.md), including AHS and Iowa Women's Health Study
- [Modeling methods](research/modeling-methods.md) and [data-readiness checklist](research/model-readiness-checklist.md)
- [Statewide industry data](research/industries-statewide-data.md): 38 years of TRI originals (60,040 chemical forms), 2024 DNR Title V inventory, and 2020 AirToxScreen Iowa extractions
- Industry research: [manufacturing](research/industries-manufacturing.md), [food and agricultural processing](research/industries-food-agprocessing.md), [energy and legacy sites](research/industries-energy-legacy.md), [services](research/industries-services.md); 93 indexed evidence records

No causal environmental or clinical treatment-selection model has been fitted. The clinical benchmark is a retrospective rank-association calculation. Catalogs distinguish saved inputs from resources identified for future access. The workspace `AGENTS.md` directs future work to this library.

## Original overview

- [Read the 19-page PDF](output/pdf/Iowa-Cancer-Research-2026-10-22.pdf)
- [Editable report with linked citations](Iowa-Cancer-Research.md)
- [Core source index: 74 references](research/source-index.csv)
- [All 99 Iowa counties: incidence, mortality, confidence intervals and trends](research/iowa-99-counties-comparison.csv)
- [Cancer-type comparisons](research/iowa-cancer-types-comparison.csv)
- [Demographic comparisons](research/iowa-demographic-comparison.csv)
- [Data definitions and limitations](research/data-dictionary.md)

## Detailed research

- [Epidemiology: rates, rankings, age, race, geography and data reconciliation](research/epidemiology.md)
- [Environmental, agricultural and occupational evidence](research/environment.md)
- [Prevention, screening, access, care and policy](research/prevention-care.md)
- [Synthesis methods and access limitations](research/synthesis-methods.md)
- [Additional source links from the memos](research/additional-source-links.csv)
- [Selected risk-evidence comparison](research/risk-evidence-matrix.csv)

## Data and original sources

Current federal incidence covers **2019-2023**; mortality covers **2020-2024**. The annual registry's **2026 projections** are separate. County tables include every county, with no deduplication or removal of unusual records. The combined county comparison has exactly 99 rows; the individual county tables also retain Iowa and U.S. reference rows.

Original federal downloads, including their source footnotes, are in `research/sources/`. Download/query provenance is in [data-provenance.json](research/data-provenance.json). Selected original public-health and policy PDFs are in `sources/` and `sources/environment/`. Some university-hosted reports blocked direct downloads; the report identifies where only indexed material or an attributed clinical summary was available. An anomalous pediatric export is flagged in the cancer-type CSV and excluded from interpretation.

## Rebuild and verification

The scripts use the bundled Codex Python/ReportLab runtime and local fonts. `scripts/build_report.py` regenerates the PDF from the editable report. `scripts/prepare_compilation.py` regenerates the source index/register. They do not refresh live cancer data.

`scripts/build_knowledge_base.py` rebuilds the searchable library from saved CSV, JSON, Markdown and source PDFs, with source hashes and integrity checks. `scripts/query_research.py` provides read-only search/SQL retrieval. See the [library guide](knowledge/INDEX.md) for table definitions, examples and modeling limits.

The finished PDF was rendered and visually checked on all 19 pages. Core figures were checked against the saved originals, the 99-county join was verified, references were checked for valid numbering, and the PDF contains clickable source links and section bookmarks. Verification details are in [quality-checks.json](research/quality-checks.json).

The review is broad, not a formally registered systematic review. It is not an individual medical assessment, household water/air test or definitive cancer-cluster investigation.
