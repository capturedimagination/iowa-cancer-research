"""Falsify depth-only explanations for a fixed lung-cancer expression score.

Patient-level summaries, finite-pool hypergeometric thinning and explicit
technical-null simulations. These are not estimates of treatment efficacy.
"""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone

import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery"
DISC = BASE / "discovery-2026-11-10"
SOURCE = BASE / "sources/egfr-resistance-2026-11-10"
PREVIOUS = BASE / "results/gse292469-alveolar-2026-11-10"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def text(values):
    return np.array([x.decode() if isinstance(x, bytes) else str(x) for x in values])


def score(counts, depths):
    return np.log1p(10000*counts.astype(float)/depths[:,None]).mean(axis=1)


def sample_means(values, codes, n):
    den = np.bincount(codes, minlength=n)
    assert (den > 0).all()
    return np.bincount(codes, weights=values, minlength=n) / den


def contrast(values, patients, subset):
    take = np.array([subset == "pooled" or p["kit_series_implied"] == subset for p in patients])
    a = values[take & np.array([p["state"] == "MRD" for p in patients])]
    b = values[take & np.array([p["state"] == "TN" for p in patients])]
    assert len(a) >= 2 and len(b) >= 2
    rank = ((a[:,None] > b).sum() + .5*(a[:,None] == b).sum())/(len(a)*len(b))
    return {"n_MRD":len(a), "n_TN":len(b), "mean_difference":float(a.mean()-b.mean()), "auc":float(rank)}


def thin(counts, total, depth, rng):
    """Exact sequential multivariate hypergeometric: 17 genes plus remainder."""
    assert (total >= depth).all()
    remaining_total = total.astype(np.int64).copy()
    remaining_draw = np.full(len(total), depth, dtype=np.int64)
    out = np.empty_like(counts, dtype=np.int64)
    for g in range(counts.shape[1]):
        good = counts[:,g].astype(np.int64)
        sampled = rng.hypergeometric(good, remaining_total-good, remaining_draw)
        out[:,g] = sampled
        remaining_total -= good
        remaining_draw -= sampled
    assert (out >= 0).all() and (out <= counts).all()
    assert (remaining_draw >= 0).all() and np.array_equal(out.sum(axis=1)+remaining_draw, np.full(len(total), depth))
    return out


def multinomial_targets(total, probabilities, rng):
    """Simulate target categories jointly, leaving a non-signature remainder."""
    assert (probabilities >= 0).all() and (probabilities.sum(axis=1) < 1).all()
    left_n = total.astype(np.int64).copy()
    left_p = np.ones(len(total))
    out = np.empty(probabilities.shape, dtype=np.int64)
    for g in range(probabilities.shape[1]):
        conditional = np.clip(probabilities[:,g]/left_p, 0, 1)
        out[:,g] = rng.binomial(left_n, conditional)
        left_n -= out[:,g]
        left_p -= probabilities[:,g]
    assert (out.sum(axis=1) <= total).all()
    return out


def summarize_runs(rows, patients):
    answer = {}
    for subset in ("pooled", "v3.1", "v4"):
        c = [contrast(v, patients, subset) for v in rows]
        answer[subset] = {"n_MRD":c[0]["n_MRD"], "n_TN":c[0]["n_TN"]}
        for metric in ("mean_difference", "auc"):
            values = np.array([r[metric] for r in c])
            answer[subset][metric] = {"mean":float(values.mean()),
                "simulation_percentiles_2_5_50_97_5":np.quantile(values,[.025,.5,.975]).tolist(),
                "monte_carlo_se_of_mean":float(values.std(ddof=1)/np.sqrt(len(values)))}
    return answer


def extract(cache, genes, patients, previous):
    manifest = json.loads((BASE / "updates/2026-11-10/acquisition-manifest.json").read_text())
    for name in ("GSE292469_counts.h5", "GSE292469_cell_metadata.tsv.gz"):
        expected = next(x for x in manifest["files"] if x["filename"] == name)
        assert sha(SOURCE/name) == expected["sha256"], f"Source changed: {name}"
    if cache.exists():
        meta = json.loads(cache.with_suffix(".json").read_text())
        assert sha(cache) == meta["sha256"] and meta["genes"] == genes
        assert meta["patient_ids"] == [p["sample_id"] for p in patients]
        assert meta["source_sha256"] == previous["input_sha256"], "Cache source provenance changed"
        with np.load(cache,allow_pickle=False) as z:
            assert z["genes"].tolist() == genes and z["patient_ids"].tolist() == meta["patient_ids"]
            cached_counts=z["counts"];cached_depths=z["depths"];cached_codes=z["codes"];cached_ids=z["cell_ids"]
        assert cached_counts.shape == (len(cached_ids),len(genes)) and len(set(cached_ids)) == len(cached_ids)
        assert cached_counts.dtype.kind in "iu" and cached_depths.dtype.kind in "iu" and cached_codes.dtype.kind in "iu"
        assert (cached_counts >= 0).all() and (cached_counts.sum(axis=1) <= cached_depths).all()
        assert (cached_codes >= 0).all() and (cached_codes < len(patients)).all()
        source_meta=pd.read_csv(SOURCE/"GSE292469_cell_metadata.tsv.gz",sep="\t").set_index("cell_id")
        selected=source_meta.sample_id.isin(meta["patient_ids"]) & source_meta.is_tumor_cell.astype(str).str.lower().eq("true") & source_meta["scDblFinder.class"].eq("singlet")
        assert set(source_meta.index[selected]) == set(cached_ids), "Cached nucleus membership changed"
        aligned=source_meta.loc[cached_ids]
        assert np.array_equal(aligned.nCount_RNA.to_numpy(),cached_depths)
        assert np.array_equal(aligned.sample_id.to_numpy(),np.array(meta["patient_ids"])[cached_codes])
        means=sample_means(score(cached_counts,cached_depths),cached_codes,len(patients))
        assert np.allclose(means,[p["score_mean"] for p in patients],rtol=0,atol=1e-12), "Cached previous-score reproduction failed"
        return
    metadata = pd.read_csv(SOURCE/"GSE292469_cell_metadata.tsv.gz", sep="\t").set_index("cell_id")
    pids = [p["sample_id"] for p in patients]
    with h5py.File(SOURCE/"GSE292469_counts.h5", "r") as f:
        m = f["matrix"]
        barcodes = text(m["barcodes"][:])
        metadata = metadata.loc[barcodes]
        selected = (metadata.sample_id.isin(pids) & metadata.is_tumor_cell.astype(str).str.lower().eq("true")
                    & metadata["scDblFinder.class"].eq("singlet")).to_numpy()
        names = text(m["features/name"][:])
        positions = []
        for gene in genes:
            indices = np.where(names == gene)[0]
            assert len(indices) == 1
            positions.append(int(indices[0]))
        ptr = m["indptr"][:]
        pieces = []
        for lo in range(0, len(barcodes), 4096):
            hi = min(lo+4096, len(barcodes))
            keep = selected[lo:hi]
            if not keep.any(): continue
            start,end = int(ptr[lo]),int(ptr[hi])
            block = csc_matrix((m["data"][start:end],m["indices"][start:end],ptr[lo:hi+1]-start),shape=(len(names),hi-lo))
            pieces.append(block[positions,:][:,keep].toarray().T)
    counts = np.vstack(pieces)
    msel = metadata.iloc[np.flatnonzero(selected)]
    depths = msel.nCount_RNA.to_numpy(dtype=np.int64)
    codes = np.array([pids.index(x) for x in msel.sample_id],dtype=np.int16)
    assert (counts.sum(axis=1) <= depths).all() and (depths >= 1000).all()
    check = sample_means(score(counts, depths), codes, len(patients))
    assert np.allclose(check, [p["score_mean"] for p in patients], rtol=0, atol=1e-12)
    np.savez_compressed(cache, counts=counts,depths=depths,codes=codes,cell_ids=msel.index.to_numpy(dtype=str),genes=np.array(genes),patient_ids=np.array(pids))
    cache.with_suffix(".json").write_text(json.dumps({"sha256":sha(cache),"genes":genes,"patient_ids":pids,
        "nuclei":len(counts),"source_sha256":previous["input_sha256"],"exact_previous_scores_reproduced":True,
        "purpose":"Local target-count extraction for simulations; no raw cell data redistributed"},indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=DISC/"depth-simulation")
    args = parser.parse_args()
    assert np.__version__ == "2.3.5"
    plan = json.loads((DISC/"depth-simulation-plan.json").read_text())
    freeze = json.loads((DISC/"depth-plan-freeze.json").read_text())
    assert sha(DISC/"depth-simulation-plan.json") == freeze["sha256"]
    previous = json.loads((PREVIOUS/"results.json").read_text())
    patients = [p for p in json.loads((PREVIOUS/"sample-scores.json").read_text()) if p["primary_eligible"]]
    genes = previous["genes"]
    cache = SOURCE/"depth-target-counts.npz"
    extract(cache, genes, patients, previous)
    with np.load(cache,allow_pickle=False) as z:
        counts=z["counts"].astype(np.int64);depths=z["depths"];codes=z["codes"]
    n = len(patients)
    raw = score(counts,depths)
    fractions = counts/depths[:,None]
    logs = np.log1p(10000*fractions)
    per_gene_fractions = np.array([sample_means(fractions[:,g],codes,n) for g in range(len(genes))]).T
    pmean = sample_means(raw,codes,n)
    rows = []
    for i,p in enumerate(patients):
        keep=codes==i
        row={k:p[k] for k in ("sample_id","state","kit_series_implied","stage","tissue")}
        row.update(nuclei=int(keep.sum()),median_UMIs=float(np.median(depths[keep])),
                   mean_log_score=float(pmean[i]),signature_fraction_mean=float(fractions[keep].sum(axis=1).mean()),
                   mean_genes_detected=float((counts[keep]>0).sum(axis=1).mean()),
                   per_gene_fraction=dict(zip(genes,per_gene_fractions[i].tolist())),
                   per_gene_log_contribution=dict(zip(genes,(logs[keep].mean(axis=0)/17).tolist())))
        rows.append(row)
    summaries={}
    for metric in ("mean_log_score","signature_fraction_mean","mean_genes_detected","median_UMIs"):
        values=np.array([r[metric] for r in rows])
        summaries[metric]={subset:contrast(values,patients,subset) for subset in ("pooled","v3.1","v4")}
    rng=np.random.default_rng(plan["seed"])
    thinning={}
    for depth in [plan["primary_depth"]]+plan["sensitivity_depths"]:
        keep=depths>=depth
        c=counts[keep];d=depths[keep];cc=codes[keep]
        assert (np.bincount(cc,minlength=n)>=20).all()
        baseline=sample_means(score(c,d),cc,n)
        trials=[]
        for rep in range(plan["replicates"]):
            y=thin(c,d,depth,rng)
            trials.append(sample_means(score(y,np.full(len(y),depth)),cc,n))
        thinning[str(depth)]={"nuclei_retained":len(c),"patients_retained":n,
            "nuclei_per_patient":np.bincount(cc,minlength=n).tolist(),
            "unthinned_retained_cell_baseline":{s:contrast(baseline,patients,s) for s in ("pooled","v3.1","v4")},
            "replicate_summary":summarize_runs(trials,patients),
            "patient_mean_scores":np.mean(trials,axis=0).tolist()}
        print("thinning finished",depth,flush=True)
    q=per_gene_fractions.mean(axis=0)
    assert q.sum()<1
    simulations={}
    for scenario in ("observed_depth_null","fixed_depth_null","fixed_depth_twofold_MRD_control"):
        totals=depths if scenario=="observed_depth_null" else np.full(len(depths),1000)
        probability=np.broadcast_to(q,(len(depths),len(q))).copy()
        if scenario=="fixed_depth_twofold_MRD_control":
            mrd=np.array([patients[c]["state"]=="MRD" for c in codes])
            assert 2*q.sum()<1, "Twofold target proportions exceed the multinomial simplex"
            probability[mrd]=2*q
        trials=[]
        for rep in range(plan["replicates"]):
            y=multinomial_targets(totals,probability,rng)
            trials.append(sample_means(score(y,totals),codes,n))
        simulations[scenario]=summarize_runs(trials,patients)
        print("simulation finished",scenario,flush=True)
    args.out.mkdir(parents=True,exist_ok=True)
    results={"created_utc":datetime.now(timezone.utc).isoformat(),"plan_sha256":freeze["sha256"],
             "code_sha256":sha(Path(__file__)),"input_cache_sha256":sha(cache),"source_sha256":previous["input_sha256"],
             "numpy":np.__version__,"seed":plan["seed"],"replicates":plan["replicates"],"genes":genes,
             "patient_ids":[p["sample_id"] for p in patients],"observed_metrics":summaries,
             "thinning":thinning,"common_profile_probabilities":dict(zip(genes,q.tolist())),"technical_simulations":simulations,
             "interval_meaning":"Monte Carlo variation conditional on observed cells or specified technical model; not patient-level biological uncertainty or treatment-effect confidence intervals.",
             "limits":["Exploratory and dataset-specific; generic normalization/thinning bias is established prior art.",
                       "Chemistry assignment conflicts in source records; stage/site/composition remain confounded.",
                       "Finite-pool thinning cannot recover unseen transcripts or correct ambient RNA.",
                       "Technical-null model assumes homogeneous transcript proportions; rejected null does not establish a biological mechanism."]}
    (args.out/"results.json").write_text(json.dumps(results,indent=2,allow_nan=False)+"\n")
    (args.out/"patient-diagnostics.json").write_text(json.dumps(rows,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"observed":summaries["mean_log_score"],"thinned1000":thinning["1000"]["replicate_summary"],"null":simulations["observed_depth_null"]},indent=2),flush=True)


if __name__=="__main__":main()
