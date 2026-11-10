"""Read the pinned Oren Figure 1 workbook without editing its contents.

Extract source matrices locally and publish structural diagnostics only. Codes,
time maps and row joins remain assumptions until independently documented.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from collections import Counter
from zipfile import ZipFile
import argparse
import hashlib
import json
import platform
import re
import xml.etree.ElementTree as ET

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/treatment-discovery/sources/lineage-2026-11-10'
OUT=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10'
URL='https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-021-03796-6/MediaObjects/41586_2021_3796_MOESM8_ESM.xlsx'
SHA='a53fe57483b0e55a3b2545f611ff2cf2a31338b8c9dffad0f9af1522222d8f7c'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()


def column(ref):
    letters=re.match(r'[A-Z]+',ref).group()
    n=0
    for ch in letters:n=26*n+ord(ch)-64
    return n-1


def read_sheet(z,path,strings):
    rows=[];formulas=0;errors=0;written=0
    with z.open(path) as f:
        for event,el in ET.iterparse(f,events=('end',)):
            if el.tag!='{'+NS['s']+'}row':continue
            r=int(el.attrib['r'])-1
            while len(rows)<=r:rows.append([])
            for c in el.findall('s:c',NS):
                k=column(c.attrib['r'])
                while len(rows[r])<=k:rows[r].append(None)
                formulas+=c.find('s:f',NS) is not None
                typ=c.attrib.get('t')
                errors+=typ=='e'
                v=c.find('s:v',NS)
                if typ=='inlineStr':value=''.join(c.itertext())
                elif v is None:value=None
                elif typ=='s':value=strings[int(v.text)]
                elif typ=='e':value=v.text
                else:value=float(v.text)
                rows[r][k]=value;written+=1
            el.clear()
    return rows,{'written_cells':written,'formulas':formulas,'error_cells':errors}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download',action='store_true',help='Acquire pinned source if absent')
    args=p.parse_args()
    SOURCE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    original=SOURCE/'Oren-2021-Figure1-source.xlsx'
    if not original.exists():
        if not args.download:raise FileNotFoundError('Source absent; use --download to acquire the pinned public workbook')
        with urlopen(Request(URL,headers={'User-Agent':'Iowa-Cancer-Research/1.0'}),timeout=60) as response:
            data=response.read()
        assert hashlib.sha256(data).hexdigest()==SHA,'Source bytes differ from pinned audit'
        original.write_bytes(data)
    assert sha(original)==SHA
    sheets={};tables={};diagnostics={}
    with ZipFile(original) as z:
        strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)] if 'xl/sharedStrings.xml' in z.namelist() else []
        rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        for s in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',NS):
            name=s.attrib['name'];target=rels[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            path=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            rows,meta=read_sheet(z,path,strings)
            width=max(map(len,rows));rows=[r+[None]*(width-len(r)) for r in rows]
            tables[name]=rows
            info={'rows':len(rows),'columns':width,**meta}
            if name in ('Figure 1b-divison','Figure 1b-death'):
                a=np.array(rows,dtype=float);sheets[name]=a
                vals,n=np.unique(a[~np.isnan(a)],return_counts=True)
                info.update({'numeric_value_counts':dict(zip(map(str,vals),map(int,n))),
                    'missing_cells':int(np.isnan(a).sum()),'rows_with_missing_cells':int(np.isnan(a).any(axis=1).sum()),
                    'first_column_value_counts':dict(Counter(map(str,a[:,0]))),'last_column_value_counts':dict(Counter(map(str,a[:,-1]))),
                    'interpretation':'Numeric structure only; do not equate source codes with events or state labels without source documentation.'})
            else:
                info['header_row']=rows[0]
                info['first_column_types']=sorted(set(type(r[0]).__name__ for r in rows))
            diagnostics[name]=info
            print('Read',name,len(rows),width,flush=True)
    assert all(x.shape==(1135,2025) for x in sheets.values())
    assert all(d['formulas']==0 and d['error_cells']==0 for d in diagnostics.values())
    cache=SOURCE/'oren-figure1-matrices.npz'
    np.savez_compressed(cache,division=sheets['Figure 1b-divison'],death=sheets['Figure 1b-death'])
    (SOURCE/'oren-figure1-small-tables.json').write_text(json.dumps({k:v for k,v in tables.items() if k not in sheets},indent=2,allow_nan=False)+'\n')
    result={'retrieved_or_verified_utc':datetime.now(timezone.utc).isoformat(),'source_url':URL,'source_path':str(original.relative_to(ROOT)),
        'source_sha256':SHA,'source_bytes':original.stat().st_size,'code_sha256':sha(__file__),
        'environment':{'python':platform.python_version(),'numpy':np.__version__},'sheets':diagnostics,
        'derived_cache':{'path':str(cache.relative_to(ROOT)),'sha256':sha(cache),'public':False},
        'limits':['Raw workbook and extracted matrices remain local; no raw source mirror published.',
                  'No inferred time mapping, event-rate estimate, row join or biological model fitted by this structural audit.',
                  'Original XLSX bytes unchanged; all cell positions and missing values retained.']}
    (OUT/'workbook-structure.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert sha(original)==SHA
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
