#!/usr/bin/env python3
"""Regenerate historical checkpoint diagnostics and withdrawn thermal FIG. 5."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'patent_drawings'


def save(fig, stem):
    fig.tight_layout()
    for ext in ('svg', 'pdf'):
        fig.savefig(OUT / f'{stem}.{ext}', bbox_inches='tight')
    plt.close(fig)


def snapshot(rung, step, stem, number):
    path = ROOT / f'sims/custom_gpu_dem/rung{rung}_checkpoints/rung{rung}_step{step}.npz'
    with np.load(path) as d:
        pos, mat = d['pos'], d['mat']
    if not np.isfinite(pos).all():
        raise ValueError(f'Non-finite coordinates: {path}')
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for material, label, marker in ((0, 'Regolith', '.'), (1, 'Iron', 'x')):
        mask = mat == material
        if mask.any():
            ax.scatter(pos[mask, 0] * 1000, pos[mask, 2], s=5,
                       marker=marker, label=label, alpha=0.5)
    ax.set(xlabel='Horizontal position x (mm)', ylabel='Particle center z (m)',
           title=f'FIG. {number} — Historical Rung {rung} checkpoint, step {step:,}\n'
                 'No physical lid: not evidence of a confined fluidized bed')
    ax.legend()
    ax.grid(alpha=0.2)
    save(fig, stem)


def goodvar():
    path = ROOT / 'sims/custom_gpu_dem/rung1_highn_checkpoints/physical_drag_real_u3.5_iron1.5mm_step002000.npz'
    with np.load(path) as d:
        pos, mat, radius = d['pos'], d['mat'], d['radius']
    bounds = np.array([0.018, 0.018, 0.060])
    centers = np.all((pos >= 0) & (pos <= bounds), axis=1)
    spheres = np.all((pos - radius[:, None] >= 0) & (pos + radius[:, None] <= bounds), axis=1)
    fig, (ax, info) = plt.subplots(1, 2, figsize=(8, 5), gridspec_kw={'width_ratios': [1, 1.15]})
    for material, label, marker in ((0, 'Regolith', '.'), (1, 'Iron', 'x')):
        mask = mat == material
        ax.scatter(pos[mask, 0] * 1000, pos[mask, 2] * 1000, s=5, marker=marker, label=label, alpha=0.5)
    ax.set(xlabel='Particle center x (mm)', ylabel='Particle center z (mm)', xlim=(0,18), ylim=(0,60))
    ax.axhline(60, color='black', linestyle='--')
    ax.legend(loc='upper left')
    info.axis('off')
    info.text(0, 0.9,
              f'Step 2000; N={len(pos)}\n\n'
              f'Regolith mean z: {pos[mat == 0, 2].mean()*1000:.5f} mm\n'
              f'Iron mean z: {pos[mat == 1, 2].mean()*1000:.5f} mm\n\n'
              f'Centers inside bounds: {centers.mean():.1%}\n'
              f'Whole spheres inside: {spheres.mean():.2%}\n\n'
              'Bounds: 18 × 18 × 60 mm\n'
              '60 mm lid is from source code;\n'
              'checkpoint has no lid metadata.\n\n'
              'Historical 3.58x mean-z ratio uses\n'
              'a separate, unmatched no-iron run.\n'
              'It is not a calibrated mixing gain.',
              va='top', fontsize=10, linespacing=1.4)
    fig.suptitle('FIG. 3 — Good-variable DEM checkpoint\nHistorical filename: real drag, 1.5 mm iron, gas input 3.5 m/s')
    save(fig, 'FIG_03_iron_agitation_goodvar_clean')


def main():
    goodvar()
    snapshot(5, 200000, 'FIG_03_iron_agitation_rung5_final', 3)
    snapshot(5, 500000, 'FIG_03_iron_agitation_rung5_500k_final', 3)
    snapshot(0, 500000, 'FIG_06_distributor_rung0_final', 6)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.axis('off')
    ax.set_title('FIG. 5 — Thermal effectiveness vs. pressure: withdrawn', pad=20)
    ax.text(0.05, 0.75,
            'The previous 75.6% at 0.14 bar claim is unsupported.\n\n'
            'The recurrence advances both streams in the same direction.\n'
            'Raw stage coefficients can exceed one in pressure sweeps.\n\n'
            'A validated counter-current energy balance is required\n'
            'before a thermal performance curve can be supplied.\n\n'
            'Audit: 2026-09-05; see docs/FIGURE_AUDIT.md.',
            transform=ax.transAxes, va='top', fontsize=11, linespacing=1.5)
    save(fig, 'FIG_05_effectiveness_vs_pressure')


if __name__ == '__main__':
    main()
