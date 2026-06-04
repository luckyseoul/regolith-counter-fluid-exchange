#!/usr/bin/env python3
"""
Rung 3 starter: Electrostatics + EDS mitigation on top of Rung 2 physics.
Demonstrates the high-leverage EDS effect at 0.14 bar (as shown in lumped models: EDS 0.97 is critical).

Simple model (defensible order-of-magnitude for patent):
- Each regolith particle has a small net charge (tribo/UV).
- Repulsive Coulomb between regolith fines (dominant cohesion problem at low P).
- Iron is treated as grounded or low charge.
- EDS effectiveness (0.0 to 1.0) reduces the effective repulsive force (or cohesion).

Run with-iron at 0.14 bar, EDS=0.97 vs EDS=0.5, compare bed mobilization / mixing.

This is the direct next rung after Rung 2 iron agitation is locked.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

# Rung 3 params
DT = 6e-7
STEPS = 2200   # Short but real for completable runs that finish before harness timeout
BOX = 0.018
U_G = 0.066
DAMP = 0.05

# EDS effectiveness (claim range 0.7-0.99, high is 0.97)
EDS_EFF = 0.97   # vs 0.5 for degraded case

def add_electrostatic_forces(force, pos, radius, mat_type, eds_eff=0.97):
    """
    Very simple repulsive electrostatics for fines + EDS mitigation.
    Real physics is more complex (image charges, gas conductivity), this is conservative proxy.
    Higher eds_eff = lower net repulsion = better fluidization (matches lumped sensitivity).
    """
    N = pos.shape[0]
    dx = pos[:, None, :] - pos[None, :, :]
    dist = cp.linalg.norm(dx, axis=2) + 1e-12
    reg = (mat_type == 0)

    # Only regolith-regolith repulsion matters for cohesion problem
    mask = reg[:, None] & reg[None, :] & (cp.arange(N)[:, None] != cp.arange(N)[None, :])
    # Effective charge ~ proportional to surface area for fines, reduced by EDS
    q = (1.0 - eds_eff) * 1.2e-12 * (radius * 1e6)**1.3   # tuned order-of-magnitude for 0.14 bar
    q = cp.where(mat_type == 1, 0.0, q)  # iron low charge

    F_mag = (8.99e9 * q[:, None] * q[None, :]) / (dist**2 + 1e-10)
    F_mag = cp.where(mask, F_mag, 0.0)
    n = dx / dist[..., None]
    F_es = F_mag[..., None] * n

    force += cp.sum(F_es, axis=1) * 0.6   # conservative scaling
    return force

def run_rung3(eds_eff, label, base_state='rung2_3000p_with_drag.npz'):
    print(f"\n=== Rung 3 EDS Demo: {label} (EDS={eds_eff}) ===")
    data = np.load(base_state, allow_pickle=True)
    pos = cp.asarray(data['pos'], dtype=cp.float32)
    vel = cp.asarray(data['vel'], dtype=cp.float32)
    radius = cp.asarray(data['radius'], dtype=cp.float32)
    mat = cp.asarray(data.get('mat_type', data.get('mat')), dtype=cp.int32)

    for s in range(STEPS):
        f, t = compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        f = add_electrostatic_forces(f, pos, radius, mat, eds_eff)

        local = estimate_local_porosity(pos, radius, BOX)
        d = compute_drag(vel, radius, mat, U_g=U_G, local_porosity=local)
        f += d

        pos, vel, _ = integrate(pos, vel, cp.zeros_like(vel), f, t, radius, mat, DT, DAMP)

        if s % 400 == 0:
            reg_z = pos[mat==0, 2]
            bed = float(cp.mean(reg_z)*1000)
            iron_z = pos[mat==1, 2]
            iron_h = float(cp.mean(iron_z)*1000) if cp.sum(mat==1)>0 else 0
            print(f"  step {s:4d} | bed={bed:6.2f}mm iron_h={iron_h:6.2f}mm")

    bed_final = float(cp.mean(pos[mat==0, 2])*1000)
    print(f"Final bed height for {label}: {bed_final:.2f} mm")
    return bed_final

if __name__ == "__main__":
    print("RCFX Rung 3 — EDS mitigation on Rung 2 baseline at 0.14 bar")
    bed_good = run_rung3(0.97, "High EDS (0.97, nominal)")
    bed_bad  = run_rung3(0.50, "Degraded EDS (0.50, sensitivity)")
    print(f"\nDelta from EDS: {bed_good - bed_bad:.2f} mm mobilization gain")
    print("Rung 3 demo complete. Next: full Rung 3 production + Rung 4 multi-stage skeleton.")
