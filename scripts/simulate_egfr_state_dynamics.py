"""Synthetic recovery-memory discrimination experiment; not clinical advice.

All parameter values are hypothetical. The frozen protocol defines controls,
noise, calibration grids and sensitivity cases before any result is generated.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from scipy.special import xlogy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "research/treatment-discovery/discovery-2026-11-10/mechanistic-simulation"
TIMES = np.array([.5, 2., 4.])
G_S = np.log(2.)
PROTOCOL_SHA256 = "a8d626c0944ce0fe31360fdc607f4babe635474e84ff18439dd75b31b4680e1e"
DESIGNS = {
    "counts_only": ([0, 1], []),
    "early_count_and_fraction": ([0], [0]),
    "early_count_and_two_fractions": ([0], [0, 1]),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def constant_exit(b, gp, f0, times=TIMES):
    """Analytic S,P solution; broadcasts b across observation times."""
    b = np.atleast_1d(b).astype(float)[:, None]
    t = np.asarray(times, dtype=float)[None, :]
    p = f0 * np.exp((gp-b)*t)
    gap = G_S-gp+b
    # Integral of exp(-gap*u), including the continuous gap=0 limit.
    integral = np.empty(np.broadcast_shapes(gap.shape, t.shape))
    np.divide(-np.expm1(-gap*t), gap, out=integral, where=np.abs(gap) > 1e-12)
    integral = np.where(np.abs(gap) <= 1e-12, t, integral)
    s = np.exp(G_S*t) * ((1-f0) + b*f0*integral)
    n = s+p
    return n, p/n


def recovery_memory(b_inf, tau, gp, f0, times=TIMES, rtol=1e-10, atol=1e-12):
    def rhs(t, y):
        b = b_inf*(-np.expm1(-t/tau))
        return [G_S*y[0]+b*y[1], (gp-b)*y[1]]
    sol = solve_ivp(rhs, (0, float(max(times))), [1-f0, f0], t_eval=times,
                    method="DOP853", rtol=rtol, atol=atol)
    assert sol.success and np.isfinite(sol.y).all() and (sol.y >= -1e-11).all()
    s,p = sol.y
    n = s+p
    return n,p/n


def observe(n, f, noise, reps, rng):
    sigma = np.sqrt(np.log1p(noise["burden_cv"]**2))
    logn = np.log(n)[None, :] - sigma*sigma/2 + sigma*rng.normal(size=(reps,len(n)))
    err = noise["symmetric_label_error"]
    q = err + (1-2*err)*np.asarray(f)
    k = rng.binomial(noise["phenotype_cells"], q, size=(reps,len(f)))
    return logn,k


def fitted_deviances(observed, model_n, model_f, noise):
    """Profile constant exit-rate nuisance parameter for each simulated dataset."""
    logn,k = observed
    sigma2 = np.log1p(noise["burden_cv"]**2)
    means = np.log(model_n)-sigma2/2
    cells = noise["phenotype_cells"]
    err = noise["symmetric_label_error"]
    q = np.clip(err+(1-2*err)*model_f, 1e-12, 1-1e-12)
    count_terms = [((logn[:,i,None]-means[None,:,i])**2)/sigma2 for i in range(2)]
    fraction_terms = []
    for i in range(2):
        y = k[:,i,None]
        sat = 2*(xlogy(y,y/cells)+xlogy(cells-y,(cells-y)/cells))
        fraction_terms.append(sat-2*y*np.log(q[None,:,i])-2*(cells-y)*np.log1p(-q[None,:,i]))
    out = {}
    for name,(count_cols,fraction_cols) in DESIGNS.items():
        loss = np.zeros_like(count_terms[0])
        for i in count_cols: loss += count_terms[i]
        for i in fraction_cols: loss += fraction_terms[i]
        out[name] = np.min(loss,axis=1)
    return out


def rate_summary(reject):
    p = float(np.mean(reject))
    return {"rate":p,"replicates":len(reject),"monte_carlo_se":float(np.sqrt(p*(1-p)/len(reject)))}


def controls():
    checks = []
    for f0,gp_ratio,b in itertools.product([0.,.1,.9],[0.,.5,1.],[0.,.1,1.]):
        gp = G_S*gp_ratio
        n,f = constant_exit(b,gp,f0)
        sol = solve_ivp(lambda t,y:[G_S*y[0]+b*y[1],(gp-b)*y[1]],(0,4),[1-f0,f0],
                        t_eval=TIMES,method="DOP853",rtol=1e-12,atol=1e-14)
        nn=sol.y.sum(axis=0)
        error=float(np.max(np.abs(n[0]-nn)))
        assert error < 1e-9
        checks.append(error)
    eqn,eqf=recovery_memory(.4,1,G_S,.9)
    equal_growth_error=float(np.max(np.abs(eqn-np.exp(G_S*TIMES))))
    assert equal_growth_error < 1e-9
    none_n,none_f=recovery_memory(.4,1,0,0)
    assert np.max(np.abs(none_n-np.exp(G_S*TIMES)))<1e-9 and np.all(none_f==0)
    n,f=recovery_memory(.4,1e-6,0,.9)
    cn,cf=constant_exit(.4,0,.9)
    limiting_error=float(np.max(np.abs(n-cn[0])))
    assert limiting_error < 1e-5
    n1,f1=recovery_memory(.4,1,.5*G_S,.9)
    n2,f2=recovery_memory(.4,1,.5*G_S,.9,rtol=1e-12,atol=1e-14)
    stability=float(max(np.max(np.abs(n1-n2)),np.max(np.abs(f1-f2))))
    assert stability < 1e-8
    return {"analytic_vs_numerical_cases":len(checks),"max_absolute_error":max(checks),
            "equal_growth_total_count_identity_max_error":equal_growth_error,
            "vanishing_memory_limit_max_error":limiting_error,
            "zero_persister_population_control":"pass","solver_tolerance_stability_max_error":stability}


def growth_alternative(b_inf,tau,gp,f0):
    n,f=recovery_memory(b_inf,tau,gp,f0)
    def loss(x):
        nn,_=constant_exit(x[0],x[1],f0)
        return np.log(nn[0,:2])-np.log(n[:2])
    fits=[least_squares(loss,[b0,g0],bounds=([0,-G_S],[1.6,1.5*G_S]),
                       xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=300)
          for b0,g0 in [(0.05,gp),(.4,gp),(1.,.5*G_S)]]
    fit=min(fits,key=lambda x:np.dot(x.fun,x.fun))
    nn,ff=constant_exit(fit.x[0],fit.x[1],f0)
    error=float(np.max(np.abs(fit.fun)))
    return {"b_inf":b_inf,"tau":tau,"gP_over_gS":gp/G_S,"f0":f0,
            "fitted_constant_b":float(fit.x[0]),"fitted_gP_over_gS":float(fit.x[1]/G_S),
            "max_abs_log_count_fit_error":error,"numerically_exact_match":error<1e-6,
            "within_one_percent_count_match":bool(error<np.log(1.01)),
            "heldout_fraction_difference_at_t0_5":float(ff[0,0]-f[0]),
            "heldout_fraction_difference_at_t2":float(ff[0,1]-f[1]),
            "heldout_log_count_difference_at_t4":float(np.log(nn[0,2])-np.log(n[2]))}


def plot_results(results, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors={"counts_only":"#777777","early_count_and_fraction":"#ba693e",
            "early_count_and_two_fractions":"#276d79"}
    labels={"counts_only":"Two burden measurements","early_count_and_fraction":"Early burden + state fraction",
            "early_count_and_two_fractions":"Early burden + two state fractions"}
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"svg.fonttype":"none",
                         "svg.hashsalt":"egfr-recovery-design-20261110","axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(1,3,figsize=(10.4,4.2),sharey=True)
    for ax,ratio in zip(axes,[0.,.5,1.]):
        for design in DESIGNS:
            rows=[x for x in results["alternative_power"] if x["noise"]=="primary" and x["f0"]==.9
                  and x["gP_over_gS"]==ratio and x["b_inf"]==.4 and x["design"]==design]
            rows=sorted(rows,key=lambda x:x["tau"])
            ax.plot([x["tau"] for x in rows],[x["rate"] for x in rows],marker="o",color=colors[design],label=labels[design])
        ax.axhline(.05,ls=":",color="#bbbbbb",lw=1)
        ax.set_xscale("log");ax.set_xticks([.25,1,4],["0.25","1","4"])
        ax.set_xlabel("Recovery-memory time scale")
        ax.set_title(f"Tolerant growth / sensitive growth = {ratio:g}")
        ax.set_ylim(0,1);ax.grid(axis="y",color="#e5e5e5")
    axes[0].set_ylabel("Simulated rejection of constant exit rate")
    fig.suptitle("Which measurement reveals time-dependent recovery?",x=.07,ha="left",fontweight="bold")
    handles,labels1=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels1,loc="lower center",ncol=3,frameon=False,bbox_to_anchor=(.5,.07),fontsize=8)
    fig.text(.07,.025,"Hypothetical parameters; initial tolerant fraction 0.9; no clinical timing or validated mechanism implied.",fontsize=8)
    fig.subplots_adjust(left=.07,right=.98,top=.82,bottom=.29,wspace=.18)
    path=out/"measurement-design-power.svg"
    fig.savefig(path,metadata={"Date":None})
    path.write_text("\n".join(x.rstrip() for x in path.read_text().splitlines())+"\n")
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",type=Path,default=DEFAULT)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    protocol=DEFAULT/"protocol.json"
    assert sha(protocol)==PROTOCOL_SHA256, "Frozen simulation protocol changed"
    spec=json.loads(protocol.read_text())
    assert np.__version__=="2.3.5"
    started=time.monotonic()
    checks=controls()
    grid=np.linspace(0,1.6,321)
    rng_cal=np.random.default_rng(spec["seeds"]["null_calibration"])
    rng_null=np.random.default_rng(spec["seeds"]["heldout_null"])
    rng_alt=np.random.default_rng(spec["seeds"]["alternative"])
    calibration=[];nulls=[];alternatives=[]
    for f0,ratio,noise in itertools.product(spec["model_parameters"]["f0"],spec["model_parameters"]["gP_over_gS"],spec["noise_settings"]):
        gp=G_S*ratio
        nn,ff=constant_exit(grid,gp,f0)
        critical={k:0. for k in DESIGNS}
        for b in spec["null_calibration"]["true_b_grid"]:
            n,f=constant_exit(b,gp,f0)
            d=fitted_deviances(observe(n[0,:2],f[0,:2],noise,2000,rng_cal),nn,ff,noise)
            for name,v in d.items():
                q=float(np.quantile(v,.95,method="higher"));critical[name]=max(critical[name],q)
                calibration.append({"f0":f0,"gP_over_gS":ratio,"noise":noise["name"],"true_b":b,"design":name,"q95":q})
        for b in spec["heldout_null"]["true_b_grid"]:
            n,f=constant_exit(b,gp,f0)
            d=fitted_deviances(observe(n[0,:2],f[0,:2],noise,2000,rng_null),nn,ff,noise)
            for name,v in d.items():
                nulls.append({"f0":f0,"gP_over_gS":ratio,"noise":noise["name"],"true_b":b,
                              "design":name,"critical_value":critical[name],**rate_summary(v>critical[name])})
        for b,tau in itertools.product(spec["model_parameters"]["b_inf"],spec["model_parameters"]["tau"]):
            n,f=recovery_memory(b,tau,gp,f0)
            d=fitted_deviances(observe(n[:2],f[:2],noise,2000,rng_alt),nn,ff,noise)
            for name,v in d.items():
                alternatives.append({"f0":f0,"gP_over_gS":ratio,"noise":noise["name"],"b_inf":b,
                                     "tau":tau,"design":name,"critical_value":critical[name],**rate_summary(v>critical[name])})
        print(f"Completed f0={f0:g}, growth ratio={ratio:g}, noise={noise['name']}",flush=True)
    specificity=[growth_alternative(b,tau,G_S*ratio,f0) for f0,ratio,b,tau in itertools.product(
        spec["model_parameters"]["f0"],spec["model_parameters"]["gP_over_gS"],
        spec["model_parameters"]["b_inf"],spec["model_parameters"]["tau"])]
    summary={}
    for design in DESIGNS:
        n=[x["rate"] for x in nulls if x["design"]==design]
        p=[x["rate"] for x in alternatives if x["design"]==design and x["noise"]=="primary"]
        summary[design]={"heldout_false_positive_min":min(n),"heldout_false_positive_max":max(n),
                         "heldout_false_positive_median":float(np.median(n)),"primary_power_min":min(p),
                         "primary_power_median":float(np.median(p)),"primary_power_max":max(p),
                         "primary_parameter_cases_at_least_80pct_power":sum(x>=.8 for x in p),"primary_parameter_cases":len(p)}
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),"protocol_sha256":sha(protocol),
            "code_sha256":sha(Path(__file__)),"scope":"Synthetic model-discrimination and measurement-design stress test only",
            "calibration_seed":spec["seeds"]["null_calibration"],"heldout_null_seed":spec["seeds"]["heldout_null"],
            "alternative_seed":spec["seeds"]["alternative"],"environment":{"numpy":np.__version__},
            "controls":checks,"summary":summary,"null_calibration":calibration,"heldout_null_false_positives":nulls,
            "alternative_power":alternatives,"growth_rate_alternative":specificity,
            "growth_alternative_summary":{"cases":len(specificity),"numerically_exact_two_count_matches":sum(x["numerically_exact_match"] for x in specificity),
              "within_one_percent_two_count_matches":sum(x["within_one_percent_count_match"] for x in specificity)},
            "wall_seconds":time.monotonic()-started,
            "limitations":["All numerical parameters and noise settings are hypothetical, not fitted to EGFR experiments.",
                "Known initial fraction and net growth rates are idealizations; changing growth can mimic switching kinetics.",
                "Simulated state labels denote functional sensitivity/tolerance; no gene-expression signature has been validated to supply them.",
                "No demographic stochasticity, patient/replicate heterogeneity or model-mismatch calibration is included.",
                "Finite-grid worst-quantile calibration is not a proof of uniform type-I error control.",
                "Rejection of a constant-rate model does not identify the cause of time dependence, demonstrate cellular memory, or propose a therapy.",
                "Memory modeling and identifiability are established prior art; novelty of this exact stress test remains unestablished."]}
    (args.out/"results.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    plot_results(result,args.out)
    print(json.dumps({"controls":checks,"summary":summary,"specificity":result["growth_alternative_summary"]},indent=2),flush=True)


if __name__=="__main__":main()
