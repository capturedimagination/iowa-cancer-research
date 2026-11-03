# Data guide

Retrieval date: October 22, 2026. Source: NCI/CDC State Cancer Profiles, with original footnotes preserved in `research/sources/`. Refer to the source URLs and each table's actual period instead of a search preview.

## Files

| File | Contents |
|---|---|
| iowa-99-counties-comparison.csv | Exactly 99 counties; incidence and mortality joined by five-digit county FIPS |
| iowa-county-incidence-2019-2023.csv | 99 counties plus Iowa and U.S. reference rows |
| iowa-county-mortality-2020-2024.csv | 99 counties plus Iowa and U.S. reference rows |
| us-state-incidence-2019-2023.csv | States, DC, Puerto Rico and U.S. reference; 53 rows |
| us-state-mortality-2020-2024.csv | Same geography layout, 53 rows |
| iowa-cancer-types-comparison.csv | Paired Iowa/U.S. rates, cancer sites, trends, exact query URLs and validation flags |
| iowa-demographic-comparison.csv | Paired Iowa/U.S. sex, race/ethnicity and age comparisons |
| data-provenance.json | Original main-table URLs, periods, source submissions, transformations and standards |
| source-index.csv / .json | Numbered core report sources and evidence types |
| additional-source-links.csv | Links appearing in detailed memos; not an independent quality ranking |

## Main county fields

- `county`, `fips`: county name and identifier. Keep FIPS as text when importing; leading zeros matter for national tables.
- `rural_urban_2023`: USDA 2023 Rural-Urban Continuum classification as supplied by NCI. County-level urban status does not mean every address is urban.
- `incidence_period`: 2019-2023. Rates are new cancers per 100,000 population per year, age-adjusted to the 2000 U.S. population.
- `mortality_period`: 2020-2024. Rates are cancer deaths per 100,000/year, age-adjusted to the 2000 U.S. population.
- `*_lower_95ci`, `*_upper_95ci`: uncertainty around the rate, not a range containing 95% of individual risks.
- `*_avg_annual_cases`, `*_avg_annual_deaths`: rounded annual average observed counts over the data period, not 2026 projections or necessarily unique persons.
- `*_ci_rank`, `*_rank_lower_ci`, `*_rank_upper_ci`: NCI's rank and uncertainty. Wide intervals mean small differences in point rank are not reliable distinctions.
- `*_trend`, `*_aapc`, `*_aapc_lower_ci`, `*_aapc_upper_ci`: recent modeled annual percent change and interval. Rising/falling requires the interval to exclude zero; stable does not mean exactly zero change.

## Other table codes

`sex_code`: 0 both sexes, 1 male, 2 female. `age_code`: 001 all ages; 009 under 50; 136 age 50+. `race_code`: 00 all races including Hispanic; 07 non-Hispanic White; 28 non-Hispanic Black; 05 Hispanic; 38 non-Hispanic American Indian/Alaska Native; 48 non-Hispanic Asian/Pacific Islander. The demographic table's `population` field labels the group; ethnicity and race definitions should not be casually interchanged.

## Interpretation safeguards

Most in-situ cancers and common basal/squamous skin cancers are excluded; bladder includes in-situ cases. A person can contribute multiple primary cancers. Breast and prostate rates use the relevant sex population. Incidence and mortality are different events in different periods: do not divide them to calculate survival.

NCI's displayed SEER incidence rates use 20 age groups and NPCR rates 19; CI*Rank uses 19 consistently. This explains Iowa's displayed-rate order versus assigned state rank. Preserve the source's assigned rank rather than recomputing it by sorting rounded displayed values.

The current all-sex Iowa mortality trend is classified stable despite falling male and female trends. This was reproduced in separate downloads. Joinpoint fitting and subgroup estimates can differ; the exact reason for the aggregate/subgroup discrepancy was not established here. Do not overwrite the published aggregate label.

The current childhood-under-20 Iowa cancer-specific export duplicates the under-15 rate/count. Its `validation_note` flags the unresolved anomaly. Preserve the original record but exclude it from substantive interpretation until clarified. The report uses the annual registry's explicitly dated pediatric comparisons instead.

County of residence at diagnosis is not lifetime residence or exposure. A high rate is a starting point for investigation, not proof of a local environmental cause. Do not average county rates to estimate a rural or state rate; use the direct aggregate queries preserved in `research/sources/`.
