#!/usr/bin/env python3
"""No-draw recovery of first-run calibration batch sufficient statistics.

The original frozen simulator and all its first aggregates stay unchanged.
This script has no random-number library or simulator import. It reconstructs
only the report dictionary lost to a metadata-key collision.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
LOCAL=ROOT/'tmp/age-calendar-2026-11-10/calibration-monte-carlo'
PROTOCOL_SHA='53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919'
SIMULATOR_SHA='e32fa093559cba285e31c0cddd07779f54bccf1f2e740727d2ae0bc611bdaeb2'
METHODS=('oracle_bin_mean','shared_fitted_mean','shared_fitted_mean_corrected','unbiased_target_sample_covariance')
CHECKS,ALPHA,SLACK,R,BATCH=5760,.001,1e-8,50000,5000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    with tmp.open('x') as f:
        json.dump(data,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.link(tmp,path);tmp.unlink()


def check_mean(value,target,variance,width,count):
    if not all(math.isfinite(x) for x in (value,target,variance,width)) or variance<0 or width<0 or count<=0:
        raise ValueError('Invalid concentration arguments')
    error=abs(value-target)
    if variance==0:
        return dict(observed=value,expected=target,absolute_error=error,
                    status='structural_agreement' if error<=SLACK else 'flag',threshold=SLACK,
                    threshold_without_numerical_slack=0.,exact_float_agreement=value==target,variance_bound=0.)
    L=math.log(2*CHECKS/ALPHA)
    bound=math.sqrt(2*variance*L/count)+2*width*L/(3*count)
    return dict(observed=value,expected=target,absolute_error=error,
                status='not_flagged' if error<=bound+SLACK else 'flag',threshold=bound+SLACK,
                threshold_without_numerical_slack=bound,variance_bound=variance)


def recover_methods(setting,batches):
    methods={}
    m,n=setting['m'],setting['n']
    ranges=dict(zip(METHODS,[[-.25,1.],[-.25,1.],[-m/(4*(m-1)),1.],
                              [-n/(4*(n-1)),n/(4*(n-1))]]))
    for name in METHODS:
        entries=[b['moments'][name] for b in batches]
        count=sum(e['count'] for e in entries)
        if count!=R:
            raise ValueError('Wrong number of whole experiments')
        sums={key:math.fsum(e[key] for e in entries) for key in
              ('sum','sum_squares','sum_squared_deviation_from_analytic_mean')}
        ref=setting['reference_methods'][name]
        expected,var=ref['mean'],ref['variance']
        # The original code used its frozen algebraic ranges, not the saved
        # reference range. Retain that identical operation sequence here.
        a,b=ranges[name];width=b-a
        mean=sums['sum']/count;msd=sums['sum_squared_deviation_from_analytic_mean']/count
        methods[name]=dict(count=count,**sums,mean=mean,mean_squared_deviation_from_analytic_mean=msd,
            minimum=min(e['minimum'] for e in entries),maximum=max(e['maximum'] for e in entries),
            nonzero_deviation_count=sum(e['nonzero_deviation_count'] for e in entries),
            mean_check=check_mean(mean,expected,var,width,count),
            squared_deviation_check=check_mean(msd,var,width*width*var,width*width,count))
    return methods


def recover(folder,output,ledger,simulator_path,log_path):
    folder=Path(folder)
    if Path(output).resolve()==Path(ledger).resolve() or Path(output).exists() or Path(ledger).exists():
        raise FileExistsError('Recovery results and ledger require distinct fresh paths')
    protocol_path=BASE/'protocol.json'
    if sha(protocol_path)!=PROTOCOL_SHA or sha(simulator_path)!=SIMULATOR_SHA:
        raise ValueError('Original first-run protocol or simulator changed')
    manifest_path=folder/'run-manifest.json'
    manifest=json.loads(manifest_path.read_text())
    signature={k:v for k,v in manifest.items() if k!='created_utc'}
    if signature['code_sha256']!=SIMULATOR_SHA or signature['protocol_sha256']!=PROTOCOL_SHA:
        raise ValueError('Manifest provenance mismatch')
    if signature['methods']!=list(METHODS) or signature['experiments_per_setting']!=R or signature['batch_size']!=BATCH:
        raise ValueError('Manifest experimental contract mismatch')
    protocol=json.loads(protocol_path.read_text())
    expected=[]
    for ci,case in enumerate(protocol['cases']):
        for li,lag in enumerate((.5,1.,2.)):
            for bi,bid in enumerate(('w2-b0','w1-b0')):
                for mi,m in enumerate((5,20,100)):
                    for ni,n in enumerate((100,1000)):
                        expected.append((f'{case["case_id"]}-l{li}-b{bi}-m{mi}-n{ni}',
                            dict(case_id=case['case_id'],bin_id=bid,lag=lag,m=m,n=n,
                                 seed_components=[2026111014,ci,li,bi,mi,ni])))
    if len(expected)!=720 or len(list(folder.glob('*/aggregate.json')))!=720:
        raise ValueError('Original setting cardinality is not 720')
    if list(folder.glob('*/failures/*.json')):
        raise ValueError('Original setting failures require explicit separate review')
    if len(list(folder.glob('*/batches/*.json')))!=7200:
        raise ValueError('Original batch cardinality is not 7200')
    recovered=[];evidence=[];fields_compared=0;max_moment_identity_error=0.
    for sid,design in expected:
        aggregate_path=folder/sid/'aggregate.json'
        old=json.loads(aggregate_path.read_text())
        if old['status']!='complete' or old['methods']!=list(METHODS):
            raise ValueError('Unexpected first aggregate failure shape')
        if any(old.get(k)!=v for k,v in signature.items()) or any(old.get(k)!=v for k,v in design.items()):
            raise ValueError('First aggregate design/provenance mismatch')
        files=old['batch_files']
        if len(files)!=10:
            raise ValueError('Wrong original batch manifest length')
        batches=[];prior_state=None
        for index,record in enumerate(files):
            expected_path=f'{sid}/batches/{index*BATCH:05d}.json'
            if record['path']!=expected_path:
                raise ValueError('Unexpected batch path/order')
            path=folder/record['path']
            if sha(path)!=record['sha256']:
                raise ValueError('Original batch SHA differs from first aggregate')
            batch=json.loads(path.read_text())
            if any(batch.get(k)!=v for k,v in signature.items()):
                raise ValueError('Batch run provenance mismatch')
            if batch['experiment_start']!=index*BATCH or batch['experiment_count']!=BATCH:
                raise ValueError('Batch coverage gap/overlap')
            setting=batch['setting']
            if setting['setting_id']!=sid or any(setting.get(k)!=v for k,v in design.items()):
                raise ValueError('Batch seed/design mismatch')
            if any(old.get(k)!=v for k,v in setting.items()):
                raise ValueError('Saved setting differs from original aggregate')
            if batches and setting!=batches[0]['setting']:
                raise ValueError('Setting changed between batches')
            if prior_state is not None and batch['rng_before']!=prior_state:
                raise ValueError('Saved RNG state chain is discontinuous')
            if batch['rng_before'].get('bit_generator')!='PCG64' or batch['rng_after'].get('bit_generator')!='PCG64':
                raise ValueError('Wrong recorded RNG algorithm')
            prior_state=batch['rng_after']
            if set(batch['moments'])!=set(METHODS):
                raise ValueError('Missing estimator moment records')
            for name,moment in batch['moments'].items():
                if moment['count']!=BATCH or not 0<=moment['nonzero_deviation_count']<=BATCH:
                    raise ValueError('Wrong whole-experiment count')
                for key in ('sum','sum_squares','sum_squared_deviation_from_analytic_mean','minimum','maximum'):
                    if not math.isfinite(moment[key]):
                        raise ValueError('Nonfinite sufficient statistic')
                if moment['sum_squares']<0 or moment['sum_squared_deviation_from_analytic_mean']<0:
                    raise ValueError('Negative squared statistic')
                target=setting['reference_methods'][name]['mean']
                alternative=moment['sum_squares']-2*target*moment['sum']+BATCH*target*target
                gap=abs(alternative-moment['sum_squared_deviation_from_analytic_mean'])
                max_moment_identity_error=max(max_moment_identity_error,gap)
                if gap>1e-8:
                    raise ValueError('Saved centered moment does not agree with raw moments')
            batches.append(batch)
        # The only altered original field is precisely the corrupted methods
        # value; every other original setting-level field remains byte-value
        # identical, including dates, seed components, references and hashes.
        result=dict(old)
        result['methods']=recover_methods(batches[0]['setting'],batches)
        for key,value in old.items():
            if key!='methods':
                if result[key]!=value:
                    raise ValueError('Recoverable original field changed')
                fields_compared+=1
        recovered.append(result)
        evidence.append(dict(setting_id=sid,original_aggregate_sha256=sha(aggregate_path),
                             batches=files,experiments=R,rng_state_chain_verified=True))
    statuses={}
    for setting in recovered:
        for method in setting['methods'].values():
            for name in ('mean_check','squared_deviation_check'):
                key=method[name]['status'];statuses[key]=statuses.get(key,0)+1
    if sum(statuses.values())!=CHECKS:
        raise ValueError('Recovered frozen gate count mismatch')
    report=dict(**signature,created_utc=now(),completed_settings=720,incomplete_settings=0,
        check_status_counts=statuses,completed_checks=CHECKS,settings=recovered,
        scope='First-run whole-experiment sufficient statistics; reconstructed report, no new random draws.',
        report_status='recovered_after_final_report_packaging_failure',first_process_exit_code=1,
        recovery_code_sha256=sha(__file__),new_random_draws=0)
    log=Path(log_path)
    audit=dict(status='RECOVERED_WITHOUT_REDRAWS',created_utc=now(),protocol_sha256=PROTOCOL_SHA,
        original_simulator_sha256=SIMULATOR_SHA,recovery_code_sha256=sha(__file__),
        first_process_exit_code=1,first_failure='Run-signature methods list replaced each setting methods dictionary; final summary .values() raised AttributeError.',
        original_run_log_sha256=sha(log),original_manifest_sha256=sha(manifest_path),
        new_random_draws=0,settings=720,batches=7200,whole_experiments=720*R,
        original_fields_except_methods_compared=fields_compared,
        maximum_saved_raw_centered_moment_identity_error=max_moment_identity_error,
        source_aggregates_and_batches_unchanged=True,evidence=evidence)
    write_new(output,report)
    audit['recovered_results_sha256']=sha(output)
    write_new(ledger,audit)
    return {k:report[k] for k in ('completed_settings','incomplete_settings','completed_checks','check_status_counts','new_random_draws')}


def fixtures():
    passed=[]
    def ok(test,name):
        if not test:raise AssertionError(name)
        passed.append(name)
    a=check_mean(.3,.3,.02,1.25,50000)
    expected=math.sqrt(2*.02*math.log(2*5760/.001)/50000)+2*1.25*math.log(2*5760/.001)/(3*50000)
    ok(a['threshold_without_numerical_slack']==expected,'unchanged Bernstein formula')
    ok(check_mean(0,0,0,1,50000)['status']=='structural_agreement','constant structural control')
    ok(check_mean(1,0,0,1,50000)['status']=='flag','structural failure retained')
    setting={'m':5,'n':100,'reference_methods':{name:{'mean':0.,'variance':0.,'range':[-.25,1.]} for name in METHODS}}
    entry=dict(sum=0.,sum_squares=0.,sum_squared_deviation_from_analytic_mean=0.,minimum=0.,maximum=0.,nonzero_deviation_count=0,count=BATCH)
    batches=[{'moments':{name:dict(entry) for name in METHODS}} for _ in range(10)]
    result=recover_methods(setting,batches)
    ok(isinstance(result,dict) and set(result)==set(METHODS),'method dictionaries survive independent reconstruction')
    ok(all(x['count']==50000 and x['mean']==0 for x in result.values()),'ten batches cover exactly fifty thousand experiments')
    nonzero_setting={'m':5,'n':100,'reference_methods':{
        name:{'mean':0.,'variance':.01,'range':[-.25+1e-15,1.]} for name in METHODS}}
    same=recover_methods(nonzero_setting,batches)
    width=1+5/(4*(5-1))
    expected_check=check_mean(0.,0.,.01,width,50000)
    ok(same['shared_fitted_mean_corrected']['mean_check']==expected_check,
       'threshold uses original algebraic range despite tolerated reference roundoff')
    bad=[{'moments':{name:{**entry,'count':4999} for name in METHODS}}]+batches[1:]
    try:recover_methods(setting,bad);raise AssertionError('count gap accepted')
    except ValueError:passed.append('incomplete count rejected')
    original={'methods':list(METHODS),'metadata':'fixture'}
    recovered=dict(original);recovered['methods']=result
    ok(original['methods']==list(METHODS) and isinstance(recovered['methods'],dict),'metadata collision fixture keeps original untouched')
    with tempfile.TemporaryDirectory(prefix='calibration-recovery-fixture-') as tmp:
        p=Path(tmp)/'result.json';write_new(p,original);before=sha(p)
        try:write_new(p,recovered);raise AssertionError('first output replaced')
        except FileExistsError:ok(sha(p)==before,'immutable first output')
    return dict(status='PASS',count=len(passed),fixtures=passed,code_sha256=sha(__file__),new_random_draws=0,scientific_recovery_run=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true')
    p.add_argument('--local',type=Path,default=LOCAL)
    p.add_argument('--output',type=Path,default=BASE/'calibration-monte-carlo/results.json')
    p.add_argument('--ledger',type=Path,default=BASE/'calibration-monte-carlo/recovery-ledger.json')
    p.add_argument('--fixture-report',type=Path)
    p.add_argument('--original-simulator',type=Path,default=ROOT/'scripts/simulate_shared_calibration.py')
    p.add_argument('--original-log',type=Path,default=ROOT/'tmp/age-calendar-2026-11-10/calibration-run.log')
    args=p.parse_args();f=fixtures()
    if args.fixture_report:write_new(args.fixture_report,f)
    print(json.dumps(f,indent=2),flush=True)
    if args.run:print(json.dumps(recover(args.local,args.output,args.ledger,args.original_simulator,args.original_log),indent=2),flush=True)


if __name__=='__main__':main()
