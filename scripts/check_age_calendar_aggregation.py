#!/usr/bin/env python3
"""Independent post-results extraction check across all three saved calculations."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
AGG=BASE/'deterministic-interpretation.json'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def summary(v):return {'n':len(v),'minimum':min(v),'median':median(v),'maximum':max(v)}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    if args.out.exists():raise FileExistsError('Preserve first checks')
    aggregate=json.loads(AGG.read_text());reports={}; hashes={}
    for filename in ['results.json','strict-results.json','independent-reference.json']:
        path=BASE/filename;data=json.loads(path.read_text());hashes[filename]=sha(path)
        signs=Counter();contrast_values=[];reductions=[];ratios=[];biases=[];floors=[]
        ordering=Counter();null_settings=0;weighted_ordering_failures=[];aliases=[];signmap={}
        for case in data['cases']:
            cid=case['case_id'];cfg=case['configuration'];pairs={(x['bin_id'],x['lag']):x for x in case['pairs']}
            for x in case['contrasts']:
                value=x['value'];label='positive' if value>1e-8 else 'negative' if value < -1e-8 else 'within_numeric_tolerance'
                signs[label]+=1;contrast_values.append(value);signmap[str((cid,x['t'],x['T_early'],x['T_late']))]=label
            for lag in [0.5,1.0,2.0]:
                context=[]
                for width in [2.0,1.0,0.5,0.25]:
                    selected=[x for x in case['bins'] if x['width']==width]
                    mass=sum(x['probability'] for x in selected)
                    context.append(sum(x['probability']*pairs[x['bin_id'],lag]['birth_probability_variance'] for x in selected)/mass)
                if context[0]>1e-8:reductions.append(1-context[-1]/context[0])
                if any(y>x+1e-8 for x,y in zip(context,context[1:])):weighted_ordering_failures.append([cid,lag])
                if (len(cfg['means'])==1 or cfg['rho']==0) and cfg['amplitude']>0 and lag==cfg['period']:
                    aliases.append({'case_id':cid,'lag':lag,'absolute_covariance':abs(pairs['w2-b0',lag]['c'])})
            for x in case['calibration']:
                methods=x['methods'];q=methods['shared_fitted_mean_corrected'];s=methods['unbiased_target_sample_covariance']
                if cfg['mu']==0:
                    assert all(v['mean']==v['variance']==0 for v in methods.values());null_settings+=1;continue
                assert s['variance']>0
                ordering['greater_by_tolerance' if q['variance']-s['variance']>1e-10 else 'other']+=1
                pair=pairs[x['bin_id'],x['lag']];p=pair['p'];v=p*(1-p)
                ratios.append(q['variance']/s['variance'])
                biases.append(methods['shared_fitted_mean']['mean']-pair['c'])
                floors.append(2*v*v/(x['m']*(x['m']-1))/q['variance'])
        reports[filename]={'cases':len(data['cases']),'contrast_sign_counts':dict(signs),
            'contrast_span':summary(contrast_values),'context_reduction':summary(reductions),
            'corrected_variance_ratio':summary(ratios),'naive_bias':summary(biases),'floor_fraction':summary(floors),
            'variance_ordering':dict(ordering),'zero_death_settings':null_settings,
            'nested_ordering_failures':weighted_ordering_failures,'aliases':aliases,'sign_map':signmap}
    primary=reports['results.json']
    assert primary['contrast_sign_counts']==aggregate['contrast_sign_counts']
    assert primary['zero_death_settings']==540 and primary['variance_ordering']=={'greater_by_tolerance':4860}
    mappings=[('contrast_span',aggregate['contrast_span']),('context_reduction',aggregate['nested_bins']['relative_reduction']),
              ('corrected_variance_ratio',aggregate['calibration']['corrected_variance_ratio']),
              ('naive_bias',aggregate['calibration']['naive_bias']),('floor_fraction',aggregate['calibration']['floor_fraction'])]
    for name,target in mappings:
        for stat in ['n','minimum','median','maximum']:assert primary[name][stat]==target[stat],(name,stat)
    difference_rows=[]
    expected_signs=primary['sign_map'].copy()
    for name,report in reports.items():
        assert report['cases']==20 and report['contrast_sign_counts']==primary['contrast_sign_counts']
        assert report['sign_map']==expected_signs
        assert report['variance_ordering']==primary['variance_ordering'] and report['zero_death_settings']==540
        assert not report['nested_ordering_failures']
        assert len(report['aliases'])==4 and max(r['absolute_covariance'] for r in report['aliases'])<=1e-8
        for metric,_ in mappings:
            assert report[metric]['n']==primary[metric]['n']
            for stat in ['minimum','median','maximum']:
                difference_rows.append({'input':name,'metric':metric,'statistic':stat,
                                       'difference_from_primary':report[metric][stat]-primary[metric][stat]})
        report.pop('sign_map')
    result={'status':'PASS','scope':'Descriptive extraction verification, not a new scientific test.',
            'script_sha256':sha(Path(__file__)),'aggregation_sha256':sha(AGG),'source_hashes':hashes,
            'source_summaries':reports,'aggregate_extrema_counts_and_medians_exactly_reproduced':True,
            'all_240_sign_classifications_identical_across_calculations':True,
            'all_4860_variance_orderings_identical_across_calculations':True,
            'summary_differences':difference_rows}
    with args.out.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':'PASS','sha256':sha(args.out)}))


if __name__=='__main__':main()
