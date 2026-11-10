from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction as F
from itertools import product
from math import isfinite
import hashlib, json
ROOT=Path.cwd(); B=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/missing-branch-bounds'; TOL=1e-12
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=json.loads((B/'protocol.json').read_text()); res=json.loads((B/'results.json').read_text()); private_path=ROOT/'tmp/hct116-missing-bounds/per-cell.json'; priv=json.loads(private_path.read_text())
graph_path=ROOT/plan['source_inputs']['candidate_graph']['path']; graph=json.loads(graph_path.read_text()); nodes={n['id']:n for n in graph['nodes']}
assert sha(B/'protocol.json')==res['protocol_sha256']=='c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771'
assert sha(ROOT/'scripts/lineage_missing_bounds.py')==res['core_sha256']; assert sha(ROOT/'scripts/bound_hct116_lineages.py')==res['script_sha256']
assert sha(graph_path)==res['source_graph_sha256']==plan['source_inputs']['candidate_graph']['sha256']; assert sha(private_path)==res['private_records_sha256']
for k in ['structure_results']:
    assert sha(ROOT/plan['source_inputs'][k]['path'])==plan['source_inputs'][k]['sha256']
assert sha(ROOT/'research/treatment-discovery/sources/lineage-2026-11-10/41467_2018_7788_MOESM5_ESM.xlsx')==plan['source_inputs']['workbook_sha256']
assert res['created_utc']>plan['frozen_at_utc']
bs=plan['baseline_frames']; offsets=plan['annotation_sensitivities']['apoptosis_death_frame_offsets']; policies=plan['annotation_sensitivities']['ambiguity_policies']; hs=plan['clock']['selection_horizons_hours']; ts=plan['clock']['common_evaluation_hours']; pairs=list(map(tuple,plan['contrasts']['pairs_hours'])); qs=sorted(set(hs+ts))
children={n:[] for n in nodes}
for e in graph['edges']: children[e['parent']].append(e['child'])
events={name:set(map(tuple,graph['event_annotation_keys'][name])) for name in ['Divisions','Apoptosis']}
div={};death={};amb={n:set() for n in nodes}
for name,dest in [('Divisions',div),('Apoptosis',death)]:
    bylabel=defaultdict(list)
    for l,f in events[name]:bylabel[l].append(f)
    for n,v in nodes.items():
        fs=[f for f in bylabel[v['label']] if v['first_frame']<=f<=v['last_frame']]
        assert len(fs)<=1;dest[n]=fs[0] if fs else None
for i in graph['issues']:
    if i['kind']=='lineage_present_p53_minus1':amb[i['node']].add(i['frame'])
    else:assert i['kind'] in ['division_no_observed_daughter','division_one_observed_daughter']
for n in nodes:
    if div[n] is not None and death[n] is not None:amb[n].add(min(div[n],death[n]))
roster={b:[r['node'] for r in graph['baseline_rosters'][str(b)] if death[r['node']] is None or death[r['node']]>b] for b in bs}
for row in res['rosters']:
    b=row['baseline_frame'];assert row['eligible_recorded_cells']==len(roster[b]);assert row['source_candidate_cells']==len(graph['baseline_rosters'][str(b)]);assert row['excluded_apoptosis_at_or_before_baseline']==0
assert len(res['rosters'])==len(bs)
# Independent iterative path-frontier accounting; exact dyadic fractions.
# Does not import or call the production mass, ratio, contrast, or joint implementation.
def reference_mass(start,b,h,o,p):
    f=b+2*h; stack=[(start,F(1))]; out=[F(0),F(0),F(0)]
    while stack:
        n,w=stack.pop();v=nodes[n]
        if h==0:out[0]+=w;continue
        issueframes=[x for x in amb[n] if x>b]
        cut=None if not issueframes else min(issueframes) if p=='first_issue' else max(v['first_frame'],b+1)
        d=None if death[n] is None else death[n]+o
        if d is not None and d<=f and (cut is None or d<cut):out[1]+=w;continue
        if cut is not None and cut<=f:out[2]+=w;continue
        if div[n] is not None and div[n]<f:
            out[2]+=w*F(2-len(children[n]),2)
            stack.extend((c,w/2) for c in children[n]);continue
        out[0 if f<=v['last_frame'] else 2]+=w
    assert sum(out)==1
    return tuple(out)
def status(m):return 1 if m[0]>0 else 0 if m[0]+m[2]==0 else None
rank={0:0,None:1,1:2}
indexed={}; masses={};statuses={};total_saved_vectors=0; maxerr=0.0;residual=0.0
for group in priv:
    key=tuple(group[k] for k in ['baseline_frame','death_frame_offset','ambiguity_policy','selection_hours']);assert key not in indexed;indexed[key]=group
    b,o,p,h=key; records=group['records'];assert len(records)==len(roster[b]);assert [r['node'] for r in records]==roster[b];assert len({r['node'] for r in records})==len(records)
    for r in records:
        n=r['node'];m=r['masses_by_elapsed_hour'];assert set(m)==set(map(str,qs)); assert r['family_status']==status(m[str(h)])
        statuses[(b,o,p,h,n)]=r['family_status']
        for t in qs:
            vector=m[str(t)];assert len(vector)==3 and all(isfinite(x) and 0<=x<=1 for x in vector)
            residual=max(residual,abs(sum(vector)-1));assert abs(sum(vector)-1)<=TOL
            ukey=(b,o,p,n,t)
            if ukey in masses:assert masses[ukey]==tuple(vector)
            else:
                expected=reference_mass(n,b,t,o,p);maxerr=max(maxerr,max(abs(float(a)-z) for a,z in zip(expected,vector)));assert max(abs(float(a)-z) for a,z in zip(expected,vector))<=TOL
                masses[ukey]=tuple(vector)
            total_saved_vectors+=1
        for t1,t2 in zip(qs,qs[1:]):
            a,z=m[str(t1)],m[str(t2)];assert z[0]<=a[0]+TOL and z[0]+z[2]<=a[0]+a[2]+TOL;assert z[1]+TOL>=a[1] and z[2]+TOL>=a[2]
        assert m['0']==[1.0,0.0,0.0]
assert set(indexed)==set(product(bs,offsets,policies,hs))
for b,o,p in product(bs,offsets,policies):
    for n in roster[b]:
        for h1,h2 in zip(hs,hs[1:]): assert rank[statuses[b,o,p,h2,n]]<=rank[statuses[b,o,p,h1,n]]
for b,o in product(bs,offsets):
    for n,t in product(roster[b],qs):
        a=masses[b,o,'first_issue',n,t];z=masses[b,o,'whole_episode',n,t]
        assert z[0]<=a[0]+TOL and z[0]+z[2]+TOL>=a[0]+a[2] and z[2]+TOL>=a[2]
# Longer annotation offset delays or coarsens death at fixed query coordinates.
for b,p in product(bs,policies):
    for n,t in product(roster[b],qs):
        a=masses[b,0,p,n,t];z=masses[b,1,p,n,t]
        assert z[0]+TOL>=a[0] and z[0]+z[2]+TOL>=a[0]+a[2]
def rational_ratio(b,o,p,h,t):
    man=[];opt=[];ex=0
    for n in roster[b]:
        a=masses[b,o,p,n,t];lo,hi=F(a[0]),F(a[0])+F(a[2]);s=statuses[b,o,p,h,n]
        if s==1: man.append((lo,hi))
        elif s is None and hi>0:opt.append((lo,hi))
        else:ex+=1
    n,m=len(man),len(opt);low=sorted(a[0] for a in opt);high=sorted((a[1] for a in opt),reverse=True)
    lower=[];upper=[]
    for k in range(m+1):
        if n+k:
            lower.append(((sum(x[0] for x in man)+sum(low[:k]))/(n+k),k));upper.append(((sum(x[1] for x in man)+sum(high[:k]))/(n+k),k))
    out={'mandatory_selected':n,'optional_selected':m,'excluded':ex,'maximum_selected':n+m,'zero_denominator_possible':n==0,'defined_for_some_completion':bool(n+m)}
    if lower:
        lo,lk=min(lower);hi,hk=max(upper);out.update(lower=float(lo),upper=float(hi),lower_optional_count=lk,upper_optional_count=hk)
    else:out.update(lower=None,upper=None,lower_optional_count=None,upper_optional_count=None)
    return out
ratios={};ratioerr=0.0
for r in res['ratio_envelopes']:
    k=tuple(r[x] for x in ['baseline_frame','death_frame_offset','ambiguity_policy','selection_hours','evaluation_hours']);assert k not in ratios;ratios[k]=r
    b,o,p,h,t=k; expected=rational_ratio(*k)
    for name,v in expected.items():
        if name in ['lower','upper'] and v is not None:ratioerr=max(ratioerr,abs(v-r[name]));assert abs(v-r[name])<=TOL
        else:assert r[name]==v
    assert r['recorded_baseline_cells']==len(roster[b]);assert abs(r['unknown_path_mass_sum']-sum(masses[b,o,p,n,t][2] for n in roster[b]))<=TOL
    if t==0 and r['defined_for_some_completion']:assert r['lower']==r['upper']==1
assert set(ratios)==set(product(bs,offsets,policies,hs,ts))
contrasts={};classes=Counter();exactclasses=Counter();bytime=defaultdict(Counter);contrasterr=0.0
for r in res['contrast_envelopes']:
    b,o,p,e,l,t=(r[x] for x in ['baseline_frame','death_frame_offset','ambiguity_policy','earlier_selection_hours','later_selection_hours','evaluation_hours']);k=(b,o,p,e,l,t);assert k not in contrasts;contrasts[k]=r
    a,z=ratios[b,o,p,e,t],ratios[b,o,p,l,t]
    if z['defined_for_some_completion']:
        cap=1-max(1,z['mandatory_selected'])/a['maximum_selected'];lo=max(z['lower']-a['upper'],-cap);hi=min(z['upper']-a['lower'],cap)
        assert r['defined_for_some_completion'];assert r['zero_denominator_possible']==z['zero_denominator_possible']
        for name,v in [('lower',lo),('upper',hi),('nesting_cap',cap)]:contrasterr=max(contrasterr,abs(v-r[name]));assert abs(v-r[name])<=TOL
        cl='strictly_positive' if r['lower']>TOL else 'strictly_negative' if r['upper']<-TOL else 'includes_zero';classes[cl]+=1;bytime[t][cl]+=1
        exactclasses['strictly_positive' if r['lower']>0 else 'strictly_negative' if r['upper']<0 else 'includes_zero']+=1
        if t==0:assert r['lower']==r['upper']==0
    else:assert not r['defined_for_some_completion'];classes['undefined']+=1;bytime[t]['undefined']+=1
assert set(contrasts)=={(b,o,p,e,l,t) for b,o,p,(e,l),t in product(bs,offsets,policies,pairs,ts)}
for b,o,h,t in product(bs,offsets,hs,ts):
    a,z=ratios[b,o,'first_issue',h,t],ratios[b,o,'whole_episode',h,t]
    if a['defined_for_some_completion']:assert z['defined_for_some_completion'] and z['lower']<=a['lower']+TOL and z['upper']+TOL>=a['upper']
for b,o,(e,l),t in product(bs,offsets,pairs,ts):
    a,z=contrasts[b,o,'first_issue',e,l,t],contrasts[b,o,'whole_episode',e,l,t]
    if a['defined_for_some_completion']:assert z['defined_for_some_completion'] and z['lower']<=a['lower']+TOL and z['upper']+TOL>=a['upper']
output={'tolerance':TOL,'source_graph_sha256':sha(graph_path),'results_sha256':sha(B/'results.json'),'private_records_sha256':sha(private_path),'protocol_sha256':sha(B/'protocol.json'),'core_sha256':res['core_sha256'],'caller_sha256':res['script_sha256'],'review_check_sha256':sha(__file__),'expected_and_observed_counts':{'baseline_sensitivity_combinations':len(bs)*len(offsets)*len(policies),'private_selection_groups':len(indexed),'unique_cell_time_mass_vectors':len(masses),'stored_cell_time_mass_vectors_including_horizon_repetition':total_saved_vectors,'ratio_cases':len(ratios),'contrast_cases':len(contrasts)},'max_absolute_errors':{'mass_conservation':residual,'independent_exact_fraction_frontier_vs_saved_mass':maxerr,'independent_rational_ratio_vs_saved_ratio':ratioerr,'independent_contrast_formula_vs_saved_contrast':contrasterr},'checks':{'all_hashes_and_freeze_order_match':True,'complete_unique_fixed_grid':True,'all_rosters_match_pinned_graph':True,'same_roster_all_horizons_and_sensitivities':True,'common_per_cell_mass_vectors_across_selection_horizons':True,'family_status_matches_selection_time_mass':True,'family_status_sets_nested_across_horizons':True,'mass_components_nonnegative_and_conserved':True,'survival_bounds_nonincreasing_in_elapsed_time':True,'dead_and_unknown_mass_nondecreasing':True,'whole_episode_mass_ratio_and_contrast_envelopes_contain_first_issue':True,'offset1_survival_bounds_no_lower_than_offset0':True,'time_zero_ratios_one_and_contrasts_zero':True,'independent_frontier_and_rational_recalculations_match':True,'joint_refinement_not_read_or_run':True},'contrast_classification_at_tolerance':dict(classes),'contrast_classification_exact_zero':dict(exactclasses),'contrast_classification_by_evaluation_hours':{str(k):dict(v) for k,v in sorted(bytime.items())},'zero_denominator_possible_ratio_cases':sum(r['zero_denominator_possible'] for r in ratios.values()),'undefined_ratio_cases':sum(not r['defined_for_some_completion'] for r in ratios.values()),'time_zero_point_zero_contrasts':sum(r['evaluation_hours']==0 and r['lower']==r['upper']==0 for r in contrasts.values()),'scope':'Finite recorded-roster primary envelopes only; no population null inference, effect-size fit, window selection, or joint-refinement output.'}
(ROOT/'tmp/hct116-lineage-structure/primary-empirical-review-checks.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
