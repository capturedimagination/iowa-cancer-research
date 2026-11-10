#!/usr/bin/env python3
"""Frozen finite-sample diagnostics for saved common-clock tree aggregates.

No branching-model implementation is imported. Default runs constructed fixtures;
--run reads saved results only after comparison-code review and pinning.
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
from scipy.stats import binomtest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
PROTOCOL_SHA='53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919'
TREE_SHA='b7cbfb48c223a0772f96eb06b6f65a0ed2a55fcb92db139116ab94737679599c'
K_BIN,K_MEAN,ALPHA,SLACK=3070,720,.001,1e-8


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()


def write_new(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    with tmp.open('x') as f:
        json.dump(data,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.link(tmp,path);tmp.unlink()


def probability(raw):
    raw=float(raw)
    if not math.isfinite(raw):raise ValueError('Nonfinite reference probability')
    p=min(1.,max(0.,raw))
    if abs(p-raw)>SLACK:raise ValueError('Material probability-domain violation')
    return p,abs(p-raw)


def binomial_check(count,total,p):
    if not isinstance(count,int) or not isinstance(total,int) or count<0 or total<0 or count>total:
        raise ValueError('Invalid exact-binomial count')
    p0,adjustment=probability(p)
    out=dict(count=count,total=total,reference_probability=p,probability_for_test=p0,
             probability_roundoff_adjustment=adjustment,per_check_alpha=ALPHA/K_BIN)
    if total==0:
        return dict(**out,status='undefined_zero_denominator',pvalue=None,estimate=None)
    pv=float(binomtest(count,total,p0,alternative='two-sided').pvalue)
    return dict(**out,status='flag' if pv<ALPHA/K_BIN else 'not_flagged',pvalue=pv,estimate=count/total)


def bounded_mean(observed,total,target,structural=False):
    p,adjustment=probability(target)
    out=dict(count=total,reference_mean=target,variance_upper_bound=p*(1-p),
             variance_probability_roundoff_adjustment=adjustment,per_check_alpha=ALPHA/K_MEAN,
             range=[0.,1.])
    if total==0:
        if observed is not None:raise ValueError('Undefined conditional mean must be None')
        return dict(**out,status='undefined_zero_denominator',estimate=None,absolute_error=None,threshold=None)
    if total<0 or observed is None or not math.isfinite(observed) or observed<0 or observed>1:
        raise ValueError('Invalid bounded empirical mean')
    error=abs(observed-target)
    if structural:
        return dict(**out,status='structural_agreement' if error<=SLACK else 'flag',
                    estimate=observed,absolute_error=error,threshold=SLACK,
                    exact_float_agreement=observed==target)
    L=math.log(2*K_MEAN/ALPHA)
    bound=math.sqrt(2*p*(1-p)*L/total)+2*L/(3*total)
    return dict(**out,status='not_flagged' if error<=bound+SLACK else 'flag',estimate=observed,
                absolute_error=error,threshold=bound+SLACK,threshold_without_numerical_slack=bound)


def index(rows,fields,count):
    result={tuple(r[k] for k in fields):r for r in rows}
    if len(rows)!=count or len(result)!=count:raise ValueError('Duplicate or missing fixed-grid rows')
    return result


def compare(primary_path,mc_path,gate_path,checkpoint_root,output,markdown):
    if Path(output).resolve()==Path(markdown).resolve() or Path(output).exists() or Path(markdown).exists():
        raise FileExistsError('Comparison JSON and Markdown require distinct fresh paths')
    if sha(BASE/'protocol.json')!=PROTOCOL_SHA:raise ValueError('Frozen protocol changed')
    primary=json.loads(Path(primary_path).read_text());mc=json.loads(Path(mc_path).read_text())
    gate=json.loads(Path(gate_path).read_text());plan=json.loads((BASE/'protocol.json').read_text())
    if (gate.get('status')!='PASS' or gate.get('cases_checked')!=20 or gate.get('failures')!=[]
            or gate.get('numeric_fields_per_source')!=96145):raise ValueError('Unverified deterministic reference')
    input_hashes=gate['input_hashes']
    if input_hashes.get(str((BASE/'results.json').relative_to(ROOT)))!=sha(primary_path):
        raise ValueError('Independent gate does not match primary input')
    if input_hashes.get(str((BASE/'protocol.json').relative_to(ROOT)))!=PROTOCOL_SHA:
        raise ValueError('Independent gate protocol mismatch')
    if primary['protocol_sha256']!=PROTOCOL_SHA or mc['protocol_sha256']!=PROTOCOL_SHA or mc['code_sha256']!=TREE_SHA:
        raise ValueError('Saved input provenance mismatch')
    if mc['completed_cases']!=20 or mc['incomplete_cases']!=0:
        raise ValueError('Complete numerical comparison requires all original cases; do not drop incomplete cases')
    prim=index(primary['cases'],['case_id'],20);sim=index(mc['cases'],['case_id'],20)
    binary=[];means=[];descriptive=[];case_checks=[];checkpoint_count=0
    for config in plan['cases']:
        cid=config['case_id'];p=prim[(cid,)];m=sim[(cid,)]
        if p['configuration']!=config or m['configuration']!=config or m['prospective_founders']!=10000:
            raise ValueError('Saved case configuration or founder count mismatch')
        if len(m['batch_files'])!=40:raise ValueError('Case has missing batch manifest entries')
        for k,entry in enumerate(m['batch_files']):
            if entry['path']!=f'{cid}/batches/{k*250:05d}.npz':raise ValueError('Checkpoint path/order mismatch')
            if sha(Path(checkpoint_root)/entry['path'])!=entry['sha256']:raise ValueError('Saved checkpoint hash mismatch')
            checkpoint_count+=1
        pf=index(p['family'],['T'],3);mf=index(m['family'],['T'],3)
        pq=index(p['Q'],['t','T'],17);mq=index(m['Q'],['t','T'],17)
        pu=index(p['U'],['t'],7);mu=index(m['U'],['t'],7)
        pc=index(p['contrasts'],['t','T_early','T_late'],12);mcx=index(m['contrasts'],['t','T_early','T_late'],12)
        pb=index(p['bins'],['bin_id'],15);mb=index(m['bins'],['bin_id'],15)
        pp=index(p['pairs'],['bin_id','lag'],45);mp=index(m['pairs'],['bin_id','lag'],45)
        if not all(m['accounting'][key] for key in ('family_path_positive_identity','time_zero_identity','birth_partitions_cover_eligible')):
            raise ValueError('Original tree accounting did not pass')
        for key,r in mf.items():
            if r['total']!=10000:raise ValueError('Family denominator is not prospective roster size')
            binary.append(dict(case_id=cid,kind='family',T=r['T'],**binomial_check(r['count'],r['total'],pf[key]['probability'])))
        for key,r in mb.items():
            if r['total']!=10000:raise ValueError('Birth-bin denominator is not prospective roster size')
            for field in ('left','right','width'):
                if r[field]!=pb[key][field]:raise ValueError('Birth-bin boundary mismatch')
            binary.append(dict(case_id=cid,kind='birth_bin_eligibility',bin_id=r['bin_id'],
                               **binomial_check(r['count'],r['total'],pb[key]['probability'])))
        if len(config['means'])==2:
            binary.append(dict(case_id=cid,kind='qualifying_mother_type0',
                **binomial_check(m['eligible_type0_count'],m['eligible_count'],p['eligible_mother_type_weights'][0])))
        for key,r in mp.items():
            if r['count']!=mb[(r['bin_id'],)]['count']:raise ValueError('Pair denominator does not match birth bin')
            for field,probfield in (('first_count','p'),('second_count','p'),('both_count','j')):
                binary.append(dict(case_id=cid,kind='pair_'+field,bin_id=r['bin_id'],lag=r['lag'],
                    **binomial_check(r[field],r['count'],pp[key][probfield])))
            if r['covariance_defined']!=(r['count']>=2):raise ValueError('Covariance denominator flag mismatch')
            if r['count']<2 and r['covariance'] is not None:raise ValueError('Undefined covariance was assigned a value')
            if r['count']>=2:
                cov=(r['both_count']-r['first_count']*r['second_count']/r['count'])/(r['count']-1)
                if abs(cov-r['covariance'])>1e-14:raise ValueError('Descriptive sample covariance count identity failed')
            descriptive.append(dict(case_id=cid,kind='pair_covariance',bin_id=r['bin_id'],lag=r['lag'],
                count=r['count'],estimate=r['covariance'],reference=pp[key]['c'],defined=r['covariance_defined'],
                gate='Descriptive only; three binary probability gates above are the frozen validation.'))
        for key,r in mq.items():
            if r['count']!=mf[(r['T'],)]['count'] or r['defined']!=(r['count']>0):raise ValueError('Q selected denominator mismatch')
            if r['count'] and abs(r['estimate']-r['sum']/r['count'])>1e-14:raise ValueError('Q mean/sum inconsistency')
            means.append(dict(case_id=cid,kind='conditional_Q',t=r['t'],T=r['T'],
                positive_loss_count=r['positive_loss_count'],
                **bounded_mean(r['estimate'],r['count'],pq[key]['value'],config['mu']==0 or r['t']==0)))
        for key,r in mu.items():
            if r['total']!=10000 or abs(r['estimate']-r['sum']/r['total'])>1e-14:raise ValueError('Unconditional U denominator/sum mismatch')
            means.append(dict(case_id=cid,kind='unconditional_U',t=r['t'],positive_loss_count=r['positive_loss_count'],
                **bounded_mean(r['estimate'],r['total'],pu[key]['value'],config['mu']==0 or r['t']==0)))
        for key,r in mcx.items():
            if (r['early_count']!=mf[(r['T_early'],)]['count']
                    or r['late_count']!=mf[(r['T_late'],)]['count']):
                raise ValueError('Contrast denominators do not match family counts')
            if r['defined']!=(r['early_count']>0 and r['late_count']>0):
                raise ValueError('Contrast defined flag disagrees with denominators')
            if not r['defined'] and r['estimate'] is not None:
                raise ValueError('Undefined contrast was assigned a value')
            if r['defined']:
                difference=mq[(r['t'],r['T_late'])]['estimate']-mq[(r['t'],r['T_early'])]['estimate']
                if abs(difference-r['estimate'])>1e-14:raise ValueError('Descriptive contrast Q identity failed')
            if r['total']!=10000 or r['removed_count']!=r['early_count']-r['late_count']:
                raise ValueError('Removed cohort accounting mismatch')
            if r['removed_count']==0 and (r['removed_loss_mean']!=0 or r['conditional_removed_loss'] is not None):
                raise ValueError('Empty removed cohort convention violated')
            if abs(r['removed_loss_mean']-r['removed_loss_sum']/10000)>1e-14:
                raise ValueError('Unconditional removed-loss denominator mismatch')
            # Stable saved positive-loss expression is algebraically the frozen
            # h1*(1-Q1)-h2*(1-Q2) target. Verify equivalence without replacing it.
            direct=(pf[(r['T_early'],)]['probability']*(1-pq[(r['t'],r['T_early'])]['value'])
                    -pf[(r['T_late'],)]['probability']*(1-pq[(r['t'],r['T_late'])]['value']))
            target=pc[key]['positive_removed_loss']
            if abs(direct-target)>SLACK:raise ValueError('Removed-loss reference identities disagree')
            means.append(dict(case_id=cid,kind='unconditional_removed_loss',t=r['t'],T_early=r['T_early'],T_late=r['T_late'],
                removed_count=r['removed_count'],positive_contributor_count=r['removed_loss_contributor_count'],
                direct_reference_identity_error=abs(direct-target),
                **bounded_mean(r['removed_loss_mean'],10000,target,config['mu']==0)))
            descriptive.append(dict(case_id=cid,kind='horizon_contrast',t=r['t'],T_early=r['T_early'],T_late=r['T_late'],
                estimate=r['estimate'],reference=pc[key]['value'],defined=r['defined'],
                gate='Descriptive only; no new Gaussian paired-influence threshold.'))
        case_checks.append(dict(case_id=cid,founders=10000,checkpoints=40,original_accounting=m['accounting']))
    if len(binary)!=K_BIN or len(means)!=K_MEAN or checkpoint_count!=800:
        raise ValueError('Frozen diagnostic/checkpoint cardinality mismatch')
    count_status=lambda rows:{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
    report=dict(created_utc=now(),status='COMPARISON_COMPLETED',protocol_sha256=PROTOCOL_SHA,code_sha256=sha(__file__),
        input_hashes=dict(primary=sha(primary_path),tree=sha(mc_path),independent_gate=sha(gate_path)),
        completed_cases=20,prospective_founders=200000,verified_checkpoint_files=checkpoint_count,
        exact_binomial_count=len(binary),bounded_mean_count=len(means),
        exact_binomial_status_counts=count_status(binary),bounded_mean_status_counts=count_status(means),
        family_alpha_per_diagnostic_family=ALPHA,joint_two_family_union_bound=2*ALPHA,numerical_slack=SLACK,
        probability_diagnostics=binary,bounded_mean_diagnostics=means,descriptive_quantities=descriptive,accounting=case_checks,
        scope='Finite-sample synthetic numerical checks conditional on model inputs, not empirical or clinical validation.',
        limitations=['No Gaussian comparison and no selected-count>=100 adequacy assumption.',
                    'Probability clipping only within numerical slack is recorded; deterministic numerical error is not interval-certified.',
                    'Earlier study flags and unresolved approximate checks remain unchanged.'])
    write_new(output,report)
    flags=[r for r in binary+means if r['status']=='flag']
    undefined=[r for r in binary+means if r['status']=='undefined_zero_denominator']
    lines=['# Complete-tree Monte Carlo comparison','',
           f'The first run completed 20 cases and 200,000 prospective founders. All 800 saved checkpoint hashes match the first aggregates.',
           '',f'The frozen comparison contains {len(binary):,} exact-binomial diagnostics and {len(means):,} bounded-mean Bernstein diagnostics. It retains {len(flags)} flags and {len(undefined)} undefined zero-denominator checks.',
           '',f'Exact-binomial status counts: `{report["exact_binomial_status_counts"]}`.',
           f'Bounded-mean status counts: `{report["bounded_mean_status_counts"]}`.','',
           'Each diagnostic family has its own alpha of 0.001; the union bound across these two families is 0.002, conditional on the model probabilities and declared numerical approximation.', '',
           'Conditional Q checks use the observed selected count. Removed-stratum loss is an unconditional prospective-founder mean, including zeros. Sister covariance and horizon contrasts are descriptive alongside their frozen component checks; no new Gaussian standard-error threshold is applied.',
           '', 'These are synthetic model checks. They do not establish biological inheritance, a cancer mechanism, treatment benefit, or novelty. Earlier study flags remain unchanged. Probability roundoff and numerical slack are retained; the integration calculations are not interval arithmetic.',
           '', 'Every case, reference, count, threshold, flag and undefined status is retained in [the comparison JSON](comparison.json).']
    if flags:
        lines.extend(['','Flagged diagnostic records:','',*['- `'+json.dumps(r,sort_keys=True)+'`' for r in flags]])
    path=Path(markdown);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:f.write('\n'.join(lines)+'\n')
    return dict(exact_binomial_status_counts=report['exact_binomial_status_counts'],bounded_mean_status_counts=report['bounded_mean_status_counts'])


def fixtures():
    passed=[]
    def ok(test,name):
        if not test:raise AssertionError(name)
        passed.append(name)
    ok(binomial_check(0,0,.5)['status']=='undefined_zero_denominator','zero conditional denominator retained')
    ok(binomial_check(0,10,0)['pvalue']==1 and binomial_check(1,10,0)['status']=='flag','exact zero-probability boundary')
    ok(binomial_check(10,10,1)['pvalue']==1 and binomial_check(9,10,1)['status']=='flag','exact one-probability boundary')
    ok(binomial_check(0,10,.5)['pvalue']==2/1024,'two-sided binomial exact tail fixture')
    ok(bounded_mean(None,0,.4)['status']=='undefined_zero_denominator','undefined selected Q is not assigned zero')
    ok(bounded_mean(0,10000,.01)['count']==10000,'empty removed cohort retains prospective denominator')
    test=bounded_mean(.5,37,.5)
    L=math.log(2*720/.001)
    ok(test['threshold_without_numerical_slack']==math.sqrt(2*.25*L/37)+2*L/(3*37),'conditional Bernstein uses actual count without count cutoff')
    ok(bounded_mean(1,100,1,True)['status']=='structural_agreement','known structural constant')
    ok(bounded_mean(0,100,1,True)['status']=='flag','structural disagreement remains flagged')
    ok(bounded_mean(0,10000,0)['threshold_without_numerical_slack']>0,'numerically zero reference alone is not structural')
    try:index([{'x':1},{'x':1}],['x'],2);raise AssertionError('duplicate join accepted')
    except ValueError:passed.append('duplicate reference join rejected')
    try:probability(-.01);raise AssertionError('invalid probability accepted')
    except ValueError:passed.append('material reference probability violation rejected')
    ok(probability(1+1e-12)[1]>0,'tiny roundoff adjustment explicitly retained')
    ok(20*(3+15+45*3)+10==3070 and 20*(17+7+12)==720,'frozen full-grid diagnostic counts')
    with tempfile.TemporaryDirectory(prefix='tree-comparator-fixture-') as tmp:
        p=Path(tmp)/'x.json';write_new(p,{'first':True});before=sha(p)
        try:write_new(p,{'replacement':True});raise AssertionError('output overwritten')
        except FileExistsError:ok(sha(p)==before,'first comparison output is immutable')
    return dict(status='PASS',count=len(passed),fixtures=passed,code_sha256=sha(__file__),comparison_run=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true');p.add_argument('--fixture-report',type=Path)
    p.add_argument('--primary',type=Path,default=BASE/'results.json')
    p.add_argument('--mc',type=Path,default=BASE/'tree-monte-carlo/results.json')
    p.add_argument('--gate',type=Path,default=BASE/'independent-comparison.json')
    p.add_argument('--checkpoints',type=Path,default=ROOT/'tmp/age-calendar-2026-11-10/tree-monte-carlo')
    p.add_argument('--output',type=Path,default=BASE/'tree-monte-carlo/comparison.json')
    p.add_argument('--markdown',type=Path,default=BASE/'tree-monte-carlo/comparison.md')
    args=p.parse_args();f=fixtures()
    if args.fixture_report:write_new(args.fixture_report,f)
    print(json.dumps(f,indent=2),flush=True)
    if args.run:print(json.dumps(compare(args.primary,args.mc,args.gate,args.checkpoints,args.output,args.markdown),indent=2),flush=True)


if __name__=='__main__':main()
