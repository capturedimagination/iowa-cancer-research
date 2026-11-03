"""Reproduce a retrospective TMB/DCB association; no prediction model or treatment effect.

Requires bundled NumPy. Uses only the immutable local public cBioPortal snapshot.
The frozen specification is research/treatment-discovery/clinical-pilot-analysis-spec.md.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import platform
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"research/treatment-discovery"
RAW=BASE/"data/nsclc_pd1_msk_2018/2026-10-29"
OUT=BASE/"results/nsclc-tmb-dcb-2026-10-29"
SPEC=BASE/"clinical-pilot-analysis-spec.md"
SEED=20261029
B=10000

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path):
    return path.relative_to(ROOT).as_posix()

def read_table(path):
    # Preserve physical line references in these one-line-per-record clinical TSVs.
    lines=path.read_text().splitlines()
    indices=[i for i,line in enumerate(lines,1) if line and not line.startswith("#")]
    reader=csv.DictReader(io.StringIO("\n".join(lines[i-1] for i in indices)),delimiter="\t")
    return [(line,row) for line,row in zip(indices[1:],reader)]

def auc_pairwise(pos,neg):
    return float(np.mean((pos[:,None]>neg[None,:]).astype(float)+0.5*(pos[:,None]==neg[None,:])))

def auc_rank(pos,neg):
    # Independent cross-check using average ranks, not the pairwise implementation.
    all_values=np.concatenate((pos,neg))
    order=np.argsort(all_values,kind="stable")
    ranks=np.empty(len(all_values),dtype=float)
    start=0
    while start<len(order):
        end=start+1
        while end<len(order) and all_values[order[end]]==all_values[order[start]]: end+=1
        ranks[order[start:end]]=(start+1+end)/2
        start=end
    n=len(pos)
    return float((ranks[:n].sum()-n*(n+1)/2)/(n*len(neg)))

assert SPEC.exists()
manifest=json.loads((RAW/"download-manifest.json").read_text())
for item in manifest["files"]:
    assert sha(RAW/item["filename"])==item["sha256"],item["filename"]
patients=read_table(RAW/"data_clinical_patient.txt")
samples=read_table(RAW/"data_clinical_sample.txt")
historical=read_table(RAW/"data_clinical_sample-original-2018-04-23.txt")
assert len(patients)==len(samples)==len(historical)==240
assert len({r["PATIENT_ID"] for _,r in patients})==240
assert len({r["PATIENT_ID"] for _,r in samples})==240
assert len({r["SAMPLE_ID"] for _,r in samples})==240
assert {r["PATIENT_ID"] for _,r in patients}=={r["PATIENT_ID"] for _,r in samples}
historical_map={r["SAMPLE_ID"]:r for _,r in historical}
assert {r["SAMPLE_ID"] for _,r in samples}==set(historical_map)
assert all(float(r["MUTATION_RATE"])==float(historical_map[r["SAMPLE_ID"]]["MUTATION_RATE"]) for _,r in samples)
sample_map={r["PATIENT_ID"]:(line,r) for line,r in samples}
rows=[]
for patient_line,patient in patients:
    sample_line,sample=sample_map[patient["PATIENT_ID"]]
    status=patient["DURABLE_CLINICAL_BENEFIT"]
    assert status in ("YES","NO","NE")
    tmb=float(sample["MUTATION_RATE"])
    assert np.isfinite(tmb) and tmb>=0
    rows.append({"patient_id":patient["PATIENT_ID"],"sample_id":sample["SAMPLE_ID"],
        "dcb_source_value":status,"dcb_binary":1 if status=="YES" else 0 if status=="NO" else None,
        "included":status!="NE","exclusion_reason":"not evaluable for source DCB" if status=="NE" else "",
        "original_mutation_rate_per_mb":tmb,"gene_panel":sample["GENE_PANEL"],
        "treatment_class":patient["TREATMENT_TYPE"],"oncotree_code":sample["ONCOTREE_CODE"],
        "patient_source_file":rel(RAW/"data_clinical_patient.txt"),"patient_source_line":patient_line,
        "sample_source_file":rel(RAW/"data_clinical_sample.txt"),"sample_source_line":sample_line})
assert Counter(r["dcb_source_value"] for r in rows)=={"YES":69,"NO":158,"NE":13}
eligible=[r for r in rows if r["included"]]
pos=np.array([r["original_mutation_rate_per_mb"] for r in eligible if r["dcb_binary"]==1])
neg=np.array([r["original_mutation_rate_per_mb"] for r in eligible if r["dcb_binary"]==0])
point=auc_pairwise(pos,neg)
assert abs(point-auc_rank(pos,neg))<1e-12
assert auc_pairwise(np.array([2.,3.]),np.array([0.,1.]))==1
assert auc_pairwise(np.array([0.,1.]),np.array([2.,3.]))==0
assert auc_pairwise(np.array([1.,1.]),np.array([1.,1.]))==0.5
rng=np.random.default_rng(SEED)
bootstrap=np.array([auc_pairwise(rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)) for _ in range(B)])
interval=np.quantile(bootstrap,[0.025,0.975],method="linear")
def description(x):
    q=np.quantile(x,[0.25,0.5,0.75],method="linear")
    return {"n":len(x),"q25":float(q[0]),"median":float(q[1]),"q75":float(q[2]),"units":"original MUTATION_RATE, mutations/Mb"}
result={"analysis_id":"NSCLC-TMB-DCB-2026-10-29","analysis_type":"retrospective within-cohort association replication",
    "computed_at_utc":datetime.now(timezone.utc).isoformat(),"cohort":"nsclc_pd1_msk_2018",
    "repository_commit":manifest["commit"],"source_license":manifest["license"],
    "analysis_spec":rel(SPEC),"analysis_spec_sha256":sha(SPEC),
    "inputs":{item["filename"]:item["sha256"] for item in manifest["files"]},
    "cohort_flow":{"source_patients":240,"source_samples":240,"one_to_one_patient_sample":True,
        "included":len(eligible),"dcb_yes":len(pos),"dcb_no":len(neg),"excluded_ne":13,"missing_primary_biomarker":0},
    "dcb_yes_biomarker":description(pos),"dcb_no_biomarker":description(neg),
    "primary_auc":{"estimate":point,"conditional_95_percentile_bootstrap_interval":interval.tolist(),
        "positive_class":"recorded DCB YES","score":"original continuous MUTATION_RATE; higher ranks toward YES",
        "ties":"half credit","bootstrap_unit":"patient","resampling":"stratified by observed DCB; fixed class sizes",
        "bootstrap_replicates":B,"rng":"numpy.default_rng/PCG64","seed":SEED,"quantile_method":"linear"},
    "source_panel_counts_all":dict(Counter(r["gene_panel"] for r in rows)),
    "source_panel_counts_included":dict(Counter(r["gene_panel"] for r in eligible)),
    "source_treatment_counts_all":dict(Counter(r["treatment_class"] for r in rows)),
    "source_treatment_counts_included":dict(Counter(r["treatment_class"] for r in eligible)),
    "checks":{"source_hashes_match":True,"original_tmb_unchanged_since_2018":True,
        "rank_and_pairwise_auc_agree":True,"auc_direction_and_ties_checked":True,
        "no_pfs_or_outcome_derived_predictors":True,"no_model_or_cutoff_fitted":True},
    "runtime":{"python":platform.python_version(),"numpy":np.__version__},
    "interpretation_limits":["Known published association, not independent discovery or external validation.",
        "Paper reports 36/240 post-immunotherapy tumor specimens; public tables cannot identify them.",
        "Retrospective discrimination is not a deployable pretreatment predictor, causal treatment benefit, overall survival or cure.",
        "No randomized untreated/alternative-treatment comparison; treatment classes, panels and patient selection differ.",
        "Bootstrap uncertainty is conditional on this cohort and class sizes; excludes confounding, selection, timing and measurement error.",
        "No claim of normal-tissue safety, drug efficacy, Iowa generalizability or clinical utility.",
        "Source DCB labels retained. NE excluded explicitly; PD-L1 analysis omitted because source-subset discrepancy remains unresolved."]}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"results.json").write_text(json.dumps(result,indent=2))
# Preserve inclusion/exclusion and source references for all 240, without copying unused clinical fields.
with (OUT/"cohort-flow.jsonl").open("w") as f:
    for row in rows: f.write(json.dumps(row)+"\n")
# Arrays support an independent arithmetic check without expanding sensitive/public record content in chat.
np.save(OUT/"bootstrap_auc.npy",bootstrap,allow_pickle=False)
summary=f"""# NSCLC biomarker replication results

Analysis date: October 29, 2026. This is a retrospective association benchmark using the public MSK immunotherapy cohort, not a fitted treatment-selection model.

Among **227 DCB-evaluable patients**, the original continuous mutation-rate score had an empirical rank AUC of **{point:.3f}**, with a conditional 95% stratified-bootstrap interval of **{interval[0]:.3f} to {interval[1]:.3f}**. An AUC here describes how often the score ranks a recorded durable-benefit patient above a recorded no-benefit patient, with half credit for ties. It does not measure the probability that treatment cures someone.

| Source DCB group | Patients | Median mutations/Mb | Interquartile range |
|---|---:|---:|---:|
| YES | {len(pos)} | {np.median(pos):.2f} | {np.quantile(pos,.25):.2f} to {np.quantile(pos,.75):.2f} |
| NO | {len(neg)} | {np.median(neg):.2f} | {np.quantile(neg,.25):.2f} to {np.quantile(neg,.75):.2f} |

All 240 source patients and samples joined one-to-one. The 13 source NE outcomes were excluded explicitly and retained in `cohort-flow.jsonl`. No biomarker values were imputed, threshold selected, feature model trained or PFS-derived predictor used. The original `MUTATION_RATE` values match the 2018 archive for all 240 samples. The later `TMB_NONSYNONYMOUS` field was not substituted. Source data are ODbL 1.0; attribution and license remain in the adjacent source snapshot.

The statistic reproduces a known published association. The source paper reports 36 post-treatment specimens that cannot be isolated with the available clinical columns, so this cannot establish pretreatment performance. All participants received checkpoint blockade; there is no randomized treatment comparison. Patient selection, smoking, tumor biology, treatment line, assay panel and specimen timing can affect the association. The interval quantifies resampling uncertainty within this cohort, not those biases or external performance.

The next clinical benchmark requires a timing-resolved independent cohort with harmonized endpoint/panel definitions and patient-overlap checks. A resistance mechanism or drug combination additionally requires perturbation and experimental evidence.

Source: [Rizvi et al., JCO 2018](https://doi.org/10.1200/JCO.2017.75.3384); [pinned public cBioPortal study](https://github.com/cBioPortal/datahub/tree/{manifest['commit']}/public/nsclc_pd1_msk_2018). See the frozen protocol and clinical-data memo in the parent research folder for endpoint definitions and access details.
"""
(OUT/"RESULTS.md").write_text(summary)
(OUT/"run-provenance.json").write_text(json.dumps({"script":rel(Path(__file__)),"script_sha256":sha(Path(__file__)),
    "results_sha256":sha(OUT/"results.json"),"source_snapshot":rel(RAW),"protocol_sha256":sha(SPEC),
    "purpose":"Reproducible known-association benchmark; not new efficacy evidence"},indent=2))
print(json.dumps({"included":len(eligible),"dcb_yes":len(pos),"dcb_no":len(neg),"excluded_ne":13,
    "auc":point,"bootstrap_95":interval.tolist(),"dcb_yes_median":float(np.median(pos)),"dcb_no_median":float(np.median(neg))},indent=2))
