#!/usr/bin/env python3
"""Frozen common-clock model and exact finite-calibration moments.

No calculations run on import. Reuses the pinned stationary positive-joint core;
the independent verifier and complete-tree simulator must not import this file.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import time

import numpy as np
from numpy.polynomial.legendre import leggauss
import scipy
from scipy.special import gamma, gammainc
from scipy.stats import binom

from age_lineage_models import ErlangModel

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
PROTOCOL_SHA = '53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919'
OLD_CORE_SHA = '2e7f53d6175b8da9215706e2eaee81758dc058265ff5d3c42583875d21987a59'
METHODS = ('oracle_bin_mean', 'shared_fitted_mean',
           'shared_fitted_mean_corrected', 'unbiased_target_sample_covariance')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_probability(value, label):
    if not math.isfinite(value) or not -1e-8 <= value <= 1+1e-8:
        raise ArithmeticError('Invalid probability: '+label+' value='+repr(value))


def clock(t, case):
    t = np.asarray(t)
    return t + case['amplitude'] * case['period'] / (2 * math.pi) * (
        1 - np.cos(2 * math.pi * t / case['period']))


def rate(t, case):
    return 1 + case['amplitude'] * np.sin(2 * math.pi * np.asarray(t) / case['period'])


def bin_grid(plan):
    cutoff = plan['times']['pair_birth_cutoff']
    return [{'bin_id': f'w{width:g}-b{i}', 'width': width,
             'left': i * width, 'right': (i + 1) * width}
            for width in plan['times']['birth_bin_widths']
            for i in range(round(cutoff / width))]


def finite_moments(p, joint, m, n):
    """Finite sum over shared independent Binomial calibration, not asymptotics."""
    if m < 2 or n < 2:
        raise ValueError('This frozen four-estimator design requires m,n >= 2')
    probabilities = np.array([1 - 2 * p + joint, p - joint, p - joint, joint])
    if not np.all(np.isfinite(probabilities)):
        raise ValueError(f'Nonfinite joint Bernoulli inputs p={p!r}, j={joint!r}, categories={probabilities.tolist()!r}')
    if np.min(probabilities) < -1e-12 or np.max(probabilities) > 1 + 1e-12:
        raise ValueError(f'Invalid joint Bernoulli inputs p={p!r}, j={joint!r}, categories={probabilities.tolist()!r}')
    if abs(probabilities.sum() - 1) > 1e-12:
        raise ValueError('Invalid probability normalization')
    # No projection is used in these deterministic moment sums.
    q = np.arange(m + 1, dtype=float) / m
    weights = binom.pmf(np.arange(m + 1), m, p)
    if abs(weights.sum() - 1) > 1e-12:
        raise ValueError('Binomial weights did not normalize')
    scores = np.stack([q*q, -q*(1-q), -q*(1-q), (1-q)**2], axis=1)
    conditional_means = scores @ probabilities
    conditional_vars = np.sum(probabilities * (scores - conditional_means[:, None])**2, axis=1) / n
    answer = {}
    for name, correction in (
        ('shared_fitted_mean', np.zeros(m + 1)),
        ('shared_fitted_mean_corrected', q*(1-q)/(m-1)),
    ):
        conditional = conditional_means - correction
        mean = float(weights @ conditional)
        variance = float(weights @ conditional_vars + weights @ ((conditional - mean)**2))
        lower = -.25 if name == 'shared_fitted_mean' else -m/(4*(m-1))
        answer[name] = {'mean': mean, 'variance': variance, 'range': [lower, 1.]}
    oracle_scores = np.array([p*p, -p*(1-p), -p*(1-p), (1-p)**2])
    oracle_mean = float(probabilities @ oracle_scores)
    oracle_var = float(probabilities @ ((oracle_scores - oracle_mean)**2)) / n
    answer['oracle_bin_mean'] = {'mean': oracle_mean, 'variance': oracle_var, 'range': [-.25, 1.]}
    c = joint - p*p
    v = p*(1-p)
    # The sample-covariance formula is separately checked by finite enumeration.
    sample_var = (v*v-c*c+c*(1-2*p)**2)/n + (v*v+c*c)/(n*(n-1))
    answer['unbiased_target_sample_covariance'] = {
        'mean': c, 'variance': sample_var,
        'range': [-n/(4*(n-1)), n/(4*(n-1))]}
    return {name: answer[name] for name in METHODS}


def born_density(model, physical, case):
    """Unnormalized first-division densities, including initial type/stage law."""
    x = clock(physical, case)
    r = rate(physical, case)
    remaining = np.arange(model.k, 0, -1)
    out = []
    for z, alpha in enumerate(model.alpha):
        density = (alpha**remaining[:, None] * x[None, :]**(remaining[:, None]-1)
                   * np.exp(-alpha*x)[None, :] / gamma(remaining)[:, None])
        out.append(r * np.exp(-model.mu*x) * np.sum(model.initial[z, :, None]*density, axis=0))
    return np.asarray(out)


def eligibility_formula(model, physical_cutoff, case):
    kleft = np.arange(model.k, 0, -1)
    effective = model.alpha + model.mu
    by_state = (model.alpha[:, None]/effective[:, None])**kleft
    by_state *= gammainc(kleft, effective[:, None]*clock(physical_cutoff, case))
    return np.sum(model.initial*by_state, axis=1)


def evaluate(case, plan, strict=False, progress=None):
    order = plan['numeric']['quadrature_orders'][int(strict)]
    model = ErlangModel(case, maximum_time=4.,
                        rtol=plan['numeric']['strict_rtol' if strict else 'primary_rtol'],
                        atol=plan['numeric']['strict_atol' if strict else 'primary_atol'])
    row = {'case_id': case['case_id'], 'configuration': case,
           'family': [], 'Q': [], 'U': [], 'contrasts': [], 'bins': [],
           'pairs': [], 'calibration': [], 'partitions': [], 'controls': []}
    if progress is not None:
        progress.update(row)
        row = progress
    queries = plan['times']['evaluation_times']
    for horizon in plan['times']['selection_horizons']:
        mapped = float(clock(horizon, case))
        h = model.family_survival(mapped)
        require_probability(h, 'family survival')
        row['family'].append({'T': horizon, 'operational_T': mapped, 'probability': h})
        for t in sorted(set([0., *queries, horizon])):
            q = model.selected_path_survival(float(clock(t, case)), mapped)
            loss = model.selected_path_loss(float(clock(t, case)), mapped)
            require_probability(q, 'selected path survival')
            require_probability(loss, 'selected path loss')
            row['Q'].append({'t': t, 'T': horizon, 'value': q, 'positive_loss': loss,
                             'joint_probability': q*h, 'complement_error': q+loss-1})
            assert abs(q+loss-1) <= 1e-8
            if t == horizon:
                assert abs(q*h-math.exp(-case['mu']*mapped)) <= 1e-8
    qindex = {(v['t'], v['T']): v for v in row['Q']}
    hindex = {v['T']: v['probability'] for v in row['family']}
    for t1, t2 in plan['times']['contrast_pairs']:
        for t in queries:
            a, b = qindex[t,t1], qindex[t,t2]
            row['contrasts'].append({'t': t, 'T_early': t1, 'T_late': t2,
                'value': b['value']-a['value'],
                'positive_removed_loss': hindex[t1]*a['positive_loss']-hindex[t2]*b['positive_loss']})
            require_probability(row['contrasts'][-1]['positive_removed_loss'], 'removed-stratum loss')
    row['U'] = [{'t': t, 'value': math.exp(-case['mu']*float(clock(t, case)))}
                for t in plan['times']['unconditional_path_queries']]
    for query in row['U']:
        require_probability(query['value'], 'unconditional path survival')
    nodes, weights = leggauss(order)
    all_type_mass = eligibility_formula(model, plan['times']['pair_birth_cutoff'], case)
    eligibility = float(all_type_mass.sum())
    require_probability(eligibility, 'pair eligibility')
    row['eligibility_probability'] = eligibility
    row['eligible_mother_type_weights'] = (all_type_mass/eligibility).tolist()
    for spec in bin_grid(plan):
        physical = spec['left'] + (nodes+1)*spec['width']/2
        integration_weights = weights*spec['width']/2
        densities = born_density(model, physical, case)
        density = densities.sum(axis=0)
        if np.any(density <= 0):
            raise ArithmeticError('Interior quadrature node has nonpositive birth density')
        type_mass = densities @ integration_weights
        mass = float(type_mass.sum())
        require_probability(mass, 'birth-bin eligibility')
        maternal = densities/density
        normalized_weights = integration_weights*density/mass
        row['bins'].append({**spec, 'probability': mass,
                            'mother_type_weights': (type_mass/mass).tolist()})
        for lag in plan['times']['pair_lags']:
            delta = clock(physical+lag, case)-clock(physical, case)
            assert np.min(delta) >= 0 and np.max(delta) <= 4
            survival = model.survival_solution.sol(delta).reshape(model.types, model.k, order)[:, 0, :]
            g = model.kernel @ survival
            p_birth = np.sum(maternal*g, axis=0)
            conditional_c = np.sum(maternal*(g-p_birth)**2, axis=0)
            p = float(normalized_weights @ p_birth)
            c_within = float(normalized_weights @ conditional_c)
            c_context = float(normalized_weights @ ((p_birth-p)**2))
            direct_joint = float(normalized_weights @ np.sum(maternal*g*g, axis=0))
            if case['mu'] == 0:
                p, c_within, c_context, direct_joint = 1., 0., 0., 1.
            c = c_within+c_context
            joint = p*p+c
            assert abs(joint-direct_joint) <= 1e-8
            no_transmission = model.types == 1 or model.rho == 0
            bound = None
            if no_transmission:
                lipschitz = 2*case['mu']*case['amplitude']*abs(math.sin(math.pi*lag/case['period']))
                if lag/case['period'] == round(lag/case['period']):
                    lipschitz = 0.
                bound = min(.25, lipschitz**2*spec['width']**2/4)
                assert c_within <= 1e-8 and c_context <= bound+1e-8
            pair = {'bin_id': spec['bin_id'], 'lag': lag, 'p': p, 'j': joint, 'c': c,
                    'mean_conditional_covariance': c_within,
                    'birth_probability_variance': c_context,
                    'no_transmission_bound': bound, 'direct_joint_integral': direct_joint,
                    'joint_reconstruction_error': joint-direct_joint}
            row['pairs'].append(pair)
            for m in plan['calibration']['m']:
                for n in plan['calibration']['n']:
                    moments = finite_moments(p, joint, m, n)
                    assert abs(moments['shared_fitted_mean']['mean']-(c+p*(1-p)/m)) <= 1e-10
                    for method in METHODS:
                        value = moments[method]
                        assert value['variance'] >= -1e-12
                        if method != 'shared_fitted_mean':
                            assert abs(value['mean']-c) <= 1e-10
                    row['calibration'].append({'bin_id': spec['bin_id'], 'lag': lag,
                                               'm': m, 'n': n, 'methods': moments})
    bin_index = {r['bin_id']: r for r in row['bins']}
    pair_index = {(r['bin_id'], r['lag']): r for r in row['pairs']}
    for lag in plan['times']['pair_lags']:
        pooled = pair_index['w2-b0', lag]
        previous_context = float('inf')
        for width in plan['times']['birth_bin_widths']:
            selected = [r for r in row['bins'] if r['width'] == width]
            mass = sum(r['probability'] for r in selected)
            assert abs(mass-eligibility) <= 1e-8
            within = sum(r['probability']*pair_index[r['bin_id'],lag]['c'] for r in selected)/mass
            conditional = sum(r['probability']*pair_index[r['bin_id'],lag]['mean_conditional_covariance'] for r in selected)/mass
            context = sum(r['probability']*pair_index[r['bin_id'],lag]['birth_probability_variance'] for r in selected)/mass
            between = sum(r['probability']*(pair_index[r['bin_id'],lag]['p']-pooled['p'])**2 for r in selected)/mass
            assert abs(within+between-pooled['c']) <= 1e-8
            assert abs(conditional-pooled['mean_conditional_covariance']) <= 1e-8
            assert context <= previous_context+1e-8
            previous_context = context
            row['partitions'].append({'lag': lag, 'width': width, 'probability_sum': mass,
                'weighted_within_covariance': within, 'weighted_conditional_covariance': conditional,
                'remaining_context_variance': context, 'between_bin_mean_variance': between})
        if case['amplitude'] == 0:
            old = model.pair_summary(lag, cutoff=2.)
            error = max(abs(pooled['p']-old['daughter_survival_mean']),
                        abs(pooled['c']-old['covariance']))
            assert error <= 1e-8
            row['controls'].append({'control': 'stationary_pair_recovery', 'lag': lag, 'error': error})
    if model.types == 1 and model.k == 1:
        assert max(abs(r['value']) for r in row['contrasts']) <= 1e-8
        row['controls'].append({'control': 'exponential_horizon_invariance', 'passed': True})
    if case['mu'] == 0:
        assert all(abs(r['value']-1) <= 1e-8 for r in row['Q'])
        assert all(r['c'] == 0 for r in row['pairs'])
    assert len(row['Q']) == 17 and len(row['bins']) == 15 and len(row['pairs']) == 45
    assert len(row['calibration']) == 270
    return row


def numeric_leaves(value, path=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from numeric_leaves(child, path+'/'+key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from numeric_leaves(child, path+'/'+str(i))
    elif isinstance(value, (int,float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ArithmeticError('Nonfinite number at '+path)
        yield path, float(value)


def enumerated_covariance(p, joint, n):
    probabilities = (1-2*p+joint, p-joint, p-joint, joint)
    mean = second = 0.
    for a in range(n+1):
        for b in range(n-a+1):
            for c in range(n-a-b+1):
                d = n-a-b-c
                counts = (a,b,c,d)
                probability = math.factorial(n)
                for k, prob in zip(counts, probabilities):
                    probability *= prob**k/math.factorial(k)
                value = n/(n-1)*(d/n-(c+d)*(b+d)/n**2)
                mean += probability*value
                second += probability*value*value
    return mean, second-mean*mean


def fixtures():
    checks=[]
    for p,c in ((.2,.04),(.4,-.05),(.73,.08),(0.,0.),(1.,0.)):
        for n in (2,3,5):
            output = finite_moments(p,p*p+c,7,n)
            reference = enumerated_covariance(p,p*p+c,n)
            actual = output['unbiased_target_sample_covariance']
            assert abs(actual['mean']-reference[0]) < 1e-13
            assert abs(actual['variance']-reference[1]) < 1e-13
            checks.append(f'finite_four_category_covariance_p{p}_c{c}_n{n}')
    for m,n in ((1,5),(5,1)):
        try:
            finite_moments(.3,.1,m,n)
            raise AssertionError('Undefined estimator accepted')
        except ValueError:
            checks.append(f'undefined_m{m}_n{n}_rejected')
    for bad in (float('nan'), float('inf'), -0.1, 1.1):
        try:
            require_probability(bad, 'fixture')
            raise AssertionError('Invalid probability accepted')
        except ArithmeticError:
            checks.append('invalid_probability_'+repr(bad)+'_rejected')
    try:
        finite_moments(float('nan'), .1, 5, 5)
        raise AssertionError('Nonfinite moment input accepted')
    except ValueError:
        checks.append('nonfinite_joint_moment_input_rejected')
    for a,P in ((0.,2.),(.75,2.),(.75,4.)):
        case={'amplitude':a,'period':P}
        x=np.linspace(0,4,101)
        assert np.all(np.diff(clock(x,case))>0)
        assert float(clock(0,case))==0 and float(clock(4,case))==4
        assert np.min(rate(x,case))>=.25
        checks.append(f'clock_support_a{a}_P{P}')
    return {'status':'PASS','count':len(checks),'checks':checks,'scientific_grid_run':False}


def save_new(path,value):
    encoded=json.dumps(value,indent=2,allow_nan=False)+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        f.write(encoded)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--out',type=Path,default=BASE/'results.json')
    parser.add_argument('--strict-out',type=Path,default=BASE/'strict-results.json')
    parser.add_argument('--fixture-report',type=Path)
    args=parser.parse_args()
    assert sha(BASE/'protocol.json')==PROTOCOL_SHA
    assert sha(ROOT/'scripts/age_lineage_models.py')==OLD_CORE_SHA
    checked=fixtures()
    if args.fixture_report:
        save_new(args.fixture_report,{**checked,'code_sha256':sha(__file__),'protocol_sha256':PROTOCOL_SHA})
    if not args.run:
        print(json.dumps(checked,indent=2));return
    if args.out.resolve() == args.strict_out.resolve():
        raise ValueError('Primary and strict output paths must differ')
    if args.out.exists() or args.strict_out.exists():
        raise FileExistsError('First outputs must be preserved; choose new paths')
    plan=json.loads((BASE/'protocol.json').read_text())
    started=time.monotonic()
    provenance={'created_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':PROTOCOL_SHA,
        'code_sha256':sha(__file__),'stationary_core_sha256':OLD_CORE_SHA,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}}
    rows=[]; strict_rows=[]; convergence=[]; current={}
    try:
        for case in plan['cases']:
            current={'case_id':case['case_id'],'primary':{},'strict':{}}
            base=evaluate(case,plan,progress=current['primary'])
            strict=evaluate(case,plan,strict=True,progress=current['strict'])
            a,b=dict(numeric_leaves(base)),dict(numeric_leaves(strict))
            assert a.keys()==b.keys()
            errors={key:abs(a[key]-b[key]) for key in a}
            bad=[key for key,error in errors.items() if error>(1e-10 if '/calibration/' in key else 1e-8)]
            assert not bad,bad[:20]
            worst=max(errors,key=errors.get)
            convergence.append({'case_id':case['case_id'],'numeric_fields':len(a),
                'maximum_absolute_difference':errors[worst],'maximum_difference_field':worst,'passed':True})
            rows.append(base);strict_rows.append(strict)
            print(json.dumps({'case_id':case['case_id'],'completed':len(rows),'total':len(plan['cases'])}),flush=True)
        result={**provenance,'status':'PASS','runtime_seconds':time.monotonic()-started,
                'cases':rows,'convergence':convergence,'completed_cases':len(rows),
                'scope':plan['scope'],'limits':plan['limits']}
        strict_result={**provenance,'solver':'DOP853 rtol1e-12 atol1e-14,96-point quadrature','cases':strict_rows}
        # Both payloads are checked before either first output is written.
        json.dumps(result,allow_nan=False);json.dumps(strict_result,allow_nan=False)
        save_new(args.out,result);save_new(args.strict_out,strict_result)
    except BaseException as error:
        failed=args.out.with_name(args.out.stem+'-failed-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
        # Diagnostic serialization never silently converts invalid values to probabilities.
        def diagnostic(v):
            if isinstance(v,dict):return {k:diagnostic(x) for k,x in v.items()}
            if isinstance(v,list):return [diagnostic(x) for x in v]
            if isinstance(v,float) and not math.isfinite(v):return {'NONFINITE_DIAGNOSTIC':repr(v)}
            return v
        save_new(failed,diagnostic({**provenance,'status':'FAILED_OR_INCOMPLETE',
            'error_type':type(error).__name__,'error':str(error),'completed_cases':rows,
            'completed_strict_cases':strict_rows,'current_case':current,'convergence':convergence}))
        raise
    print(json.dumps({'status':'PASS','cases':len(rows),'pair_bins':sum(len(r['pairs']) for r in rows),
                     'calibration_settings':sum(len(r['calibration']) for r in rows)},indent=2))


if __name__=='__main__':
    main()
