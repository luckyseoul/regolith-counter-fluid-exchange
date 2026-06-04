#!/usr/bin/env python3
"""
Minimal working Rung 2 custom GPU DEM runner on V100.
Uses the fixed kernels for real Hertz + JKR cohesion + friction + rolling.

This is now the active path for generating Rung data (LIGGGHTS abandoned due to time/memory).
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

# =============================================================================
# Parameters (Rung 2 at 0.14 bar, small but real for validation)
# =============================================================================
DT = 1e-6
N_STEPS = 5000          # Short but real physics for first output
DUMP_EVERY = 500
BOX_SIZE = 0.015        # Small box for speed

def generate_small_particles(n_reg=800, n_iron=60):
    np.random.seed(42)
    # Simplified bimodal regolith + iron
    fine_d = np.random.lognormal(np.log(18e-6), 0.6, int(n_reg * 0.4))
    fine_d = np.clip(fine_d, 5e-6, 40e-6)
    coarse_d = np.random.lognormal(np.log(140e-6), 0.5, int(n_reg * 0.6))
    coarse_d = np.clip(coarse_d, 60e-6, 400e-6)
    reg_diam = np.concatenate([fine_d, coarse_d])
    np.random.shuffle(reg_diam)

    iron_diam = np.random.uniform(0.0015, 0.0035, n_iron)

    all_diam = np.concatenate([reg_diam, iron_diam])
    mat = np.array([0] * len(reg_diam) + [1] * n_iron, dtype=np.int32)

    radii = all_diam / 2.0

    # Random placement (will have some overlap - kernels will handle)
    pos = np.random.rand(len(radii), 3).astype(np.float32) * (BOX_SIZE - 0.001)
    pos = np.clip(pos, radii[:, None] + 1e-6, BOX_SIZE - radii[:, None] - 1e-6)

    vel = np.zeros((len(radii), 3), dtype=np.float32)
    omega = np.zeros((len(radii), 3), dtype=np.float32)

    return (cp.asarray(pos), cp.asarray(vel), cp.asarray(omega),
            cp.asarray(radii, dtype=cp.float32), cp.asarray(mat))

if __name__ == "__main__":
    print("=== Custom GPU DEM - Rung 2 (0.14 bar) with DRAG on V100 ===")

    # Load the latest ~3000 particle state (from previous GPU run)
    data = np.load('rung2_3000p_current.npz')
    pos = cp.asarray(data['pos'], dtype=cp.float32)
    vel = cp.asarray(data['vel'], dtype=cp.float32)
    radius = cp.asarray(data['radius'], dtype=cp.float32)
    mat_type = cp.asarray(data['mat'], dtype=cp.int32)
    omega = cp.zeros_like(vel)   # start with zero spin for this demo

    print(f"Loaded {len(pos)} particles (regolith + iron) from rung2_3000p_current.npz")
    print("Adding proper per-particle gas drag (Stokes + quadratic, stronger on iron)")

    # Drag parameters (tied to ~68 W blower point from lumped model)
    U_G = 0.066          # m/s superficial gas velocity
    DRAG_STRENGTH = 1.0  # can tune later against 75.6% effectiveness

    damping = 0.05       # keep some small numerical damping

    N_STEPS = 8000
    DUMP_EVERY = 400

    for step in range(N_STEPS):
        force, torque = compute_forces(pos, vel, omega, radius, mat_type, DT)

        # Add physical gas drag with local solid-fraction modulation
        local_eps = estimate_local_porosity(pos, radius, box_size=0.015)
        drag = compute_drag(vel, radius, mat_type, U_g=U_G, local_porosity=local_eps)
        force += DRAG_STRENGTH * drag

        pos, vel, omega = integrate(pos, vel, omega, force, torque, radius, mat_type, DT, damping)

        if step % DUMP_EVERY == 0:
            ke_reg = 0.5 * cp.sum(cp.linalg.norm(vel, axis=1)**2 * (3100 * (4/3 * cp.pi * radius**3)) * (mat_type == 0))
            ke_iron = 0.5 * cp.sum(cp.linalg.norm(vel, axis=1)**2 * (7870 * (4/3 * cp.pi * radius**3)) * (mat_type == 1))
            iron_z = cp.mean(pos[mat_type == 1, 2]) if cp.any(mat_type == 1) else 0.0
            print(f"Step {step:5d} | KE_reg={float(ke_reg):.3e} KE_iron={float(ke_iron):.3e} | iron_z={float(iron_z):.4f} | max|v|={float(cp.max(cp.linalg.norm(vel, axis=1))):.2e}")

    # Save new state with drag active
    out = {
        'pos': cp.asnumpy(pos),
        'vel': cp.asnumpy(vel),
        'radius': cp.asnumpy(radius),
        'mat_type': cp.asnumpy(mat_type),
        'steps': N_STEPS,
        'U_G': U_G,
        'pressure': 0.14,
        'note': 'First run with proper per-particle Stokes+quadratic drag (stronger on iron)'
    }
    np.savez('rung2_3000p_with_drag.npz', **out)
    print("\n=== Run complete with drag. Saved rung2_3000p_with_drag.npz ===")
    print("Iron should now be visibly fluidized and transferring energy to the regolith.")