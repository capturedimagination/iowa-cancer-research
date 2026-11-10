"""Validate a sampling-induced two-stage lifetime law in a branching model.

Source workbook observations do not enter this entirely synthetic experiment.
The numerical shortcut samples a random tagged path plus extinction outcomes of
its discarded sister subtrees. A separate full-tree reviewer checks this model.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import platform

import numpy as np
import scipy
from scipy.integrate import quad

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def extinction(s,lam,mu):
    s=np.asarray(s,dtype=float)
    if lam==mu:return lam*s/(1+lam*s)
    e=np.exp(-(lam-mu)*s)
    return mu*(-np.expm1(-(lam-mu)*s))/(lam-mu*e)


def sister_extinction_factor(t,lam,mu,T):
    if lam==mu:return (1+lam*(T-t))/(1+lam*T)
    return (lam*np.exp((lam-mu)*(T-t))-mu)/(lam*np.exp((lam-mu)*T)-mu)


def selected_tag_survival(t,lam,mu):
    if lam==mu:return np.exp(-lam*t)*(1+lam*t)
    return (lam*np.exp(-mu*t)-mu*np.exp(-lam*t))/(lam-mu)


def analytic_bin(lo,hi,lam,mu,T,group):
    if group=='path_survives':return {'exposure':hi-lo,'divisions':lam*(hi-lo),'deaths':0.0}
    if group=='prospective':
        risk=lambda t:np.exp(-mu*t)
        exposure=quad(risk,lo,hi,epsabs=1e-12)[0]
        return {'exposure':exposure,'divisions':lam*exposure,'deaths':mu*exposure}
    h=1-float(extinction(T,lam,mu))
    def birth(t):
        q=float(extinction(T-t,lam,mu));a=sister_extinction_factor(t,lam,mu,T)
        return lam*np.exp(-mu*t)*(1-q*q*a)/h
    return {'exposure':quad(lambda t:selected_tag_survival(t,lam,mu),lo,hi,epsabs=1e-12)[0],
        'divisions':quad(birth,lo,hi,epsabs=1e-12)[0],
        'deaths':float(selected_tag_survival(lo,lam,mu)-selected_tag_survival(hi,lam,mu))}


def rate_summary(events,exposure,expected_events,expected_exposure):
    n=len(events);r=float(events.sum()/exposure.sum())
    se=float(np.std(events-r*exposure,ddof=1)/np.sqrt(n)/exposure.mean())
    expected=expected_events/expected_exposure
    return {'events':int(events.sum()),'at_risk_time':float(exposure.sum()),'rate':r,
        'delta_method_founder_Monte_Carlo_SE':se,'ratio_of_exact_expected_events_to_exposure':expected,
        'difference_in_Monte_Carlo_SE':None if se==0 else (r-expected)/se}


def run_case(lam,mu,spec,rng):
    n=spec['prospective_founders_per_case'];T=spec['model']['horizon'];bins=spec['observation_bins']
    death=np.full(n,np.inf) if mu==0 else rng.exponential(1/mu,n)
    stop=np.minimum(death,T)
    counts=rng.poisson(lam*stop)
    owners=np.repeat(np.arange(n),counts)
    times=rng.random(len(owners))*stop[owners]
    q=extinction(T-times,lam,mu)
    assert ((q>=0)&(q<=1)).all()
    with np.errstate(divide='ignore'):
        log_all=np.bincount(owners,weights=np.log(q),minlength=n)
    side_survival=-np.expm1(log_all)
    path_survives=death>T
    family=path_survives | (rng.random(n)<side_survival)
    h=1-float(extinction(T,lam,mu))
    hse=np.sqrt(h*(1-h)/n)
    ans={'lambda':lam,'mu':mu,'prospective_founders':n,'family_selected_founders':int(family.sum()),
        'path_selected_founders':int(path_survives.sum()),'family_survival_fraction':float(family.mean()),
        'exact_family_survival_probability':h,'family_survival_probability_Monte_Carlo_SE':float(hse),
        'family_inclusion_z':None if hse==0 else float((family.mean()-h)/hse),
        'family_selected_tag_deaths':int((family & ~path_survives).sum()),'groups':{}}
    groups={'prospective':np.ones(n,dtype=bool),'path_survives':path_survives,'family_survives':family}
    grid=np.linspace(0,T,bins+1)
    for name,take in groups.items():
        assert take.sum()>1
        record={'founders':int(take.sum()),'survival_curve':[],'bins':[]}
        for t in grid:
            observed=float((stop[take]>=t).mean()) if t<T else float(path_survives[take].mean())
            exact=1.0 if name=='path_survives' else float(np.exp(-mu*t) if name=='prospective' else selected_tag_survival(t,lam,mu))
            se=np.sqrt(exact*(1-exact)/take.sum())
            record['survival_curve'].append({'time':float(t),'observed':observed,'exact':exact,
                'conditional_binomial_Monte_Carlo_SE':float(se),'difference_in_Monte_Carlo_SE':None if se==0 else (observed-exact)/se})
        for lo,hi in zip(grid[:-1],grid[1:]):
            exposure=np.clip(stop-lo,0,hi-lo)[take]
            de=((death>=lo)&(death<hi))[take].astype(int)
            be=np.bincount(owners[(times>=lo)&(times<hi)],minlength=n)[take]
            exact=analytic_bin(lo,hi,lam,mu,T,name)
            record['bins'].append({'start':float(lo),'end':float(hi),
                'division':rate_summary(be,exposure,exact['divisions'],exact['exposure']),
                'death':rate_summary(de,exposure,exact['deaths'],exact['exposure'])})
        ans['groups'][name]=record
    return ans


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,default=BASE/'sampling-simulation');args=ap.parse_args()
    spec=json.loads((BASE/'sampling-simulation-plan.json').read_text());freeze=json.loads((BASE/'plan-freeze.json').read_text())
    assert sha(BASE/'sampling-simulation-plan.json')==freeze['sha256']
    rng=np.random.default_rng(spec['seed'])
    rows=[run_case(lam,mu,spec,rng) for lam,mu in spec['rate_pairs']]
    # Algebraic consistency checks are independent of random draws.
    max_identity=0.;max_exchange=0.
    for lam,mu in spec['rate_pairs']:
        for t in np.linspace(0,1,101):
            h=1-float(extinction(1,lam,mu));q=float(extinction(1-t,lam,mu));a=sister_extinction_factor(t,lam,mu,1)
            joint=np.exp(-mu*t)*(1-q*a)/h
            max_identity=max(max_identity,abs(joint-selected_tag_survival(t,lam,mu)))
            max_exchange=max(max_exchange,abs(selected_tag_survival(t,lam,mu)-selected_tag_survival(t,mu,lam)))
    assert max_identity<1e-12 and max_exchange<1e-12
    # Exact edge fixtures do not depend on Monte Carlo tolerance.
    for r in rows:
        if r['lambda']==0 or r['mu']==0:assert r['family_selected_tag_deaths']==0
        if r['mu']==0:assert r['family_selected_founders']==r['prospective_founders']
    zs=[abs(x['difference_in_Monte_Carlo_SE']) for r in rows for g in r['groups'].values()
        for x in g['survival_curve'] if x['difference_in_Monte_Carlo_SE'] is not None]
    result={'created_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':freeze['sha256'],'script_sha256':sha(__file__),
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'seed':spec['seed'],'model':'Synthetic homogeneous binary branching birth/death; no empirical calibration.',
        'cases':rows,'checks':{'max_joint_risk_identity_error':max_identity,'max_death_law_rate_exchange_error':max_exchange,
        'max_survival_curve_Monte_Carlo_SE_discrepancy':max(zs),'zero_rate_edge_fixtures_passed':True},
        'interpretation':['Family-surviving random tags, endpoint-surviving tags and unselected tags are distinct observations.',
            'Exact selected tagged lifetime is hypoexponential (Erlang2 at equal rates), censored at T; it does not establish two biological death stages.',
            'Death-only selected observations cannot distinguish exchange of division and death rates in this model.',
            'No claim of universal source-sampling correction, cancer mechanism, clinical effect or first-ever priority.']}
    args.out.mkdir(parents=True,exist_ok=True);(args.out/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'cases':len(rows),'founders_per_case':spec['prospective_founders_per_case'],'checks':result['checks']},indent=2))


if __name__=='__main__':main()
