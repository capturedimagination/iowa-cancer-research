"""Independent marginal-distribution and source checks for depth simulations.

Does not import the simulator. Binomial and hypergeometric marginal sums check
expected mean-log scores; they do not independently reproduce rank-AUC sampling.
"""
from pathlib import Path
import hashlib
import json
import math
from datetime import datetime, timezone

import h5py
import numpy as np
from scipy.stats import binom, hypergeom

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery"
SOURCE = BASE / "sources/egfr-resistance-2026-11-10"
OUT = BASE / "discovery-2026-11-10/depth-simulation"
PREVIOUS = BASE / "results/gse292469-alveolar-2026-11-10"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while b := f.read(8 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def binomial_expected_score(depth_values, probabilities):
    """Sum marginal PMFs, retaining all but <=1e-13 upper-tail mass per gene."""
    ns, reverse = np.unique(depth_values, return_inverse=True)
    expectations = np.zeros(len(ns))
    tail_bound = 0.0
    for p in probabilities:
        for lo in range(0, len(ns), 256):
            sizes = ns[lo:lo + 256]
            upper = binom.ppf(1 - 1e-13, sizes, p).astype(int)
            k = np.arange(int(upper.max()) + 1)
            mass = binom.pmf(k[None, :], sizes[:, None], p)
            logs = np.log1p(10000 * k[None, :] / sizes[:, None])
            expectations[lo:lo + len(sizes)] += (mass * logs).sum(axis=1) / len(probabilities)
            tail_bound += float(np.max(binom.sf(int(upper.max()), sizes, p))) * math.log1p(10000) / len(probabilities)
    # Sum over chunks above is deliberately a conservative bound for every cell.
    return expectations[reverse], tail_bound


def hypergeometric_expected_score(counts, totals, draw):
    """Exact finite-support marginal PMFs; captures mean, not joint variance."""
    answer = np.zeros(len(totals))
    largest_mass_error = 0.0
    for g in range(counts.shape[1]):
        active = np.flatnonzero(counts[:, g] > 0)
        pairs, inverse = np.unique(np.column_stack((totals[active], counts[active, g])), axis=0, return_inverse=True)
        order = np.argsort(pairs[:, 1], kind="stable")
        values = np.zeros(len(pairs))
        for lo in range(0, len(order), 256):
            ix = order[lo:lo + 256]
            N, K = pairs[ix].T
            k = np.arange(min(draw, int(K.max())) + 1)
            mass = hypergeom.pmf(k[None, :], N[:, None], K[:, None], draw)
            largest_mass_error = max(largest_mass_error, float(np.max(np.abs(mass.sum(axis=1) - 1))))
            values[ix] = (mass * np.log1p(10000 * k / draw)[None, :]).sum(axis=1)
        answer[active] += values[inverse] / counts.shape[1]
    return answer, largest_mass_error


def patient_average(values, codes, n):
    return np.array([math.fsum(map(float, values[codes == i])) / int(np.sum(codes == i)) for i in range(n)])


def contrast(values, patients, subset):
    a = [float(v) for v, p in zip(values, patients) if p["state"] == "MRD" and (subset == "pooled" or p["kit_series_implied"] == subset)]
    b = [float(v) for v, p in zip(values, patients) if p["state"] == "TN" and (subset == "pooled" or p["kit_series_implied"] == subset)]
    return {"mean_difference":math.fsum(a) / len(a) - math.fsum(b) / len(b),
            "auc":math.fsum(1 if x > y else .5 if x == y else 0 for x in a for y in b) / (len(a) * len(b))}


def main():
    patients = [p for p in json.loads((PREVIOUS / "sample-scores.json").read_text()) if p["primary_eligible"]]
    cache = SOURCE / "depth-target-counts.npz"
    metadata = json.loads(cache.with_suffix(".json").read_text())
    assert digest(cache) == metadata["sha256"]
    with np.load(cache, allow_pickle=False) as z:
        c, N, codes = z["counts"], z["depths"], z["codes"]
        cell_ids, genes, patient_ids = z["cell_ids"], z["genes"].tolist(), z["patient_ids"].tolist()
    assert patient_ids == [p["sample_id"] for p in patients]
    assert len(set(cell_ids)) == len(cell_ids)
    assert [int(np.sum(codes == i)) for i in range(len(patients))] == [p["malignant_nuclei"] for p in patients]
    assert (c >= 0).all() and (c.sum(axis=1) <= N).all()

    # Separate scalar arithmetic and direct HDF5 reads for source spot checks.
    selected = sorted(set(np.linspace(0, len(c) - 1, 100, dtype=int).tolist() +
                          [int(np.flatnonzero(codes == i)[0]) for i in range(len(patients))]))
    scalar_scores = []
    with h5py.File(SOURCE / "GSE292469_counts.h5", "r") as f:
        m = f["matrix"]
        names = [x.decode() if isinstance(x, bytes) else str(x) for x in m["features/name"][:]]
        barcodes = [x.decode() if isinstance(x, bytes) else str(x) for x in m["barcodes"][:]]
        bar_index = {x:i for i, x in enumerate(barcodes)}
        gene_positions = [names.index(g) for g in genes]
        for i in selected:
            j = bar_index[str(cell_ids[i])]
            start, end = map(int, m["indptr"][j:j + 2])
            nonzero = dict(zip(map(int, m["indices"][start:end]), map(int, m["data"][start:end])))
            assert sum(nonzero.values()) == int(N[i])
            assert [nonzero.get(g, 0) for g in gene_positions] == c[i].tolist()
            scalar_scores.append(math.fsum(math.log1p(10000 * int(x) / int(N[i])) for x in c[i]) / 17)
    raw = np.log1p((c.astype(float) / N[:, None]) * 10000).sum(axis=1) / 17
    assert np.allclose(raw[selected], scalar_scores, atol=1e-12, rtol=0)
    raw_patient = patient_average(raw, codes, len(patients))
    assert np.allclose(raw_patient, [p["score_mean"] for p in patients], atol=1e-12, rtol=0)
    fractions = c / N[:, None]
    patient_gene_fractions = np.stack([fractions[codes == i].mean(axis=0) for i in range(len(patients))])
    q = patient_gene_fractions.mean(axis=0)
    print("source and patient arithmetic passed", flush=True)

    expected_observed, tail_observed = binomial_expected_score(N, q)
    expected_fixed, tail_fixed = binomial_expected_score(np.full(len(N), 1000), q)
    expected_double, tail_double = binomial_expected_score(np.full(len(N), 1000), 2 * q)
    is_mrd = np.array([patients[int(i)]["state"] == "MRD" for i in codes])
    positive = np.where(is_mrd, expected_double, expected_fixed)
    print("binomial expectations calculated", flush=True)
    expected_thinned, mass_error = hypergeometric_expected_score(c, N, 1000)
    print("hypergeometric expectations calculated", flush=True)

    # Read only after the main workflow has reported completion.
    results_path = OUT / "results.json"
    results = json.loads(results_path.read_text())
    diagnostics = json.loads((OUT / "patient-diagnostics.json").read_text())
    assert results["input_cache_sha256"] == digest(cache)
    assert results["genes"] == genes and results["patient_ids"] == patient_ids
    assert np.allclose(q, list(results["common_profile_probabilities"].values()), atol=1e-14, rtol=0)
    observed = {}
    diagnostic_max_error = 0.0
    for i, row in enumerate(diagnostics):
        assert row["sample_id"] == patient_ids[i]
        mask = codes == i
        checks = {
            "mean_log_score":raw_patient[i],
            "signature_fraction_mean":math.fsum(map(float, fractions[mask].sum(axis=1))) / int(mask.sum()),
            "mean_genes_detected":math.fsum(map(float, (c[mask] > 0).sum(axis=1))) / int(mask.sum()),
            "median_UMIs":float(np.median(N[mask])),
        }
        for key, value in checks.items():
            error = abs(value - row[key]); diagnostic_max_error = max(diagnostic_max_error, error)
            assert error < 1e-11, (row["sample_id"], key, error)
        for g, gene in enumerate(genes):
            fraction = float(patient_gene_fractions[i, g])
            contribution = math.fsum(map(float, np.log1p(10000 * fractions[mask, g]))) / int(mask.sum()) / 17
            assert abs(fraction - row["per_gene_fraction"][gene]) < 1e-12
            assert abs(contribution - row["per_gene_log_contribution"][gene]) < 1e-12
    for metric in ("mean_log_score", "signature_fraction_mean", "mean_genes_detected", "median_UMIs"):
        v = np.array([r[metric] for r in diagnostics])
        observed[metric] = {s:contrast(v, patients, s) for s in ("pooled", "v3.1", "v4")}
        for s in observed[metric]:
            for k, value in observed[metric][s].items():
                assert abs(value - results["observed_metrics"][metric][s][k]) < 1e-11

    comparisons = {}
    for scenario, cells in [("observed_depth_null", expected_observed), ("fixed_depth_null", expected_fixed),
                            ("fixed_depth_twofold_MRD_control", positive), ("primary_thinning_1000", expected_thinned)]:
        values = patient_average(cells, codes, len(patients))
        comparisons[scenario] = {}
        reference = results["thinning"]["1000"]["replicate_summary"] if scenario == "primary_thinning_1000" else results["technical_simulations"][scenario]
        for s in ("pooled", "v3.1", "v4"):
            exact = contrast(values, patients, s)["mean_difference"]
            estimated = reference[s]["mean_difference"]
            error = estimated["mean"] - exact
            z = error / estimated["monte_carlo_se_of_mean"]
            comparisons[scenario][s] = {"marginal_expected_mean_difference":exact,
                "reported_monte_carlo_mean":estimated["mean"], "difference":error,
                "reported_monte_carlo_se_of_mean":estimated["monte_carlo_se_of_mean"], "difference_in_mc_se":z,
                "within_five_mc_se":abs(z) < 5}
            assert abs(z) < 5, (scenario, s, z)
    review = {
        "reviewed_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"Independent source, arithmetic and marginal-expectation checks passed",
        "checker_sha256":digest(__file__), "simulator_code_sha256_in_results":results["code_sha256"],
        "result_sha256":digest(results_path), "cache_sha256":digest(cache),
        "n_patients":len(patients), "n_nuclei":len(c), "h5_spot_checks":len(selected),
        "diagnostic_max_abs_error":diagnostic_max_error,
        "binomial_truncation_upper_bounds_per_score":{"observed":tail_observed, "fixed":tail_fixed, "double":tail_double},
        "hypergeometric_max_abs_pmf_mass_error":mass_error,
        "observed_patient_contrasts":observed, "marginal_expectation_checks":comparisons,
        "limits":["Does not import the simulator or replay its random stream.",
                  "Marginal expectations verify mean contrasts, not joint variance or rank-AUC sampling.",
                  "Same permitted source data; independent computation is not independent biological validation or external peer review.",
                  "Monte Carlo percentiles condition on data/model, with only 100 replicates; they are not patient confidence intervals.",
                  "Source-H5 checks cover selected nuclei; full source integrity is additionally asserted by the simulator's input hashes."]
    }
    (OUT / "independent-review.json").write_text(json.dumps(review, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status":review["status"], "spot_checks":len(selected), "max_abs_mc_se":max(abs(r["difference_in_mc_se"]) for v in comparisons.values() for r in v.values()), "hypergeometric_mass_error":mass_error}, indent=2), flush=True)


if __name__ == "__main__":
    main()
