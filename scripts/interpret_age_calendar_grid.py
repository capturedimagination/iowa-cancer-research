#!/usr/bin/env python3
"""Post-results descriptive aggregation; no fitting, model selection or new runs."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
TOL = 1e-8
MOMENT_TOL = 1e-10


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def finite(v):
    if isinstance(v, dict):
        for item in v.values(): finite(item)
    elif isinstance(v, list):
        for item in v: finite(item)
    elif isinstance(v, float): assert isfinite(v)


def span(rows, field):
    if not rows:
        return {'n': 0, 'minimum': None, 'maximum': None, 'median': None}
    low, high = min(rows, key=lambda r:r[field]), max(rows, key=lambda r:r[field])
    return {'n':len(rows), 'minimum':low[field], 'maximum':high[field],
            'median':median(r[field] for r in rows),
            'minimum_location':{k:v for k,v in low.items() if k in ('case_id','t','T_early','T_late','lag','bin_id','m','n')},
            'maximum_location':{k:v for k,v in high.items() if k in ('case_id','t','T_early','T_late','lag','bin_id','m','n')}}


def sign(x, tol=TOL):
    return 'positive' if x>tol else 'negative' if x < -tol else 'within_numeric_tolerance'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise FileExistsError('Preserve first aggregation')
    names=['protocol.json','results.json','strict-results.json','independent-reference.json','independent-comparison.json']
    inputs={name:json.loads((BASE/name).read_text()) for name in names}
    for value in inputs.values(): finite(value)
    plan, primary, comparison=inputs['protocol.json'],inputs['results.json'],inputs['independent-comparison.json']
    assert primary['status']==comparison['status']=='PASS' and not comparison['failures']
    for name in names[:4]:
        assert comparison['input_hashes'][str((BASE/name).relative_to(ROOT))]==sha(BASE/name)
    ids=[c['case_id'] for c in plan['cases']]
    assert ids==[c['case_id'] for c in primary['cases']]
    contrasts=[]; profiles=[]; cases=[]; bins=[]; calibration=[]
    all_signs=Counter(); strata=defaultdict(list)
    for case in primary['cases']:
        cfg=case['configuration']; cid=case['case_id']
        no_type=len(cfg['means'])==1 or cfg['rho']==0
        changing=cfg['amplitude']>0
        positive=cfg['mu']>0
        age=cfg['k']>1
        stratum=('zero_death' if not positive else
                 'no_transmission_exponential' if no_type and not age else
                 'no_transmission_age_calendar' if no_type and changing else
                 'no_transmission_age_constant' if no_type else
                 'transmission_calendar' if changing else 'transmission_constant')
        ci=[]
        assert len(case['contrasts'])==12
        for row in case['contrasts']:
            item={**row,'case_id':cid,'stratum':stratum,'sign':sign(row['value'])}
            contrasts.append(item);ci.append(item);strata[stratum].append(item);all_signs[item['sign']]+=1
        pairs={(r['bin_id'],r['lag']):r for r in case['pairs']}
        assert len(pairs)==45
        for row in case['pairs']:
            bins.append({**row,'case_id':cid,'no_transmission':no_type,'positive_death':positive,
                         'changing_clock':changing,'stratum':stratum})
        cp=[]
        for lag in plan['times']['pair_lags']:
            parts=[r for r in case['partitions'] if r['lag']==lag]
            assert [r['width'] for r in parts]==plan['times']['birth_bin_widths']
            pool=pairs['w2-b0',lag]
            context=[r['remaining_context_variance'] for r in parts]
            q={'case_id':cid,'lag':lag,'stratum':stratum,'no_transmission':no_type,
               'positive_death':positive,'changing_clock':changing,'nonexponential':age,
               'period':cfg['period'],'pooled_covariance':pool['c'],
               'exact_birth_conditional_covariance':pool['mean_conditional_covariance'],
               'pooled_context_variance':pool['birth_probability_variance'],
               'partition_widths':plan['times']['birth_bin_widths'],
               'remaining_context_variances':context,
               'weighted_within_covariances':[r['weighted_within_covariance'] for r in parts],
               'context_reduction_fraction':(1-context[-1]/context[0]) if context[0]>TOL else None,
               'monotonicity_pass':all(y<=x+TOL for x,y in zip(context,context[1:])),
               'period_alias_control':no_type and changing and abs(lag/cfg['period']-round(lag/cfg['period']))<1e-15}
            profiles.append(q);cp.append(q)
        cases.append({'case_id':cid,'configuration':cfg,'stratum':stratum,
                      'contrast_sign_counts':dict(Counter(r['sign'] for r in ci)),
                      'contrast_span':span(ci,'value'),'pooled_pair_profiles':cp})
        for row in case['calibration']:
            pair=pairs[row['bin_id'],row['lag']]
            p=pair['p'];v=p*(1-p);m,n=row['m'],row['n']; methods=row['methods']
            cvar=methods['unbiased_target_sample_covariance']['variance']
            corrected=methods['shared_fitted_mean_corrected']; naive=methods['shared_fitted_mean']
            floor=2*v*v/(m*(m-1))
            bias=naive['mean']-pair['c']
            q={'case_id':cid,'bin_id':row['bin_id'],'lag':row['lag'],'m':m,'n':n,
               'positive_death':positive,'stratum':stratum,'bin_covariance':pair['c'],
               'naive_bias':bias,'naive_bias_formula_error':abs(bias-v/m),
               'corrected_mean_error':abs(corrected['mean']-pair['c']),
               'benchmark_variance':cvar,'corrected_variance':corrected['variance'],
               'calibration_variance_floor':floor,
               'floor_fraction':floor/corrected['variance'] if corrected['variance']>0 else None,
               'corrected_minus_benchmark_variance':corrected['variance']-cvar,
               'corrected_variance_ratio':corrected['variance']/cvar if cvar>0 else None,
               'uncorrected_variance_ratio':naive['variance']/cvar if cvar>0 else None,
               'uncorrected_MSE_ratio':(naive['variance']+bias*bias)/cvar if cvar>0 else None,
               'oracle_variance_ratio':methods['oracle_bin_mean']['variance']/cvar if cvar>0 else None}
            if positive: assert cvar>0 and corrected['variance']>0
            else: assert all(x['variance']==0 and x['mean']==0 for x in methods.values())
            calibration.append(q)
    assert len(contrasts)==240 and len(profiles)==60 and len(bins)==900 and len(calibration)==5400
    active_cal=[r for r in calibration if r['positive_death']]
    assert len(active_cal)==4860
    covariance_groups={}
    for stratum in strata:
        rows=[r for r in profiles if r['stratum']==stratum]
        covariance_groups[stratum]={'profile_count':len(rows),
            'pooled_covariance_sign_counts':dict(Counter(sign(r['pooled_covariance']) for r in rows)),
            'conditional_covariance_sign_counts':dict(Counter(sign(r['exact_birth_conditional_covariance']) for r in rows)),
            'pooled_covariance':span(rows,'pooled_covariance'),
            'pooled_context_variance':span(rows,'pooled_context_variance'),
            'exact_birth_conditional_covariance':span(rows,'exact_birth_conditional_covariance')}
    active_profiles=[r for r in profiles if r['pooled_context_variance']>TOL]
    by_cal_design={}
    for m in plan['calibration']['m']:
        for n in plan['calibration']['n']:
            rows=[r for r in active_cal if r['m']==m and r['n']==n]
            by_cal_design[f'm{m}-n{n}']={'positive_death_settings':len(rows),
                'zero_death_settings':sum(not r['positive_death'] and r['m']==m and r['n']==n for r in calibration),
                **{field:span(rows,field) for field in ['naive_bias','corrected_variance_ratio',
                    'uncorrected_MSE_ratio','floor_fraction','oracle_variance_ratio']}}
    aliases=[r for r in profiles if r['period_alias_control']]
    limits=[r for r in bins if r['no_transmission_bound'] is not None]
    positive_bounds=[dict(r, bound_ratio=r['birth_probability_variance']/r['no_transmission_bound'])
                     for r in limits if r['no_transmission_bound']>TOL]
    result={'status':'COMPLETE_DESCRIPTIVE_POST_RESULTS_AGGREGATION',
       'created_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':sha(Path(__file__)),
       'input_hashes':{str((BASE/name).relative_to(ROOT)):sha(BASE/name) for name in names},
       'design_boundaries':{'no_new_scientific_runs':True,'no_parameters_or_gates_changed':True,
           'classification_tolerance':TOL,'calibration_difference_tolerance':MOMENT_TOL,
           'reason_for_tolerance':'Reuse frozen numerical-agreement scale for descriptive zero labels; not a significance test.',
           'relative_reduction_denominator':'Only context variance >1e-8. All other profiles remain recorded with reduction undefined.',
           'variance_ratio_denominator':'Positive sample-covariance variance; all 540 zero-death settings remain recorded separately.',
           'cost_comparison':'Same n evaluation pairs; external calibration additionally uses m independent singles. Not matched total cost.',
           'posthoc_metrics':'Variance ratios, floor fraction, MSE ratio and fine-bin relative reduction summarize frozen outputs; no confidence or power claims.'},
       'counts':{'cases':20,'contrasts':240,'pair_profiles':60,'bins':900,'calibration_settings':5400,
                 'positive_death_calibration_settings':4860,'zero_death_calibration_settings':540},
       'contrast_sign_counts':dict(all_signs),'contrast_span':span(contrasts,'value'),
       'contrast_by_stratum':{key:{'count':len(rows),'sign_counts':dict(Counter(r['sign'] for r in rows)),
                                 'span':span(rows,'value')} for key,rows in strata.items()},
       'pair_by_stratum':covariance_groups,
       'nested_bins':{'profiles':60,'transitions':180,'monotonicity_failures':[r for r in profiles if not r['monotonicity_pass']],
            'context_above_numeric_tolerance_profiles':len(active_profiles),
            'near_zero_context_profiles':len(profiles)-len(active_profiles),
            'relative_reduction':span(active_profiles,'context_reduction_fraction'),
            'relative_reduction_no_transmission':span([r for r in active_profiles if r['no_transmission']],'context_reduction_fraction'),
            'relative_reduction_transmitted_type':span([r for r in active_profiles if not r['no_transmission']],'context_reduction_fraction')},
       'period_aliases':{'count':len(aliases),'profiles':aliases},
       'lipschitz_bounds':{'applicable_bins':len(limits),'positive_bound_bins':len(positive_bounds),
            'violations':[r for r in limits if r['birth_probability_variance']>r['no_transmission_bound']+TOL],
            'actual_over_bound':span(positive_bounds,'bound_ratio')},
       'calibration':{'positive_death_settings':len(active_cal),'all_settings':len(calibration),
            'corrected_variance_greater_than_benchmark_by_tolerance':sum(r['corrected_minus_benchmark_variance']>MOMENT_TOL for r in active_cal),
            'corrected_variance_lower_than_benchmark_by_tolerance':sum(r['corrected_minus_benchmark_variance']< -MOMENT_TOL for r in active_cal),
            **{field:span(active_cal,field) for field in ['naive_bias','naive_bias_formula_error',
                'corrected_mean_error','corrected_variance_ratio','uncorrected_variance_ratio',
                'uncorrected_MSE_ratio','oracle_variance_ratio','floor_fraction','calibration_variance_floor']},
            'by_design':by_cal_design},
       'cases':cases,'all_contrasts':contrasts,'all_pair_profiles':profiles,
       'notes':['No mechanism, empirical validation, or novelty claim follows.',
                'Fine bins do not equal exact context conditioning.',
                'Reference agreement does not supply an interval-arithmetic certificate.',
                'Mean/covariance mixtures over known birth context are different from unobserved family environment.',
                'All source values remain in immutable primary, strict and independent-reference files.']}
    finite(result)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':result['status'],'output':str(args.out),'sha256':sha(args.out)}))


if __name__=='__main__':main()
