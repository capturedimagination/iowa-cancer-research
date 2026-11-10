"""Plot the synthetic family-selection identity without empirical cell claims."""
from pathlib import Path
import argparse,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/sampling-simulation'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=DEFAULT);ap.add_argument('--preview',type=Path);args=ap.parse_args()
    data=json.loads((DEFAULT/'results.json').read_text())
    case=next(r for r in data['cases'] if r['lambda']==r['mu']==2)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'lineage-family-2026-11-10'})
    fig,axes=plt.subplots(1,2,figsize=(12.2,4.8));fig.subplots_adjust(left=.08,right=.98,top=.86,bottom=.25,wspace=.29)
    blue='#2F6176';orange='#BB5934';t=np.linspace(0,1,201)
    ax=axes[0]
    ax.plot(t,np.exp(-2*t),color=blue,lw=2,label='Unselected random path')
    ax.plot(t,np.exp(-2*t)*(1+2*t),color=orange,lw=2,label='Family-selected path = two-stage law')
    s=case['groups']['family_survives']['survival_curve']
    ax.plot([x['time'] for x in s],[x['observed'] for x in s],'o',ms=4,color=orange,markeredgecolor='white',label='Simulated family-selected paths')
    ax.set(xlabel='Time / selection horizon',ylabel='Probability tagged path remains alive',ylim=(0,1.05),title='Selection creates an apparent delay')
    ax.legend(frameon=False,fontsize=8,loc='lower left');ax.grid(axis='y',alpha=.2)
    ax=axes[1]
    ax.axhline(2,color=blue,lw=2,label='True constant cell death rate')
    ax.plot(t,4*t/(1+2*t),color=orange,lw=2,label='Family-selected tagged death hazard')
    bins=case['groups']['family_survives']['bins']
    ax.errorbar([(b['start']+b['end'])/2 for b in bins],[b['death']['rate'] for b in bins],
        yerr=[2*b['death']['delta_method_founder_Monte_Carlo_SE'] for b in bins],fmt='o',ms=4,color=orange,capsize=2,
        markeredgecolor='white',label='Simulated bin rate ± 2 Monte Carlo SE')
    ax.set(xlabel='Time / selection horizon',ylabel='Death events per tagged time at risk',ylim=(0,2.2),title='A changing observed rate without adaptation')
    ax.legend(frameon=False,fontsize=8,loc='lower right');ax.grid(axis='y',alpha=.2)
    fig.text(.08,.12,'Synthetic model: division = death = 2; 200,000 prospective founders; one random sister path per founder.',fontsize=9)
    fig.text(.08,.065,'Select families with any survivor at T = 1. Equivalence is limited to observations censored at T; no patient data.',fontsize=9)
    args.out.mkdir(parents=True,exist_ok=True);svg=args.out/'sampling-induced-delay.svg'
    fig.savefig(svg,metadata={'Date':None})
    svg.write_text('\n'.join(x.rstrip() for x in svg.read_text().splitlines())+'\n')
    if args.preview:
        args.preview.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.preview,dpi=150)


if __name__=='__main__':main()
