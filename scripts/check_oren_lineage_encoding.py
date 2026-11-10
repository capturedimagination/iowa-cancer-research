"""Check source-code patterns without assigning empirical times or hazards."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10'
SOURCE=ROOT/'research/treatment-discovery/sources/lineage-2026-11-10'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    structure=json.loads((BASE/'workbook-structure.json').read_text())
    freeze=json.loads((BASE/'plan-freeze.json').read_text())
    assert sha(BASE/'sampling-simulation-plan.json')==freeze['sha256']
    assert sha(SOURCE/'oren-figure1-matrices.npz')==structure['derived_cache']['sha256']
    with np.load(SOURCE/'oren-figure1-matrices.npz',allow_pickle=False) as z:
        division=z['division'];death=z['death']
    tables=json.loads((SOURCE/'oren-figure1-small-tables.json').read_text())
    assert division.shape==death.shape==(1135,2025)
    assert np.isfinite(division).all() and np.isfinite(death).all()
    assert np.equal(division,np.round(division)).all()
    dd=np.diff(division,axis=1);dx=np.diff(death,axis=1)
    after_first_one=np.maximum.accumulate(death==1,axis=1)[:,:-1]
    f1d=np.asarray(tables['Figure 1d'][1:],dtype=float)
    positional_mismatches=np.flatnonzero(f1d[:,0]!=death[:,-1])
    result={'checked_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':freeze['sha256'],
        'code_sha256':sha(__file__),'source_sha256':structure['source_sha256'],
        'source_cache_sha256':structure['derived_cache']['sha256'],
        'numpy':np.__version__,'matrix_shape':list(division.shape),
        'division':{'first_column_all_zero':bool((division[:,0]==0).all()),
            'decreasing_steps':int((dd<0).sum()),'positive_steps':int((dd>0).sum()),
            'steps_larger_than_one':int((dd>1).sum()),'maximum_positive_step':float(dd.max()),
            'positive_step_entries_after_prior_death_code_one':int(((dd>0)&after_first_one).sum()),
            'rows_with_positive_step_after_prior_death_code_one':int(((dd>0)&after_first_one).any(axis=1).sum())},
        'death':{'first_column_all_zero':bool((death[:,0]==0).all()),'decreasing_steps':int((dx<0).sum()),
            'positive_steps':int((dx>0).sum()),'rows_with_multiple_positive_steps':int(((dx>0).sum(axis=1)>1).sum()),
            'terminal_zero_rows':int((death[:,-1]==0).sum()),'terminal_one_rows':int((death[:,-1]==1).sum())},
        'figure1d':{'header':tables['Figure 1d'][0],'data_rows':len(f1d),
            'first_column_value_counts':dict(zip(*[x.tolist() for x in np.unique(f1d[:,0],return_counts=True)])),
            'second_column_range':[float(f1d[:,1].min()),float(f1d[:,1].max())]},
        'unverified_positional_join':{'comparison':'Figure1d first column versus terminal death-matrix code, same row number; identity/order not certified',
            'different_rows':len(positional_mismatches),'matrix_excel_row_numbers':(positional_mismatches+1).tolist(),
            'interpretation':'Agreement or disagreement by position cannot establish a biological row join.'},
        'bounds':['Monotone integer patterns are consistent with cumulative encodings, not proof of the study-specific export transformation.',
            'Zeros do not certify observation, alive-at-risk status or unselected founder eligibility.',
            'No empirical event rate, timestamp conversion, censoring-code inference or biological model fit performed.']}
    (BASE/'encoding-checks.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
