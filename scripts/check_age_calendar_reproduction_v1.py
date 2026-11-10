#!/usr/bin/env python3
"""Exact scientific-payload comparison of seed-identical reproductions.

No simulator/model import and no random-number generation. First outputs remain
untouched. Timestamp, runtime, byte-container hash and documented v1/v2 metadata
name/code differences are explicitly excluded, while arrays, moments, thresholds,
reference inputs, seed components and RNG states must agree exactly.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
LOCAL=ROOT/'tmp/age-calendar-2026-11-10'
TREE_SHA='b7cbfb48c223a0772f96eb06b6f65a0ed2a55fcb92db139116ab94737679599c'
CAL_V1='e32fa093559cba285e31c0cddd07779f54bccf1f2e740727d2ae0bc611bdaeb2'
CAL_V2='b996075a2080f4a308e055d3aedc2f55d2ae2ceef038ab9a8068c2bcdb634cda'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def without(obj,keys):return {k:v for k,v in obj.items() if k not in keys}


def write_new(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    with tmp.open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.link(tmp,path);tmp.unlink()


def tree_equal(first_path,second_path,first_root,second_root):
    first,second=read(first_path),read(second_path)
    if first['code_sha256']!=TREE_SHA or second['code_sha256']!=TREE_SHA:
        raise ValueError('Tree generator changed between runs')
    if without(first,{'created_utc','cases'})!=without(second,{'created_utc','cases'}):
        raise ValueError('Tree run signatures/scopes differ')
    if first['completed_cases']!=20 or first['incomplete_cases']!=0:
        raise ValueError('Tree run incomplete')
    if len(first['cases'])!=20 or len(second['cases'])!=20:raise ValueError('Tree case count mismatch')
    arrays=0;batches=0;cells=0
    exclusions={'created_utc','runtime_seconds_this_invocation','batch_files'}
    for a,b in zip(first['cases'],second['cases']):
        if without(a,exclusions)!=without(b,exclusions):raise ValueError('Tree aggregate scientific field differs: '+a['case_id'])
        if len(a['batch_files'])!=40 or len(b['batch_files'])!=40:raise ValueError('Wrong tree batch count')
        cells+=a['diagnostics']['generated_cells']
        for fa,fb in zip(a['batch_files'],b['batch_files']):
            if fa['path']!=fb['path']:raise ValueError('Tree checkpoint label differs')
            pa,pb=Path(first_root)/fa['path'],Path(second_root)/fb['path']
            if sha(pa)!=fa['sha256'] or sha(pb)!=fb['sha256']:raise ValueError('Tree checkpoint hash invalid')
            with np.load(pa,allow_pickle=False) as da,np.load(pb,allow_pickle=False) as db:
                if set(da.files)!=set(db.files):raise ValueError('Tree checkpoint fields differ')
                for key in da.files:
                    if key=='metadata':
                        ma,mb=json.loads(str(da[key])),json.loads(str(db[key]))
                        if without(ma,{'created_utc'})!=without(mb,{'created_utc'}):raise ValueError('Tree checkpoint RNG/provenance differs')
                    else:
                        if not np.array_equal(da[key],db[key],equal_nan=True):raise ValueError('Tree founder array differs: '+key)
                        arrays+=1
            batches+=1
    return dict(status='EXACT_SCIENTIFIC_EQUALITY',cases=20,founders=200000,batches=batches,
                generated_cells=cells,arrays_compared=arrays,aggregate_exclusions=sorted(exclusions),
                batch_metadata_exclusions=['created_utc'],top_level_exclusions=['created_utc','cases (compared individually)'])


def normalized_calibration_batch(obj):
    out=without(obj,{'created_utc','code_sha256'})
    if 'method_names' in out:
        if 'methods' in out:raise ValueError('Conflicting method metadata keys')
        out['methods']=out.pop('method_names')
    return out


def calibration_equal(first_path,second_path,first_root,second_root):
    first,second=read(first_path),read(second_path)
    if first['code_sha256']!=CAL_V1 or second['code_sha256']!=CAL_V2:raise ValueError('Unexpected calibration version lineage')
    for report in (first,second):
        if report['completed_settings']!=720 or report['incomplete_settings']!=0 or report['completed_checks']!=5760:
            raise ValueError('Calibration run is incomplete')
    if first['check_status_counts']!=second['check_status_counts']:raise ValueError('Calibration gate outcomes differ')
    if len(first['settings'])!=720 or len(second['settings'])!=720:raise ValueError('Wrong calibration setting count')
    exclusions={'created_utc','code_sha256','batch_files','method_names'}
    batches=0;method_records=0
    for a,b in zip(first['settings'],second['settings']):
        if without(a,exclusions)!=without(b,exclusions):raise ValueError('Calibration aggregate field differs: '+a['setting_id'])
        if set(a['methods'])!=set(b['methods']) or not isinstance(a['methods'],dict):raise ValueError('Missing per-method records')
        method_records+=len(a['methods'])
        if len(a['batch_files'])!=10 or len(b['batch_files'])!=10:raise ValueError('Wrong calibration batch count')
        for fa,fb in zip(a['batch_files'],b['batch_files']):
            if fa['path']!=fb['path']:raise ValueError('Calibration batch label differs')
            pa,pb=Path(first_root)/fa['path'],Path(second_root)/fb['path']
            if sha(pa)!=fa['sha256'] or sha(pb)!=fb['sha256']:raise ValueError('Calibration batch hash invalid')
            if normalized_calibration_batch(read(pa))!=normalized_calibration_batch(read(pb)):
                raise ValueError('Calibration moment/RNG/seed batch differs')
            batches+=1
    return dict(status='EXACT_SCIENTIFIC_EQUALITY',settings=720,batches=batches,
                whole_experiments=36000000,method_records=method_records,all_5760_checks_identical=True,
                aggregate_exclusions=sorted(exclusions),batch_exclusions=['created_utc','code_sha256'],
                metadata_normalization='method_names renamed back to methods only at run/batch metadata level; per-setting methods dictionary compared unchanged',
                first_failure='Original first-run final packaging exit 1 retained; first comparison source is no-RNG recovered report.')


def fixtures():
    a={'created_utc':'first','code_sha256':CAL_V1,'methods':['x'],'moments':{'x':{'sum':2}},'rng_after':{'state':123}}
    b={'created_utc':'second','code_sha256':CAL_V2,'method_names':['x'],'moments':{'x':{'sum':2}},'rng_after':{'state':123}}
    assert normalized_calibration_batch(a)==normalized_calibration_batch(b)
    c={**b,'moments':{'x':{'sum':2.001}}};assert normalized_calibration_batch(a)!=normalized_calibration_batch(c)
    d={**b,'rng_after':{'state':124}};assert normalized_calibration_batch(a)!=normalized_calibration_batch(d)
    assert np.array_equal(np.array([1.,np.nan]),np.array([1.,np.nan]),equal_nan=True)
    assert not np.array_equal(np.array([1.]),np.array([1.+1e-12]),equal_nan=True)
    return dict(status='PASS',count=5,code_sha256=sha(__file__),fixtures=['only documented metadata differences normalized','changed numerical moment rejected','changed RNG state rejected','matching missing-event NaN preserved','no numerical equality tolerance'],reproduction_comparison_run=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true');p.add_argument('--fixture-report',type=Path)
    p.add_argument('--tree-first',type=Path,default=BASE/'tree-monte-carlo/results.json')
    p.add_argument('--tree-second',type=Path,default=BASE/'tree-monte-carlo/clean-reproduction-results.json')
    p.add_argument('--tree-first-root',type=Path,default=LOCAL/'tree-monte-carlo')
    p.add_argument('--tree-second-root',type=Path,default=LOCAL/'tree-monte-carlo-clean')
    p.add_argument('--calibration-first',type=Path,default=BASE/'calibration-monte-carlo/results.json')
    p.add_argument('--calibration-second',type=Path,default=BASE/'calibration-monte-carlo/clean-v2-results.json')
    p.add_argument('--calibration-first-root',type=Path,default=LOCAL/'calibration-monte-carlo')
    p.add_argument('--calibration-second-root',type=Path,default=LOCAL/'calibration-monte-carlo-clean-v2')
    p.add_argument('--output',type=Path,default=BASE/'monte-carlo-reproduction.json')
    args=p.parse_args();f=fixtures()
    if args.fixture_report:write_new(args.fixture_report,f)
    print(json.dumps(f,indent=2),flush=True)
    if args.run:
        tree=tree_equal(args.tree_first,args.tree_second,args.tree_first_root,args.tree_second_root)
        cal=calibration_equal(args.calibration_first,args.calibration_second,args.calibration_first_root,args.calibration_second_root)
        obj=dict(status='EXACT_SCIENTIFIC_EQUALITY',created_utc=datetime.now(timezone.utc).isoformat(),code_sha256=sha(__file__),
                 input_hashes={k:sha(v) for k,v in vars(args).items() if k in ('tree_first','tree_second','calibration_first','calibration_second')},
                 tree=tree,calibration=cal,scope='Same-seed exact reproducibility, not an independent statistical replicate or replacement of first outcomes.')
        write_new(args.output,obj);print(json.dumps({'tree':tree,'calibration':cal},indent=2),flush=True)


if __name__=='__main__':main()
