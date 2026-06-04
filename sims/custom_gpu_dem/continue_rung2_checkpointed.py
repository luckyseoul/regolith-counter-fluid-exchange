#!/usr/bin/env python3
"""
Rung 2 production continuation WITH CHECKPOINTS.
Saves state every 1500 steps so runs can survive harness timeouts / be resumed.
This is how we actually finish long physical-time Rung 2 evidence without stalling.

Run this, when it hits time limit, just re-run the same command — it will pick up the last checkpoint.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
import os
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

DT = 6.5e-7
CHECKPOINT_EVERY = 1500
TOTAL_TARGET_EXTRA_STEPS = 25000   # ~16 ms additional physical time goal
BOX = 0.015
U_G = 0.066
DAMP = 0.055

CHECKPOINT_DIR = Path("rung2_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

def count_iron_reg_contacts(pos, radius, mat_type):
    N = pos.shape[0]
    dx = pos[:, None, :] - pos[None, :, :]
    dist = cp.linalg.norm(dx, axis=2) + 1e-12
    rsum = radius[:, None] + radius[None, :]
    iron = mat_type == 1
    reg = mat_type == 0
    m = (dist < rsum * 1.03) & (cp.arange(N)[:, None] != cp.arange(N)[None, :])
    return int(cp.sum(m & iron[:, None] & reg[None, :]))

def save_checkpoint(pos, vel, radius, mat, step, prefix):
    cp.savez(CHECKPOINT_DIR / f"{prefix}_step{step:05d}.npz",
             pos=cp.asnumpy(pos), vel=cp.asnumpy(vel), radius=cp.asnumpy(radius),
             mat=cp.asnumpy(mat), step=step)

def load_latest_checkpoint(prefix):
    files = sorted(CHECKPOINT_DIR.glob(f"{prefix}_step*.npz"))
    if not files:
        return None, 0
    latest = files[-1]
    d = np.load(latest, allow_pickle=True)
    print(f"Resuming from checkpoint {latest.name} (step {int(d['step'])})")
    return (cp.asarray(d['pos']), cp.asarray(d['vel']),
            cp.asarray(d['radius']), cp.asarray(d['mat']), int(d['step']))

def run_one_case(state_file, prefix, is_iron=True):
    print(f"\n=== Rung 2 Checkpointed Continuation: {prefix} ===")
    ck = load_latest_checkpoint(prefix)
    if ck[0] is not None:
        pos, vel, radius, mat, start_step = ck
    else:
        d = np.load(state_file, allow_pickle=True)
        pos = cp.asarray(d['pos'])
        vel = cp.asarray(d['vel'])
        radius = cp.asarray(d['radius'])
        mat = cp.asarray(d.get('mat_type', d.get('mat')))
        start_step = 0

    n_iron = int(cp.sum(mat == 1))
    steps_to_do = TOTAL_TARGET_EXTRA_STEPS - start_step
    if steps_to_do <= 0:
        print("Already at target steps for this case.")
        return

    print(f"Starting at step {start_step}, target extra {steps_to_do} steps ({n_iron} iron)")

    t0 = time.time()
    for s in range(steps_to_do):
        step = start_step + s
        f, tq = compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        eps = estimate_local_porosity(pos, radius, BOX)
        dr = compute_drag(vel, radius, mat, U_g=U_G, local_porosity=eps)
        f += dr

        pos, vel, _ = integrate(pos, vel, cp.zeros_like(vel), f, tq, radius, mat, DT, DAMP)

        if (s + 1) % 300 == 0:
            bed = float(cp.mean(pos[mat==0, 2]) * 1000)
            ironh = float(cp.mean(pos[mat==1, 2]) * 1000) if n_iron > 0 else 0
            print(f"  step {step+1:5d} bed={bed:6.2f} iron_h={ironh:6.2f}")

        if (s + 1) % CHECKPOINT_EVERY == 0:
            save_checkpoint(pos, vel, radius, mat, step + 1, prefix)
            print(f"  [checkpoint saved at step {step+1}]")

    # final checkpoint + summary
    save_checkpoint(pos, vel, radius, mat, start_step + steps_to_do, prefix)
    wall = time.time() - t0
    bed_final = float(cp.mean(pos[mat==0, 2]) * 1000)
    print(f"{prefix} done in {wall:.1f}s. Final bed: {bed_final:.2f} mm")

if __name__ == "__main__":
    print("RCFX Rung 2 — Checkpointed production continuation (resume-safe)")
    # With iron (main)
    run_one_case("rung2_3000p_with_drag.npz", "with_iron_rung2", is_iron=True)
    # No-iron control
    run_one_case("rung2_3000p_noiron_with_drag.npz", "noiron_rung2", is_iron=False)

    print("\nRung 2 checkpointed runs complete (or checkpointed). Post-process the latest checkpoints for final EMI.")
    print("When ready, move to Rung 3 (run_rung3_eds_demo.py already written).")
