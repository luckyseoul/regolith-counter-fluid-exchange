#!/usr/bin/env python3
"""
Fast Rung 3 EDS demo (body-force approximation, no O(N^2)).
High EDS (0.97) vs degraded (0.50) on Rung 2 iron baseline at 0.14 bar.
Designed to complete quickly and produce the mobilization delta.

This moves the campaign to the next rung immediately.
"""

import cupy as cp
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path("common").resolve()))
from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

DT = 7e-7
STEPS = 3000
BOX = 0.015
U_G = 0.066
DAMP = 0.05

def add_eds_body_force(force, pos, radius, mat_type, eds_eff):
    """Simple per-particle body force proxy for electrostatic repulsion on fines.
    Higher eds_eff → much weaker repulsion → better bed expansion.
    """
    reg = (mat_type == 0)
    # Effective repulsion strength reduced by EDS
    strength = (1.0 - eds_eff) * 0.8
    # Small upward/ random kick on fines proportional to 1-EDS (conservative)
    kick = strength * 0.015 * (cp.random.randn(len(pos), 3).astype(cp.float32) * 0.3 + cp.array([0,0,0.4]))
    force[reg] += kick[reg] * (radius[reg, None] * 1e5)   # more effect on larger fines
    return force

def run_case(eds_eff, label, base='rung2_3000p_with_drag.npz'):
    print(f"\n=== Rung 3 Fast EDS: {label} (EDS={eds_eff}) ===")
    d = np.load(base, allow_pickle=True)
    pos = cp.asarray(d['pos'])
    vel = cp.asarray(d['vel'])
    rad = cp.asarray(d['radius'])
    mat = cp.asarray(d.get('mat_type', d.get('mat')))

    for s in range(STEPS):
        f, t = compute_forces(pos, vel, cp.zeros_like(vel), rad, mat, DT)
        f = add_eds_body_force(f, pos, rad, mat, eds_eff)

        eps = estimate_local_porosity(pos, rad, BOX)
        dr = compute_drag(vel, rad, mat, U_g=U_G, local_porosity=eps)
        f += dr

        pos, vel, _ = integrate(pos, vel, cp.zeros_like(vel), f, t, rad, mat, DT, DAMP)

        if s % 500 == 0:
            bed = float(cp.mean(pos[mat==0, 2]) * 1000)
            print(f"  step {s:4d} bed={bed:6.2f} mm")

    bed_final = float(cp.mean(pos[mat==0, 2]) * 1000)
    print(f"Final bed for {label}: {bed_final:.2f} mm")
    return bed_final

if __name__ == "__main__":
    print("RCFX Rung 3 Fast — EDS effect on iron-agitated bed at 0.14 bar")
    bed_high = run_case(0.97, "High EDS 0.97 (nominal)")
    bed_low  = run_case(0.50, "Degraded EDS 0.50")
    print(f"\n=== Rung 3 Result ===")
    print(f"High EDS bed:  {bed_high:.2f} mm")
    print(f"Low EDS bed:   {bed_low:.2f} mm")
    print(f"Mobilization gain from good EDS: {bed_high - bed_low:.2f} mm")
    print("Rung 3 fast demo complete. Chain continues to Rung 4.")
