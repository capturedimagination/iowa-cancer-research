#!/usr/bin/env python3
"""Compare production bounds with the independently frozen rational verifier.

Only synthetic interval/status records are used. The empirical driver is read
for provenance, never imported or invoked. Original verification files stay intact.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'scripts'))
import lineage_missing_bounds as production

spec = importlib.util.spec_from_file_location('independent_bounds_truth', BASE/'verify_bounds.py')
truth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(truth)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    tolerance = 1e-12
    core = ROOT/'scripts/lineage_missing_bounds.py'
    driver = ROOT/'scripts/bound_hct116_lineages.py'
    core_hash = sha(core)
    plan = json.loads((BASE/'protocol.json').read_text())
    assert sha(BASE/'protocol.json') == 'c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771'
    original_freeze = json.loads((BASE/'verification-freeze.json').read_text())
    assert sha(BASE/'verify_bounds.py') == original_freeze['script_sha256']
    assert sha(BASE/'verification-protocol.json') == original_freeze['protocol_sha256']
    failures, controls = [], []
    comparisons = 0
    maximum_absolute_error = 0.0

    def compare_ratio(name, status, lower, upper, endpoint=False):
        nonlocal comparisons, maximum_absolute_error
        # Endpoint certainty belongs to the caller; the generic production API
        # cannot infer whether a positive lower value is at t<T or at t=T.
        s, a, b = truth.normalize(status, lower, upper, endpoint)
        expected = truth.exhaustive_bounds(s, a, b)
        production_status = s if endpoint else status
        actual = production.ratio_bounds([(float(x), float(y), z) for x, y, z in zip(a, b, production_status)])
        comparisons += 1
        n = sum(v == 1 for v in s)
        m = sum(v is None and y > 0 for v, y in zip(s, b))
        passed = (actual['mandatory_selected'] == n and actual['optional_selected'] == m
                  and actual['maximum_selected'] == n+m and actual['zero_denominator_possible'] == (n == 0))
        if expected is None:
            passed &= not actual['defined_for_some_completion'] and actual['lower'] is None and actual['upper'] is None
        else:
            errors = [abs(actual[k]-float(v)) for k, v in zip(('lower','upper'), expected)]
            maximum_absolute_error = max(maximum_absolute_error, *errors)
            passed &= actual['defined_for_some_completion'] and max(errors) <= tolerance
        if not passed:
            failures.append({'case':name,'check':'ratio','expected':truth.display(expected),'actual':actual})
        return actual, expected, passed

    fixtures = [
        ('mandatory',[1,1],['1/4','3/4'],['1/2','1'],False),
        ('extinct_later_alive_earlier',[0,1],['1','1/4'],['1','1/2'],False),
        ('optional_low_and_high',[1,None,None],['1/2','0','3/4'],['1/2','1/4','1'],False),
        ('optional_only',[None,None],['1/4','3/4'],['1/2','1'],False),
        ('initial_alive',[1,None],['1','1'],['1','1'],False),
        ('selected_zero_infimum',[1],['0'],['1/2'],False),
        ('endpoint_promotes_positive_lower',[None,None],['1/4','0'],['1/2','1'],True),
        ('zero_upper_cannot_be_selected',[None,1],['0','1/2'],['0','1/2'],False),
        ('empty_selection',[0,0],['1','0'],['1','1/2'],False),
        ('empty_roster',[],[],[],False),
        ('all_optional_zero_upper',[None,None],['0','0'],['0','0'],False),
        ('nonbinary_fraction_arithmetic',[1,None,None],['1/3','1/7','2/5'],['2/3','3/7','4/5'],False),
    ]
    for name, status, lower, upper, endpoint in fixtures:
        actual, expected, passed = compare_ratio(name,status,lower,upper,endpoint)
        controls.append({'name':name,'expected':truth.display(expected),'actual':actual,'passed':passed})
    for name, rows in [
        ('selected_zero_upper_rejected',[(0.,0.,1)]),
        ('invalid_interval_rejected',[(0.8,0.2,None)]),
    ]:
        try:
            production.ratio_bounds(rows)
            passed = False
        except ValueError:
            passed = True
        controls.append({'name':name,'passed':passed})
        if not passed: failures.append({'case':name})
    # A zero-upper optional row must not inflate the maximum earlier count.
    early = production.ratio_bounds([(0.,0.,None),(0.25,0.75,None)])
    late = production.ratio_bounds([(0.,0.,0),(0.25,0.75,1)])
    cap_control = production.contrast_bounds(early,late)
    passed = cap_control['lower'] == cap_control['upper'] == cap_control['nesting_cap'] == 0 and not cap_control['zero_denominator_possible']
    controls.append({'name':'known_later_possible_earlier_zero_upper_pruned','actual':cap_control,'passed':passed})
    if not passed: failures.append({'case':'known_later_possible_earlier_zero_upper_pruned'})
    empty_late = production.contrast_bounds(early,production.ratio_bounds([(1.,1.,0)]))
    passed = not empty_late['defined_for_some_completion'] and empty_late['lower'] is None and empty_late['upper'] is None
    controls.append({'name':'undefined_later_contrast','actual':empty_late,'passed':passed})
    if not passed: failures.append({'case':'undefined_later_contrast'})
    for name, early_rows, late_rows in [
        ('later_known_earlier_impossible_rejected',[(1.,1.,0)],[(1.,1.,1)]),
        ('known_later_exceeds_possible_earlier_rejected',[(1.,1.,1)],[(1.,1.,1),(1.,1.,1)]),
    ]:
        try:
            production.contrast_bounds(production.ratio_bounds(early_rows),production.ratio_bounds(late_rows))
            passed = False
        except ValueError:
            passed = True
        controls.append({'name':name,'passed':passed})
        if not passed: failures.append({'case':name})

    original_plan = json.loads((BASE/'verification-protocol.json').read_text())
    grid = original_plan['nested_horizon_grid']
    intervals = [(F(a),F(b)) for a,b in grid['intervals_in_row_order']]
    status_cases = contained = no_later = 0
    for size in grid['roster_sizes']:
        lower,upper = zip(*intervals[:size])
        for pairs in product(grid['per_row_status_pairs'],repeat=size):
            status_cases += 1
            early_s,late_s = zip(*pairs)
            early,_,_ = compare_ratio('grid_early',early_s,lower,upper)
            late,_,_ = compare_ratio('grid_late',late_s,lower,upper)
            outer = production.contrast_bounds(early,late)
            count = 0
            for e in truth.selection_vectors(early_s):
                for l in truth.selection_vectors(late_s):
                    if not sum(l) or any(y>x for x,y in zip(e,l)):
                        continue
                    for probabilities in product(*[(a,b) for a,b in intervals[:size]]):
                        first = sum((x*p for x,p in zip(e,probabilities)),F(0))/sum(e)
                        second = sum((x*p for x,p in zip(l,probabilities)),F(0))/sum(l)
                        delta = second-first
                        count += 1
                        if not outer['defined_for_some_completion'] or not outer['lower']-tolerance <= float(delta) <= outer['upper']+tolerance:
                            failures.append({'case':'grid_contrast','statuses':pairs,'true_delta':str(delta),'production':outer})
            contained += count
            if not count: no_later += 1
    assert sha(core) == core_hash, 'Production core changed during this check'
    scenarios = len(plan['baseline_frames'])*len(plan['annotation_sensitivities']['apoptosis_death_frame_offsets'])*len(plan['annotation_sensitivities']['ambiguity_policies'])
    expected_q = scenarios*len(plan['clock']['selection_horizons_hours'])*len(plan['clock']['common_evaluation_hours'])
    expected_contrast = scenarios*len(plan['contrasts']['pairs_hours'])*len(plan['clock']['common_evaluation_hours'])
    assert (scenarios,expected_q,expected_contrast)==(20,300,300)
    return {
        'version':1,'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS' if not failures else 'FAIL',
        'production_core_sha256':core_hash,'production_driver_sha256':sha(driver),'empirical_protocol_sha256':sha(BASE/'protocol.json'),
        'independent_truth_code_sha256':sha(BASE/'verify_bounds.py'),'checker_sha256':sha(Path(__file__)),
        'synthetic_controls':controls,'ratio_comparisons':comparisons,'maximum_absolute_ratio_error':maximum_absolute_error,
        'float_comparison_tolerance':tolerance,'nested_status_cases':status_cases,'exact_rational_contrasts_checked':contained,
        'nested_status_cases_without_positive_later_selection':no_later,
        'driver_static_counts':{'scenarios':scenarios,'ratio_rows':expected_q,'contrast_rows':expected_contrast},
        'failures':failures,'empirical_driver_invoked':False,'source_records_read':False,
        'scope':'Production arithmetic versus independent exact rectangular-closure enumeration; not empirical validation or outward-rounded interval certification'
    }


if __name__ == '__main__':
    result = run()
    (BASE/'production-check.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['status','production_core_sha256','ratio_comparisons','maximum_absolute_ratio_error','nested_status_cases','exact_rational_contrasts_checked','driver_static_counts','failures']},indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)
