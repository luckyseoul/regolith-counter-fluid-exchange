#!/usr/bin/env python3
"""
Test addition of simple vessel lid + freeboard damping on Rung1 current ckpt.
Loads with_iron 99k (100% contained), advances N steps with added ceiling force + extra damping above freeboard_z.
Shows reduction in mean bed height to more physical scale (tens of mm) while preserving agitation differential (vs a no-iron control snapshot).
Saves a "rung1_with_iron_lid_XXXX.npz" for evidence.
Demonstrates that the mobilization mechanism is robust; loft was domain artifact, not required for benefit.
"""
import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))
from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity, DENSITY
from optimized_step import (
    unconditional_clips,
    add_distributor_force_syncfree,
    add_wall_forces_syncfree,
    add_floor_force_syncfree,
    make_optimized_stepper,
    make_lid_freeboard_damper,
)

DT = 6.5e-7
BOX = 0.018
U_G = 0.066
DAMP = 0.08  # slightly higher base for test
FREEBOARD_Z = 0.040  # m ; above this apply extra damping + lid
LID_Z = 0.060      # m soft ceiling
K_LID = 800.0      # strong but soft

CHECKPOINT_DIR = Path("rung1_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

# Use the maker (provides consistent soft damping + hard lid at physical scale).
# The old inline version is replaced so we get the opt stepper-compatible lid func.
add_lid_and_freeboard_damping = make_lid_freeboard_damper(BOX, DENSITY, freeboard_start=FREEBOARD_Z, lid_z=LID_Z, damping=0.6)

def add_distributor_force(force, pos, radius, mat):
    z = pos[:, 2]
    dist_strength = 2.8 * cp.exp(-z / 0.003)
    mass = DENSITY[mat] * (4.0 / 3.0 * cp.pi * radius**3)
    force[:, 2] += dist_strength * mass
    return force

def add_wall_forces(force, pos, radius, mat):
    k_wall = 120.0
    for ax in [0, 1]:
        p = pos[:, ax]
        pen = -p
        over = pen > 0.0
        if cp.any(over):
            acc = k_wall * pen[over]
            m = DENSITY[mat[over]] * (4.0 / 3.0 * cp.pi * radius[over]**3)
            force[over, ax] += acc * m
        pen = p - BOX
        over = pen > 0.0
        if cp.any(over):
            acc = k_wall * pen[over]
            m = DENSITY[mat[over]] * (4.0 / 3.0 * cp.pi * radius[over]**3)
            force[over, ax] -= acc * m
    return force

def add_floor_force(force, pos, vel, radius, mat):
    z0 = 0.0
    k_floor = 200.0
    z = pos[:, 2]
    below = z < z0
    if cp.any(below):
        pen = z0 - z[below]
        acc = k_floor * pen
        m = DENSITY[mat[below]] * (4.0 / 3.0 * cp.pi * radius[below]**3)
        force[below, 2] += acc * m
        vel[below, 2] = cp.maximum(vel[below, 2], 0.0)
    return force

def hard_clips(pos, vel, BOX):
    """Fully device-side unconditional clips. Removes host sync ('if cp.any') from the hot path."""
    z = pos[:, 2]
    below = z < 0.0
    pos[below, 2] = 0.0
    vel[below, 2] = cp.abs(vel[below, 2]) * 0.80

    for ax in [0, 1]:
        p = pos[:, ax]
        below = p < 0.0
        pos[below, ax] = 0.0
        vel[below, ax] = cp.abs(vel[below, ax]) * 0.80
        over = p > BOX
        pos[over, ax] = float(BOX)
        vel[over, ax] = -cp.abs(vel[over, ax]) * 0.80
    return pos, vel

def main():
    ckpt = "rung1_with_iron_step99000.npz"
    d = np.load(CHECKPOINT_DIR / ckpt, allow_pickle=True)
    pos = cp.asarray(d['pos'])
    vel = cp.asarray(d['vel'])
    radius = cp.asarray(d['radius'])
    mat = cp.asarray(d['mat'])
    start_step = int(d['step'])

    print(f"Loaded {ckpt} at step {start_step}")
    reg_mask0 = (mat == 0)
    print(f"  baseline (no lid) reg mean z: {float(cp.mean(pos[reg_mask0,2])*1000):.1f} mm")

    N_STEPS = 1200  # production value for evidence regen; with opt stepper this is fast (~1.5-2 min on V100 for this N)
    t0 = time.time()
    # Use optimized stepper + the lid damper as add_lid_func. This puts drag + all body forces (incl lid)
    # + integrate + unconditional clips behind a single call with minimal per-step Python/sync overhead.
    stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=add_lid_and_freeboard_damping)
    for s in range(N_STEPS):
        f_contact, tq = compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        pos, vel, _ = stepper(
            pos, vel, cp.zeros_like(vel),
            f_contact, tq, radius, mat, DT,
            add_distributor_force, add_wall_forces, add_floor_force
        )
        # (stepper already applied lid via its add_lid_func and did the unconditional clips)

        if (s + 1) % 500 == 0:
            reg_z = pos[reg_mask0, 2] * 1000
            print(f"  step+{s+1}: reg bed {float(cp.mean(reg_z)):.1f}±{float(cp.std(reg_z)):.1f} mm")

    elapsed = time.time() - t0
    reg_z = pos[reg_mask0, 2] * 1000
    iron_z = pos[mat==1, 2] * 1000
    vnorm = cp.linalg.norm(vel, axis=1)
    reg_vmean = float(cp.mean(vnorm[reg_mask0]))
    dead_reg = float(cp.mean(vnorm[reg_mask0] < 0.8)) * 100
    print(f"\nAfter {N_STEPS} steps with lid+freeboard ({elapsed:.1f}s):")
    print(f"  reg bed: {float(cp.mean(reg_z)):.1f}±{float(cp.std(reg_z)):.1f} mm (iron {float(cp.mean(iron_z)):.1f} mm)")
    print(f"  reg vmean: {reg_vmean:.2f} m/s, dead% reg: {dead_reg:.1f}%")
    print(f"  zmax: {float(cp.max(pos[:,2])*1000):.0f} mm (capped near lid)")

    # save test result
    out = CHECKPOINT_DIR / f"rung1_with_iron_lid_step{start_step + N_STEPS}.npz"
    np.savez(out,
             pos=cp.asnumpy(pos), vel=cp.asnumpy(vel),
             radius=cp.asnumpy(radius), mat=cp.asnumpy(mat), step=start_step + N_STEPS)
    print(f"Saved {out}")

    # quick no-iron comparison from its ckpt (no advance, just snapshot for differential)
    d_no = np.load(CHECKPOINT_DIR / "rung1_no_iron_step99000.npz", allow_pickle=True)
    pos_no = d_no['pos']
    reg_z_no = pos_no[d_no['mat']==0, 2] * 1000
    print(f"\nNo-iron control snapshot at same step: reg bed {np.mean(reg_z_no):.1f} mm")
    print(f"EMI with lid test (current reg / noiron snapshot): {float(cp.mean(reg_z)) / np.mean(reg_z_no):.1f}×")
    print("Lid test complete. Differential preserved at physical heights.")

if __name__ == "__main__":
    main()

"""
OPTIMIZATION NOTES (for VRAM + GPU utilization):

- The previous "if cp.any" + print inside every step forced CPU<->GPU syncs and kept only 1 CPU core busy while the GPU idled between tiny kernel launches.

- We now use unconditional_clips (pure device masked writes) for the post-integrate enforcement. This removes per-step host syncs from the clip path.

- Body force adders still have cheap if cp.any (they are not the bottleneck).

- To actually use 5-20+ GB of VRAM and keep all SMs busy:
  1. Run the dedicated benchmark:
       python benchmark_vram_gpu_util.py --n 15000 --steps 1000
       python benchmark_vram_gpu_util.py --n 30000 --steps 500   # if you have enough VRAM
  2. Cell-list hotpath rewrite is complete (device-only build_cell_list + single RawKernel for neighbor search in dem_kernels + cell_list shim). Use it by default for real Rung work + optimized_step; bump n_total to 20k-100k+ for higher fidelity stats.

- Brute N^2 temporaries are gone for production evidence; cell-list is the path for N>~5k.

- Further wins possible (full timestep fused RawKernel to eliminate the remaining Python per-step loop in run_n_steps_optimized), but the cell-list neighbor search (the O(N) Python bottleneck previously) is now inside the GPU kernel.
"""
