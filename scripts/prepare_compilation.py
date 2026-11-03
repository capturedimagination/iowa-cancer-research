from pathlib import Path
import json,csv,re
root=Path(__file__).resolve().parents[1]
p=root/'Iowa-Cancer-Research.md'
s=p.read_text()
# Idempotent: references are regenerated from the canonical table.
s=s.split('\n<!-- SOURCES START -->')[0]
data='''1|NCI State Cancer Profiles: all-site incidence by state, live 2019-2023 download|https://statecancerprofiles.cancer.gov/incidencerates/index.php?stateFIPS=00&areatype=state&cancer=001&race=00&sex=0&age=001&type=incd&year=0&sortVariableName=rate&sortOrder=desc&output=1|Federal surveillance
2|NCI State Cancer Profiles: all-site mortality by state, live 2020-2024 download|https://statecancerprofiles.cancer.gov/deathrates/index.php?stateFIPS=00&areatype=state&cancer=001&race=00&sex=0&age=001&type=death&year=0&sortVariableName=rate&sortOrder=desc&output=1|Federal surveillance
3|Iowa Cancer Registry: Cancer in Iowa 2026, especially pages 3-6|https://shri.public-health.uiowa.edu/wp-content/uploads/2026/03/2026-Cancer-in-Iowa.pdf|Registry report; indexed content, direct download blocked
4|University of Iowa: 2026 report and Agricultural Health Study farming findings|https://www.public-health.uiowa.edu/news-items/2026-cancer-in-iowa-report-highlights-cancer-incidence-among-iowas-farming-population/|University research release
5|NCI: all-site Iowa county incidence, 2019-2023|https://statecancerprofiles.cancer.gov/incidencerates/index.php?stateFIPS=19&areatype=county&cancer=001&race=00&sex=0&age=001&type=incd&year=0&sortVariableName=rate&sortOrder=desc&output=1|Federal surveillance
6|NCI: all-site Iowa county mortality, 2020-2024|https://statecancerprofiles.cancer.gov/deathrates/index.php?stateFIPS=19&areatype=county&cancer=001&race=00&sex=0&age=001&type=death&year=0&sortVariableName=rate&sortOrder=desc&output=1|Federal surveillance
7|NCI query collection: cancer types, demographics and rural/urban filters; exact query URLs in project data|https://statecancerprofiles.cancer.gov/|Federal surveillance; archived queries in research/sources and CSVs
8|Iowa HHS: Cancer Data definitions and limitations|https://hhs.iowa.gov/about/data-reports/cancer-data|Official surveillance documentation
9|Iowa Medical Society: Year One Cancer Drivers clinical summary|https://www.iowamedical.org/cancer-resources/|Clinical summary of research; not original full methods
10|Iowa HHS: cancer study landing page and Year 1 report link|https://hhs.iowa.gov/health-prevention/cancer|Official project landing page
11|University of Iowa: Key Drivers interim report, February 2026|https://iphprp.org/wp-content/uploads/2026/02/Interim-Progress-Report-Cancer-Driver-Project-Feb-2026-final-.pdf|Interim research report; indexed content
12|Islami et al. 2024: modifiable risk factors and U.S. cancer burden, original model|https://pubmed.ncbi.nlm.nih.gov/38990124/|Original research; U.S. adults 30+, 2019
13|NCI: tobacco and cancer|https://www.cancer.gov/about-cancer/causes-prevention/risk/tobacco/cessation-fact-sheet|Official cancer-risk and cessation guidance
14|U.S. Surgeon General: Alcohol and Cancer Risk advisory, 2025|https://www.hhs.gov/sites/default/files/oash-alcohol-cancer-risk.pdf|Official evidence assessment
15|NCI: obesity and cancer|https://www.cancer.gov/about-cancer/causes-prevention/risk/obesity/obesity-fact-sheet|Official cancer-risk guidance
16|Iowa HHS: 2025 BRFSS findings brief, October 2026|https://hhs.iowa.gov/media/19634/download?inline=|Primary survey report; 2025 crude weighted estimates
17|Iowa HHS: 2024 BRFSS findings brief, October 2025|https://publications.iowa.gov/54375/1/2024%20BRFSS%20Survey%20Findings%20Brief_Final.pdf|Primary survey report; 2024 screening measures
18|Iowa HHS: melanoma data and UV risk|https://hhs.iowa.gov/about/data-reports/cancer/melanoma-skin-data|Official cancer-risk guidance
19|CDC: HPV vaccination considerations|https://www.cdc.gov/hpv/hcp/vaccination-considerations/|Current official guidance
20|CDC MMWR: 2025 adolescent vaccination coverage, September 3, 2026, Table 3|https://www.cdc.gov/mmwr/volumes/75/wr/mm7534a1.htm|Primary survey analysis
21|NCI: Genetic Testing for Inherited Cancer Risk|https://www.cancer.gov/about-cancer/causes-prevention/genetics/genetic-testing-fact-sheet|Official clinical information
22|Iowa HHS: Radon Resources, household survey and residential rules|https://hhs.iowa.gov/health-prevention/providers-professionals/radiological-health/radon/radon-resources|Official state guidance; historical survey
23|Field et al. 2000: Iowa residential radon and lung cancer study|https://academic.oup.com/aje/article-abstract/151/11/1091/87328|Original case-control study; doi:10.1093/oxfordjournals.aje.a010153
24|EPA: radon action level and its meaning|https://www.epa.gov/radon/what-epas-action-level-radon-and-what-does-it-mean|Official action guidance
25|Iowa HHS: radon in K-12 schools|https://hhs.iowa.gov/health-prevention/providers-professionals/radiological-health/radon/radon-k-12-schools|Official state requirements
26|Iowa HHS: public-water nitrate results and units|https://hhs.iowa.gov/about/data-reports/environment/drinking-water/nitrate|Official water guidance
27|Inoue-Choi et al. 2015: nitrate and ovarian cancer, Iowa Women's Health Study|https://pubmed.ncbi.nlm.nih.gov/25430487/|Original cohort study; doi:10.1002/ijc.29365
28|Jones et al. 2016: nitrate and bladder cancer, Iowa Women's Health Study|https://pubmed.ncbi.nlm.nih.gov/27258851/|Original cohort study; doi:10.1289/EHP191
29|Ammons et al. 2025: water contaminants and ovarian cancer, Agricultural Health Study|https://pubmed.ncbi.nlm.nih.gov/40370528/|Original cohort study; doi:10.1097/EE9.0000000000000382
30|Spaur et al. 2026: drinking-water nitrate and prostate cancer, Agricultural Health Study|https://pubmed.ncbi.nlm.nih.gov/41423865/|Original cohort study; doi:10.1093/jnci/djaf350
31|NCI DCEG: drinking-water contaminant research, including positive and null Iowa findings|https://dceg.cancer.gov/research/what-we-study/drinking-water-contaminants|Official research synthesis
32|Iowa DNR: 2025 public-water compliance report, June 2026, printed pages 1 and 21|https://www.iowadnr.gov/media/9746/download?inline=|Primary monitoring report
33|Iowa DNR: private-well testing and grants|https://www.iowadnr.gov/environmental-protection/water-quality/private-well-program/well-testing|Official testing guidance
34|EPA: nitrate drinking-water FAQs and response to an exceedance|https://www.epa.gov/mn/what-should-i-do-if-my-water-has-elevated-nitrates-andor-exceeds-mcl|Official health/treatment guidance
35|Jones et al. 2017: nitrate and kidney cancer, Iowa Women's Health Study|https://pmc.ncbi.nlm.nih.gov/articles/PMC5538922/|Original cohort study; doi:10.1097/EDE.0000000000000647
36|IARC: atrazine, alachlor and vinclozolin evaluation, November 21, 2025|https://www.iarc.who.int/news-events/iarc-monographs-evaluation-of-the-carcinogenicity-of-atrazine-alachlor-and-vinclozolin/|Primary hazard evaluation
37|Andreotti et al. 2018: glyphosate and cancer incidence, Agricultural Health Study|https://pmc.ncbi.nlm.nih.gov/articles/PMC6279255/|Original cohort study; doi:10.1093/jnci/djx233
38|EPA: glyphosate assessment and registration-review status|https://www.epa.gov/ingredients-used-pesticide-products/glyphosate|Official regulatory/scientific status
39|Remigio et al. 2024: atrazine and cancer incidence, Agricultural Health Study|https://pubmed.ncbi.nlm.nih.gov/38381478/|Original cohort study; doi:10.1289/EHP13684
40|Lerro et al. 2020: dicamba and cancer incidence, Agricultural Health Study|https://pubmed.ncbi.nlm.nih.gov/32357211/|Original cohort study; doi:10.1093/ije/dyaa066
41|Son et al. 2026: animal feeding operation density and county cancer incidence|https://pubmed.ncbi.nlm.nih.gov/41856233/|Original ecological study; doi:10.1016/j.envres.2026.124298
42|Jones et al. 2020: proximity to animal feeding operations and cancer in Iowa AHS|https://pmc.ncbi.nlm.nih.gov/articles/PMC7889404/|Original cohort analysis; exposure proxies and nonmonotonic findings
43|IARC: PFOA and PFOS carcinogenicity evaluation, 2023|https://www.iarc.who.int/news-events/iarc-monographs-evaluate-the-carcinogenicity-of-perfluorooctanoic-acid-pfoa-and-perfluorooctanesulfonic-acid-pfos.|Primary hazard evaluation
44|Iowa DNR: targeted PFAS public-water sampling, March 2023 report|https://www.iowadnr.gov/media/7038/download?inline=|Primary monitoring report; 2021-2022 sampling
45|EPA: proposed PFOA/PFOS compliance extension, May 2026|https://www.epa.gov/sdwa/proposed-pfoa-and-pfos-compliance-extension-rule|Official proposal; distinguish from final rule
46|Iowa DNR: PFAS and private wells|https://www.iowadnr.gov/media/4619/download?inline=|Official testing information
47|EPA: filters certified to reduce PFAS|https://www.epa.gov/water-research/identifying-drinking-water-filters-certified-reduce-pfas|Official treatment guidance
48|NCI: cancer-causing substances in the environment|https://www.cancer.gov/about-cancer/causes-prevention/risk/substances|Official hazard information
49|IARC: occupational firefighting carcinogenicity evaluation, July 2022|https://www.iarc.who.int/wp-content/uploads/2022/07/pr317_E.pdf|Primary hazard evaluation
50|USPSTF: final breast screening recommendation, April 2024|https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening|Final clinical recommendation
51|USPSTF: final colorectal screening recommendation, May 2021|https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/colorectal-cancer-screening|Final clinical recommendation
52|USPSTF: final lung screening recommendation, March 2021|https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/lung-cancer-screening|Final clinical recommendation
53|USPSTF: final cervical screening recommendation, August 2018|https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cervical-cancer-screening|Final recommendation; update in progress
54|USPSTF: final prostate screening recommendation, May 2018|https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/prostate-cancer-screening|Final recommendation; update in progress
55|Iowa HHS: cancer screening participant eligibility, July 2026-June 2027|https://hhs.iowa.gov/health-prevention/cancer/cancer-services-participant-eligibility|Current program eligibility; confirm with coordinator
56|Quitline Iowa|https://www.quitlineiowa.org/|Direct service resource
57|NCI: Holden Comprehensive Cancer Center designation|https://www.cancer.gov/research/infrastructure/cancer-centers/find/iowaholden|Official cancer-center profile
58|UI Health Care: cancer clinical trials|https://uihc.org/cancer/cancer-clinical-trials|Direct treatment/research resource
59|UI Health Care: cancer financial and billing assistance|https://uihc.org/cancer/financial-and-billing-assistance|Direct financial-assistance resource
60|American Cancer Society: Hope Lodge|https://www.cancer.org/support-programs-and-services/patient-lodging/hope-lodge.html|Direct lodging resource; eligibility/availability apply
61|Iowa Cancer Consortium: 2023-2027 Iowa Cancer Plan|https://canceriowa.org/iowa-cancer-plan/|Statewide collaborative plan
62|IDALS: Farm to Faucet bill signing and funding, June 1, 2026|https://iowaagriculture.gov/news/farm-faucet-water-quality-bill-sign|Official enacted-program announcement
63|University of Iowa: Cancer Assessment appropriation narrative|https://budget.fo.uiowa.edu/special-purpose-appropriations-budget-narratives/cancer-assessment-narrative|Official project scope/budget
64|CDC: cancer patterns, cluster definition and investigation limits, May 2026|https://www.cdc.gov/cancer-environment/php/guidelines/characteristics.html|Official investigation guidance
65|Iowa Cancer Registry: Cancer in Iowa 99 Counties Project|https://shri.public-health.uiowa.edu/cancer-data/cancer-in-iowa-99-counties-project/|Direct public-education resource
66|Iowa Acts 2026 chapter 1087, HF2635, sections 7-11, pages 4-7|https://www.legis.iowa.gov/docs/publications/iactc/91.2/CH1087.pdf|Enacted law; January 2027 applicability
67|IEC/Harkin: Environmental Risk Factors and Iowa's Cancer Crisis, March 2026|https://www.iaenvironment.org/webres/File/Environmental%20Risk%20Factors%20and%20Iowa%27s%20Cancer%20Crisis%20-%20Report.pdf|Secondary literature/policy synthesis; original studies prioritized
68|NCI: questions and answers about multicancer detection tests|https://prevention.cancer.gov/research-areas/networks-consortia-programs/csrn/q-a-about-mcd-tests|Official screening evidence guidance
69|Nash et al. 2026: rural Iowa cancer burden and stakeholder care-access study|https://pmc.ncbi.nlm.nih.gov/articles/PMC13079507/|Original mixed-methods study; doi:10.1007/s10552-026-02166-9
70|UI Health Care: Mission Cancer + Blood network acquisition, January 2025|https://uihealthcare.org/press-release/mission-cancer-blood-now-officially-part-university-iowa-health-care|Direct health-system announcement
71|CDC: hepatitis B prevention|https://www.cdc.gov/hepatitis-b/prevention/index.html|Official infection-prevention guidance
72|American Cancer Society: lung cancer screening guideline|https://www.cancer.org/cancer/types/lung-cancer/detection-diagnosis-staging/detection.html|Clinical guideline; differs from USPSTF
73|IARC: glyphosate classification and questions, 2015|https://www.iarc.who.int/featured--news/media-centre-iarc-news-glyphosate|Primary hazard evaluation
74|CDC: hepatitis C treatment and liver-cancer prevention|https://www.cdc.gov/hepatitis-c/treatment/index.html|Official clinical guidance'''
refs=[]
for line in data.splitlines():
 n,title,url,kind=line.split('|',3);refs.append(dict(id=int(n),title=title,url=url,evidence_type=kind,access_date='2026-10-22'))
(root/'research/source-index.json').write_text(json.dumps(refs,indent=2))
with (root/'research/source-index.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=refs[0].keys());w.writeheader();w.writerows(refs)
register='\n<!-- SOURCES START -->\n\n<!-- PAGE -->\n\n## Source register\n\nAll sources were checked or retrieved on October 22, 2026. Data periods and access limitations are recorded in the report and detailed memos. Citation 7 is a collection of live federal queries; the exact cancer-specific URLs are retained in the cancer-types CSV, with subgroup and rural/urban originals in `research/sources/`.\n\n'
for r in refs: register+=f"**{r['id']}.** [{r['title']}]({r['url']}). {r['evidence_type']}.\n\n"
register+='\n'+ '\n'.join(f"[{r['id']}]: {r['url']}" for r in refs)+'\n'
p.write_text(s+register)
# Additional sources are discoverable without treating every link as equally authoritative.
links={}
for note in sorted((root/'research').glob('*.md')):
 for url in re.findall(r'https?://[^\s<>\]\)]+',note.read_text()):
  url=url.rstrip('.,;');links.setdefault(url,set()).add(note.name)
with (root/'research/additional-source-links.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['url','research_memos']);w.writerows((u,'; '.join(sorted(m))) for u,m in sorted(links.items()))
print(f'{len(refs)} core sources; {len(links)} memo links; report {len(s.split())} words before register')
