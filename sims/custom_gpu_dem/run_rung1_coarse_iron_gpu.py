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

from dem_kernels import compute_forces, compute_forces_raw, integrate, compute_drag, estimate_local_porosity, DENSITY
# NOTE: high-N evidence path (migrate_rung1_highn, benchmark) now defaults to compute_forces_raw for sustained GPU util.
# This coarse/low-N runner kept on high-level compute_forces for compatibility with old ckpt style.
from optimized_step import (
    unconditional_clips,
    add_distributor_force_syncfree,
    add_wall_forces_syncfree,
    add_floor_force_syncfree,
    make_optimized_stepper,
)  # sync-free everything for hot loop (no GIL peg / host syncs per step)

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


# Thin wrappers over the sync-free (no cp.any, no host sync per step) implementations.
# The entire body-force + integrate + clip path now runs without Python-level branches
# that force device syncs. This directly addresses "pegging a single cpu core" while
# the GPU was starved; larger N (via benchmark) drives VRAM to 12-16 GB.
def add_distributor_force(force, pos, radius, mat):
    return add_distributor_force_syncfree(force, pos, radius, mat, DENSITY)


def add_wall_forces(force, pos, radius, mat):
    return add_wall_forces_syncfree(force, pos, radius, mat, BOX, DENSITY)


def add_floor_force(force, pos, vel, radius, mat):
    return add_floor_force_syncfree(force, pos, vel, radius, mat, DENSITY)


def generate_coarse_particles(n_total=6500, with_iron=True):  # high-N migration default (full VRAM ~16.5GB); was 2600 low-N historical
    np.random.seed(42)
    n_iron = int(0.07 * n_total) if with_iron else 0  # 7% for high-N consistency with benchmark/migration
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

    # Use the optimized stepper (drag + body forces + integrate + unconditional clips)
    # with the local sync-free adders. This keeps the Python per-step overhead minimal
    # and eliminates host syncs from the inner loop.
    stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=None)

    for s in range(steps_to_do):
        step = start_step + s
        f_contact, tq = compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        # Let the optimized stepper handle drag (porosity + compute_drag) + adds + integrate + clips.
        # This keeps a single source of truth for the non-contact physics and minimizes sync points.
        pos, vel, _ = stepper(
            pos, vel, cp.zeros_like(vel),   # omega slot (coarse rung1 does not track angular velocity meaningfully)
            f_contact, tq, radius, mat, DT,
            add_distributor_force, add_wall_forces, add_floor_force
        )
        # Note: stepper already did unconditional_clips inside.

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
