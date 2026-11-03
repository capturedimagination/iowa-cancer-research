# Primary data-source catalog for future Iowa cancer models

Snapshot: October 22, 2026. The JSON companion is the canonical structured catalog. This is a source and method index, not a merged causal dataset. Documentation and links were verified; not every remote table or access path was downloaded/tested. A related archived report is distinguished from a downloaded dataset.

Local status and paths below describe the dated research workspace. The public copy excludes some cached sources and generated files; [publication/source-manifest.json](../publication/source-manifest.json) records availability and upstream source links. An excluded file may still be present in the original local workspace.

Archived State Cancer Profiles incidence is 2019-2023 and mortality 2020-2024. USCS June 2026 tables extend incidence through 2023. UCMR 5's final dataset was released August 2026. USGS final 2018-2022 pesticide estimates are planned for December 2026, after this cutoff. The 2025 ACS 1-year release is scheduled October 29, 2026, also after cutoff. Use each source's data period rather than its publication year.

## Join and model rules

- Freeze each source's release date, data years, query, dictionary and original hash. Publication year, exposure year, diagnosis year and death year are separate fields.
- Define cancer site, age, sex/race, stage, rate type, population and latency before joining. Incidence, mortality, survival, prevalence and projected counts are different endpoints.
- Keep geography and residence time explicit. Diagnosis residence, death residence, workplace, water-service area, county farm production, ZIP, ZCTA, tract and custom zone are not interchangeable.
- Use source IDs as text with leading zeros. Require a reviewed FRS/TRI/DNR crosswalk; do not infer shared identity from similar names or numeric-looking IDs.
- Keep suppressed, unmeasured, not reported, below detection and zero separate. Preserve reporting limits, qualifiers, confidence intervals and unstable-rate flags.
- Use chemical-specific units and matrices. Nitrate-as-N versus nitrate-as-NO3 differs by 62/14; do not convert without basis. TRI pounds/grams, DNR tons, air ug/m3 and water ng/L are not one common exposure score.
- Do not add overlapping pollutant components or combine measured concentration, emitted mass and modeled risk as equal quantities. HAP is a regulatory list, not a uniform carcinogen category.
- Use lagged exposure windows and sensitivity analyses chosen from biology/history. Current facility status cannot reconstruct 1980-2000 exposure, and county residence cannot reconstruct a worker's job history.
- Age-adjusted rates are for comparison, not simple additive quantities. For modeling, obtain valid counts, age-specific denominators and uncertainty; avoid regressions on unstable rounded rates alone.
- PLACES and CAMSA are modeled products. Their predictors/smoothing can induce associations and shared measurement structure. Do not treat predictions as independent validation or direct local trends.
- TRI history is not yet a harmonized exposure panel. Sector/list/threshold changes, revisions, ownership, missingness and spatial relocation require explicit treatment before trend or health models.
- An ecological association cannot identify an individual's cause or a facility's attributable cancer count. Negative or absent data are evidence gaps, not proof of zero risk.

## Cancer outcomes

### OUT-01: State Cancer Profiles

Publisher: NCI/CDC. [Source 1](https://statecancerprofiles.cancer.gov/); [Source 2](https://statecancerprofiles.cancer.gov/incidencerates/index.php?stateFIPS=19&areatype=county&cancer=001&race=00&sex=0&age=001&type=incd&year=0&sortVariableName=rate&sortOrder=desc&output=1).

**Coverage/time:** US states and counties; Iowa 99 counties. Archived live incidence 2019-2023; mortality 2020-2024. Trend intervals are distinct and query-specific.

**Grain/joins:** Geography x cancer site x sex/race/age/stage filter x rate/trend window. Keys: 5-digit state/county FIPS as text; Cancer/site recode; Exact demographic filters and window.

**Units/access:** Cases/deaths per 100,000, average annual counts, AAPC percent, CIs/rank intervals. Public CSV through output=1; preserve preamble/footnotes and exact query URL.

**Use/limits:** Primary comparable county/state summaries, subgroups, trends. Suppression and unstable small-area rates; rank uncertainty; age adjustment. Search caches still display older 2018-2022. Incidence and mortality are different outcomes.

**Local status:** `downloaded_query_extracts`. `research/source-index.json`; `research/sources/iowa-county-incidence-nci-original.csv`; `research/sources/iowa-county-mortality-nci-original.csv`; `research/iowa-county-incidence-2019-2023.csv`.

### OUT-02: USCS Data Visualizations downloadable tables

Publisher: CDC/NCI. [Source 1](https://www.cdc.gov/united-states-cancer-statistics/dataviz/data-tables.html); [Source 2](https://www.cdc.gov/united-states-cancer-statistics/technical-notes/pdf/uscs-data-visualizations-tool-technical-notes-2023-june-508-final.pdf).

**Coverage/time:** United States/state and available county outputs. June 2026 release; diagnosis years 1999-2023. CDC reports latest incidence 2023 and mortality 2024; inspect endpoint-specific file.

**Grain/joins:** Preanalyzed geographic/demographic/site/year or pooled-period cell. Keys: Geographic code; Site; Sex/race/age; Year/window.

**Units/access:** Counts; crude and age-adjusted rates per 100,000; intervals. Public delimited ASCII/Excel packages; no case-level linkage to identify people.

**Use/limits:** Reproducible federal tabulations and cross-source comparison. Suppression/publication rules and registry coverage vary by year. Projected estimates are separate from observed registry cases. A release year is not diagnosis year.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### OUT-03: USCS public-use and restricted-access incidence databases

Publisher: CDC NPCR/NCI SEER. [Source 1](https://www.cdc.gov/united-states-cancer-statistics/public-use/); [Source 2](https://www.cdc.gov/united-states-cancer-statistics/public-use/pdf/uscs-public-use-database-technical-documentation-2001-2023-final-508.pdf); [Source 3](https://www.cdc.gov/cancer/data/).

**Coverage/time:** Qualifying US registries; public-use does not provide county at diagnosis. Current technical documentation 2001-2023.

**Grain/joins:** Cancer case record with permitted clinical/demographic variables. Keys: Registry/geography allowed by product; Diagnosis year; Site/morphology/stage variables.

**Units/access:** Case-level coded variables; population denominators for rates. SEER*Stat access/account/data agreement; restricted-access adds county and other fields through approved process.

**Use/limits:** Subtype/stage/demographic analysis after permitted access. Not an unrestricted patient download. Cases are tumors, not necessarily unique people. County cannot be assumed available in public-use data. No residential history or direct exposure variables.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### OUT-04: SEER Research and Research Plus

Publisher: National Cancer Institute. [Source 1](https://seer.cancer.gov/data-software/); [Source 2](https://seer.cancer.gov/data/access.html); [Source 3](https://seer.cancer.gov/data-software/documentation/seerstat/nov2025/TextData.FileDescription-nov2025.pdf); [Source 4](https://seer.cancer.gov/registries/iowa.html).

**Coverage/time:** SEER registry areas, including Iowa; not all US. Nov 2025 submission/April 2026 documentation: 1975-2023; coverage depends on registry/database.

**Grain/joins:** Tumor/case record with registry, diagnosis, clinical and follow-up variables. Keys: Registry; Allowed county variable; Diagnosis year; Site recode; Patient/tumor IDs only within approved product.

**Units/access:** Coded cases; survival; counts/rates using compatible populations. Personal registration and data agreement. Research Plus requires eRA Commons/HHS authentication and additional eligibility. SEER*Stat is Windows software.

**Use/limits:** Iowa longitudinal subtype/survival analyses with correct product and denominator. Changing registry coverage; Research versus Plus variables differ; Iowa registry began 1973 but current standard research series says 1975 onward. No unauthorized cross-dataset identification.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### OUT-05: Iowa Cancer Registry research/data request route

Publisher: University of Iowa/Iowa Cancer Registry. [Source 1](https://shri.public-health.uiowa.edu/research/); [Source 2](https://shri.public-health.uiowa.edu/cancer-data/reports/iowa-cancer-reports/); [Source 3](https://hhs.iowa.gov/about/data-reports/cancer-data).

**Coverage/time:** Iowa residents at diagnosis; statewide registry since 1973. Registry historical series since 1973; custom approved release determines end year; annual 2026 report includes 2026 projections.

**Grain/joins:** Registry cancer case and approved aggregate tables. Keys: Approved registry keys; Diagnosis date/site; Residence geography under approved agreement.

**Units/access:** Cases, rates, clinical characteristics; annual projections separately labeled. Public summaries; more detailed data require registry review/application and applicable privacy/research approvals.

**Use/limits:** Best route for specific historical Iowa subtype/geographic questions. Public reports do not substitute for case-level research data. Preserve observed versus projected. No direct download of identifying cases or implicit approval for linkage.

**Local status:** `report_indexed_download_blocked`. `research/sources/2026-Cancer-in-Iowa-download-403.html`; `research/source-index.json`.

**Public copy exclusions:** `research/sources/2026-Cancer-in-Iowa-download-403.html` (`linked_source_only`). See the publication manifest for source links and restoration details.

### OUT-06: CAMSA and Iowa Cancer Zones

Publisher: Iowa Cancer Registry. [Source 1](https://shri.public-health.uiowa.edu/cancer-data/interactive-iowa-data-tools/); [Source 2](https://shri.public-health.uiowa.edu/camsa/); [Source 3](https://shri.public-health.uiowa.edu/camsa/assets/FAQ.pdf); [Source 4](https://shri.public-health.uiowa.edu/cancer-zones/).

**Coverage/time:** Iowa county/ZIP-level CAMSA; Cancer Zones are purpose-built larger small-area aggregations. CAMSA uses selected five-year case windows and annual updates; exact current window must be extracted from displayed/export metadata. Zones use fixed historical inputs, including 2015-2019 ACS on documented map.

**Grain/joins:** Cancer site x geographic area x selected window; modeled/smoothed rates and uncertainty. Keys: Tool-specific ZIP/zone ID; County FIPS; Boundary vintage; Cancer/site/window.

**Units/access:** Age-adjusted estimated incidence per 100,000, risk probability, uncertainty. Public interactive tools; indexed documentation accessible, direct UIowa requests intermittently 403.

**Use/limits:** Generate small-area hypotheses with uncertainty and retrieve exact methods before modeling. ZIP is not automatically ZCTA. Smoothed estimates are not raw cases or independently observed rates. Uncertainty classes are ranked standard-deviation groups, not a uniform CI. Do not assume zone/year equivalence.

**Local status:** `metadata_only`. No dataset downloaded for this catalog.

### OUT-07: Iowa Public Health Tracking cancer data

Publisher: Iowa HHS/ICR. [Source 1](https://hhs.iowa.gov/about/data-reports/cancer-data).

**Coverage/time:** Iowa state and available local/demographic groups. Portal documents 2000 through latest available; usually 3-4 year lag. Current end year must be read from actual export, not guessed.

**Grain/joins:** Cancer site x residence geography x demographic group x year/window. Keys: Geography/FIPS; Cancer site; Age/sex/race; Year.

**Units/access:** Case counts and rates per 100,000; small-count stability flags. Public portal/linked site-specific pages; February 2023 source change to direct ICR.

**Use/limits:** Iowa-specific official context and portal-defined comparisons. Address at diagnosis only; no prior residence, smoking/diet or latency. Counts represent cancers, not unique people. 2000-2016 measures may differ after source change.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### OUT-08: CDC WONDER underlying-cause mortality

Publisher: CDC NCHS. [Source 1](https://wonder.cdc.gov/ucd-icd10-expanded.html); [Source 2](https://wonder.cdc.gov/wonder/help/mcd-expanded.html).

**Coverage/time:** US/state/county residence at death. Current final Single Race series 2018-2024; older bridged-race series separate.

**Grain/joins:** Death count/rate cell by year, geography, cause and permitted demographic filters. Keys: County FIPS; ICD-10 cause group; Year; Age/sex/race/Hispanic category.

**Units/access:** Deaths, crude/age-adjusted rates per 100,000, CI/SE where available. Public query/export with data-use restrictions and suppression; preserve actual query.

**Use/limits:** Cancer mortality and competing-cause context; verify county-rate availability. Death certificates differ from incidence. 1-9 counts suppressed; current reliability/age-adjustment limits must follow current help, not older rules. Race-series/denominator comparability changes.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.


## Exposure/environment

### EXP-01: USGS county agricultural pesticide-use estimates

Publisher: USGS National Water Quality Program. [Source 1](https://water.usgs.gov/nawqa/pnsp/usage/maps/county-level/); [Source 2](https://water.usgs.gov/nawqa/pnsp/usage/maps/); [Source 3](https://doi.org/10.5066/P9EDTHQL).

**Coverage/time:** Conterminous US county estimates including Iowa. Available 1992-2017 final plus 2018-2019 preliminary. Updated Aug 19, 2026 page plans final 2018-2022 inDec 2026, after this cutoff.

**Grain/joins:** County x year x pesticide active ingredient x EPest-high/low. Keys: State/county FIPS; Year; Ingredient/compound name; Estimate type.

**Units/access:** Kilograms active ingredient/year in data releases; inspect each file dictionary. Public release links/DOIs and tables; do not use superseded archived preliminary files as current.

**Use/limits:** Historical broad exposure hypotheses and latency-aligned sensitivity analyses. Seed-treatment estimates discontinued beginning 2015. Agricultural use excludes many nonagricultural uses. High/low are estimation alternatives, not personal dose or guaranteed confidence bounds. USGS cautions against detailed specific-county comparisons.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-02: USDA Census of Agriculture and NASS Quick Stats

Publisher: USDA NASS. [Source 1](https://www.nass.usda.gov/AgCensus/); [Source 2](https://data.nass.usda.gov/Publications/AgCensus/2022/); [Source 3](https://data.nass.usda.gov/Quick_Stats/).

**Coverage/time:** US/state/county; commodity-specific publication coverage. 2022 most recent agricultural census; five-year censuses; annual survey series vary by commodity.

**Grain/joins:** County x year x commodity/practice/item/statistic/source. Keys: State/county ANSI or FIPS; Year; Commodity; Statistic/unit; CENSUS versus SURVEY source.

**Units/access:** Acres, farms, animals, production quantities, dollars and other explicit units. Public tables/CSV/bulk; Quick Stats API requires key and query limits.

**Use/limits:** Crop/livestock/practice context; acreage denominators and historical land-use covariates. Disclosure suppressions such as D are missing, not zero. Animals/inventory/sales and capacity are different. County farm production is not personal pesticide exposure or residence-based employment.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-03: EPA TRI Basic Data Iowa history

Publisher: US EPA. [Source 1](https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present); [Source 2](https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/2024_IA/csv).

**Coverage/time:** Iowa reporting facilities; selected sectors/chemical/reporting thresholds. Downloaded 1987-2024, 38 annual files, 60,040 source records.

**Grain/joins:** Facility x chemical x reporting year/form; revisions and Form A/R matter. Keys: TRI facility ID; FRS ID where populated; CAS/chemical category; Year/form; NAICS and location.

**Units/access:** Pounds for most chemicals; grams for dioxin-type entries; media-specific releases and waste management separate. Public CSV; archived source manifests/hashes.

**Use/limits:** Historical facility/agent/media inventory after harmonization. Nonreporting is not zero. Lists/thresholds/sectors/ownership change. Offsite transfers differ from onsite releases. Form A is unquantified certification. OSHA carcinogen flag is not IARC classification or potency.

**Local status:** `downloaded`. `sources/industries/tri-history/`; `research/industries/tri-history-manifest.json`; `research/industries/tri-2024-iowa-facilities.csv`; `research/industries/tri-2024-iowa-chemicals.csv`.

### EXP-04: EPA AirToxScreen

Publisher: US EPA. [Source 1](https://www.epa.gov/AirToxScreen); [Source 2](https://www.epa.gov/AirToxScreen/2020-airtoxscreen-assessment-results); [Source 3](https://www.epa.gov/AirToxScreen/airtoxscreen-frequent-questions).

**Coverage/time:** National model; 2020 block outputs and population-weighted county/state summaries. Archived 2020 cancer-risk results. Current landing page separately offers 2021 emissions/concentrations; do not assume 2021 risk release.

**Grain/joins:** Geography x pollutant or source group x modeled assessment year. Keys: FIPS/GEOID and boundary vintage; Pollutant name/code; Source group; Assessment year.

**Units/access:** Modeled lifetime cancer risk per 1 million; concentration units in specific files; hazard index separate. Public downloads; local national workbooks and complete 99 Iowa county extracts.

**Use/limits:** Prioritize chemical/source/geographic follow-up with model limitations. Screening snapshot, not observed cases or annual incidence. Model/method changes prevent simple year-over-year trend. No quantified diesel-PM cancer contribution; no radon/most indoor/occupational pathways. Secondary chemistry is not facility attribution. Rounded totals need not equal displayed components.

**Local status:** `downloaded_2020_summary_outputs`. `sources/industries/statewide/national_cancerrisk_by_county_poll.xlsx`; `sources/industries/statewide/national_cancerrisk_by_county_srcgrp.xlsx`; `research/industries/airtoxscreen-2020-iowa-county-poll.csv`; `research/industries/airtoxscreen-2020-iowa-county-srcgrp.csv`; `research/industries/statewide-industry-data-provenance.json`.

### EXP-05: Iowa DNR Title V point-source inventory

Publisher: Iowa DNR. [Source 1](https://www.iowadnr.gov/media/2277/download?inline=).

**Coverage/time:** 283 Iowa Title V facility IDs. 2024 emissions; actual PDF dated 2026-02-25 despite 2021 search metadata.

**Grain/joins:** Facility x emissions year; 9 pollutant-total columns. Keys: DNR inventory facility ID; Reviewed crosswalk to FRS/TRI/DNR site IDs; Facility names/locations with historical aliases.

**Units/access:** Report labels tons/year without explicit short/metric definition; no conversion applied. Archived PDF, complete 283 row CSV, reproduction script and provenance.

**Use/limits:** Facility coverage/process context and source-specific annual mass. Not every Iowa source; excludes mobile, biogenic, nonpoint. HAPs include noncarcinogens and overlap VOC/PM. PM2.5 is a subset of PM10. Mass is not dose/risk. Do not add to TRI.

**Local status:** `downloaded`. `sources/industries/food-agprocessing/iowa-point-source-emissions-2024-feb2026.pdf`; `research/iowa-title-v-facilities-emissions-2024.csv`; `research/iowa-title-v-2024-provenance.json`; `scripts/extract_iowa_title_v_2024.py`.

**Public copy exclusions:** `sources/industries/food-agprocessing/iowa-point-source-emissions-2024-feb2026.pdf` (`linked_source_only`). See the publication manifest for source links and restoration details.

### EXP-06: EPA AQS/AirData measured ambient pollution

Publisher: US EPA/state and local monitoring agencies. [Source 1](https://www.epa.gov/aqs/obtaining-aqs-data); [Source 2](https://aqs.epa.gov/aqsweb/airdata/download_files.html); [Source 3](https://aqs.epa.gov/aqsweb/documents/data_api.html).

**Coverage/time:** Monitor sites, not continuous coverage; Iowa network varies by pollutant/year. Historical/current hourly, daily, annual records; actual completeness/site periods vary; current year provisional.

**Grain/joins:** Site x parameter x POC x duration/method x time/standard/event treatment. Keys: State 2+county 3+site 4 AQS site ID; Parameter; POC; Sample date/time; Method/duration/standard.

**Units/access:** Parameter-specific units; preserve units, detection limits, qualifiers and completeness. Public pregenerated files; AQS API key/email registration and query limits.

**Use/limits:** Measured ambient concentration series with QA and siting context. Sparse monitors and changed sites. Multiple standards, event rules, durations can produce multiple summary rows. AQI is not a cancer metric. 2021 Iowa carbonyl report/current 2026 network differ.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-07: UCMR occurrence data, especially UCMR 5 PFAS/lithium

Publisher: US EPA. [Source 1](https://www.epa.gov/dwucmr/occurrence-data-unregulated-contaminant-monitoring-rule).

**Coverage/time:** Sampled public water systems; UCMR 5 large/all mid-size and selected small systems; not private wells. UCMR 5 scheduled 2023-2025 sampling; final dataset released Aug 2026. Older cycles 2001-2005, 2008-2010, 2013-2015, 2018-2020.

**Grain/joins:** PWS x sampling location x sample event x analyte x analytical result. Keys: PWSID; Facility/sampling point IDs; Sample ID/date; Contaminant/method; Result/unit/MRL.

**Units/access:** Analyte-specific concentration units; preserve unit field. 1 ng/L = 1 ppt in water; 1 ug/L = 1000 ng/L. Public ZIP text, state ZIPs and Data Finder. Finder Excel limit 1 million records; whole All file exceeds Excel rows.

**Use/limits:** Finished-water occurrence by chemical/system with sampling design. Nondetect below MRL is not zero. Sampled detection is not household personal intake or a regulatory compliance determination. System address/county is not a service area boundary. Rounds differ in list/sensitivity.

**Local status:** `report_only`. `sources/environment/iowa-dnr-pfas-testing-tiers1-3-march2023.pdf`; `sources/environment/iowa-dnr-pfas-private-wells.pdf`.

**Public copy exclusions:** `sources/environment/iowa-dnr-pfas-private-wells.pdf` (`linked_source_only`); `sources/environment/iowa-dnr-pfas-testing-tiers1-3-march2023.pdf` (`linked_source_only`). See the publication manifest for source links and restoration details.

### EXP-08: SDWIS/Fed and ECHO drinking-water data

Publisher: US EPA/state primacy agencies. [Source 1](https://www.epa.gov/DWdata/sdwis-federal-reporting-services-data-dictionary); [Source 2](https://echo.epa.gov/help/drinking-water-qlik-dashboard-help).

**Coverage/time:** Regulated public water systems and reported service areas; no private well census. Quarterly/current federal snapshots; violation/date histories vary by system/product.

**Grain/joins:** PWS/facility inventory; violation/enforcement records; selected sample tables. Keys: PWSID; Facility ID; Contaminant/rule; Violation ID/start/end/status; Snapshot quarter.

**Units/access:** Population served, connections, categorical violations; concentration only where available. Public reports/downloads; record extract/snapshot date.

**Use/limits:** Public water identity, compliance history and crosswalk to UCMR/state actual samples. EPA acknowledges underreporting/inaccuracies. Federal data do not contain all routine sample values. Monitoring violation is not chemical exceedance. System address is not complete exposure geography.

**Local status:** `report_only`. `sources/environment/iowa-dnr-drinking-water-compliance-2025-june2026.pdf`.

**Public copy exclusions:** `sources/environment/iowa-dnr-drinking-water-compliance-2025-june2026.pdf` (`linked_source_only`). See the publication manifest for source links and restoration details.

### EXP-09: Iowa Wells Information System

Publisher: Iowa DNR. [Source 1](https://programs.iowadnr.gov/iowawellinformationsystem); [Source 2](https://www.iowadnr.gov/environmental-protection/water-quality/private-well-program).

**Coverage/time:** Recorded Iowa private wells; location/depth/geology/water quality. Historical records differ by well; active application current as of access.

**Grain/joins:** Well construction/location and associated sample/result records. Keys: IWIS/well ID; Coordinates/CRS; Sample date/analyte; Well depth/aquifer.

**Units/access:** Well depth and analyte-specific concentration units; nitrate-as-N versus nitrate-as-NO3 must be identified. Public map/query; public bulk/export capability not independently verified here.

**Use/limits:** Groundwater exposure hypotheses with geology/depth and sample dates. Not a census of all wells or users; voluntary/targeted sampling and treatment status. Coordinates and repeated samples need QA. Raw well water versus drinking water tap are different.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-10: Iowa HHS private well tracking summaries

Publisher: Iowa HHS/DNR PWTS. [Source 1](https://hhs.iowa.gov/about/data-reports/environment/well-water).

**Coverage/time:** Iowa tested private wells; summarized state/county/local coverage as per portal. 2000 through latest available according to docs; extract end year from actual export.

**Grain/joins:** Geography x year x analyte/test measure; underlying tested well records. Keys: County FIPS; Year; Analyte; Measure/threshold.

**Units/access:** Tests, wells, percent above threshold; nitrate/arsenic concentration units depend on measure. Public tracking portal; underlying PWTS microdata may need request.

**Use/limits:** Document observed testing coverage and contamination indicators. Selection bias; repeated tests do not mean independent wells; tested wells are not all homes. Arsenic, nitrate, coliform measure different hazards; do not use bacteria as a cancer measure.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-11: Radon zone maps and Iowa testing data route

Publisher: US EPA/Iowa HHS. [Source 1](https://www.epa.gov/radon/epa-map-radon-zones-and-supplemental-information); [Source 2](https://www.epa.gov/sites/production/files/2014-08/documents/iowa.pdf); [Source 3](https://hhs.iowa.gov/health-prevention/providers-professionals/radiological-health/radon); [Source 4](https://www.cdc.gov/environmental-health-tracking/php/data-research/radon-testing.html).

**Coverage/time:** EPA county zone potential; lab/home tests where available through tracking/state program. EPA zones developed 1993; home test date coverage varies; modern state testing microdata not downloaded.

**Grain/joins:** County zone or individual/aggregated building test; these are different data products. Keys: County FIPS or proper geographic ID; Test date/type; Building/floor/mitigation status if available.

**Units/access:** pCi/L or Bq/m3; 1 pCi/L = 37 Bq/m3; category zone is not measured concentration. Public zone map; state/CDC aggregated test coverage; detailed Iowa testing export/access not verified.

**Use/limits:** Keep geologic potential separate from measured building exposure; identify data access gap. All Iowa counties Zone 1 cannot explain between-county variation. Zone predicts potential, not individual home level. Tested homes not random sample; duplicates, short/long tests, season, mitigation matter.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-12: USGS Water Data time-series and discrete Samples API

Publisher: USGS. [Source 1](https://www.usgs.gov/tools/usgs-water-data-apis); [Source 2](https://water.code-pages.usgs.gov/dataretrieval/articles/Status.html).

**Coverage/time:** USGS sites including Iowa surface/groundwater; location-dependent. Historical to current measurements; NWIS discrete water quality froze March 2024; new/updated data use Samples API or new WQP.

**Grain/joins:** Site x time x parameter x method/qualifier; discrete sample versus continuous sensor. Keys: USGS monitoring location/site ID; Parameter code; Datetime/time zone; Sample/result identifier.

**Units/access:** Parameter-specific concentrations, streamflow and related units; preserve qualifiers and reporting limits. Public modern APIs; migrate legacy waterservices/readNWIS code; current API limits docs.

**Use/limits:** Historical water-pathway context and measured timelines with API provenance. Surface water/raw intake concentrations are not finished tap water. Frozen legacy endpoint can look current while missing new records. Different measurement media/methods/times must not be pooled blindly.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-13: Iowa DNR animal feeding operations inventory/GIS

Publisher: Iowa DNR. [Source 1](https://www.iowadnr.gov/environmental-protection/animal-feeding-operations/afo-online-services); [Source 2](https://programs.iowadnr.gov/afoemmp/Home/PublicSearch); [Source 3](https://geodata.iowa.gov/datasets/iowadnr%3A%3Aanimal-feeding-operations-download).

**Coverage/time:** Reported regulated Iowa livestock/poultry facilities; download metadata says active>= 300 animal units. Live inventory snapshot; historical statuses/animal counts must be obtained separately.

**Grain/joins:** Facility/location x status/capacity/animal type; permit/construction records. Keys: AFO Facility ID; Coordinates; Snapshot date; Animal type/unit basis.

**Units/access:** Head counts and animal units/capacity, not interchangeable; facility counts. Public query/inventory reports and GIS downloads.

**Use/limits:** Exposure inventory with explicit definition/date; refine ecological livestock-density hypotheses. Small/unreported operations and historical closures may be missing. AFO, confinement, feedlot and EPA-CAFO definitions differ. Current capacity is not actual annual animal number, manure mass or personal exposure.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-14: EPA ECHO/FRS facility crosswalk/compliance

Publisher: US EPA. [Source 1](https://echo.epa.gov/tools/data-downloads); [Source 2](https://www.epa.gov/frs).

**Coverage/time:** Regulated facilities program-dependent, nationwide including Iowa. Snapshot and program-specific history; keep data refresh date.

**Grain/joins:** FRS facility and program identifier; inspections/violations/enforcement events. Keys: FRS registry ID; TRI ID; NPDES ID; ICIS-Air ID; State program IDs and coordinates.

**Units/access:** Categorical compliance, event dates, penalties; some emissions/discharge measures in separate tables. Public download/web services; dataset-specific coverage.

**Use/limits:** Join reviewed facility records across air/water/waste and dated enforcement. One physical campus can have multiple program IDs or subfacilities. Fine amount and violation count are not cancer risk. No automatic name-only join; inspect aliases/location/period.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-15: EPA Risk-Screening Environmental Indicators (RSEI) and Geographic Microdata

Publisher: US EPA. [Source 1](https://www.epa.gov/rsei/ways-get-rsei-results); [Source 2](https://www.epa.gov/rsei/rsei-data-dictionary); [Source 3](https://www.epa.gov/rsei/rsei-data-dictionary-disaggregated-grid-cell-geographic-microdata); [Source 4](https://www.epa.gov/rsei/rsei-geographic-microdata-rsei-gm); [Source 5](https://www.epa.gov/rsei/understanding-rsei-results); [Source 6](https://www.epa.gov/rsei/how-rsei-should-be-used); [Source 7](https://gaftp.epa.gov/rsei/Current_Version/V2312_RY2022/).

**Coverage/time:** United States and territories, including Iowa. Air microdata use 810 m by 810 m receptor grid cells, with block-group, tract and ZIP aggregates; water microdata use downstream NHD flowlines. Receptors may be affected by sources outside their own county or state. Current verified data dictionary: version 2.3.12, TRI reporting years 1988-2022, released March 2024; TRI input snapshot frozen fall 2023. Do not infer RSEI coverage through 2024 from this project's newer raw TRI files. EPA download page offers 2020-2022 grid microdata; expanded 1988-2022 datasets can be requested.

**Grain/joins:** Air disaggregated microdata: submission year x modeled chemical release/media x receptor grid cell, with concentration, toxicity-weighted concentration, score and population. Aggregated products sum releases over a receptor area. Facility, industry and release summaries are separate products. Keys: Model version plus SubmissionYear; GridCode + X + Y for air receptor cells; ReleaseNumber, ChemicalNumber and FacilityNumber within the same version; TRI facility identifier through the corresponding Facility table; NHD flowline keys for water; documented geographic crosswalk and boundary vintage.

**Units/access:** RSEI Score is unitless and relative; it incorporates surrogate dose, toxicity and population. Air Conc is modeled ug/m3. ToxConc is toxicity-weighted concentration; CTConc and NCTConc isolate cancer and noncancer weights. These are distinct metrics, not observed cancer cases or absolute lifetime probabilities. Public EasyRSEI browser dashboards, all-years dashboard, table CSVs and data dictionary. Geographic Microdata and crosswalk/shapefile directories are public; very large disaggregated national files can exceed 100 GB/year. Some expanded geographies/years require an EPA request. No request or large download performed here.

**Use/limits:** Compare chemical-specific toxicity-weighted screening indicators and receptor areas within one model version; investigate high scores with refined exposure data. Avoid ranking cancer burden by raw TRI mass alone. Scores support screening and prioritization, not facility-specific causal findings, actual personal exposure or individual risk. Overall scores can combine cancer and noncancer effects. Verify stack parameters, location and chemical speciation; category toxicity may use conservative assumptions. TRI reporting limits and omitted sources remain. Do not combine RSEI model versions: internal keys and model results change; a consistent version recalculates historical years. Separate score changes caused by population, toxicity, modeling or input revisions from release changes.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### EXP-16: EPA National Emissions Inventory (NEI), including 2023 inventory

Publisher: US EPA with state, local and Tribal air agencies. [Source 1](https://www.epa.gov/air-emissions-inventories/get-air-emissions-data-0); [Source 2](https://www.epa.gov/air-emissions-inventories/2023-national-emissions-inventory-nei); [Source 3](https://www.epa.gov/air-emissions-inventories/2023-nei-supporting-data-and-summaries); [Source 4](https://www.epa.gov/air-emissions-inventories/what-are-units-nei-emissions-data); [Source 5](https://gaftp.epa.gov/Air/nei/2023/doc/TSD/where-can-i-obtain-the-2023-nei-data.html); [Source 6](https://gaftp.epa.gov/Air/nei/2023/doc/TSD/how-is-the-nei-constructed.html).

**Coverage/time:** Nationwide including Iowa: point facilities, nonpoint county/tribal totals, onroad and nonroad mobile sources. Facility summaries and national/state/county sector summaries are separate aggregations; biogenics and fire supporting products require their own scope definitions. 2023 triennial inventory is publicly available at the October 22, 2026 cutoff; supporting-data page updated October 15, 2026 lists October 2026 data summaries. Full NEI releases every three years; intervening-year modeling platforms and facility summaries are different products. Freeze the exact release/revision and inventory year.

**Grain/joins:** Annual emissions by source category and pollutant. Detailed point data may identify facility, unit, process/SCC and release point; nonpoint/mobile products aggregate by county/tribe, source category and pollutant. Facility-by-pollutant and sector/tier summaries must not be counted as additional emissions. Keys: Inventory year plus release/revision; EIS facility/site identifier and agency identifiers for point data; Unit/process/release-point keys where supplied; County FIPS or Tribal geographic code; Pollutant code/CAS plus unit field; Source Classification Code (SCC), EIS sector or tier definition; Reviewed crosswalk to FRS, TRI and DNR program IDs.

**Units/access:** EPA units documentation specifies annual CAP/precursor emissions in short tons/year and HAP emissions in pounds/year. Preserve the actual product's pollutant and unit columns: summaries, modeling inputs and supplemental files can use different formats. Do not assume every column labeled emissions has the same unit. Public 2023 retrieval tool, facility mapping, custom county/sector/tier queries, zipped CSV summaries, SMOKE modeling inputs and technical documentation. National CSV packages are large and may exceed Excel capacity; select Iowa or a smaller summary. EIS Gateway has restricted agency/EPA access and differs from public downloads. No large download performed here.

**Use/limits:** Broaden chemical/source coverage beyond TRI and Iowa Title V facilities, including mobile and nonpoint emissions; build a dated, pollutant-specific source inventory before exposure modeling. Estimated emissions inventory, not ambient concentration, personal dose or health risk. It blends reported data, factors, models and EPA augmentation; HAP completeness and method uncertainty vary. NEI uses TRI and other programs as inputs, so adding NEI to TRI or DNR totals can double count. CAPs, HAPs and particulate/speciation categories overlap. Historic comparisons need consistent methods, coverage and units. Current EIS facility names/IDs can differ from the frozen public inventory attributes; TSD notes public point reports generated April 15, 2026.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.


## Covariates/denominators

### COV-01: BRFSS annual survey data

Publisher: CDC/Iowa HHS. [Source 1](https://www.cdc.gov/brfss/annual_data/annual_data.htm); [Source 2](https://www.cdc.gov/brfss/annual_data/annual_2025.html).

**Coverage/time:** State-representative adult telephone survey; Iowa included; local direct estimates limited. Annual since 1984; current 2025 dataset released Aug 2026; question/module availability varies.

**Grain/joins:** Survey respondent x year with weights/strata/PSU and behavior/screening responses. Keys: State code; Year; Question/calculated variable; Survey weights/design variables.

**Units/access:** Weighted prevalence percent and survey responses; correct eligible population denominator. Public ASCII/SAS XPT plus codebooks; national latest 356,158 records 284 variables.

**Use/limits:** Smoking, alcohol, obesity, screening and health access covariates with survey design. Self report/nonresponse; cellphone/raking break 2011; module rotations/question changes; not county representative simply by assigning state values. 2025 excludes CA, MS, NV from national aggregate. Confirm actual included states from the selected data file/codebook; the annual webpage and Overview describe national participation differently.

**Local status:** `report_only`. `sources/Iowa-BRFSS-2024.pdf`.

**Public copy exclusions:** `sources/Iowa-BRFSS-2024.pdf` (`linked_source_only`). See the publication manifest for source links and restoration details.

### COV-02: PLACES small-area estimates

Publisher: CDC. [Source 1](https://www.cdc.gov/places/current-release-notes/); [Source 2](https://www.cdc.gov/places/methodology/index.html); [Source 3](https://www.cdc.gov/places/faqs/index.html).

**Coverage/time:** County, place, tract, ZCTA adult small areas. Current Dec 2025 release: 35 measures from 2023 BRFSS, 5 from 2022; ACS 2019-2023; county 2023 population.

**Grain/joins:** Geography x modeled measure x release/data-year/type. Keys: LocationID/GEOID; MeasureID; DataValueType; Release/data-year; Boundary vintage.

**Units/access:** Modeled crude/age-adjusted prevalence percent and 95% intervals; tract/ZCTA no age-adjusted estimates. Public data.cdc.gov CSV/API/GIS-friendly files.

**Use/limits:** Cross-sectional context/prioritization, with model uncertainty and measure-specific vintage. MRP modeled prevalence, not direct local observation or cancer incidence. Cannot reliably track local trend/evaluate local interventions using release changes. No individual inference. ACS may already be a model input: avoid circular covariate validation.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### COV-03: American Community Survey

Publisher: US Census Bureau. [Source 1](https://www.census.gov/programs-surveys/acs/news/data-releases/2024/release-schedule.html); [Source 2](https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release-schedule.html); [Source 3](https://www.census.gov/data/developers/data-sets/acs-5year.html).

**Coverage/time:** 1-year eligible large areas; 5-year all counties/tracts/block groups where tabulated. Latest available 1 year 2024; 5 year 2020-2024 released Jan 29, 2026. 2025 one year estimates scheduled Oct 29, 2026, after cutoff; remaining 2025 products TBD.

**Grain/joins:** Geography x table variable x 1 year or 5 year period; estimates and MOEs. Keys: GEOID/state+county+tract as text; Table/variable ID; Period; Geographic vintage.

**Units/access:** Counts, percent, dollars, various medians; MOEs usually 90%. Public API/summary files/data.census.gov; variable metadata and annotations needed.

**Use/limits:** Age/race/ethnicity, education, poverty, income, housing, insurance, rurality context. 5 year is a period estimate, not a single annual observation. Overlapping windows correlated. 1 year not all 99 Iowa counties. CPI/reference-year for income and boundary/variable changes matter. Special 2020 one year estimates not standard comparable.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### COV-04: QCEW employment/wages

Publisher: US Bureau of Labor Statistics. [Source 1](https://www.bls.gov/cew/overview.htm); [Source 2](https://www.bls.gov/cew/downloadable-data-files.htm); [Source 3](https://www.bls.gov/news.release/cewqtr.nr0.htm).

**Coverage/time:** County/state industry employment where publishable; covers > 95% US jobs. Quarterly/annual history; current release 2026 Q1 on Aug 28, 2026; historical NAICS/SIC and versions vary.

**Grain/joins:** Area x ownership x industry x quarter/year; monthly employment within quarter. Keys: Area FIPS code; Ownership; NAICS code/version; Quarter/year; Aggregation level.

**Units/access:** Covered jobs/establishments, wages/payroll in explicit dollars. Public CSV/ZIP/Open Data; suppression and disclosure flags.

**Use/limits:** Industry size/history and workplace labor context, not resident cancer denominator. Place of work establishments, not resident workers or people ever exposed. Multiple jobholders count in jobs. Some farm/self employment excluded; commuting, industry recodes, coverage/revisions matter.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### COV-05: County Business Patterns

Publisher: US Census Bureau. [Source 1](https://www.census.gov/programs-surveys/cbp/data/datasets.html); [Source 2](https://www.census.gov/programs-surveys/cbp/about.html).

**Coverage/time:** US/state/county/ZIP and other business geographies. Public dataset index verified 1986-2023; latest listed 2023 released June 26, 2025. 2024 expected Sep 2026 in training docs, but availability not verified and not assumed.

**Grain/joins:** Geography x NAICS x establishment size x year. Keys: State/county FIPS or ZIP; NAICS/version; Year; Employment size/LFO where applicable.

**Units/access:** Establishments, March 12 reference-week employment, first quarter/annual payroll. Public CSV/API; data index and dictionary per year.

**Use/limits:** Industry presence/establishments and employment context complementary to QCEW. Employer business coverage excludes most government, self employed and many agricultural workers. Workplace geography, not residence. Suppression/noise flags and NAICS versions; not a historical person exposure cohort.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### COV-06: SEER county populations and standard populations

Publisher: NCI/US Census Bureau. [Source 1](https://seer.cancer.gov/popdata/); [Source 2](https://seer.cancer.gov/popdata/download.html); [Source 3](https://seer.cancer.gov/stdpopulations/).

**Coverage/time:** US counties including Iowa; age/sex/race/Hispanic strata. Current download 1969-2024; vintage and bridged/single-race series must be selected.

**Grain/joins:** County x year x demographic stratum; standard age weights in separate files. Keys: County FIPS; Year; Age group; Sex; Race/Hispanic category; Population vintage.

**Units/access:** Resident population/person-year approximation; standard age weights. Public ASCII/downloads; SEER Prep if needed for SEER Stat.

**Use/limits:** Compatible expected case counts, rates/standardization and latency-population context. Use population series compatible with outcomes/race groups. Revisions alter historical rates. Do not average age-adjusted county rates weighted by total population to obtain state rate.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

### COV-07: Census TIGER/Line and geographic relationship files

Publisher: US Census Bureau. [Source 1](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html); [Source 2](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html).

**Coverage/time:** State/county/tract/block/ZCTA and other published geographies. Year-specific boundary releases; 2010-2020 relationship files; statistical geographies retain census vintage.

**Grain/joins:** Geographic polygon/relationship row with identifiers and intersection areas. Keys: GEOID; State/county/tract/block components; ZCTA code; Boundary vintage.

**Units/access:** Geometry/land-water area; not demographic counts. Public shapefiles/geodatabases/relationship files.

**Use/limits:** Safe geographic joins/crosswalks and explicit spatial exposure definitions. ZIP postal routes are not ZCTAs; zones not counties. No automatic one-to-one crosswalk. Area-weighted allocation of people/exposure can mislead; use population and geographic vintage appropriate weights. Centroid distance is not dose.

**Local status:** `not_downloaded`. No dataset downloaded for this catalog.

## Practical acquisition order

For an initial county model, start with the already archived cancer extracts and compatible population denominators. Add historical chemical-specific exposure series and independently measured or model-aware covariates after defining cancer site and latency. Use ACS 5-year estimates for all 99 counties, BRFSS for direct state trends, and PLACES for limited cross-sectional local context. Retrieve actual finished-water measurements and service areas before assigning water exposure. Keep QCEW/CBP workplace employment separate from residential populations. Obtain approved registry data when finer subtype or geography is required; public county products cannot provide individual job or residential history.

Full USCS/SEER case databases, complete USGS pesticide files, USDA county panels, UCMR 5, IWIS/PWTS, AQS, ACS, QCEW/CBP and population/geographic files were not downloaded for this catalog. These are acquisition gaps, not evidence that exposure or disease is absent.
