#!/usr/bin/env python3
"""Independent whole-experiment shared-calibration Monte Carlo.

Default: deterministic score/range/precision fixtures only. --run additionally
requires a saved, independently verified primary aggregate; external review must
first authorize it. No numerical branching model is imported. Whole experiments
are the independent units: a single calibration fit is reused by all target pairs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import tempfile
import traceback

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
PROTOCOL = BASE / 'protocol.json'
PROTOCOL_SHA = '53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919'
LOCAL = ROOT / 'tmp/age-calendar-2026-11-10/calibration-monte-carlo'
PUBLIC = BASE / 'calibration-monte-carlo/results.json'
SEED = 2026111014
EXPERIMENTS, BATCH, CHECKS, ALPHA, SLACK = 50_000, 5_000, 5760, .001, 1e-8
METHODS = ('oracle_bin_mean','shared_fitted_mean','shared_fitted_mean_corrected',
           'unbiased_target_sample_covariance')
MC_BINS, LAGS, MS, NS = ('w2-b0','w1-b0'), (.5,1.,2.), (5,20,100), (100,1000)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json_new(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    with tmp.open('x') as f:
        json.dump(data,f,indent=2,allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.link(tmp,path)
    tmp.unlink()


def load_protocol():
    if sha256(PROTOCOL)!=PROTOCOL_SHA:
        raise ValueError('Protocol hash mismatch')
    p=json.loads(PROTOCOL.read_text())
    assert len(p['cases'])==20 and p['calibration']['seed_entropy']==SEED
    assert p['calibration']['monte_carlo_settings']==720
    assert p['calibration']['monte_carlo_experiments_per_setting']==EXPERIMENTS
    assert p['calibration']['monte_carlo_batch_size']==BATCH
    assert tuple(p['calibration']['methods'])==METHODS
    return p


def score_ranges(m,n):
    return dict(zip(METHODS,[[-.25,1.],[-.25,1.],[-m/(4*(m-1)),1.],
                             [-n/(4*(n-1)),n/(4*(n-1))]]))


def scores(calibration, counts, p, m, n):
    """Four count categories are always 00,01,10,11."""
    x, counts=np.asarray(calibration),np.asarray(counts)
    if counts.ndim!=2 or counts.shape!=(len(x),4):
        raise ValueError('Each whole experiment requires exactly four pair counts')
    if np.any(counts<0) or np.any(np.sum(counts,axis=1)!=n) or np.any(counts!=np.floor(counts)):
        raise ValueError('Invalid multinomial target counts')
    if m<2 or n<2 or np.any(x<0) or np.any(x>m) or np.any(x!=np.floor(x)):
        raise ValueError('Invalid calibration/sample size')
    f=x/m
    joint=counts[:,3]/n
    first=(counts[:,2]+counts[:,3])/n
    second=(counts[:,1]+counts[:,3])/n
    total=first+second
    naive=joint-f*total+f*f
    return dict(zip(METHODS,[joint-p*total+p*p,naive,naive-f*(1-f)/(m-1),
                             n/(n-1)*(joint-first*second)]))


def projected_probabilities(p,j):
    """Only documented <=1e-8 probability roundoff adjustments are allowed."""
    raw=np.array([1-2*p+j,p-j,p-j,j],dtype=float)
    if not np.isfinite(p) or not np.isfinite(j) or np.any(~np.isfinite(raw)):
        raise ValueError('Nonfinite reference probability')
    pp=float(np.clip(p,0,1))
    jj=float(np.clip(j,max(0,2*pp-1),pp))
    probs=np.array([1-2*pp+jj,pp-jj,pp-jj,jj])
    probs=np.maximum(probs,0)
    probs/=float(np.sum(probs))
    # NumPy treats the last multinomial category as the remaining mass.
    probs[-1]=1-float(np.sum(probs[:-1]))
    delta=max(abs(pp-p),abs(jj-j),float(np.max(np.abs(probs-raw))))
    if delta>SLACK or np.any(probs<0) or np.any(probs>1):
        raise ValueError('Reference probability needs a material projection')
    return pp,probs,dict(raw_p=p,raw_j=j,raw_category_probabilities=raw.tolist(),
        sampling_p=pp,sampling_category_probabilities=probs.tolist(),
        maximum_absolute_adjustment=delta,any_adjustment=delta>0,
        category_order=['00','01','10','11'])


def bounded_check(observed, expected, variance_bound, range_width, count):
    if not all(math.isfinite(v) for v in (observed,expected,variance_bound,range_width)):
        raise ValueError('Nonfinite concentration input')
    if variance_bound<0 or range_width<0 or count<=0:
        raise ValueError('Invalid concentration input')
    error=abs(observed-expected)
    if variance_bound==0:
        return dict(observed=observed,expected=expected,absolute_error=error,
                    status='structural_agreement' if error<=SLACK else 'flag',
                    threshold=SLACK,threshold_without_numerical_slack=0.,
                    exact_float_agreement=observed==expected,variance_bound=0.)
    log=math.log(2*CHECKS/ALPHA)
    threshold=math.sqrt(2*variance_bound*log/count)+2*range_width*log/(3*count)
    return dict(observed=observed,expected=expected,absolute_error=error,
                status='not_flagged' if error<=threshold+SLACK else 'flag',
                threshold=threshold+SLACK,threshold_without_numerical_slack=threshold,
                variance_bound=variance_bound)


def summarize_batch(values, references, m, n):
    ranges=score_ranges(m,n)
    out={}
    for name in METHODS:
        y=values[name]
        a,b=ranges[name]
        if np.any(~np.isfinite(y)) or np.min(y)<a-SLACK or np.max(y)>b+SLACK:
            raise ValueError(f'Score outside its frozen range: {name}')
        mean=float(references[name]['mean'])
        delta=y-mean
        out[name]=dict(sum=float(np.sum(y)),sum_squares=float(np.dot(y,y)),
                       sum_squared_deviation_from_analytic_mean=float(np.dot(delta,delta)),
                       minimum=float(np.min(y)),maximum=float(np.max(y)),
                       nonzero_deviation_count=int(np.sum(delta!=0)),
                       count=int(len(y)))
    return out


def setting_id(case_id,li,bi,mi,ni):
    return f'{case_id}-l{li}-b{bi}-m{mi}-n{ni}'


def prepare_settings(protocol, reference):
    """Strict saved-record joins; no primary numerical code or model imports."""
    records=reference['cases']
    by_id={r.get('case_id',r.get('configuration',{}).get('case_id')):r for r in records}
    if len(by_id)!=20 or len(records)!=20:
        raise ValueError('Expected exactly twenty unique saved case records')
    result=[]
    for ci,case in enumerate(protocol['cases']):
        r=by_id[case['case_id']]
        if r['configuration']!=case:
            raise ValueError('Saved configuration differs from frozen protocol')
        pairkeys=[(x['bin_id'],float(x['lag'])) for x in r['pairs']]
        if len(pairkeys)!=45 or len(set(pairkeys))!=45:
            raise ValueError('Pair record join cardinality mismatch')
        pairs=dict(zip(pairkeys,r['pairs']))
        ckeys=[(x['bin_id'],float(x['lag']),int(x['m']),int(x['n'])) for x in r['calibration']]
        if len(ckeys)!=270 or len(set(ckeys))!=270:
            raise ValueError('Calibration join cardinality mismatch')
        calibrations=dict(zip(ckeys,r['calibration']))
        for li,lag in enumerate(LAGS):
            for bi,bid in enumerate(MC_BINS):
                pair=pairs[(bid,lag)]
                p,j=float(pair['p']),float(pair['j'])
                sampling_p,pi,projection=projected_probabilities(p,j)
                for mi,m in enumerate(MS):
                    for ni,n in enumerate(NS):
                        row=calibrations[(bid,lag,m,n)]
                        ref=row['methods']
                        if set(ref)!=set(METHODS):
                            raise ValueError('Saved estimator names do not match protocol')
                        expected_ranges=score_ranges(m,n)
                        for name in METHODS:
                            rr=ref[name]
                            if not math.isfinite(rr['mean']) or not math.isfinite(rr['variance']) or rr['variance']<0:
                                raise ValueError('Saved analytic moment is invalid')
                            if any(abs(a-b)>1e-14 for a,b in zip(rr['range'],expected_ranges[name])) or len(rr['range'])!=2:
                                raise ValueError('Saved score range differs from frozen range')
                        result.append(dict(setting_id=setting_id(case['case_id'],li,bi,mi,ni),case_id=case['case_id'],
                            bin_id=bid,lag=lag,m=m,n=n,seed_components=[SEED,ci,li,bi,mi,ni],
                            raw_p=p,raw_j=j,sampling_p=sampling_p,probabilities=pi.tolist(),
                            probability_projection=projection,reference_methods=ref))
    if len(result)!=720:
        raise ValueError('Frozen calibration setting count mismatch')
    return result


def validate_gate(gate, reference, reference_hash):
    """Require the actual complete deterministic comparison, not a truthy file."""
    if (gate.get('status') != 'PASS' or gate.get('cases_checked') != 20
            or gate.get('failures') != [] or gate.get('numeric_fields_per_source') != 96145):
        raise ValueError('Independent deterministic comparison has not passed the frozen full grid')
    hashes = gate.get('input_hashes', {})
    protocol_key = str(PROTOCOL.relative_to(ROOT))
    if hashes.get(protocol_key) != PROTOCOL_SHA:
        raise ValueError('Independent gate refers to another protocol')
    if reference.get('protocol_sha256') != PROTOCOL_SHA:
        raise ValueError('Reference refers to another protocol')
    primary_key = str((BASE / 'results.json').relative_to(ROOT))
    if hashes.get(primary_key) != reference_hash:
        raise ValueError('Independent gate does not verify the supplied primary reference bytes')
    return dict(status='PASS', cases_checked=20, numeric_fields_per_source=96145,
                protocol_input_key=protocol_key, primary_input_key=primary_key,
                verified_primary_sha256=reference_hash)


def finish_setting(setting, batches):
    result=dict(status='complete',**setting,experiments=EXPERIMENTS,batch_size=BATCH,methods={})
    for name in METHODS:
        records=[x['moments'][name] for x in batches]
        count=sum(r['count'] for r in records)
        if count!=EXPERIMENTS:
            raise ValueError('Incomplete experiments cannot produce complete aggregate')
        sums={key:math.fsum(r[key] for r in records) for key in
              ('sum','sum_squares','sum_squared_deviation_from_analytic_mean')}
        expected=setting['reference_methods'][name]
        mean,variance=float(expected['mean']),float(expected['variance'])
        a,b=score_ranges(setting['m'],setting['n'])[name]
        width=b-a
        mean_observed=sums['sum']/count
        squared=sums['sum_squared_deviation_from_analytic_mean']/count
        result['methods'][name]=dict(count=count,**sums,mean=mean_observed,
            mean_squared_deviation_from_analytic_mean=squared,
            minimum=min(r['minimum'] for r in records),maximum=max(r['maximum'] for r in records),
            nonzero_deviation_count=sum(r['nonzero_deviation_count'] for r in records),
            mean_check=bounded_check(mean_observed,mean,variance,width,count),
            squared_deviation_check=bounded_check(squared,variance,width*width*variance,width*width,count))
    return result


def run_setting(setting, folder, signature):
    location=folder/setting['setting_id']
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence(setting['seed_components'])))
    batches=[]
    for start in range(0,EXPERIMENTS,BATCH):
        path=location/'batches'/f'{start:05d}.json'
        before=rng.bit_generator.state
        identity=dict(**signature,setting=setting,experiment_start=start,experiment_count=BATCH,rng_before=before)
        if path.exists():
            batch=json.loads(path.read_text())
            if any(batch.get(k)!=v for k,v in identity.items()):
                raise ValueError(f'Batch identity mismatch: {setting["setting_id"]}, {start}')
            rng.bit_generator.state=batch['rng_after']
        else:
            try:
                # Frozen order: independent calibration first, target counts second.
                x=rng.binomial(setting['m'],setting['sampling_p'],size=BATCH)
                counts=rng.multinomial(setting['n'],setting['probabilities'],size=BATCH)
                values=scores(x,counts,setting['raw_p'],setting['m'],setting['n'])
                moments=summarize_batch(values,setting['reference_methods'],setting['m'],setting['n'])
                batch=dict(**identity,moments=moments,rng_after=rng.bit_generator.state,created_utc=utc_now())
                write_json_new(path,batch)
            except Exception as exc:
                failure=dict(status='incomplete',**signature,setting=setting,completed_experiments=start,
                             rng_batch_before=before,rng_at_failure=rng.bit_generator.state,
                             error_class=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),created_utc=utc_now())
                write_json_new(location/'failures'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),failure)
                return failure
        batches.append(batch)
    result=finish_setting(setting,batches)
    result.update(dict(**signature,created_utc=utc_now(),
        batch_files=[dict(path=str(p.relative_to(folder)),sha256=sha256(p)) for p in sorted((location/'batches').glob('*.json'))]))
    aggregate=location/'aggregate.json'
    if aggregate.exists():
        old=json.loads(aggregate.read_text())
        comparable=lambda x:{k:v for k,v in x.items() if k!='created_utc'}
        if comparable(old)!=comparable(result):
            raise ValueError('Existing aggregate differs from checkpoint reconstruction')
        return old
    write_json_new(aggregate,result)
    return result


def run_all(reference_path, gate_path, folder=LOCAL, output=PUBLIC, resume=False):
    protocol=load_protocol()
    folder,output=Path(folder),Path(output)
    # Authorization to execute is external; the gate itself is validated here.
    reference=json.loads(Path(reference_path).read_text())
    gate=json.loads(Path(gate_path).read_text())
    gate_validation=validate_gate(gate,reference,sha256(reference_path))
    settings=prepare_settings(protocol,reference)
    signature=dict(protocol_sha256=PROTOCOL_SHA,code_sha256=sha256(__file__),
        reference_sha256=sha256(reference_path),independent_gate_sha256=sha256(gate_path),
        independent_gate_validation=gate_validation,
        python_version=platform.python_version(),numpy_version=np.__version__,scipy_version=scipy.__version__,
        seed_entropy=SEED,experiments_per_setting=EXPERIMENTS,batch_size=BATCH,
        methods=list(METHODS),planned_settings=720,planned_checks=CHECKS,
        family_alpha=ALPHA,numerical_slack=SLACK,batch_paths_relative_to='explicit checkpoint root')
    manifest=folder/'run-manifest.json'
    if manifest.exists():
        if not resume:
            raise FileExistsError('Run exists; resume the same run explicitly')
        old=json.loads(manifest.read_text())
        if any(old.get(k)!=v for k,v in signature.items()):
            raise ValueError('Resume provenance/environment mismatch')
    else:
        if resume:
            raise FileNotFoundError('No run manifest to resume')
        if folder.exists() and any(folder.iterdir()):
            raise FileExistsError('Unmanifested nonempty checkpoint folder')
        write_json_new(manifest,dict(**signature,created_utc=utc_now()))
    if output.exists():
        raise FileExistsError('First aggregate outputs cannot be overwritten')
    results=[]
    for index,setting in enumerate(settings):
        try:
            result=run_setting(setting,folder,signature)
        except Exception as exc:
            result=dict(status='incomplete',setting_id=setting['setting_id'],**signature,
                        created_utc=utc_now(),error=str(exc),error_class=type(exc).__name__,traceback=traceback.format_exc())
            write_json_new(folder/setting['setting_id']/'failures'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),result)
        results.append(result)
        if (index+1)%12==0 or result['status']!='complete':
            print(f'Completed {index+1}/720 settings; latest {setting["setting_id"]}: {result["status"]}',flush=True)
    statuses={}
    for result in results:
        for method in result.get('methods',{}).values():
            for key in ('mean_check','squared_deviation_check'):
                s=method[key]['status']
                statuses[s]=statuses.get(s,0)+1
    complete=sum(r['status']=='complete' for r in results)
    report=dict(**signature,created_utc=utc_now(),completed_settings=complete,incomplete_settings=720-complete,
                check_status_counts=statuses,completed_checks=sum(statuses.values()),settings=results,
                scope='Whole-experiment numerical validation, not biological uncertainty or a novel covariance estimator.')
    write_json_new(output,report)
    return report


def fixtures():
    passed=[]
    def check(ok,name):
        if not ok:
            raise AssertionError(name)
        passed.append(name)
    # Counts from explicit four pairs, one of each category, independent m=2 fit.
    y=scores([1],[[1,1,1,1]],.5,2,4)
    check(y[METHODS[0]][0]==0 and y[METHODS[1]][0]==0,'oracle and shared-fit hand-pair means')
    check(y[METHODS[2]][0]==-.25 and y[METHODS[3]][0]==0,'binomial correction and sample covariance distinct')
    # Aggregate discordance alone is insufficient for unbiased covariance.
    orientation=scores([0,0],[[0,2,0,0],[0,1,1,0]],.5,2,2)
    check(orientation[METHODS[3]].tolist()==[0.,-.5],'four categories retain discordant orientations')
    allsame=scores([2,2],[[0,0,0,4],[4,0,0,0]],.5,2,4)
    check(allsame[METHODS[0]].tolist()==[.25,.25] and allsame[METHODS[3]].tolist()==[0.,0.],'constant target pairs have zero sample covariance')
    zero=scores(np.array([0,0]),np.array([[4,0,0,0],[4,0,0,0]]),0.,2,4)
    one=scores(np.array([2,2]),np.array([[0,0,0,4],[0,0,0,4]]),1.,2,4)
    check(all(np.all(zero[k]==0) and np.all(one[k]==0) for k in METHODS),'exact zero/one survival controls')
    # Exhaustively enumerate all small count outcomes and calibration values;
    # this is deterministic support checking, not a scientific stochastic run.
    for m,n in ((2,2),(3,3),(5,4)):
        xx,cc=[],[]
        for a in range(n+1):
            for b in range(n-a+1):
                for c in range(n-a-b+1):
                    for x in range(m+1):
                        xx.append(x);cc.append([a,b,c,n-a-b-c])
        out=scores(xx,cc,.37,m,n)
        ranges=score_ranges(m,n)
        check(all(np.min(out[k])>=ranges[k][0]-1e-14 and np.max(out[k])<=ranges[k][1]+1e-14 for k in METHODS),f'all small-support score ranges m{m} n{n}')
    pp,pi,ledger=projected_probabilities(.3,.12)
    check(abs(pp-.3)<1e-15 and np.allclose(pi,[.52,.18,.18,.12]) and ledger['maximum_absolute_adjustment']<=1e-15,'exchangeable pair category law')
    _,_,roundoff=projected_probabilities(1.+1e-12,1.+1e-12)
    check(roundoff['any_adjustment'] and roundoff['maximum_absolute_adjustment']<=1e-8,'tiny probability projection explicitly recorded')
    try:
        projected_probabilities(.2,.3)
        raise AssertionError('invalid pair law accepted')
    except ValueError:
        passed.append('materially invalid joint probability rejected')
    for counts in ([[0,0,0,3]],[[0,-1,1,4]]):
        try:
            scores([1],counts,.5,2,4)
            raise AssertionError('invalid counts accepted')
        except ValueError:
            passed.append('invalid target counts rejected '+str(counts))
    check(bounded_check(0.,0.,0.,1.,50000)['status']=='structural_agreement','zero-variance constant handled without division')
    check(bounded_check(1.,0.,0.,1.,50000)['status']=='flag','zero-variance disagreement remains flagged')
    bound=bounded_check(.1,.1,.03,1.25,50000)
    L=math.log(2*5760/.001)
    check(abs(bound['threshold_without_numerical_slack']-(math.sqrt(2*.03*L/50000)+2*1.25*L/(3*50000)))<1e-15,'frozen Bonferroni Bernstein threshold')
    check(bounded_check(.9,.1,.03,1.25,50000)['status']=='flag','bounded mean excess remains flagged')
    references={name:dict(mean=0.,variance=0.) for name in METHODS}
    summary=summarize_batch(zero,references,2,4)
    check(all(v['sum_squared_deviation_from_analytic_mean']==0 and v['count']==2 for v in summary.values()),'batch moments count independent whole experiments')
    check(len({tuple([SEED,c,l,b,m,n]) for c in range(20) for l in range(3) for b in range(2) for m in range(3) for n in range(2)})==720,'all frozen setting seeds distinct')
    protocol_key=str(PROTOCOL.relative_to(ROOT))
    primary_key=str((BASE/'results.json').relative_to(ROOT))
    good_gate=dict(status='PASS',cases_checked=20,failures=[],numeric_fields_per_source=96145,
                   input_hashes={protocol_key:PROTOCOL_SHA,primary_key:'fixture-reference-hash'})
    good_reference=dict(protocol_sha256=PROTOCOL_SHA)
    check(validate_gate(good_gate,good_reference,'fixture-reference-hash')['status']=='PASS',
          'gate binds full verified field count protocol and reference bytes')
    bad_gates=[{'nonempty':True},{**good_gate,'status':'FAIL'},
               {**good_gate,'cases_checked':19},{**good_gate,'failures':['fixture']},
               {**good_gate,'input_hashes':{protocol_key:'wrong',primary_key:'fixture-reference-hash'}},
               {**good_gate,'input_hashes':{protocol_key:PROTOCOL_SHA,primary_key:'wrong'}}]
    for index,bad in enumerate(bad_gates):
        try:
            validate_gate(bad,good_reference,'fixture-reference-hash')
            raise AssertionError('unverified evidence accepted')
        except ValueError:
            passed.append(f'gate rejects invalid evidence {index+1}')
    with tempfile.TemporaryDirectory(prefix='calibration-fixture-') as tmp:
        path=Path(tmp)/'x.json'
        write_json_new(path,{'first':True})
        before=sha256(path)
        try:
            write_json_new(path,{'first':False})
            raise AssertionError('first result overwritten')
        except FileExistsError:
            check(sha256(path)==before,'first calibration result preserved')
    return dict(status='pass',count=len(passed),fixtures=passed,scientific_simulations_run=False,
                protocol_sha256=PROTOCOL_SHA,code_sha256=sha256(__file__),created_utc=utc_now())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--reference',type=Path)
    p.add_argument('--independent-gate',type=Path)
    p.add_argument('--fixture-report',type=Path)
    p.add_argument('--local',type=Path,default=LOCAL)
    p.add_argument('--output',type=Path,default=PUBLIC)
    args=p.parse_args()
    load_protocol()
    report=fixtures()
    if args.fixture_report:
        write_json_new(args.fixture_report,report)
    print(json.dumps(report,indent=2),flush=True)
    if args.run:
        if not args.reference or not args.independent_gate:
            p.error('--run requires saved --reference and reviewed --independent-gate evidence')
        run_all(args.reference,args.independent_gate,args.local,args.output,args.resume)
    elif args.resume:
        p.error('--resume requires --run')


if __name__=='__main__':
    main()
