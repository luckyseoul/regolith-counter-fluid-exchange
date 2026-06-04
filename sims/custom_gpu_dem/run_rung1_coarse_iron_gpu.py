#!/usr/bin/env python3
"""
Rung 1 backfill — Coarse Non-Cohesive Fraction + Iron Shot
Uses the exact same physics/kernels/drag as the validated Rung 2 work.
Cohesion disabled for regolith (coarse only).
Runs with-iron vs no-iron at the same 0.14 bar target conditions.
Checkpointed so it can run long.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity, DENSITY

# Force no cohesion on regolith for Rung 1
import dem_kernels
dem_kernels.SURFACE_ENERGY = cp.array([[0.0, 0.0],
                                     [0.0, 0.0]], dtype=cp.float32)

DT = 6.5e-7
CHECKPOINT_EVERY = 1500
TOTAL_TARGET_STEPS = 500000  # forced long run for backfill - ignore previous targets
BOX = 0.018
U_G = 0.066
DAMP = 0.05

CHECKPOINT_DIR = Path("rung1_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

def save_checkpoint(pos, vel, radius, mat, step, prefix):
    cp.savez(CHECKPOINT_DIR / f"{prefix}_step{step:05d}.npz",
             pos=cp.asnumpy(pos), vel=cp.asnumpy(vel),
             radius=cp.asnumpy(radius), mat=cp.asnumpy(mat), step=step)

def load_latest_checkpoint(prefix):
    files = list(CHECKPOINT_DIR.glob(f"{prefix}_step*.npz"))
    if not files:
        return None, 0
    def step_num(p):
        try:
            return int(p.name.split("_step")[1].split(".")[0])
        except Exception:
            return 0
    files.sort(key=step_num)
    latest = files[-1]
    d = np.load(latest, allow_pickle=True)
    print(f"Resuming {prefix} from {latest.name} (step {int(d['step'])})")
    return (cp.asarray(d['pos']), cp.asarray(d['vel']),
            cp.asarray(d['radius']), cp.asarray(d['mat']), int(d['step']))


def add_distributor_force(force, pos, radius, mat):
    """Body-force acceleration (upward) near bottom to simulate high distributor ΔP / gas injection support.
    Treated as acceleration (m/s^2) and scaled by particle mass to produce proper force (N).
    This fixes previous version that added a constant to the force array (producing mass-dependent
    insane accelerations for small regolith particles, leading to unphysical 79 m/s launch and 10+m "bed" CoM).
    2.8 m/s^2 is a few x lunar g near the plate, decaying over mm scale.
    """
    z = pos[:, 2]
    dist_strength = 2.8 * cp.exp(-z / 0.003)   # acceleration (m/s^2) upward, decays quickly
    mass = DENSITY[mat] * (4.0 / 3.0 * cp.pi * radius**3)
    force[:, 2] += dist_strength * mass
    return force


def add_wall_forces(force, pos, radius, mat):
    """Lateral box walls (x/y containment within [0, BOX]) to keep particles inside the simulated vessel.
    Prevents radial escape that makes mean-z 'bed height' meaningless (CoM of spray instead of fluidized bed).
    Uses acceleration-style (scaled by mass) for consistency with distributor; stiff but stable.
    """
    k_wall = 120.0  # m/s^2 per meter of penetration (tuned for small particles)
    for ax in [0, 1]:  # x and y
        p = pos[:, ax]
        # low side (x=0 or y=0)
        pen = -p
        over = pen > 0.0
        if cp.any(over):
            acc = k_wall * pen[over]
            m = DENSITY[mat[over]] * (4.0 / 3.0 * cp.pi * radius[over]**3)
            force[over, ax] += acc * m
        # high side (x=BOX or y=BOX)
        pen = p - BOX
        over = pen > 0.0
        if cp.any(over):
            acc = k_wall * pen[over]
            m = DENSITY[mat[over]] * (4.0 / 3.0 * cp.pi * radius[over]**3)
            force[over, ax] -= acc * m
    return force


def add_floor_force(force, pos, vel, radius, mat):
    """Hard floor support at z=0 (prevents penetration, models distributor plate + vessel bottom).
    Acceleration based + vel clip to avoid sinking. Complements the soft exponential distributor.
    """
    z0 = 0.0
    k_floor = 200.0  # m/s^2 per m pen
    z = pos[:, 2]
    below = z < z0
    if cp.any(below):
        pen = z0 - z[below]
        acc = k_floor * pen
        m = DENSITY[mat[below]] * (4.0 / 3.0 * cp.pi * radius[below]**3)
        force[below, 2] += acc * m
        vel[below, 2] = cp.maximum(vel[below, 2], 0.0)
    return force


def generate_coarse_particles(n_total=2600, with_iron=True):
    np.random.seed(42)
    n_iron = 180 if with_iron else 0
    n_reg = n_total - n_iron

    # Coarse only (Rung 1 definition)
    reg_diam = np.random.uniform(60e-6, 400e-6, n_reg)

    iron_diam = np.random.uniform(0.0018, 0.0033, n_iron) if n_iron > 0 else np.array([])

    all_diam = np.concatenate([reg_diam, iron_diam])
    mat = np.array([0] * n_reg + [1] * n_iron, dtype=np.int32)

    radii = all_diam / 2.0
    pos = np.random.rand(len(radii), 3).astype(np.float32) * (BOX * 0.9)
    pos[:, 2] *= 0.4
    pos = np.clip(pos, radii[:, None] + 1e-6, BOX - radii[:, None] - 1e-6)

    return (cp.asarray(pos), cp.zeros((len(radii), 3), dtype=cp.float32),
            cp.asarray(radii, dtype=cp.float32), cp.asarray(mat))

def run_rung1(with_iron=True):
    prefix = "rung1_with_iron" if with_iron else "rung1_no_iron"
    print(f"\n=== Rung 1 Checkpointed: {prefix} ===")

    ck = load_latest_checkpoint(prefix)
    if ck[0] is not None:
        pos, vel, radius, mat, start_step = ck
    else:
        pos, vel, radius, mat = generate_coarse_particles(with_iron=with_iron)
        start_step = 0

    n_iron = int(cp.sum(mat == 1))
    steps_to_do = TOTAL_TARGET_STEPS - start_step
    # Force long backfill run - do not early exit even if previous target was met
    print(f"Running {steps_to_do} steps from {start_step} (FORCED LONG BACKFILL)")

    for s in range(steps_to_do):
        step = start_step + s
        f, tq = compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        eps = estimate_local_porosity(pos, radius, BOX)
        dr = compute_drag(vel, radius, mat, U_g=U_G, local_porosity=eps)
        f += dr
        f = add_distributor_force(f, pos, radius, mat)
        f = add_wall_forces(f, pos, radius, mat)
        f = add_floor_force(f, pos, vel, radius, mat)
        pos, vel, _ = integrate(pos, vel, cp.zeros_like(vel), f, tq, radius, mat, DT, DAMP)

        # Hard post-integrate floor + wall enforcement (restitution <1 to damp, prevent tunneling/escape)
        # Ensures 100% of regolith stays inside vessel domain for meaningful bed height (mean z of contained bed)
        z = pos[:, 2]
        below = z < 0.0
        if cp.any(below):
            pos[below, 2] = 0.0
            vel[below, 2] = cp.abs(vel[below, 2]) * 0.80
        for ax in [0, 1]:
            p = pos[:, ax]
            below = p < 0.0
            if cp.any(below):
                pos[below, ax] = 0.0
                vel[below, ax] = cp.abs(vel[below, ax]) * 0.80
            over = p > BOX
            if cp.any(over):
                pos[over, ax] = float(BOX)
                vel[over, ax] = -cp.abs(vel[over, ax]) * 0.80

        if (s + 1) % 500 == 0:
            reg_mask = (mat == 0)
            reg_z = pos[reg_mask, 2]
            bed = float(cp.mean(reg_z) * 1000)
            bed_std = float(cp.std(reg_z) * 1000)
            zmax = float(cp.max(reg_z) * 1000)
            inside = float(cp.sum((pos[:, 0] >= 0) & (pos[:, 0] <= BOX) & (pos[:, 1] >= 0) & (pos[:, 1] <= BOX) & (pos[:, 2] >= 0)) ) / len(pos) * 100.0
            print(f"  step {step+1:5d} bed={bed:.2f}±{bed_std:.2f} mm (zmax={zmax:.0f}mm inside={inside:.1f}%)")

        if (s + 1) % CHECKPOINT_EVERY == 0:
            save_checkpoint(pos, vel, radius, mat, step + 1, prefix)
            print(f"  [checkpoint saved]")

    save_checkpoint(pos, vel, radius, mat, start_step + steps_to_do, prefix)
    reg_mask = (mat == 0)
    reg_z = pos[reg_mask, 2]
    bed = float(cp.mean(reg_z) * 1000)
    bed_std = float(cp.std(reg_z) * 1000)
    inside = float(cp.sum((pos[:, 0] >= 0) & (pos[:, 0] <= BOX) & (pos[:, 1] >= 0) & (pos[:, 1] <= BOX) & (pos[:, 2] >= 0))) / len(pos) * 100.0
    print(f"{prefix} done. Final bed: {bed:.2f}±{bed_std:.2f} mm (inside={inside:.1f}%)")

if __name__ == "__main__":
    run_rung1(with_iron=True)
    run_rung1(with_iron=False)
