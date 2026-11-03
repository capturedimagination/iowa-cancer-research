from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal
import csv,json,hashlib,openpyxl
R=Path(__file__).resolve().parents[1];out=R/'research/industries';out.mkdir(exist_ok=True);raw=R/'sources/industries/statewide'
url='https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/2024_IA/csv'
rows=list(csv.DictReader((raw/'tri-2024-iowa-original.csv').open(encoding='utf-8-sig')))
assert len(rows)==1695 and {x['1. YEAR'] for x in rows}=={'2024'} and {x['8. ST'] for x in rows}=={'IA'}
def num(x,k):return Decimal(x[k] or '0')
def save(name,rs):
 with (out/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
metrics={'air':lambda x:num(x,'51. 5.1 - FUGITIVE AIR')+num(x,'52. 5.2 - STACK AIR'),'water':lambda x:num(x,'53. 5.3 - WATER'),'onsite':lambda x:num(x,'65. ON-SITE RELEASE TOTAL'),'offsite':lambda x:num(x,'88. OFF-SITE RELEASE TOTAL'),'total':lambda x:num(x,'107. TOTAL RELEASES')}
# Preserve all source rows. Group all units separately; Form A is an unquantified certification, not proof of zero release.
def group(keys):
 g={}
 for x in rows:
  identity=tuple(x[k] for k in keys)
  if identity not in g:
   rec={k.split('. ',1)[1].lower().replace(' ','_'):x[k] for k in keys}
   rec.update({'reporting_year':2024,'chemical_forms':0,'unquantified_form_a':0,'quantified_form_r_pounds':0,'quantified_form_r_grams':0})
   for unit in ['pounds','grams']:
    for metric in metrics:rec[f'reported_{metric}_{unit}']=Decimal(0)
    for metric in ['air','total']:rec[f'osha_carc_flag_{metric}_{unit}']=Decimal(0)
   rec.update({'source_url':url,'retrieved':'2026-10-22','interpretation':'Reported chemical quantities; not toxicity-weighted exposure or observed cancer. Form A certifications do not quantify releases.'});g[identity]=rec
  rec=g[identity];rec['chemical_forms']+=1
  if x['49. FORM TYPE']=='A':rec['unquantified_form_a']+=1;continue
  unit=x['50. UNIT OF MEASURE'].lower();assert unit in ['pounds','grams']
  rec[f'quantified_form_r_{unit}']+=1
  for m,fn in metrics.items():rec[f'reported_{m}_{unit}']+=fn(x)
  if x['46. CARCINOGEN']=='YES':
   for m in ['air','total']:rec[f'osha_carc_flag_{m}_{unit}']+=metrics[m](x)
 for rec in g.values():
  rec['quantity_status']='Form R reported quantities only; Form A releases unknown' if rec['unquantified_form_a'] else 'Form R reported quantities only'
  for unit in ['pounds','grams']:
   if rec[f'quantified_form_r_{unit}']==0:
    for m in metrics:rec[f'reported_{m}_{unit}']=None
    for m in ['air','total']:rec[f'osha_carc_flag_{m}_{unit}']=None
 return list(g.values())
fac=group(['2. TRIFD'])
for a in fac:
 matches=[x for x in rows if x['2. TRIFD']==a['trifd']]
 for key in ['3. FRS ID','4. FACILITY NAME','6. CITY','7. COUNTY','23. INDUSTRY SECTOR','30. PRIMARY NAICS']:
  a[key.split('. ',1)[1].lower().replace(' ','_')]='; '.join(sorted({x[key] for x in matches}))
 a['multiple_reported_naics_or_sectors']=len({x['30. PRIMARY NAICS'] for x in matches})>1 or len({x['23. INDUSTRY SECTOR'] for x in matches})>1
assert len(fac)==463
save('tri-2024-iowa-facilities.csv',sorted(fac,key=lambda x:x['facility_name']))
sec=group(['23. INDUSTRY SECTOR']);save('tri-2024-iowa-sectors.csv',sorted(sec,key=lambda x:x['industry_sector']))
chem=group(['37. CHEMICAL','40. CAS#','46. CARCINOGEN','50. UNIT OF MEASURE']);save('tri-2024-iowa-chemicals.csv',sorted(chem,key=lambda x:x['chemical']))
carc=[dict(x,source_url=url,retrieved='2026-10-22') for x in rows if x['46. CARCINOGEN']=='YES'];save('tri-2024-iowa-carcinogen-flagged-records.csv',carc)
# Original xlsx files are read only; Iowa extractions preserve all source columns and units.
state={};county={};urls=[]
for geo in ['state','county']:
 for typ in ['srcgrp','poll']:
  name=f'national_cancerrisk_by_{geo}_{typ}.xlsx';u=f'https://www.epa.gov/system/files/documents/2025-01/{name}';urls.append(u)
  w=openpyxl.load_workbook(raw/name,read_only=True,data_only=True);it=w.active.iter_rows(values_only=True);hdr=next(it);rs=[dict(zip(hdr,x)) for x in it];ia=[x for x in rs if x['State']=='IA']
  if geo=='county':
   assert len(ia)==99
   for x in ia:x['FIPS']=str(x['FIPS']).zfill(5)
  for x in ia:x.update({'assessment_year':2020,'source_url':u,'retrieved':'2026-10-22'})
  save(f'airtoxscreen-2020-iowa-{geo}-{typ}.csv',ia)
  (state if geo=='state' else county)[typ]=ia
summary={'retrieved':'2026-10-22','tri_reporting_year':2024,'tri_page_processed_as_of':'2025-11-05','tri_rows':len(rows),'tri_facilities':len(fac),'tri_sectors':len(sec),'tri_osha_carc_flag_rows':len(carc),'tri_form_a_certifications':sum(x['49. FORM TYPE']=='A' for x in rows),'tri_units':dict(Counter(x['50. UNIT OF MEASURE'] for x in rows)),'tri_all_chemicals_reported_total_pounds':str(sum((x['reported_total_pounds'] or Decimal(0)) for x in sec)),'tri_all_chemicals_reported_air_pounds':str(sum((x['reported_air_pounds'] or Decimal(0)) for x in sec)),'tri_carc_flag_total_pounds':str(sum((x['osha_carc_flag_total_pounds'] or Decimal(0)) for x in sec)),'tri_carc_flag_air_pounds':str(sum((x['osha_carc_flag_air_pounds'] or Decimal(0)) for x in sec)),'airtoxscreen_assessment_year':2020,'airtoxscreen_iowa_counties':len(county['poll']),'airtoxscreen_iowa_total_lifetime_risk_per_million_rounded':state['poll'][0]['Total Cancer Risk (per million)'],'airtoxscreen_cautions':['Not an annual incidence rate or number of observed cases.','Totals rounded by EPA to one significant figure; components retain numerical model precision, not scientific precision.','Does not quantify diesel particulate cancer risk; diesel-related other pollutants may contribute.','Does not include every workplace exposure, indoor source, radon or contaminant pathway.','Secondary chemistry is not a simple facility or industry attribution.','2020 conditions, including pandemic effects; not proof of current conditions.'],'sources':[url]+urls,'original_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in raw.iterdir() if p.suffix in ['.csv','.xlsx']},'transformations':['Raw files retained without modification.','All 1695 TRI forms retained in original; groupings sum reported numeric Form R quantities, with Form A counted separately as unquantified.','Pounds and grams always kept separate; absent numeric Form R records in a unit yield blank summary quantities, not inferred zero releases.','OSHA carcinogen flag is the source category; it is not a uniform potency or IARC Group 1 classification.','Iowa rows extracted from national AirToxScreen workbooks; all 99 counties retained; source columns preserved.','Four facilities report more than one primary NAICS across chemical forms; all values retained as semicolon lists in facility summary.','No release-risk or release-cancer correlations calculated.']}
(out/'statewide-industry-data-provenance.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['original_sha256','sources','airtoxscreen_cautions','transformations']},indent=2))
print('AirToxScreen Iowa county total risk range',min(x['Total Cancer Risk (per million)'] for x in county['poll']),max(x['Total Cancer Risk (per million)'] for x in county['poll']))
