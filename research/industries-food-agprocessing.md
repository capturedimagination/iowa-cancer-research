# Iowa food, grain, biofuel and fertilizer industries: cancer evidence

Research cutoff: October 22, 2026. This expansion looks beyond farm pesticide application. It distinguishes an established carcinogen, workplace measurements, a permit or enforcement record, a worker-cancer association, and a causal finding about community cancer. Those are different kinds of evidence.

## Most useful findings

- Iowa's food/industrial sector deserves attention, but total hazardous-air-pollutant (HAP) pounds cannot rank cancer risk. Soybean extraction emits substantial hexane; n-hexane's best-established hazard is nerve damage, while EPA finds inadequate information to assess its carcinogenic potential. Commercial hexane mixtures have a different, suggestive EPA assessment.
- Historical Iowa poultry investigations actually measured chlorine/chloramine exposure and documented respiratory symptoms and improvement after controls. They did **not** establish that the plant caused cancer.
- A new 2026 U.S. poultry-worker cohort has a **non-significant overall cancer-mortality result**, but elevated results for selected hiring periods. This is a stronger and more nuanced source than simply claiming all meat workers have a fixed excess risk.
- Direct Iowa and Upper Midwest occupational case-control studies provide leads involving food processing, grain/farm-product wholesale and other industries. They use broad job categories and many comparisons; no particular plant or agent is identified as the cause.
- The state's current 2026 monitoring plan describes **four carbonyl-toxics sites**, not the five sites of the 2021 report: two in Des Moines, one in Cedar Rapids, one in Clinton. Cedar Rapids also has VOC canister sampling. Monitoring coverage is limited and changed over time.

## 1. Statewide actual-emissions inventory now archived

The live DNR PDF at https://www.iowadnr.gov/media/2277/download?inline= has misleading search metadata (“2021”), but its actual cover is **2024 Iowa Point Source Emissions Summary, February 25, 2026**. It covers 283 Title V facilities and excludes mobile, biogenic and nonpoint sources. Its report total is 5,484 tons of HAPs; Appendix A sums to 5,483.81 after rounding individual records. Food and Kindred Products accounts for 64.32% of HAP mass and dry-mill ethanol 6.36%; these are **mass shares, not cancer-risk shares**. Facility estimates may change because of new emission factors or corrections as well as actual operational changes.

Saved complete machine-readable Appendix A: `research/iowa-title-v-facilities-emissions-2024.csv`. Exactly 283 unique facility IDs were extracted, with no exclusions or deduplication. Each has nine emissions columns, data year, PDF page, units and a caution. The original 34-page PDF and extracted text are in `sources/industries/food-agprocessing/`. HAPs can overlap VOC or particulate categories: do not sum all pollutant columns as independent toxic quantities.

This inventory provides an Iowa presence/actual-emission record for corn milling, ethanol, soybean extraction, food factories and nitrogen-fertilizer facilities. It does not give a patient's inhaled dose, occupational exposure or facility-specific cancer count. Those require pollutant speciation, dispersion/exposure assessment and linked health research.

## 2. Soybean extraction and vegetable-oil production

**Process to investigate:** solvent extraction, desolventizing, solvent recovery, leaks and building ventilation. DNR permits explicitly identify hexane/soybean extraction and the vegetable-oil extraction NESHAP. Example permit: https://www.iowadnr.gov/portals/idnr/uploads/air/operpermit/finalpermits/11-TV-004R2.pdf (final January 18, 2023; extraction unit and records on PDF p.33).

**Cancer classification needs care:** EPA IRIS says there is inadequate information to assess the carcinogenic potential of **n-hexane**, with peripheral neuropathy the basis of the inhalation reference concentration. https://iris.epa.gov/ChemicalLanding/%26substance_nmbr%3D486 . ATSDR's April 2025 summary agrees: https://wwwn.cdc.gov/tsp/toxfaqs/toxfaqsdetails.aspx?faqid=392&toxid=68 . In contrast, EPA's 2022 PPRTV document lists **commercial hexane** as having suggestive carcinogenic potential, based principally on animal findings; do not collapse mixture and individual-chemical assessments. https://cfpub.epa.gov/ncea/pprtv/documents/TotalPetroleumHydrocarbonsAliphaticLow.pdf (Table 9).

DNR's 2024 records include Bunge, Cargill, ADM and AG Processing sites. These make the sector visible for further exposure work; high mass alone does not establish high cancer potency or community disease. EPA's older AGP Mason City enforcement notice specifically confirms hexane extraction, but the cited matter involved spill-response planning/oil releases, not a cancer determination: https://archive.epa.gov/region07/public_notices/CWA/cwa-archive/web/html/ag_processing_mason_city_ia.html .

## 3. Corn wet milling, ethanol and coproduct processing

Investigate fermentation vapors, acetaldehyde, boiler combustion, dryers, protein coproduct processing, thermal oxidizers/scrubbers and maintenance events. EPA's historical ADM Cedar Rapids permit clearinghouse documents addition of an ethanol dry mill to wet milling/boiler operations: https://cfpub.epa.gov/rblc/index.cfm?Facility_ID=26699&action=PermitDetail.FacilityInfo . Permitted increases are **not** actual emissions or individual exposure.

Acetaldehyde is classified in EPA's older IRIS framework as B2, probable human carcinogen, based on animal evidence: https://iris.epa.gov/ChemicalLanding/%26substance_nmbr%3D290 . Do not treat beverage-alcohol epidemiology as direct proof of the same risk from outdoor ethanol-plant vapor exposure. Different chemicals, routes and doses require separate assessment.

**Muscatine:** EPA issued a March 2012 notice alleging Grain Processing Corporation opacity and reporting violations during 2007-2011: https://www.epa.gov/archive/epapages/newsroom_archive/newsreleases/71c2022dc7698d8d852579ce00637fe1.html . A 2014 state plan addressed fine particulate emissions at GPC, Muscatine Power and Water and Union Tank Car: https://www.epa.gov/archive/epapages/newsroom_archive/newsreleases/b5fb96ecb88915d785257da800718a54.html . These support a historical air-quality concern, not an epidemiologic attribution of Muscatine cancers. DNR's current Facility Explorer retains GPC facility identification: https://facilityexplorer.iowadnr.gov/facilityexplorer/SiteDetail.aspx?facID=310637862 .

**Shell Rock:** DNR's July 11, 2024 release confirms a consent order requiring POET Biorefining–Shell Rock to pay 2021/2022 emissions fees, supply permit information, make required changes and pay a $10,000 penalty. https://www.iowadnr.gov/news-release/2024-07-11/dnr-enforcement-actions-published-07112024 . Secondary reporting describes acetaldehyde/VOC exceedances and a protein-processing control problem, but the original full order was not recovered in this subtask; do not present the reported “nine times” and “27 times” figures as independently verified here. The state's document search is the route to the original: https://www.iowadnr.gov/about/enforcement-actions .

## 4. Ambient carbonyl measurements and monitoring gaps

DNR's **2021** monitoring report measured formaldehyde and acetaldehyde at five locations, with upper-bound modeled lifetime risks above a one-per-million screening benchmark. Its highest formaldehyde estimate was about 50 per million at Davenport and acetaldehyde about 11.2 per million at Clinton. These are model-based risk estimates derived from annual concentrations, **not observed cancer cases**. The report notes substantial secondary atmospheric formation, meaning it cannot assign the measured chemicals to one nearby factory. https://www.iowadnr.gov/media/2587/download?inline= (PDF pp.5-6,16).

The **2026** network plan states four current carbonyl sites: two Des Moines, one Cedar Rapids and one Clinton; McKinley Academy in Cedar Rapids also collects VOC toxics by canister. No changes were anticipated before the next plan. https://www.iowadnr.gov/media/9624/download?inline= (actual cover 2026 despite search metadata 2025; PDF p.14). DNR's May 18, 2026 announcement identifies that plan: https://www.iowadnr.gov/news-release/2026-05-18/iowas-2026-air-monitoring-network-plan-available-public-review-and-comment .

For comparison, the 2025 plan proposed ending Davenport/Muscatine carbonyl sampling for budget/lab-cost reasons. https://www.iowadnr.gov/media/9127/download?inline= . Use the newer four-site description for current status. Neither a sparse network nor a compliant criteria-pollutant AQI proves the absence of all carcinogenic air exposures.

## 5. Meatpacking, slaughter, poultry and rendering

**Potential exposure routes:** meat/blood bioaerosols, processing fumes, cleaning/disinfection chemicals, combustion, maintenance materials and occupational schedules. The relevant hypothesis must identify an agent and job task; handling a food product is not the same exposure as eating it.

**Original 2026 U.S. union cohort:** Ball et al. compared 30,411 poultry and 16,405 non-poultry food workers with mortality through 2019. Overall cancer mortality aHR was **1.05 (95% CI 0.97-1.13)**, not statistically significant. Hiring-period analyses found higher cancer mortality before 1960 and during the 1980s; the pre-1960 aHR was 1.62 (1.25-2.11), and 1980-1989 1.86 (1.39-2.48). This is not an Iowa-specific cohort estimate. Smoking/alcohol were not directly measured adequately; exposure histories and non-union generalizability are limitations. Source: https://pubmed.ncbi.nlm.nih.gov/41813116/ ; original article https://oem.bmj.com/content/early/2026/03/11/oemed-2025-110495 (DOI10.1136/oemed-2025-110495).

**Older U.S. meat cohort:** Johnson et al. 1995 followed 5,522 abattoir and 4,589 meatpacking workers and found several excess mortality outcomes. Its authors explicitly lacked smoking, alcohol and diet adjustment. It is not evidence that a named Iowa plant caused cancer. https://pubmed.ncbi.nlm.nih.gov/7747745/ (DOI10.1002/ajim.4700270308).

**Smoking-adjusted European case-control study:** Durusoy et al. 2006 reported a non-significant overall meat-aerosol lung association, OR1.27 (0.92-1.75), but a highest cumulative-exposure category OR1.73 (1.03-2.92). This supports further occupational investigation while showing why exposure level and confounding matter. https://pubmed.ncbi.nlm.nih.gov/16353144/ (DOI10.1002/ijc.21690).

**Iowa-containing glioma study:** Upper Midwest Health Study, 1995-1997 cases in Iowa/Michigan/Minnesota/Wisconsin, found food processing (mostly butchers/meat cutters) OR1.78 (0.99-3.18), a borderline result across 27 cases/21 controls. Many occupational comparisons and broad job groups limit causal inference. https://pmc.ncbi.nlm.nih.gov/articles/PMC4530494/ . Earlier Iowa work used 375 glioma cases and 2,434 controls and generated numerous occupational leads; it cannot identify a specific workplace agent. https://pubmed.ncbi.nlm.nih.gov/11322092/ .

Rendering-specific Iowa cancer cohorts were not located in the targeted search. This is an evidence gap, not a finding of safety or a reason to transfer all slaughter/poultry estimates to renderers.

## 6. A measured Iowa poultry hazard, with an effective control example

NIOSH's **Bil-Mar Foods, Storm Lake, 2003** HHE investigated workers' eye/respiratory complaints, chlorine/chloramine exposures and ventilation. The 2002-2003 evaluation found exposure and symptom contrasts between evisceration and a comparison area. It was a respiratory hazard evaluation, not cancer surveillance. https://www.cdc.gov/niosh/hhe/reports/pdfs/2002-0257-2916.pdf .

The **Sara Lee Foods, Storm Lake, 2006** follow-up found reduced soluble chlorine and fewer symptoms after engineering/ventilation controls. Detection limits changed and intermittent production conditions limited exact comparisons. This is direct evidence that controls helped a specific Iowa workplace; neither report diagnoses a cancer cluster. https://www.cdc.gov/niosh/hhe/reports/pdfs/2006-0153-3022.pdf . Both original PDFs are archived locally. Historical facility names are retained; the reports do not establish present ownership or current exposure levels.

## 7. Grain elevators, flour/feed mills and storage

OSHA identifies serious grain-handling hazards including fumigants, grain dust, molds, engulfment and explosions. Its fumigant warning includes cancer, but this must be evaluated by the actual ingredient and historical use. Ordinary grain dust should not be automatically labeled equivalent to carcinogenic wood dust or crystalline silica. https://www.osha.gov/grain-handling .

The original 1990 NCI/U.S. flour-industry study followed 22,938 white men during 1955-1985. Lower all-cause mortality coexisted with selected flour-worker cancer excesses and nested case-control signals. It used historical workplace/pesticide information that could not identify personal exposure; this is not a current Iowa risk estimate. https://pubmed.ncbi.nlm.nih.gov/2332902/ (DOI10.1093/jnci/82.10.840). IARC's assessment gives the flour-worker NHL estimate as SMR1.5 (0.9-2.3), illustrating uncertainty: https://www.ncbi.nlm.nih.gov/books/NBK499667/ .

A 1987 Swedish grain-miller study found no overall cancer elevation but a liver signal, highlighting geographic differences and fungal/pesticide hypotheses. https://pubmed.ncbi.nlm.nih.gov/3682015/ . Grain contamination, worker inhalation and dietary mycotoxin exposure must be distinguished; absence of measured aflatoxin dose prevents attributing an Iowa worker's cancer to that pathway.

## 8. Nitrogen-fertilizer manufacturing and ag-chemical production

CF Industries' Port Neal complex is documented by DNR and EPA facility records: https://facilityexplorer.iowadnr.gov/FacilityExplorer/SiteDetail.aspx?facID=310631577 ; https://frs-public.epa.gov/ords/frs_public2/fii_query_dtl.disp_program_facility?p_registry_id=110000414089 . The 2011 Terra settlement covered NOx allegations at nitric-acid plants including Sergeant Bluff: https://www.epa.gov/enforcement/terra-industries-clean-air-act-settlement . A prior violation is not proof of a present violation, nor a cancer outcome.

DNR's 2024 inventory also documents Koch Fertilizer Wever. Nitrogen products, hydrogen/natural gas, process combustion, maintenance and water pathways deserve separate assessments. High ammonia toxicity is primarily an acute/respiratory concern, not proof of carcinogenicity. NIOSH describes chronic carcinogenic information as inconclusive: https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750013.html . The hydrogen-fire injury in OSHA's Wever record was an acute burn incident, not a cancer case: https://www.osha.gov/ords/imis/establishment.inspection_detail?id=1242420.015 .

Pesticide formulation/manufacturing needs historical ingredient/process inventories, not only today's product hazard labels or crop-application studies. DNR's 2024 inventory includes Bayer CropScience Muscatine facilities, but does not identify a worker cancer cohort or quantify exposure to each ingredient. The existing environmental memo covers agent-specific pesticide evidence; that does not automatically estimate manufacturing-worker risk.

Original fertilizer-worker studies have mixed findings. Hagmar et al. (1991), Sweden, followed cancer morbidity during 1963-1986 among 2,131 nitrate-fertilizer workers. Total, stomach and lung cancer were not significantly elevated. Prostate cancer was elevated (SMR1.61, 95%CI1.07-2.39), but did not strengthen with a 10-year latency restriction and there was no nitrate-dose association. A separate 1,148-worker non-nitrate comparison cohort had elevated lung cancer. https://pubmed.ncbi.nlm.nih.gov/1649801/ . Zandjani et al. (1994), Norway, studied 1,756 men employed at least one year during 1947-1980: 195 total cancers versus 208.8 expected, but 28 stomach cancers versus 19.9 expected. https://pubmed.ncbi.nlm.nih.gov/7814099/ . Neither is an Iowa estimate, and the mixture of total/site-specific findings prevents treating fertilizer manufacture as one uniform cancer exposure.

## 9. Other food-related sectors and routes

- **Cold storage/dairies/refrigeration:** ammonia spills can burn/injure lungs. NIOSH identifies commercial refrigeration and food processing as exposure settings; this does not establish ammonia as an Iowa cancer driver. https://archive.cdc.gov/www_cdc_gov/niosh/topics/ammonia/default.html . No Iowa-specific dairy-processing cancer cohort was located.
- **Restaurants/commercial kitchens:** IARC classifies emissions from high-temperature frying as probably carcinogenic (Group2A). Evidence is largely from other populations and cooking systems; apply to the measured ventilation/process, not every Iowa restaurant employee. https://www.ncbi.nlm.nih.gov/books/NBK385521/ .
- **Consumption of processed meat:** IARC's Group1 classification concerns **eating** processed meat and colorectal cancer. It is not a classification of “working in meatpacking.” https://www.iarc.who.int/featured-news/media-centre-iarc-news-redmeat/ .
- **Biofuel safety:** ethanol-production hazards include fire, confined spaces and process chemicals. These important hazards do not each establish cancer causation. https://www.osha.gov/otm/section-4-safety-hazards/chapter-5 .

## 10. Investigation priorities

For a credible follow-up, combine plant identifiers and historical aliases; actual emissions by chemical and year; air/water/waste pathways; stack/dispersion or measured workplace exposure; job task and tenure; prior residences; smoking/alcohol and screening; cancer subtype and latency. Include workers who left employment and immigrant/non-union workers, who may be missed by older union cohorts. Evaluate interventions and post-control data as well as exceedances.

Do not use HAP mass, a permit limit, a fine amount, an odor report, a map's proximity or an isolated case as a cancer-risk score. Conversely, an inability to quantify a statewide industrial attributable fraction does not justify ignoring known carcinogens or a documented exposure failure.

## 11. Reuse as research knowledge

The structured companion files `research/industry-food-agprocessing-evidence.csv` and `.json` contain 32 scoped records. A record is a claim, analysis, source definition or explicit search gap, **not necessarily an independent study**. For example, the 2026 poultry overall and hiring-period records belong to the same cohort. Fields retain source date, population, Iowa scope, process/agent, design, exposure measure, outcome, effect/uncertainty and allowed/prohibited inference. Empty effect fields mean not extracted/not applicable; they do not mean zero association. Search-gap records are labeled and must not be ingested as primary null studies.

`research/iowa-title-v-2024-provenance.json` documents the complete inventory extraction, identifiers, overlap, period and coverage. `scripts/extract_iowa_title_v_2024.py` reproduces all 283 rows and checks uniqueness and the 5,483.81-ton HAP sum. The PDF labels units **tons** without explicitly defining the ton basis; no pounds conversion is made here. Confirm the underlying inventory unit definition before joining to TRI pounds. DNR point-source inventory IDs differ from FRS, TRI and DNR Facility Explorer IDs. Current names and ownership require a dated identity crosswalk.
