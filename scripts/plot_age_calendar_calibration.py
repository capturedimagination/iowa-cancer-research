#!/usr/bin/env python3
"""Plot every declared model/design from saved deterministic study results.

Descriptive visualization chosen after outcomes; no statistical test is added.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration'
SOURCE_SHA = '4948c049'  # Full value is bound by the independent comparison below.


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=BASE)
    args = parser.parse_args()
    source = BASE / 'results.json'
    gate = json.loads((BASE / 'independent-comparison.json').read_text())
    assert gate['status'] == 'PASS' and gate['failures'] == []
    assert gate['input_hashes'][str(source.relative_to(ROOT))] == sha(source)
    assert sha(source).startswith(SOURCE_SHA)
    d = json.loads(source.read_text())
    cases = d['cases']
    assert len(cases) == 20
    args.out.mkdir(parents=True, exist_ok=True)
    names = ['age-context-grid.svg', 'age-context-grid.png',
             'calibration-variance.svg', 'calibration-variance.png', 'figure-provenance.json']
    if any((args.out / name).exists() for name in names):
        raise FileExistsError('Use a new output directory; figures are not overwritten')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'svg.hashsalt': 'age-calendar-2026-11-10',
                         'axes.spines.top': False, 'axes.spines.right': False})
    contrast = np.array([[r['value'] for r in c['contrasts']] for c in cases])
    pairs = [[r for r in c['pairs'] if r['bin_id'] == 'w2-b0'] for c in cases]
    raw = np.array([[r['c'] for r in rows] for rows in pairs])
    conditional = np.array([[r['mean_conditional_covariance'] for r in rows] for rows in pairs])
    labels = [f"{c['case_id']}  {c['configuration']['base_label'].replace('_', ' ')} / "
              f"{c['configuration']['clock_id']}" for c in cases]
    fig, axes = plt.subplots(1, 3, figsize=(15.8, 10), gridspec_kw={'width_ratios': [2.8, 1.1, 1.1]})
    m = max(abs(contrast.min()), abs(contrast.max()))
    im = axes[0].imshow(contrast, cmap='RdBu_r', vmin=-m, vmax=m, aspect='auto')
    axes[0].set_yticks(range(20), labels, fontsize=8)
    axes[0].set_xticks(range(12), [f"{r['t']:g}\n{r['T_early']:g}→{r['T_late']:g}" for r in cases[0]['contrasts']], fontsize=8)
    axes[0].set_xlabel('Observation time t / selection horizons')
    axes[0].set_title('Selected-survival contrast\nQ later − Q earlier', loc='left', fontsize=12)
    fig.colorbar(im, ax=axes[0], orientation='horizontal', fraction=.045, pad=.12)
    vmax = float(max(raw.max(), conditional.max()))
    for ax, values, title in zip(axes[1:], [raw, conditional],
                                ['Pooled sister covariance', 'Exact birth-conditioned\ncovariance, averaged']):
        im = ax.imshow(values, cmap='viridis', vmin=0, vmax=vmax, aspect='auto')
        ax.set_yticks(range(20), [c['case_id'] for c in cases], fontsize=8)
        ax.set_xticks(range(3), ['0.5', '1', '2'])
        ax.set_xlabel('Elapsed daughter lag')
        ax.set_title(title, loc='left', fontsize=12)
        fig.colorbar(im, ax=ax, orientation='horizontal', fraction=.045, pad=.12)
    fig.suptitle('Age and shared calendar context can imitate paired lineage signals', x=.03, ha='left', fontsize=17)
    fig.text(.03, .017, 'All 20 hypothetical models and all 240 contrasts. Both division and death share one clock. '
             'A19–A20 have zero death. No empirical cell outcomes are fitted.', fontsize=9)
    fig.tight_layout(rect=[.015, .05, .99, .95])
    for ext in ['svg', 'png']:
        fig.savefig(args.out / f'age-context-grid.{ext}', dpi=160, metadata={'Date': None} if ext == 'svg' else {})
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
    ms, ns = [5, 20, 100], [100, 1000]
    summaries = []
    for ni, n in enumerate(ns):
        med, low, high = [], [], []
        for m in ms:
            ratios = []
            zeros = 0
            for c in cases:
                for r in c['calibration']:
                    if (r['m'], r['n']) != (m, n):
                        continue
                    methods = r['methods']
                    den = methods['unbiased_target_sample_covariance']['variance']
                    num = methods['shared_fitted_mean_corrected']['variance']
                    if den == 0:
                        assert num == 0
                        zeros += 1
                    else:
                        ratios.append(num / den)
            assert len(ratios) == 810 and zeros == 90
            low.append(min(ratios)); med.append(float(np.median(ratios))); high.append(max(ratios))
            summaries.append(dict(m=m, n=n, nondegenerate_designs=len(ratios), zero_variance_designs=zeros,
                                  minimum=low[-1], median=med[-1], maximum=high[-1]))
        x = np.arange(3) + (ni - .5) * .13
        axes[0].errorbar(x, med, yerr=[np.subtract(med, low), np.subtract(high, med)],
                         fmt='o-', capsize=4, label=f'n = {n:,} target pairs')
    axes[0].axhline(1, color='#65717a', ls='--', lw=1)
    axes[0].set_xticks(range(3), [str(m) for m in ms])
    axes[0].set_yscale('log')
    axes[0].set_ylabel('Corrected shared-fit variance / sample covariance variance')
    axes[0].set_xlabel('m independent calibration singles')
    axes[0].set_title('Full-grid median and range', loc='left')
    axes[0].legend(frameon=False, fontsize=9)
    reductions = []
    for c in cases:
        for lag in [.5, 1., 2.]:
            rows = sorted([r for r in c['partitions'] if r['lag'] == lag], key=lambda x: -x['width'])
            base = rows[0]['remaining_context_variance']
            # Descriptive numerical-zero convention, not an inferential threshold.
            if base <= 1e-12:
                continue
            ratios = [r['remaining_context_variance'] / base for r in rows]
            reductions.append(dict(case_id=c['case_id'], lag=lag, widths=[r['width'] for r in rows], ratios=ratios))
            axes[1].plot(range(4), ratios, color='#256d80', alpha=.22, lw=1)
    axes[1].set_xticks(range(4), ['2', '1', '0.5', '0.25'])
    axes[1].set_xlabel('Birth-time bin width')
    axes[1].set_ylabel('Weighted remaining context variance / pooled context variance')
    axes[1].set_ylim(-.02, 1.04)
    axes[1].set_title(f'All {len(reductions)} nonzero context targets', loc='left')
    fig.suptitle('Calibration uncertainty and incomplete context adjustment', x=.035, ha='left', fontsize=16)
    fig.text(.035, .035, 'Left: 5,400 analytic designs; 540 zero-variance controls have undefined ratios. '
             'Calibration adds m observations; this is not a cost-matched comparison.\n'
             'Right: 38 of 60 targets; 22 numerical-zero controls have undefined normalized ratios. '
             'Post-results descriptive plots; no hypothesis test is added.', fontsize=8.4)
    fig.tight_layout(rect=[.015, .13, .99, .93])
    for ext in ['svg', 'png']:
        fig.savefig(args.out / f'calibration-variance.{ext}', dpi=160, metadata={'Date': None} if ext == 'svg' else {})
    plt.close(fig)
    # Matplotlib emits trailing spaces in path coordinates. Keep equivalent SVG
    # tokens while avoiding whitespace noise in the public Git diff.
    for name in ['age-context-grid.svg', 'calibration-variance.svg']:
        path = args.out / name
        path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()) + '\n')
    provenance = dict(source_sha256=sha(source), code_sha256=sha(__file__),
                      input=str(source.relative_to(ROOT)), contrast_records=240, pooled_pair_records=60,
                      calibration_records=5400, variance_ratio_summaries=summaries,
                      context_ratio_zero_convention=1e-12, context_reductions=reductions,
                      selection='All frozen outcomes; descriptive plotting choices made after results.',
                      output_hashes={name: sha(args.out / name) for name in names[:-1]})
    (args.out / names[-1]).write_text(json.dumps(provenance, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
