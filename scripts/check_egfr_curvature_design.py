"""Review-only independent checks of the frozen synthetic curvature design.

No implementation functions are imported from the simulation under review.
The estimated-variance calculation is a separate sensitivity, not a change to
the frozen protocol. It assumes independent Gaussian log errors with a common
variance estimated from within-time replicate wells.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
from statistics import NormalDist

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.linalg import expm
from scipy.optimize import brentq, differential_evolution
from scipy.special import gammaln, ndtr
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "research/treatment-discovery/discovery-2026-11-10/mechanistic-simulation/v2"
G_S = math.log(2)
NORMAL = NormalDist()
Z = NORMAL.inv_cdf(.975)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gaussian_power(mean, sd, lower, upper):
    return NORMAL.cdf((lower-mean)/sd) + NORMAL.cdf((mean-upper)/sd)


def estimated_variance_power(delta, degrees_freedom, critical):
    """Integrate over U~chi-square(df), conditional on the Gaussian contrast.

    Reject |(Z+delta)/sqrt(U/df)| > critical. Mean contrasts and within-time
    residual variance are independent under the stated normal model.
    """
    df = degrees_freedom

    def integrand(u):
        if u == 0:
            return 0.0
        density = math.exp((df/2-1)*math.log(u)-u/2-(df/2)*math.log(2)-gammaln(df/2))
        edge = critical * math.sqrt(u/df)
        return (ndtr(-edge-delta)+ndtr(delta-edge))*density

    return quad(integrand, 0, math.inf, epsabs=1e-11, epsrel=1e-11)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "tmp/discovery-novelty/curvature-independent-checks.json")
    args = parser.parse_args()
    result_file = V2 / "results.json"
    result = json.loads(result_file.read_text())
    assert sha(V2 / "protocol.json") == result["protocol_sha256"]
    assert sha(ROOT / "scripts/simulate_egfr_curvature_design.py") == result["script_sha256"]

    # Independent scalar bisection using the standard-library Gaussian CDF.
    lower, upper = 0., 5.
    for _ in range(100):
        middle = (lower+upper)/2
        if gaussian_power(middle, 1, -Z, Z) < .8:
            lower = middle
        else:
            upper = middle
    delta80 = (lower+upper)/2
    threshold_error = max(abs(row["minimum_contrast_for_80_percent_power"]
        -delta80*math.sqrt(6*math.log1p(row["cv"]**2)/row["replicates_per_time"]))
        for row in result["minimum_detectable_contrast"])

    # Numerical quadrature of the hazard and integrating-factor solution,
    # independent of both the submitted closed form and ODE solver.
    trajectories = {}
    state_error = bulk_error = power_error = null_error = 0.
    for row in result["alternatives"]:
        key = tuple(row[k] for k in ("f0", "gP_over_gS", "b_inf", "tau", "T"))
        if key not in trajectories:
            f, g_ratio, b, tau, time = key
            g_p = g_ratio*G_S

            def hazard(u):
                return quad(lambda x:b*(1-math.exp(-x/tau)), 0, u,
                            epsabs=1e-13, epsrel=1e-13)[0]

            def log_p(u):
                return math.log(f)+g_p*u-hazard(u)

            def total(u):
                flux = quad(lambda x:b*(1-math.exp(-x/tau))*math.exp(log_p(x)-G_S*x),
                            0, u, epsabs=1e-12, epsrel=1e-12)[0]
                return math.exp(log_p(u))+math.exp(G_S*u)*(1-f+flux)

            state_c = 2*log_p(time)-log_p(0)-log_p(2*time)
            bulk_c = 2*math.log(total(time))-math.log(total(0))-math.log(total(2*time))
            trajectories[key] = state_c, bulk_c
        state_c, bulk_c = trajectories[key]
        state_error = max(state_error, abs(state_c-row["expected_state_contrast"]))
        bulk_error = max(bulk_error, abs(bulk_c-row["expected_bulk_contrast"]))
        sd = math.sqrt(6*math.log1p(row["cv"]**2)/row["replicates_per_time"])
        envelope = result["bulk_null_envelopes"][str(row["T"])]
        power_error = max(power_error,
            abs(gaussian_power(state_c, sd, -Z*sd, Z*sd)-row["absolute_state"]["analytic_rate"]),
            abs(gaussian_power(bulk_c, sd, envelope["min"]-Z*sd, envelope["max"]+Z*sd)-row["bulk"]["analytic_rate"]))

    # The constant-rate two-state solution is verified with a matrix exponential.
    for row in result["heldout_null"]:
        matrix = np.array([[G_S, row["b"]], [0., row["gP_over_gS"]*G_S-row["b"]]])
        initial = np.array([1-row["f0"], row["f0"]])
        time = row["T"]
        c = (2*math.log((expm(matrix*time)@initial).sum())
             -math.log(initial.sum())-math.log((expm(matrix*2*time)@initial).sum()))
        null_error = max(null_error, abs(c-row["bulk_expected_contrast"]))

    # Independent continuous-parameter numerical exploration, not a proof
    # of global extrema. The transformed positive-mixture formula is derived
    # separately from the simulator's source/target integral expression.
    envelopes = {}
    for time in [.5, 1, 2]:
        def bulk_objective(parameters):
            f, g_ratio, b = parameters
            difference = G_S*(1-g_ratio)
            gap = difference+b
            if gap == 0:
                return 0.
            weight = f*difference/gap
            return (2*math.log1p(weight*math.expm1(-gap*time))
                    -math.log1p(weight*math.expm1(-2*gap*time)))
        fit = differential_evolution(bulk_objective, [(.1,.9),(0,1),(0,1.6)],
                                     seed=9876, tol=1e-11, polish=True)
        key = str(int(time)) if int(time) == time else str(time)
        grid = result["bulk_null_envelopes"][key]
        envelopes[key] = {"optimized_min":float(fit.fun),
            "parameters_f_gP_ratio_b":fit.x.tolist(),"grid_min":grid["min"],
            "grid_minus_optimized_min":float(grid["min"]-fit.fun),
            "optimizer_success":bool(fit.success)}

    # Review-only power sensitivity: estimate common log variance from the
    # three groups of r independent wells, giving 3(r-1) residual degrees of freedom.
    unknown_variance = []
    for replicates in [3, 6, 12]:
        df = 3*(replicates-1)
        critical = student_t.ppf(.975, df)
        delta = brentq(lambda d:estimated_variance_power(d, df, critical)-.8, 0, 10)
        unknown_variance.append({"replicates_per_time":replicates, "residual_df":df,
            "critical_two_sided_t":float(critical),
            "minimum_contrast_80_percent_if_common_variance_estimated_within_times":
                float(delta*math.sqrt(6*math.log1p(.1**2)/replicates)),
            "verified_power":estimated_variance_power(delta, df, critical),
            "null_rate":estimated_variance_power(0, df, critical)})

    assert threshold_error < 1e-10 and state_error < 1e-9
    assert bulk_error < 1e-8 and power_error < 1e-8 and null_error < 1e-10
    assert all(abs(x["verified_power"]-.8)<1e-9 and abs(x["null_rate"]-.05)<1e-9 for x in unknown_variance)
    alternative_envelope_distances = []
    for key, (_, bulk_c) in trajectories.items():
        time = key[-1]
        bounds = result["bulk_null_envelopes"][str(time)]
        alternative_envelope_distances.append(min(bulk_c-bounds["min"], bounds["max"]-bulk_c))
    answer = {"reviewer_method":"Independent derivation and numerical checks; simulator functions not imported",
        "checker_sha256":sha(__file__),"reviewed_results_sha256":sha(result_file),
        "reviewed_protocol_sha256":result["protocol_sha256"],"reviewed_script_sha256":result["script_sha256"],
        "environment":{"numpy":np.__version__,"scipy":scipy.__version__},
        "standardized_delta80":delta80,"max_threshold_absolute_error":threshold_error,
        "quadrature_unique_alternative_cases":len(trajectories),"analytic_power_rows_checked":len(result["alternatives"]),
        "max_state_contrast_error":state_error,"max_bulk_contrast_error":bulk_error,
        "max_all_alternative_analytic_power_error":power_error,"max_null_matrix_exponential_error":null_error,
        "continuous_bulk_minima_numerical_check":envelopes,
        "independently_counted_80_percent_alternatives":{k:sum(v[k]["analytic_rate"]>=.8 for v in result["alternatives"])
            for k in ["absolute_state","bulk"]},
        "minimum_assumed_contrast_noise_sd":min(v["contrast_noise_sd"] for v in result["alternatives"]),
        "bulk_comparator_overlap":{
            "unique_alternative_window_cases":len(trajectories),
            "noiseless_contrasts_inside_envelope":sum(x>=0 for x in alternative_envelope_distances),
            "noiseless_contrasts_outside_envelope":sum(x<0 for x in alternative_envelope_distances),
            "minimum_signed_distance_to_envelope_boundary":min(alternative_envelope_distances),
            "maximum_bulk_analytic_power":max(v["bulk"]["analytic_rate"] for v in result["alternatives"])},
        "optional_unknown_variance_sensitivity_not_original_simulation":{
            "model":"Independent Gaussian log errors; common variance estimated from within-time independent wells. Pooled variance df=3(r-1); noncentral-t power computed by normal/chi-square quadrature.",
            "r1":"Variance cannot be estimated from within-time replicates when r=1.",
            "cv_for_comparison":.1,"results":unknown_variance},
        "all_computational_checks_passed":True}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(answer,indent=2,allow_nan=False)+"\n")
    print(json.dumps(answer,indent=2))


if __name__ == "__main__":
    main()
