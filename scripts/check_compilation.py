from pathlib import Path
import csv,json,re,hashlib
from pypdf import PdfReader
R=Path(__file__).resolve().parents[1]
def rows(f):return list(csv.DictReader((R/f).open()))
counties=rows('research/iowa-99-counties-comparison.csv')
assert len(counties)==99 and len({x['fips'] for x in counties})==99
for x in counties:
 for measure in ['incidence','mortality']:
  assert float(x[f'{measure}_lower_95ci'])<=float(x[f'{measure}_rate'])<=float(x[f'{measure}_upper_95ci'])
  assert x[f'{measure}_period']==('2019-2023' if measure=='incidence' else '2020-2024')
for f in ['research/us-state-incidence-2019-2023.csv','research/us-state-mortality-2020-2024.csv']:
 assert len(rows(f))==53
src=json.loads((R/'research/source-index.json').read_text());assert [x['id'] for x in src]==list(range(1,75))
text=(R/'Iowa-Cancer-Research.md').read_text()
for m in re.finditer(r'\[([0-9]+(?:\s*[-,]\s*[0-9]+)*)\]',text):
 for n in re.findall(r'\d+',m.group(1)): assert 1<=int(n)<=len(src)
pdf=R/'output/pdf/Iowa-Cancer-Research-2026-10-22.pdf';reader=PdfReader(pdf)
assert len(reader.pages)==19
alltext='\n'.join(p.extract_text() for p in reader.pages)
for phrase in ['504.1','453.4','148.2','143.2','21,700','76%','2.98','January 1, 2027','74.']:
 assert phrase in alltext,phrase
assert 'HTTP 403' in alltext
assert not any(token in alltext for token in ['turn80view','turn4search','TODO','PLACEHOLDER'])
links=sum(len(p.get('/Annots',[])) for p in reader.pages);assert links>200
pdf_sources=[]
for p in (R/'sources').rglob('*.pdf'):
 assert p.read_bytes().startswith(b'%PDF'),str(p)
 pdf_sources.append(str(p.relative_to(R)))
flags=[x for x in rows('research/iowa-cancer-types-comparison.csv') if x.get('validation_note')]
assert flags,'Pediatric anomaly must remain flagged'
result={'checked_date':'2026-10-22','pdf_pages':len(reader.pages),'core_sources':len(src),'county_rows':len(counties),'unique_county_fips':99,'state_rows_each':53,'rate_confidence_interval_order':'passed','period_labels':'passed','numbered_references':'passed','key_pdf_text':'passed','clickable_pdf_annotations':links,'pdf_header_validation':'passed','archived_primary_and_review_pdfs':pdf_sources,'pediatric_anomaly':'flagged in original/derived table; excluded from interpretation','visual_review':'All 19 pages rendered and inspected; detailed checks of source list, nitrate table and screening table','pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'data_provenance':'research/data-provenance.json','note':'Checks validate compilation integrity, not the truth of every underlying scientific claim.'}
(R/'research/quality-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
# Comparison matrix uses plain evidence categories, not invented numeric confidence scores.
entries=[
 ('Tobacco','Established cause of multiple cancers','Current prevalence misses past smoking exposure','Iowa cessation/smoke-free measures; no individual attribution','13'),
 ('Alcohol','Established cause at multiple cancer sites','Site totals are not alcohol-attributable counts','Reduce exposure; share Iowa-specific education','14'),
 ('Excess body fat','Established risk for multiple cancer sites','National attributable fractions do not explain Iowa excess','Support activity and sustainable healthy weight','12;15'),
 ('Ultraviolet radiation','Established skin-cancer cause','Melanoma diagnosis also reflects detection and susceptibility','UV protection and avoid tanning','18'),
 ('HPV/HBV/HCV','Established infection-related cancer pathways','Vaccination does not treat established HPV infection','Indicated vaccination; HCV detection and treatment','19;71;74'),
 ('Radon','Established lung carcinogen with Iowa individual-level evidence','Historical 71.6% home survey is not a current census','Test; mitigate at EPA action levels; retest','22;23;24'),
 ('Drinking-water nitrate','Mixed cancer-specific observational evidence','Different contrasts, exposure models and null findings; no statewide causal fraction','Measure actual water; address exceedances; investigate long-term exposure','26;27;28;29;30;31;35'),
 ('Glyphosate','IARC probable hazard; divergent EPA assessment; AHS mixed findings','Main AHS overall/NHL null; AML imprecise/lagged signals','Ingredient-specific controls and updated assessment','37;38;73'),
 ('Atrazine/alachlor','IARC Group 2A since November 2025','Classification is not an Iowa attributable fraction','Reduce avoidable exposure; evaluate specific cancer evidence','36;39'),
 ('Dicamba','AHS liver/bile-duct association','Limited exposed cases; other earlier signals not persistent','Specific controls; replication and historical exposure assessment','40'),
 ('PFOA/PFOS','PFOA IARC Group 1; PFOS Group 2B','Targeted water sample not statewide random prevalence; no statewide attribution','Review monitoring; certified treatment where appropriate','43;44;45;46;47'),
 ('Animal feeding operations','Exploratory ecological and proxy-based cohort associations','No fixed personal risk from distance; nonmonotonic findings','Better individual exposure studies and source controls','41;42'),
 ('Arsenic/workplace carcinogens','Known hazards relevant to specific exposures','Do not presume source or dose from county residence','Well testing and occupational controls','31;33;48'),
 ('Firefighting','Established carcinogenic occupational circumstance','Not a general-population statewide risk estimate','Workplace exposure reduction and surveillance','49')]
with (R/'research/risk-evidence-matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['factor','evidence','main_limit','iowa_implication','report_source_ids']);w.writerows(entries)
