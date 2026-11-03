# Iowa cancer epidemiology — verified research memo

Research date: October 22, 2026. This memo distinguishes live NCI exports from older indexed search results and annual forecasts. All rates below are age adjusted, per 100,000 people per year. Cancer-specific breast, prostate, cervix, ovary, and uterus rates use the relevant sex population. Data snapshots and full source footnotes are retained locally.

## The current headline has changed since the March annual report

**The live National Cancer Institute State Cancer Profiles CSV exports now cover incidence in 2019–2023 and deaths in 2020–2024.** Search-engine copies of the same pages still show 2018–2022. Do not mix the versions. Exports generated October 22, 2026, cite the November 2025 SEER submission and 2025 NPCR submission for incidence.

| Measure | Iowa | U.S. | Interpretation |
|---|---:|---:|---|
| Incidence, 2019–2023 | 504.1 (95% CI 500.9–507.3) | 453.4 (453.1–453.7) | Iowa 11.2% higher, calculated from displayed rates |
| Observed average annual new cases | 20,505 | 1,872,272 | Historical average; different from 2026 projections |
| Recent incidence AAPC | +0.7% (0.5–1.0) | −0.6% (−1.0 to −0.2) | Iowa rising; U.S. falling |
| Mortality, 2020–2024 | 148.2 (146.5–149.8) | 143.2 (143.0–143.4) | Iowa 3.5% higher, calculated |
| Observed average annual deaths | 6,372 | 609,828 | Deaths occurring during historical observation period |
| Recent mortality AAPC | −0.5% (−1.3 to +0.1) | −1.4% (−1.6 to −1.2) | Iowa statistically stable; U.S. falling |
| Mortality CI*Rank | 22 (rank CI 17–28) | — | Iowa is not second-highest for cancer mortality |

Primary live sources:

- [Iowa county incidence export](https://statecancerprofiles.cancer.gov/incidencerates/index.php?areatype=county&cancer=001&race=00&ruralurban=0&sex=0&statefips=19&type=incd&year=0&datatype=01&sortVariableName=rate&sortOrder=desc&output=1)
- [State incidence export](https://statecancerprofiles.cancer.gov/incidencerates/index.php?stateFIPS=00&areatype=state&cancer=001&race=00&sex=0&age=001&type=incd&year=0&sortVariableName=rate&sortOrder=desc&output=1)
- [Iowa county mortality export](https://statecancerprofiles.cancer.gov/deathrates/index.php?stateFIPS=19&areatype=county&cancer=001&race=00&sex=0&age=001&type=death&year=0&sortVariableName=rate&sortOrder=desc&output=1)
- [State mortality export](https://statecancerprofiles.cancer.gov/deathrates/index.php?stateFIPS=00&areatype=state&cancer=001&race=00&sex=0&age=001&type=death&year=0&sortVariableName=rate&sortOrder=desc&output=1)

### Ranking subtlety

The current state table displays Kentucky 524.7, Iowa 504.1, West Virginia 503.8. **The table's uniform CI*Rank field nevertheless ranks West Virginia 2 and Iowa 3 (Iowa rank CI 2–3).** Its footnote explains that displayed rates use 20 age groups for SEER states and 19 for NPCR states, while CI*Rank uses 19 groups for both. Thus report “among the country's highest; CI*Rank 3 in the current NCI table,” with this note, rather than treating tiny differences as a meaningful second-versus-third distinction. Iowa's familiar “second-highest” headline is well supported by the earlier 2018–2022 table and March 2026 report, but needs its period attached.

The current export classifies **five** states as rising: Iowa, Wisconsin, Oklahoma, Utah, Hawaii. Earlier claims of “only one,” “only two,” or “only three” rising states refer to different releases/time windows. State tables contain 53 rows: U.S., 50 states, D.C., and Puerto Rico. The national comparison excludes Puerto Rico.

Trend labels refer to confidence intervals of modeled average annual percent changes. The portal notes that fitting periods can differ by geography. Separate sex, race, rural/urban, and overall Joinpoint fits need not yield the same trend classification; do not average their AAPCs to “correct” the overall trend. No independently verified explanation for the all-sex stable versus sex-specific falling mortality classifications was found.

## Annual 2026 estimates are forecasts

[Cancer in Iowa 2026, Iowa Cancer Registry](https://shri.public-health.uiowa.edu/wp-content/uploads/2026/03/2026-Cancer-in-Iowa.pdf), released March 13, 2026. Direct PDF retrieval returned CloudFront 403; the primary PDF's indexed page text was accessible and used. It has not been falsely saved as a readable original PDF. Failed retrieval is retained as HTML. Registry report webpages name this the latest annual report.

- p.2: estimated 21,700 new invasive cancers and 6,400 deaths in 2026; estimated 175,290 people living after a cancer diagnosis. “Survivor” includes people living with a cancer history, not necessarily cured or treatment free.
- p.3 projected new cases: prostate 3,100; breast 3,050; lung 2,600; colorectal 1,630; melanoma 1,500; kidney/renal pelvis 950; bladder 900; non-Hodgkin lymphoma 870; leukemia 720; uterus 680; pancreas 630; oral cavity/pharynx 620; thyroid 550; liver/bile duct 370; myeloma 300; other 3,230.
- p.4 projected deaths: lung 1,460; colorectal 550; pancreas 530; breast 380; prostate 370; liver/bile duct 270; leukemia 250; NHL 240; esophagus 200; kidney 200; bladder 170; brain 170; uterus 130; myeloma 110; ovary 110; other 1,260. Lung accounts for 22.8% of predicted cancer deaths.
- The report's map colors use observed 2018–2022 age-adjusted rates, while numbers printed inside counties are 2026 projected counts. These are not the same measure or period.

The [American Cancer Society 2026 primary statistical paper](https://pmc.ncbi.nlm.nih.gov/articles/12798275/) forecasts 22,710 Iowa cases and 6,330 deaths, differing from the registry's 21,700/6,400 because projections come from different models. Do not silently substitute or combine forecasts. ACS also uses delay-adjusted incidence in some comparisons; keep it separate from unadjusted State Cancer Profiles rates.

## Leading cancers and less discussed sites, current observed data

Source: live NCI state exports, individual cancer codes. See `iowa-cancer-types-comparison.csv` for every source URL, count, CI, rank, and trend, with raw originals under `sources/cancer-specific-*`. Incidence period 2019–2023; mortality period 2020–2024. The denominators differ for sex-specific cancers, so do not sum these rates.

| Cancer | Iowa incidence | U.S. incidence | Iowa recent incidence trend | Iowa mortality | U.S. mortality |
|---|---:|---:|---|---:|---:|
| Prostate | 133.4 | 119.9 | rising +3.2%/y | 19.2 | 18.9 |
| Female breast | 139.2 | 133.0 | rising +1.6%/y | 17.1 | 18.9 |
| Lung/bronchus | 59.6 | 51.8 | falling −0.9%/y | 33.7 | 30.2 |
| Colon/rectum | 40.3 | 36.9 | stable | 13.3 | 12.7 |
| Melanoma | 33.7 | 23.8 | rising +3.4%/y | 2.5 | 2.0 |
| Kidney/renal pelvis | 21.6 | 17.9 | rising +1.8%/y | 4.1 | 3.4 |
| Bladder | 21.2 | 18.7 | falling −3.5%/y | 4.0 | 4.1 |
| Non-Hodgkin lymphoma | 21.4 | 18.5 | stable | 5.4 | 4.8 |
| Leukemia | 17.3 | 14.5 | rising +0.6%/y | 6.2 | 5.7 |
| Oral cavity/pharynx | 14.9 | 12.3 | rising +2.0%/y | 2.6 | 2.7 |
| Pancreas | 14.0 | 13.9 | rising +1.3%/y | 11.2 | 11.3 |
| Thyroid | 14.2 | 13.0 | stable | 0.5 | 0.5 |
| Uterus | 30.8 | 28.2 | rising +0.6%/y | 5.4 | 5.4 |
| Ovary | 10.3 | 10.1 | stable | 5.8 | 5.7 |
| Cervix | 7.0 | 7.5 | stable | 1.5 | 2.1 |
| Liver/bile duct | 7.8 | 8.7 | rising +3.8%/y | 5.8 | 6.6 |
| Esophagus | 5.8 | 4.6 | stable | 4.6 | 3.7 |
| Stomach | 5.2 | 6.6 | stable | 1.7 | 2.7 |
| Brain/other nervous system | 6.5 | 6.2 | falling −1.6%/y | 4.5 | 4.4 |

Current incidence CI*Ranks: oral/pharynx 2 (rank CI 1–7); NHL 3 (1–7); leukemia 3 (1–7); melanoma 4 (3–8); esophagus 5 (2–17); kidney 8 (4–10). These are release-specific. High incidence does not necessarily mean high mortality: Iowa female-breast mortality is below the national rate even while its incidence is higher.

## Age, children, adolescents, and young adults

The annual report p.6 (2018–2022) separates the following groups:

| Age | Total observed cases over 5 years | Average/y | Total observed deaths over 5 years | Average/y |
|---|---:|---:|---:|---:|
| 0–14 | 497 | 100 | 63 | 13 |
| 15–19 | 245 | 49 | 31 | 6 |
| 20–39 | 4,006 | 801 | 374 | 75 |

For ages 20–39, melanoma, breast, and thyroid were each approximately 14% of cases; testicular cancer 8%. Incidence increased from 95.1 per 100,000 in 2008–2012 to 102.3 in 2018–2022; the latter was second-highest nationally and significantly above the U.S. rate. Mortality was 10.4 then 9.7, similar to U.S. rates. Localized diagnoses: Iowa 57% versus U.S. 51%. This pattern can reflect detection/stage differences; it does not by itself prove the cause of Iowa's excess.

Childhood and adolescent incidence in that comparison was similar to the U.S. and did not significantly increase between those two five-year windows. Thus “Iowa's childhood cancer rate is exploding” is not supported by that report. This does not mean childhood cancer is harmless or fully understood.

The latest NCI under-50 download (2019–2023) shows Iowa incidence 116.7 (114.5–118.9) versus U.S. 107.6; Iowa recent trend stable at +0.8% (−1.5 to +1.1). The latest under-50 mortality (2020–2024) is Iowa 13.8 (13.0–14.5) versus U.S. 14.2; Iowa trend falling −1.7%/y. Age 50+ incidence is Iowa 1,518.5 versus U.S. 1,363.3, with 18,322 of the state's average 20,505 annual cases occurring among people 50+. Do not conflate ages 20–39, under 50, and the conventional adolescent/young-adult 15–39 band.

**Data anomaly to exclude from a polished table:** current NCI childhood <20 Iowa export duplicates the <15 rate and count (17.0 and 103/year), even though its national figures differ. Raw snapshots retained; no explanation verified. The <15 current estimate is 17.0 (15.6–18.6) versus U.S. 16.4, and portal recent trend rising +0.7% (0.1–1.3). This latest trend is a different analysis from comparing two five-year windows in the March annual report. For clarity, use the annual report's age-specific pediatric section unless the new anomalous export is resolved with the registry.

## Race/ethnicity and sex

Live primary sources use race codes 07 non-Hispanic White, 28 non-Hispanic Black, 05 Hispanic of any race, 38 non-Hispanic American Indian/Alaska Native, 48 non-Hispanic Asian/Pacific Islander. Ethnicity and race should not be casually combined or treated as biological explanations. Rates are age adjusted; smaller populations have greater statistical uncertainty and possible classification problems.

| Population | Iowa incidence 2019–23 | U.S. incidence | Iowa mortality 2020–24 | U.S. mortality |
|---|---:|---:|---:|---:|
| Male | 549.4 | 490.4 | 175.8 | 168.3 |
| Female | 473.0 | 428.9 | 128.0 | 124.7 |
| Non-Hispanic White | 505.6 | 471.8 | 149.7 | 149.4 |
| Non-Hispanic Black | 553.5 | 458.1 | 190.9 | 163.1 |
| Hispanic, any race | 312.5 | 362.0 | 78.7 | 104.5 |
| NH American Indian/Alaska Native | 538.1 | 424.3 | 119.8 | 124.1 |
| NH Asian/Pacific Islander | 308.6 | 303.8 | 107.7 | 91.0 |

Iowa NH Black mortality CI 175.6–206.9, versus NH White 148.0–151.5. The displayed rates imply approximately 27.5% higher Black than White mortality. AI/AN mortality is based on only 12 average annual deaths, with a wide 90.3–155.7 CI and suppressed trend. Avoid confident rankings from small numbers. The current NH Black mortality rank is 3 but rank CI 1–22, illustrating why a precise ordinal headline can mislead.

The [2021 registry disparities release](https://www.public-health.uiowa.edu/news-items/state-health-registry-of-iowa-issues-cancer-in-iowa-2021-report-highlights-racial-disparities/) also identified >25% greater age-adjusted Black mortality, but use the newer numbers above in a current report.

## Geography: all 99 counties and Pella-area context

All 99 county incidence and death tables have been downloaded, normalized, merged on five-digit FIPS and checked for exactly 99 county rows. Keep statewide and U.S. reference rows in the separate per-measure CSVs. `iowa-99-counties-comparison.csv` is the combined table with periods, CIs, mean annual counts, CI*Rank intervals, trends and AAPCs.

Current selected county rates:

| County | Incidence 2019–23 (95% CI) | Annual cases | Mortality 2020–24 (95% CI) | Annual deaths |
|---|---|---:|---|---:|
| Marion | 532.3 (501.6–564.4) | 243 | 163.5 (147.5–180.8) | 80 |
| Mahaska | 506.3 (468.9–546.1) | 147 | 173.3 (152.7–196.1) | 54 |
| Jasper | 504.3 (476.4–533.4) | 264 | 155.8 (141.2–171.7) | 87 |
| Iowa reference | 504.1 (500.9–507.3) | 20,505 | 148.2 (146.5–149.8) | 6,372 |
| U.S. reference | 453.4 (453.1–453.7) | 1,872,272 | 143.2 (143.0–143.4) | 609,828 |

Marion incidence rising +0.7%/y (0.4–1.0); mortality falling −0.6%/y (−1.1 to −0.1). Mahaska incidence and mortality statistically stable. Jasper incidence stable; mortality falling −1.2%/y (−1.9 to −0.5). **Marion County is context for Pella, not a Pella-specific rate.** These county rates cannot identify a person's exposure or explain the cause of a family member's cancer.

Highest displayed incidence rates: Cass 601.4, Pocahontas 591.0, Palo Alto 563.1, Grundy 553.5, Clinton 553.3. Lowest: Buena Vista 416.9, Adair 438.1, Kossuth 447.0, Jefferson 452.3, Wayne 453.9. Highest displayed mortality rates: Palo Alto 186.8, Franklin 186.6, Wapello 181.9, Lucas 181.8, Monroe 181.4. Lowest: Johnson 105.0, Sioux 112.1, Dallas 113.7, Clay 114.5, Story 120.6.

Computed from the current table, **95 of 99 counties have point estimates above the national incidence rate**, and 55 exceed the Iowa point rate. That is not a claim of 95 statistically significant excesses. Wide overlapping intervals and differences in cancer type, screening, population composition, migration, historical exposures and chance matter. Cass incidence rank CI 1–35; Pocahontas 1–75; Palo Alto 1–85. Do not read a rank map as a causal map.

[Iowa Cancer Registry zone maps](https://shri.public-health.uiowa.edu/cancer-zones/) use 48 aggregates of census tracts, minimum 50,000 residents, and suppress rates based on fewer than 16 cases. [CAMSA and other registry tools](https://shri.public-health.uiowa.edu/cancer-data/interactive-iowa-data-tools/) provides modeled small-area estimates; model uncertainty and geographic smoothing need explanation if used. Confirm the current geography and dates, rather than describing every map as ZIP-code observed counts.

## Rural and urban patterns

Current primary NCI filtered rates (2023 Rural–Urban Continuum Codes):

| Place | Incidence 2019–23 (95% CI) | Mortality 2020–24 (95% CI) |
|---|---|---|
| Iowa rural | 507.2 (502.2–512.2) | 152.0 (149.4–154.6) |
| Iowa urban | 501.8 (497.6–506.0) | 145.5 (143.3–147.7) |
| U.S. rural | 466.6 (465.9–467.4) | 164.9 (164.4–165.3) |
| U.S. urban | 450.9 (450.6–451.2) | 139.2 (139.1–139.4) |

These are aggregate age-adjusted rates calculated from cases/populations, not arithmetic averages of county rates. Iowa's high incidence affects rural and urban communities. Iowa rural mortality exceeds Iowa urban mortality, but remains below the national rural mortality rate. Files: `sources/iowa-incidence-ruralurban1.csv`, `...2.csv`, and mortality counterparts. Source URL adds `ruralurban=1` or `2` to the county export.

A [2026 primary mixed-methods Iowa study](https://link.springer.com/article/10.1007/s10552-026-02166-9), using older registry incidence/mortality 2015–2019, survival 2014–2019, BRFSS 2020–2021 and 2023 interviews, found rural disadvantages for colorectal incidence/deaths and survival for lung, pancreatic and ovarian cancer/myeloma. Rural respondents reported transportation and accessible-care barriers. Its screening/vaccination findings should retain their older data years. Do not present its 2015–2019 rankings as 2026 rankings.

## Interpretation safeguards

1. A cancer case is a new primary tumor, not necessarily a unique person; metastatic recurrence is not a new incidence event at the metastatic organ.
2. Registry rates generally exclude common basal/squamous skin cancers and most in-situ tumors; bladder invasive and in-situ are included. “All cancers” is a surveillance definition.
3. More cases can reflect population aging/growth and detection. Higher age-adjusted rates are not explained solely by Iowa being older.
4. Incidence, mortality, survival, prevalence and projected future counts answer different questions. Dividing annual deaths by annual diagnoses does not estimate a case-fatality rate.
5. Mortality may fall while incidence rises due to treatment, stage mix, screening and diagnostic changes. Survival can improve partly through lead-time and overdiagnosis; death-rate trends add important context.
6. Registry residence is generally at diagnosis and is not lifetime residence. Long cancer latency makes current county maps poor stand-ins for cumulative environmental exposure.
7. County-level association cannot establish individual causation. A high cancer county is not automatically a statistically verified cancer cluster, and a low county rate cannot prove an exposure is safe.
8. Comparisons containing 2020 are affected by pandemic diagnostic disruptions. Do not call the rebound in diagnoses proof of a new carcinogenic exposure without separate evidence.
9. Keep detailed primary-source datasets as the audit record. Search results can remain cached after the underlying live data changes; that happened in this research.

## Local files delivered to root

- `iowa-99-counties-comparison.csv`: 99 county rows, combined measures, all uncertainties.
- `iowa-county-incidence-2019-2023.csv`, `iowa-county-mortality-2020-2024.csv`: cleaned source tables including Iowa/U.S.
- `us-state-incidence-2019-2023.csv`, `us-state-mortality-2020-2024.csv`: all 53 source rows, including U.S./DC/PR.
- `iowa-demographic-comparison.csv`: selected age, sex, race/ethnicity rates for Iowa and U.S.
- `iowa-cancer-types-comparison.csv`: paired Iowa/U.S. cancer-specific data and URLs; childhood <20 anomaly flagged above.
- `data-provenance.json`: main source URLs, periods, data release/submission notes, generated time.
- `sources/*`: unmodified CSV downloads with footnotes and access-failure HTML.
