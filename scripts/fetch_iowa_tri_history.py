from pathlib import Path
import urllib.request,concurrent.futures,hashlib,json,csv,io,time
R=Path(__file__).resolve().parents[1];base=R/'sources/industries/tri-history';base.mkdir(parents=True,exist_ok=True)
def fetch(y):
 u=f'https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{y}_IA/csv';p=base/f'tri-{y}-iowa-original.csv'
 if p.exists():b=p.read_bytes()
 elif y==2024 and (R/'sources/industries/statewide/tri-2024-iowa-original.csv').exists():b=(R/'sources/industries/statewide/tri-2024-iowa-original.csv').read_bytes();p.write_bytes(b)
 else:
  try:
   b=urllib.request.urlopen(u,timeout=45).read()
   text=b.decode('utf-8-sig');rows=list(csv.DictReader(io.StringIO(text)))
   if not rows or not any('YEAR' in k for k in rows[0]):raise ValueError('Response was not a populated TRI CSV')
   p.write_bytes(b)
  except Exception as e:return {'year':y,'url':u,'status':'failed','error':str(e),'retrieved':'2026-10-22'}
 rows=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))))
 return {'year':y,'url':u,'status':'downloaded','file':str(p.relative_to(R)),'bytes':len(b),'rows':len(rows),'fields':len(rows[0]),'sha256':hashlib.sha256(b).hexdigest(),'retrieved':'2026-10-22'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=sorted(ex.map(fetch,range(1987,2025)),key=lambda x:x['year'])
(R/'research/industries/tri-history-manifest.json').write_text(json.dumps({'snapshot_date':'2026-10-22','source_page':'https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present','warning':'Raw reporting history, not a harmonized exposure panel. Chemical list, thresholds, sectors, definitions, ownership and facility reporting change. Nonreporting is not zero. No health association model has been fitted from these files.','files':r},indent=2))
print(json.dumps({'years_downloaded':sum(x['status']=='downloaded' for x in r),'rows':sum(x.get('rows',0) for x in r),'bytes':sum(x.get('bytes',0) for x in r),'failures':[x for x in r if x['status']!='downloaded']},indent=2))
