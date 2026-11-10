"""Plot the fixed technical-depth simulations; intervals are Monte Carlo only."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results_dir",type=Path)
    ap.add_argument("--preview",type=Path)
    args=ap.parse_args()
    j=json.loads((args.results_dir/"results.json").read_text())
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
        "axes.spines.right":False,"svg.fonttype":"none","svg.hashsalt":"signature-depth-20261110"})
    fig,axes=plt.subplots(1,2,figsize=(10,4.7),gridspec_kw={"width_ratios":[1.15,1]})
    ax=axes[0]
    methods=[("Observed",None,"#252525",-.16),
             ("1,000 UMI thinning",j["thinning"]["1000"]["replicate_summary"],"#315f75",0),
             ("Depth-only null",j["technical_simulations"]["observed_depth_null"],"#b15b32",.16)]
    for label,result,color,offset in methods:
        for i,group in enumerate(("pooled","v3.1","v4")):
            if result is None:
                y=j["observed_metrics"]["mean_log_score"][group]["mean_difference"]
                ax.scatter(i+offset,y,color=color,s=32,label=label if i==0 else None,zorder=3)
            else:
                d=result[group]["mean_difference"];y=d["mean"];lo,_,hi=d["simulation_percentiles_2_5_50_97_5"]
                ax.errorbar(i+offset,y,yerr=[[y-lo],[hi-y]],fmt="o",color=color,ms=4.5,capsize=3,label=label if i==0 else None)
    ax.axhline(0,color="#888888",lw=.8)
    ax.set_xticks([0,1,2],["All patients","v3.1*","v4*"])
    ax.set_ylabel("Residual minus untreated mean score")
    ax.set_title("Opposite kit-stratum directions persist",fontsize=11,loc="left")
    ax.legend(frameon=False,fontsize=8,loc="upper left")
    ax=axes[1]
    for group,color,label in [("pooled","#252525","All patients"),("v3.1","#315f75","v3.1*"),("v4","#b15b32","v4*")]:
        xs=[];ys=[];los=[];his=[]
        for depth in (250,500,1000,2000):
            d=j["thinning"][str(depth)]["replicate_summary"][group]["mean_difference"]
            xs.append(depth);ys.append(d["mean"]);lo,_,hi=d["simulation_percentiles_2_5_50_97_5"];los.append(d["mean"]-lo);his.append(hi-d["mean"])
        ax.errorbar(xs,ys,yerr=[los,his],color=color,fmt="o-",ms=4,capsize=3,label=label)
    ax.axhline(0,color="#888888",lw=.8)
    ax.set_xscale("log",base=2);ax.set_xticks([250,500,1000,2000],["250","500","1,000","2,000†"])
    ax.set_xlabel("Molecules retained per nucleus")
    ax.set_title("Depth changes magnitude, not the reversal",fontsize=11,loc="left")
    ax.legend(loc="center right",fontsize=8,frameon=True,facecolor="white",edgecolor="white")
    for ax in axes:
        ax.grid(axis="y",color="#e5e5e5",lw=.6);ax.set_axisbelow(True)
    fig.text(.075,.09,"Bars: central 95% of 100 technical simulations, not patient confidence intervals.",fontsize=9)
    fig.text(.075,.045,"* Source-implied kit labels conflict with GSM records. † 2,000-UMI analysis retains fewer nuclei.",fontsize=8)
    fig.subplots_adjust(left=.075,right=.98,bottom=.24,top=.88,wspace=.28)
    svg=args.results_dir/"depth-falsification.svg"
    fig.savefig(svg,metadata={"Date":None});svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
    if args.preview:
        args.preview.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.preview,dpi=160)
    plt.close(fig)


if __name__=="__main__":main()
