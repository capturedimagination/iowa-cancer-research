# Statewide industrial data: definitions and usable snapshots

Research snapshot: October 22, 2026. The files below are reference inputs for later analysis, not evidence that any facility caused a cancer case.

## TRI reporting history, 1987-2024

Downloaded all 38 Iowa annual basic files from EPA's public endpoint, preserving 60,040 chemical-report records. Each original file has a URL, row count, byte count and SHA-256 hash in `industries/tri-history-manifest.json`. The source page reported forms processed through November 5, 2025. This is a retrieved version of historical reporting, including subsequent revisions, not a reconstruction of what was publicly known in each historical year.

Official source and documentation: https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present ; https://www.epa.gov/system/files/documents/2025-09/basic_data_files_documentation_august_2024.pdf .

The 2024 snapshot contains 1,695 forms, 463 unique TRI facility IDs and 22 reported sectors. There are 285 Form A certifications, which do not quantify releases. Sixteen rows use grams for dioxins; other rows use pounds. Derived files keep those units separate. Four facilities have multiple primary NAICS codes across their chemical forms, and three span more than one reported sector. These variations are retained rather than silently selecting a first value.

The raw EPA export fills Form A release fields with numeric zeros; those values are certification placeholders, not quantified zero releases. The extraction script excludes Form A from release sums and counts them separately. It writes blank quantitative fields when a group has no Form R records in that unit, including **37 facilities with only Form A**; actual release quantities for those facilities remain unknown. Another 74 facilities mix Form A and Form R. For modeling, retain raw values and form type, map Form A quantities to null/unquantified, and interpret aggregate values as sums of quantified Form R records rather than complete facility emissions.

Reported 2024 total releases sum to approximately 34.77 million pounds; air releases approximately 18.43 million pounds. Rows carrying EPA's OSHA carcinogen flag account for approximately 1.98 million pounds total and 1.69 million pounds to air. These are chemical quantities under a reporting classification, not uniform toxic potency, human exposure, cancer incidence or an IARC Group 1-only total. The original gram quantities remain separate.

### Required interpretation before modeling

TRI covers listed chemicals, specified activities/sectors and reporting thresholds. A missing facility-year is not zero exposure. Chemical lists, thresholds, exemptions, sectors, ownership and reporting practices change over time; a sum of all chemicals is not automatically a comparable time series. Form A, reported numeric zero, estimated quantity and nonreporting must remain distinguishable. A numeric Form R value is not necessarily a direct measurement. Metal categories do not identify every chemical species or valence.

On-site air, surface-water releases, land disposal, off-site disposal and waste treatment/recycling are distinct pathways. Total waste managed is not a synonym for releases. A transfer to treatment is not proof that its entire quantity reached a person's drinking water. Coordinates and FRS identifiers can reflect updated registry information; historical residential or workplace exposure requires additional reconstruction.

## Iowa DNR 2024 Title V inventory

The food/ag-processing subtask extracted all 283 facilities from the actual 2024 Point Source Emissions Summary, dated February 25, 2026. Its reported total HAP quantities sum to **5,483.81 tons**, matching the rounded report total. The PDF says "tons" without explicitly defining short tons versus metric tonnes; no conversion is justified from this document alone. It uses DNR facility identifiers and annual 2024 inventory quantities, not TRI IDs or TRI pounds. The 2026 publication date is not the emissions year. Source: https://www.iowadnr.gov/media/2277/download?inline= .

This is a different reporting population and pollutant scope from TRI. PM2.5 can be a subset of PM10, and HAP/VOC/PM categories overlap; they must not be added into a purported total toxic dose. The inventory does not quantify all mobile, small-source, household or occupational exposures. The source-specific memo documents extraction and validation.

## 2020 AirToxScreen model

Archived EPA's original national state/county workbooks and extracted Iowa records for all 99 counties, separately by pollutant and source group. This is a modeled lifetime inhalation-risk framework using 2020 emissions and assumptions, not observed cancer cases or an annual cancer rate. Source: https://www.epa.gov/AirToxScreen/2020-airtoxscreen-assessment-results .

The state total is reported as 20 per million after EPA's one-significant-figure rounding. Source/pollutant components retain numerical model precision; their sum need not equal the rounded displayed total. Do not report component decimals as that degree of scientific certainty. Formaldehyde is the largest modeled pollutant contributor; secondary atmospheric chemistry is the largest source grouping. Secondary formation cannot be assigned directly to one industry without precursor/source attribution.

EPA does not quantify diesel particulate cancer risk in this model because it has not adopted a cancer unit risk estimate. Small diesel-related source entries for other pollutants must not be interpreted as proving diesel exhaust unimportant. The model also is not a complete accounting of radon, indoor/workplace exposures, ingestion or historical cancer-generating exposure. FAQ and limitations: https://www.epa.gov/AirToxScreen/airtoxscreen-frequent-questions ; https://www.epa.gov/AirToxScreen/airtoxscreen-limitations .

The current NEI data page lists the 2023 NEI and 2023 facility summaries, whereas the retrieved AirToxScreen assessment uses 2020. Do not infer that the newest emissions inventory automatically has a corresponding completed cancer-risk assessment. https://www.epa.gov/air-emissions-inventories/get-air-emissions-data-0 .

## RSEI and regulatory records

RSEI toxicity/exposure/population-weighted scores can prioritize follow-up, but are not observed cases or individual cancer probabilities. EPA recommends verifying release records, speciation, stack parameters and other assumptions before drawing local risk conclusions. https://www.epa.gov/rsei/how-rsei-should-be-used .

An emission permit is not an exposure measurement; an enforcement finding is not a cancer outcome; a Superfund listing is not proof of an active completed exposure pathway. For each future claim, retain the source record type and date instead of combining them into a single "pollution" variable.

## Local files and reproducibility

- `sources/industries/tri-history/`: 38 untouched annual CSVs.
- `research/industries/tri-history-manifest.json`: annual provenance and hashes.
- `research/industries/tri-2024-iowa-*.csv`: facilities, sectors, chemicals and all carcinogen-flagged records.
- `sources/industries/statewide/`: original 2024 TRI download and four national AirToxScreen workbooks.
- `research/industries/airtoxscreen-2020-iowa-*.csv`: all Iowa state/county extracts.
- `research/industries/statewide-industry-data-provenance.json`: definitions and transformations.
- `scripts/fetch_iowa_tri_history.py` and `scripts/analyze_industry_records.py`: retrieval and extraction logic. Refreshes must retain old snapshots and record new versions.
