"""Patient-level joint-expression diagnostic for a fixed lung-cancer signature.

Independent within-patient/depth-bin gene permutations preserve all marginal
measurements. They test joint structure, not a causal mechanism or mean shift.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/treatment-discovery/discovery-2026-11-10/coexpression"
PLAN_SHA = "c3ebe1106843832006e0757cd734da9a6e4a823df2f68efab485dfdeeb09e1b9"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metrics(values):
    scores = values.mean(axis=1)
    breadth = (values > 0).sum(axis=1)
    return np.array([scores.var(ddof=0), (breadth >= 5).mean()])


def permute_columns(values, bins, rng):
    result = np.empty_like(values)
    for indices in bins:
        for gene in range(values.shape[1]):
            result[indices, gene] = values[rng.permutation(indices), gene]
    return result


def analytical_null(values, bins):
    """Exact expected endpoints under independent within-bin permutations."""
    k = values.shape[1]
    total = len(values)
    overall_mean = values.mean()
    expected_variance = 0.0
    expected_breadth = 0.0
    for indices in bins:
        block = values[indices]
        weight = len(indices) / total
        expected_variance += weight * (
            block.var(axis=0, ddof=0).sum() / k**2
            + (block.mean() - overall_mean)**2
        )
        probabilities = (block > 0).mean(axis=0)
        pmf = np.zeros(k + 1)
        pmf[0] = 1.0
        for probability in probabilities:
            pmf = pmf * (1 - probability) + np.r_[0, pmf[:-1]] * probability
        assert np.isclose(pmf.sum(), 1, rtol=0, atol=1e-12)
        expected_breadth += weight * pmf[5:].sum()
    return np.array([expected_variance, expected_breadth])


def self_check():
    fixture = np.zeros((200, 17))
    fixture[:100, :5] = 1
    bins = [np.arange(200)]
    known_observed = np.array([25 / (4 * 17**2), 0.5])
    known_null = np.array([5 / (4 * 17**2), 0.5**5])
    assert np.allclose(metrics(fixture), known_observed, rtol=0, atol=1e-14)
    assert np.allclose(analytical_null(fixture, bins), known_null, rtol=0, atol=1e-14)
    shuffled = permute_columns(fixture, bins, np.random.default_rng(81))
    assert np.array_equal(np.sort(fixture, axis=0), np.sort(shuffled, axis=0))
    assert fixture.mean() == shuffled.mean()
    assert (fixture > 0).sum() == (shuffled > 0).sum()
    zero = np.zeros((20, 17))
    assert np.array_equal(analytical_null(zero, [np.arange(20)]), [0, 0])
    assert np.array_equal(metrics(zero), [0, 0])
    return {"passed": True, "perfect_coexpression_observed": known_observed.tolist(),
            "independence_null_expectations": known_null.tolist(),
            "zero_fixture_passed": True, "marginal_invariance_fixture_passed": True}


def summarize(values, draws, rng):
    boot = values[rng.integers(0, len(values), size=(draws, len(values)))].mean(axis=1)
    return {"n_patients": len(values), "mean": float(values.mean()),
            "median": float(np.median(values)),
            "patient_bootstrap_95_percentile_interval": np.quantile(boot, [.025, .975]).tolist()}


def group_summaries(patient_rows, observed, null_mean):
    result = {}
    for kit in ("pooled", "v3.1", "v4"):
        members = np.array([kit == "pooled" or p["kit_series_implied"] == kit for p in patient_rows])
        states = np.array([p["state"] for p in patient_rows])
        result[kit] = {}
        for metric_i, metric in enumerate(("score_variance", "fraction_detecting_at_least5")):
            record = {}
            for state in ("TN", "MRD"):
                selected = members & (states == state)
                record[state] = {"n_patients": int(selected.sum()),
                    "observed_mean": float(observed[selected, metric_i].mean()),
                    "null_mean": float(null_mean[selected, metric_i].mean()),
                    "excess_mean": float((observed-null_mean)[selected, metric_i].mean())}
            record["MRD_minus_TN_excess_mean"] = record["MRD"]["excess_mean"]-record["TN"]["excess_mean"]
            result[kit][metric] = record
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--self-check-only", action="store_true")
    args = parser.parse_args()
    checks = self_check()
    if args.self_check_only:
        print(json.dumps(checks, indent=2))
        return
    protocol_file = OUT / "protocol.json"
    assert sha(protocol_file) == PLAN_SHA, "Frozen protocol changed"
    protocol = json.loads(protocol_file.read_text())
    assert np.__version__ == "2.3.5", "Use the pinned environment"
    files = {k: ROOT / v for k, v in protocol["input_files"].items()}
    for key, path in files.items():
        assert sha(path) == protocol["input_sha256"][key], f"Input changed: {key}"
    sidecar = json.loads(files["sidecar"].read_text())
    assert sidecar["sha256"] == sha(files["cache"])
    patients = [p for p in json.loads(files["labels"].read_text()) if p["primary_eligible"]]
    patient_ids = [p["sample_id"] for p in patients]
    with np.load(files["cache"], allow_pickle=False) as archive:
        counts = archive["counts"]
        depths = archive["depths"]
        codes = archive["codes"]
        genes = archive["genes"].tolist()
        assert archive["patient_ids"].tolist() == patient_ids == sidecar["patient_ids"]
        assert len(np.unique(archive["cell_ids"])) == len(counts)
    assert counts.shape == (121083, 17) and len(patients) == 35
    assert genes == sidecar["genes"]
    assert np.issubdtype(counts.dtype, np.integer) and (counts >= 0).all()
    assert np.issubdtype(depths.dtype, np.integer) and (depths >= 1000).all()
    assert (counts.sum(axis=1) <= depths).all()
    assert np.array_equal(np.unique(codes), np.arange(len(patients)))
    assert np.bincount(codes).tolist() == [p["malignant_nuclei"] for p in patients]
    logs = np.log1p(10000 * counts.astype(np.float64) / depths[:, None])
    repeats = protocol["permutation"]["replicates"]
    rng = np.random.default_rng(protocol["permutation"]["seed"])
    tie_rng = np.random.default_rng(protocol["bins"]["tie_seed"])
    observed = np.empty((35, 2))
    simulated = np.empty((35, repeats, 2))
    exact = np.empty((35, 2))
    patient_records = []
    max_mean_error = 0.0
    max_breadth_error = 0.0
    max_gene_sum_error = 0.0
    for patient_i, patient in enumerate(patients):
        selected = codes == patient_i
        values = logs[selected]
        patient_depths = depths[selected]
        order = np.lexsort((tie_rng.random(len(values)), patient_depths))
        bins = np.array_split(order, protocol["bins"]["number"])
        assert all(len(b) >= 2 for b in bins)
        baseline_mean = values.mean(axis=1).mean()
        baseline_breadth = (values > 0).sum(axis=1).mean()
        gene_sums = values.sum(axis=0)
        assert abs(baseline_mean-patient["score_mean"]) < 1e-12
        observed[patient_i] = metrics(values)
        exact[patient_i] = analytical_null(values, bins)
        for repeat in range(repeats):
            permuted = permute_columns(values, bins, rng)
            permuted_sums = permuted.sum(axis=0)
            assert np.allclose(gene_sums, permuted_sums, rtol=1e-11, atol=1e-10)
            mean_error = abs(permuted.mean(axis=1).mean() - baseline_mean)
            breadth_error = abs((permuted > 0).sum(axis=1).mean()-baseline_breadth)
            assert mean_error < 1e-12 and breadth_error < 1e-12
            max_mean_error = max(max_mean_error, mean_error)
            max_breadth_error = max(max_breadth_error, breadth_error)
            max_gene_sum_error = max(max_gene_sum_error, float(np.max(np.abs(permuted_sums-gene_sums))))
            simulated[patient_i, repeat] = metrics(permuted)
        row = {k:patient[k] for k in ("sample_id", "state", "kit_series_implied", "stage", "tissue")}
        row.update(nuclei=len(values), mean_score=float(baseline_mean),
            mean_detected_genes=float(baseline_breadth),
            depth_bins=[{"nuclei":len(b), "depth_min":int(patient_depths[b].min()),
                         "depth_max":int(patient_depths[b].max())} for b in bins])
        for metric_i, name in enumerate(("score_variance", "fraction_detecting_at_least5")):
            null = simulated[patient_i, :, metric_i]
            null_mean = null.mean()
            mcse = null.std(ddof=1) / np.sqrt(repeats)
            row[name] = {"observed":float(observed[patient_i, metric_i]),
                "null_mean":float(null_mean), "null_sd":float(null.std(ddof=1)),
                "null_mcse":float(mcse), "null_percentiles_2_5_50_97_5":np.quantile(null, [.025,.5,.975]).tolist(),
                "observed_minus_null_mean":float(observed[patient_i, metric_i]-null_mean),
                "exact_expected_null":float(exact[patient_i, metric_i]),
                "mc_mean_minus_exact":float(null_mean-exact[patient_i, metric_i]),
                "mc_deviation_standard_errors":float((null_mean-exact[patient_i, metric_i])/mcse) if mcse > 0 else None,
                "null_replicates":null.tolist()}
            if metric_i == 0:
                row[name]["observed_null_ratio"] = float(observed[patient_i,metric_i]/null_mean) if null_mean > 0 else None
        patient_records.append(row)
        print("finished", patient["sample_id"], flush=True)
    null_mean = simulated.mean(axis=1)
    excess = observed - null_mean
    bootstrap_rng = np.random.default_rng(protocol["inference"]["bootstrap_seed"])
    primary = {}
    for metric_i, name in enumerate(("score_variance", "fraction_detecting_at_least5")):
        primary[name] = summarize(excess[:,metric_i], 10000, bootstrap_rng)
        primary[name].update(observed_patient_mean=float(observed[:,metric_i].mean()),
            null_patient_mean=float(null_mean[:,metric_i].mean()),
            exact_expected_null_patient_mean=float(exact[:,metric_i].mean()),
            patients_positive_excess=int((excess[:,metric_i] > 0).sum()),
            patients_negative_excess=int((excess[:,metric_i] < 0).sum()),
            patients_zero_excess=int((excess[:,metric_i] == 0).sum()))
    checks.update(cache_hash_and_IDs_verified=True,previous_patient_means_reproduced=True,
        max_additive_mean_error=float(max_mean_error),max_mean_breadth_error=float(max_breadth_error),
        max_per_gene_sum_absolute_error=float(max_gene_sum_error),
        protocol_unchanged_after_run=sha(protocol_file)==PLAN_SHA)
    result = {"created_utc":datetime.now(timezone.utc).isoformat(),"protocol_sha256":PLAN_SHA,
        "code_sha256":sha(Path(__file__)), "input_sha256":protocol["input_sha256"],
        "numpy":np.__version__,"genes":genes,"n_patients":35,"n_nuclei":len(logs),
        "replicates":repeats,"seeds":{"permutation":protocol["permutation"]["seed"],
            "ties":protocol["bins"]["tie_seed"],"bootstrap":protocol["inference"]["bootstrap_seed"]},
        "validation":checks,"primary_patient_excess_summaries":primary,
        "descriptive_state_and_kit_summaries":group_summaries(patients,observed,null_mean),
        "patients":patient_records,"intervals":protocol["inference"]["uncertainty"],
        "interpretation_limits":protocol["interpretation_rules"],
        "null_boundary":protocol["permutation"]["boundary"]}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"results.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"primary":primary,"validation":checks},indent=2),flush=True)


if __name__ == "__main__":
    main()
