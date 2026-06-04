#!/usr/bin/env python3
"""
Rung 0 backfill — Gas + Distributor performance at low pressure (0.14 bar conditions).
Uses the EXACT same physics stack (kernels, drag, DT, materials, containment forces) as the validated Rung 1/Rung 2 contained runs for same-physics consistency and patent defensibility.
Distributor modeled as strong upward body force near z=0 (high distributor ΔP).
Measures bed height variance and dead zone fraction (vel<0.8m/s proxy) as uniformity proxy.
Full containment (walls + floor + v2 dist + post clips 0.8 rest) + numeric loader + inside=100.0% logging enforced.
Only post-containment (inside=100.0%, zmin>=0) .npz numbers citable for distributor uniformity / 0.14 bar claims.
Checkpointed 1500-step .npz resume pattern (matches Rung 1/2).
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity, DENSITY

DT = 6.5e-7
CHECKPOINT_EVERY = 1500
TOTAL_TARGET_STEPS = 500000  # forced long backfill run
BOX = 0.016
U_G = 0.055          # representative for 0.14 bar conditions
DAMP = 0.04

CHECKPOINT_DIR = Path("rung0_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

def add_distributor_force(force, pos, radius, mat):
    """Body-force acceleration (upward) near bottom to simulate high distributor ΔP / gas injection support.
    Treated as acceleration (m/s^2) and scaled by particle mass -> force (N).
    (Corrected from earlier constant-to-force version that caused unphysical blasts for small particles.)
    """
    z = pos[:, 2]
    dist_strength = 2.8 * cp.exp(-z / 0.003)   # acceleration (m/s^2)
    mass = DENSITY[mat] * (4.0 / 3.0 * cp.pi * radius**3)
    force[:, 2] += dist_strength * mass
    return force


def add_wall_forces(force, pos, radius, mat):
    """Lateral box walls (x/y containment within [0, BOX]) to keep particles inside the simulated vessel.
    Prevents radial escape that makes mean-z 'bed height' meaningless (CoM of spray instead of fluidized bed).
    Uses acceleration-style (scaled by mass) for consistency with distributor; stiff but stable.
    Same as validated in Rung 1/Rung 2 contained runs.
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
    Same as validated in Rung 1 contained runs for 100% inside guarantee.
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


def save_checkpoint(pos, vel, radius, mat, step):
    cp.savez(CHECKPOINT_DIR / f"rung0_step{step:05d}.npz",
             pos=cp.asnumpy(pos), vel=cp.asnumpy(vel),
             radius=cp.asnumpy(radius), mat=cp.asnumpy(mat), step=step)

def load_latest_checkpoint():
    files = list(CHECKPOINT_DIR.glob("rung0_step*.npz"))
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
    print(f"Resuming Rung 0 from {latest.name} (step {int(d['step'])})")
    return (cp.asarray(d['pos']), cp.asarray(d['vel']),
            cp.asarray(d['radius']), cp.asarray(d['mat']), int(d['step']))

def run_rung0():
    print("\n=== Rung 0 Checkpointed Distributor Test (0.14 bar conditions, contained physics) ===")
    ck = load_latest_checkpoint()
    if ck[0] is not None:
        pos, vel, radius, mat, start_step = ck
    else:
        np.random.seed(7)
        n = 1800
        d = np.random.uniform(60e-6, 380e-6, n)
        radius = d / 2.0
        mat = np.zeros(n, dtype=np.int32)
        pos = np.random.rand(n, 3).astype(np.float32) * (BOX * 0.9)
        pos[:, 2] *= 0.35
        pos = np.clip(pos, radius[:, None] + 1e-6, BOX - radius[:, None] - 1e-6)
        vel = cp.zeros((n, 3), dtype=cp.float32)
        radius = cp.asarray(radius, dtype=cp.float32)
        mat = cp.asarray(mat)
        pos = cp.asarray(pos)
        start_step = 0

    steps_to_do = TOTAL_TARGET_STEPS - start_step
    # Force long backfill - do not early exit
    print(f"Running {steps_to_do} steps from {start_step} (FORCED LONG BACKFILL)")
    print("Containment active (walls+floor+dist v2+post 0.8); logging inside=100.0% + zmin; only these citable. Same kernels/drag as Rung1/Rung2.")

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

        # Hard post-integrate floor + wall enforcement (restitution 0.8) - ensures 100% inside for defensible bed/dead-zone stats
        # Same pattern as Rung 1 contained runs (zmin>0, inside=100.0% always after fix)
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
            bed_mean = float(cp.mean(pos[:, 2]) * 1000)
            bed_std = float(cp.std(pos[:, 2]) * 1000)
            zmax = float(cp.max(pos[:, 2]) * 1000)
            zmin = float(cp.min(pos[:, 2]) * 1000)
            inside = float(cp.sum((pos[:, 0] >= 0) & (pos[:, 0] <= BOX) & (pos[:, 1] >= 0) & (pos[:, 1] <= BOX) & (pos[:, 2] >= 0))) / len(pos) * 100.0
            low_v = cp.sum(cp.linalg.norm(vel, axis=1) < 0.8)
            dead_frac = float(low_v) / len(pos)
            print(f"  step {step+1:5d} bed={bed_mean:.2f}±{bed_std:.2f} mm (zmax={zmax:.0f}mm zmin={zmin:.2f}mm inside={inside:.1f}%) dead%={dead_frac*100:.1f}")

        if (s + 1) % CHECKPOINT_EVERY == 0:
            save_checkpoint(pos, vel, radius, mat, step + 1)
            print(f"  [checkpoint saved]")

    save_checkpoint(pos, vel, radius, mat, start_step + steps_to_do)
    bed_final = float(cp.mean(pos[:, 2]) * 1000)
    bed_std_final = float(cp.std(pos[:, 2]) * 1000)
    zmax_final = float(cp.max(pos[:, 2]) * 1000)
    zmin_final = float(cp.min(pos[:, 2]) * 1000)
    inside_final = float(cp.sum((pos[:, 0] >= 0) & (pos[:, 0] <= BOX) & (pos[:, 1] >= 0) & (pos[:, 1] <= BOX) & (pos[:, 2] >= 0))) / len(pos) * 100.0
    low_v_final = cp.sum(cp.linalg.norm(vel, axis=1) < 0.8)
    dead_final = float(low_v_final) / len(pos)
    print(f"rung0 done. Final bed: {bed_final:.2f}±{bed_std_final:.2f} mm (zmax={zmax_final:.0f}mm zmin={zmin_final:.2f}mm inside={inside_final:.1f}%) dead%={dead_final*100:.1f}")

if __name__ == "__main__":
    run_rung0()
