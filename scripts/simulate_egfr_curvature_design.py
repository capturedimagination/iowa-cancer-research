"""Version 2 synthetic abundance-curvature design; no clinical parameters.

The protocol is frozen and hash checked. Analytic power is validated against
independent simulations. Positive curvature is NOT specific evidence of memory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research/treatment-discovery/discovery-2026-11-10/mechanistic-simulation/v2"
PROTOCOL_SHA256 = "0a643d27634f4e336a4355d8d685c531089bb2359d8bc5627d8a2ae19949ced0"
G_S = np.log(2.)
WEIGHTS = np.array([-1., 2., -1.])
Z = norm.ppf(.975)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contrast(values):
    return np.log(values) @ WEIGHTS


def constant_total(b, gp, f0, times):
    """Analytic no-re-entry solution, vectorized over parameter cases."""
    b, gp, f0 = np.broadcast_arrays(b, gp, f0)
    b, gp, f0 = b[..., None], gp[..., None], f0[..., None]
    t = np.asarray(times)
    gap = G_S-gp+b
    integral = np.empty(np.broadcast_shapes(gap.shape, t.shape))
    np.divide(-np.expm1(-gap*t), gap, out=integral, where=np.abs(gap)>1e-12)
    integral = np.where(np.abs(gap)<=1e-12, t, integral)
    p = f0*np.exp((gp-b)*t)
    s = np.exp(G_S*t)*((1-f0)+b*f0*integral)
    return s+p


def memory_trajectory(b, tau, gp, f0, times, rtol=1e-11, atol=1e-13):
    def rhs(t, y):
        exit_rate = b*(-np.expm1(-t/tau))
        return [G_S*y[0]+exit_rate*y[1], (gp-exit_rate)*y[1]]
    sol = solve_ivp(rhs, (0., float(max(times))), [1-f0, f0], t_eval=times,
                    rtol=rtol, atol=atol, method="DOP853")
    assert sol.success and np.all(sol.y>0)
    return sol.y.sum(axis=0), sol.y[1]


def log_p_formula(b, tau, gp, f0, times):
    t = np.asarray(times)
    return np.log(f0)+(gp-b)*t+b*tau*(-np.expm1(-t/tau))


def expected_p_contrast(b, tau, T):
    return b*tau*(-np.expm1(-T/tau))**2


def power(mean, sd, lo, hi):
    return float(norm.cdf((lo-mean)/sd)+norm.sf((hi-mean)/sd))


def summarize(reject, analytic=None):
    rate = float(np.mean(reject))
    row = {"rate": rate, "simulated_experiments": len(reject),
           "monte_carlo_se": float(np.sqrt(rate*(1-rate)/len(reject)))}
    if analytic is not None:
        row["analytic_rate"] = analytic
        row["absolute_monte_carlo_error"] = abs(rate-analytic)
    return row


def contrast_noise(rng, sigma, r, experiments):
    # Each column is the mean of r independent Gaussian log errors. This is
    # distributionally identical to generating every replicate measurement.
    # Equal mean-log bias cancels because the weights sum to zero.
    return (sigma/np.sqrt(r)) * (rng.normal(size=(experiments, 3)) @ WEIGHTS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT)
    args = parser.parse_args()
    start = time.monotonic()
    protocol_path = DEFAULT / "protocol.json"
    assert sha(protocol_path) == PROTOCOL_SHA256, "Frozen protocol has changed"
    protocol = json.loads(protocol_path.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    param_names = ["f0", "gP_over_gS", "b_inf", "tau"]
    cases = [dict(zip(param_names, v)) for v in itertools.product(
        *(protocol["alternative_parameters"][k] for k in param_names))]
    settings = list(itertools.product(protocol["T"], protocol["measurement_cv"],
                                       protocol["replicates_per_time"]))
    # Deterministic calibration contains no held-out alternative information.
    f_grid, g_grid, b_grid = np.meshgrid(np.linspace(.1, .9, 17),
        np.linspace(0., 1., 21), np.linspace(0., 1.6, 161), indexing="ij")
    envelopes = {}
    for T in protocol["T"]:
        c = contrast(constant_total(b_grid.ravel(), G_S*g_grid.ravel(),
                                     f_grid.ravel(), [0., T, 2*T]))
        envelopes[T] = {"min": float(c.min()), "max": float(c.max()),
                        "grid_cases": int(c.size)}

    # Independent mathematical/numerical checks, plus precomputed trajectories.
    trajectory, errors, stability_errors, equivalence_errors = {}, [], [], []
    for i, case in enumerate(cases):
        f0, gp, b, tau = case["f0"], G_S*case["gP_over_gS"], case["b_inf"], case["tau"]
        for T in protocol["T"]:
            t = np.array([0., T, 2*T])
            n, p = memory_trajectory(b, tau, gp, f0, t)
            lp = log_p_formula(b, tau, gp, f0, t)
            cp = expected_p_contrast(b, tau, T)
            errors.append(max(np.max(np.abs(np.log(p)-lp)), abs(contrast(p)-cp)))
            n2, p2 = memory_trajectory(b, tau, gp, f0, t, 1e-13, 1e-15)
            stability_errors.append(max(abs(contrast(p)-contrast(p2)), abs(contrast(n)-contrast(n2))))
            # Alternative 1: independent scalar ODE, with time-varying growth
            # and NO switching. This reproduces P but not necessarily S or N.
            growth = solve_ivp(lambda x,y:(gp-b*(-np.expm1(-x/tau)))*y,
                (0., 2*T), [f0], t_eval=t, method="DOP853", rtol=1e-12, atol=1e-14)
            # Alternative 2: biological P grows constantly but marker retention
            # falls over time. Only observed labeled abundance equals model P.
            marker = np.exp(-b*(t-tau*(-np.expm1(-t/tau))))
            labeled = f0*np.exp(gp*t)*marker
            equivalence_errors.append(max(np.max(np.abs(np.log(growth.y[0])-lp)),
                                          np.max(np.abs(np.log(labeled)-lp))))
            trajectory[i,T] = (cp, float(contrast(n)))
    assert max(errors)<1e-7 and max(stability_errors)<1e-7 and max(equivalence_errors)<1e-7
    constant_errors=[]
    for f0,gp,b in itertools.product([.1,.9],[0.,G_S],[0.,1.6]):
        t=np.array([0.,1.,2.])
        sol=solve_ivp(lambda x,y:[G_S*y[0]+b*y[1],(gp-b)*y[1]],(0.,2.),[1-f0,f0],
                      t_eval=t,method="DOP853",rtol=1e-12,atol=1e-14)
        constant_errors.append(float(np.max(np.abs(sol.y.sum(axis=0)-constant_total(b,gp,f0,t)))))
        assert abs(contrast(f0*np.exp((gp-b)*t)))<1e-12
    assert max(constant_errors)<1e-8

    null_rng=np.random.default_rng(protocol["seeds"]["heldout_null"])
    null_params=null_rng.uniform([.1,0.,0.],[.9,1.,1.6], size=(64,3))
    null_results=[]
    null_outside=0
    for ni,(f0,g_ratio,b) in enumerate(null_params):
        for T,cv,r in settings:
            sigma=np.sqrt(np.log1p(cv**2)); sd=np.sqrt(6.)*sigma/np.sqrt(r)
            envelope=envelopes[T]
            cn=float(contrast(constant_total(b,g_ratio*G_S,f0,[0.,T,2*T])))
            if cn<envelope["min"]-1e-12 or cn>envelope["max"]+1e-12: null_outside+=1
            noise=contrast_noise(null_rng,sigma,r,5000)
            lo,hi=envelope["min"]-Z*sd,envelope["max"]+Z*sd
            null_results.append({"null_case":ni,"f0":float(f0),"gP_over_gS":float(g_ratio),
                "b":float(b),"T":T,"cv":cv,"replicates_per_time":r,"bulk_expected_contrast":cn,
                "absolute_state":summarize(np.abs(noise)>Z*sd,.05),
                "bulk":summarize((cn+noise<lo)|(cn+noise>hi),power(cn,sd,lo,hi))})

    alt_rng=np.random.default_rng(protocol["seeds"]["alternative"])
    alternatives=[]
    for i,case in enumerate(cases):
        for T,cv,r in settings:
            cp,cn=trajectory[i,T]
            sigma=np.sqrt(np.log1p(cv**2)); sd=np.sqrt(6.)*sigma/np.sqrt(r)
            noise=contrast_noise(alt_rng,sigma,r,5000)
            lo,hi=envelopes[T]["min"]-Z*sd,envelopes[T]["max"]+Z*sd
            state=summarize(np.abs(cp+noise)>Z*sd,power(cp,sd,-Z*sd,Z*sd))
            bulk=summarize((cn+noise<lo)|(cn+noise>hi),power(cn,sd,lo,hi))
            alternatives.append({**case,"T":T,"cv":cv,"replicates_per_time":r,
                "expected_state_contrast":cp,"expected_bulk_contrast":cn,"contrast_noise_sd":float(sd),
                "absolute_state":state,"bulk":bulk,
                "time_varying_growth_and_marker_drift_analytic_power":state["analytic_rate"]})

    delta80=brentq(lambda d:power(d,1.,-Z,Z)-.8,0.,10.)
    xmax=brentq(lambda x:np.expm1(x)-2*x,.01,4.)
    mda=[]
    for cv,r in itertools.product(protocol["measurement_cv"],protocol["replicates_per_time"]):
        sd=np.sqrt(6.*np.log1p(cv**2)/r)
        mda.append({"cv":cv,"replicates_per_time":r,"minimum_contrast_for_80_percent_power":float(delta80*sd)})

    stress_rng=np.random.default_rng(protocol["seeds"]["heteroscedastic_stress"])
    sigmas=np.sqrt(np.log1p(np.array([.1,.1,.2])**2))
    bias=float((-.5*sigmas**2)@WEIGHTS)
    stress=[]
    for r in protocol["replicates_per_time"]:
        noise=((stress_rng.normal(size=(100000,3))*sigmas/np.sqrt(r))@WEIGHTS)+bias
        naive_sd=np.sqrt(6.)*sigmas[0]/np.sqrt(r)
        correct_sd=np.sqrt(np.sum((WEIGHTS*sigmas)**2)/r)
        stress.append({"replicates_per_time":r,"expected_uncorrected_contrast_bias":bias,
            "naive_known_cv_0_1":summarize(np.abs(noise)>Z*naive_sd,power(bias,correct_sd,-Z*naive_sd,Z*naive_sd)),
            "known_variance_and_bias_corrected":summarize(np.abs(noise-bias)>Z*correct_sd,.05)})

    def aggregate(rows,field):
        rates=np.array([row[field]["rate"] for row in rows])
        analytic=np.array([row[field]["analytic_rate"] for row in rows])
        return {"cases":len(rows),"min_simulated":float(rates.min()),"median_simulated":float(np.median(rates)),
            "max_simulated":float(rates.max()),"max_absolute_monte_carlo_error":float(np.max(np.abs(rates-analytic))),
            "analytic_at_least_80_percent_cases":int(np.sum(analytic>=.8))}
    summaries=[]
    for T,cv,r in settings:
        rows=[a for a in alternatives if (a["T"],a["cv"],a["replicates_per_time"])==(T,cv,r)]
        summaries.append({"T":T,"cv":cv,"replicates_per_time":r,
            "absolute_state":aggregate(rows,"absolute_state"),"bulk":aggregate(rows,"bulk")})
    results={"version":2,"created_utc":datetime.now(timezone.utc).isoformat(),
        "protocol_sha256":sha(protocol_path),"script_sha256":sha(__file__),
        "environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
        "scope":"Synthetic only; rejecting constant net state growth does not identify memory.",
        "controls":{"alternative_trajectory_cases":len(errors),"max_log_p_or_contrast_formula_error":float(max(errors)),
            "max_solver_tolerance_contrast_change":float(max(stability_errors)),
            "max_specificity_counterexample_log_trajectory_error":float(max(equivalence_errors)),
            "max_constant_total_ode_error":max(constant_errors),"off_grid_null_envelope_violations":null_outside},
        "analytic":{"two_sided_z":float(Z),"standardized_contrast_for_80_percent_power":float(delta80),
            "tau_over_T_maximizing_signal":float(1/xmax),
            "maximum_C_over_b_inf_T":float((-np.expm1(-xmax))**2/xmax)},
        "minimum_detectable_contrast":mda,"bulk_null_envelopes":envelopes,
        "heldout_null_summary":{d:aggregate(null_results,d) for d in ["absolute_state","bulk"]},
        "all_alternative_summary":{d:aggregate(alternatives,d) for d in ["absolute_state","bulk"]},
        "summary_by_setting":summaries,"heteroscedastic_null_stress":stress,
        "heldout_null":null_results,"alternatives":alternatives,
        "runtime_seconds":time.monotonic()-start}
    (args.out/"results.json").write_text(json.dumps(results,indent=2,allow_nan=False)+"\n")
    make_plot(results,args.out)
    print(json.dumps({"controls":results["controls"],"all_alternative_summary":results["all_alternative_summary"],
        "heldout_null_summary":results["heldout_null_summary"],"analytic":results["analytic"],
        "minimum_detectable_contrast":mda,"heteroscedastic_null_stress":stress,"runtime_seconds":results["runtime_seconds"]},indent=2))


def make_plot(results,out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"svg.hashsalt":"egfr-curvature-v2","font.size":10})
    fig,axes=plt.subplots(1,2,figsize=(11,4.2),constrained_layout=True)
    colors=["#247b95","#e49a36","#9a4263"]
    for cv,color in zip([.05,.1,.2],colors):
        rows=[r for r in results["minimum_detectable_contrast"] if r["cv"]==cv]
        axes[0].plot([r["replicates_per_time"] for r in rows],
            [r["minimum_contrast_for_80_percent_power"] for r in rows],"o-",label=f"CV {cv:.0%}",color=color)
    axes[0].set(xlabel="Independent replicates per time",ylabel="Minimum log contrast for 80% detection",
                title="Precision needed by the three-point test",xticks=[1,3,6,12])
    axes[0].legend(frameon=False)
    for T,color in zip([.5,1,2],colors):
        rows=[r for r in results["summary_by_setting"] if r["cv"]==.1 and r["T"]==T]
        axes[1].plot([r["replicates_per_time"] for r in rows],
            [100*r["absolute_state"]["analytic_at_least_80_percent_cases"]/81 for r in rows],
            "o-",color=color,label=f"State abundance, T={T:g}")
    rows=[r for r in results["summary_by_setting"] if r["cv"]==.1 and r["T"]==1]
    axes[1].plot([r["replicates_per_time"] for r in rows],
        [100*r["bulk"]["analytic_at_least_80_percent_cases"]/81 for r in rows],"s--",color="#444444",label="Bulk envelope, T=1")
    axes[1].set(xlabel="Independent replicates per time",ylabel="Prespecified cases reaching 80% detection (%)",
                title="Known 10% CV; hypothetical parameter grid",xticks=[1,3,6,12],ylim=(-3,103))
    axes[1].legend(frameon=False,fontsize=8)
    for ax in axes:
        ax.spines[["top","right"]].set_visible(False)
        ax.grid(axis="y",alpha=.18)
    fig.suptitle("Curvature detects changing net state growth; its cause remains unidentified",fontsize=12)
    path=out/"curvature-design-power.svg"
    fig.savefig(path,metadata={"Date":None})
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines())+"\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
