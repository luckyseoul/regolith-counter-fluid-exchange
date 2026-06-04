#!/usr/bin/env python3
"""
Quick benchmark to drive higher VRAM usage and better GPU utilization.

Run with different N to see scaling:
  python benchmark_vram_gpu_util.py --n 8000 --steps 2000
  python benchmark_vram_gpu_util.py --n 20000 --steps 500

This uses the current (small) rung1-style physics but with larger N + the
unconditional-clip optimized loop.

On a 8-12GB card you should be able to go to N=30k-80k+ before OOM depending
on temporaries in compute_forces (brute O(N^2) uses a lot of temp memory).

For production large N, switch the runner to cell_list + the optimized_step helpers.
"""
import argparse
import time
import cupy as cp
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "common"))
from dem_kernels import (
    compute_forces, compute_drag, estimate_local_porosity, integrate,
    DENSITY
)

# Import our new optimized helpers
from optimized_step import unconditional_clips as unconditional_hard_clips  # the one without if-any

BOX = 0.018
U_G = 0.066
DAMP = 0.05
DT = 6.5e-7

def generate_particles(n_total=8000, with_iron=True, seed=42):
    np.random.seed(seed)
    n_iron = int(0.07 * n_total) if with_iron else 0
    n_reg = n_total - n_iron

    reg_diam = np.random.uniform(60e-6, 400e-6, n_reg)
    iron_diam = np.random.uniform(0.0018, 0.0033, n_iron) if n_iron > 0 else np.array([])

    all_diam = np.concatenate([reg_diam, iron_diam])
    mat = np.array([0] * n_reg + [1] * n_iron, dtype=np.int32)
    radii = all_diam / 2.0

    pos = np.random.rand(len(radii), 3).astype(np.float32) * (BOX * 0.9)
    pos[:, 2] *= 0.4
    pos = np.clip(pos, radii[:, None] + 1e-6, BOX - radii[:, None] - 1e-6)

    return (cp.asarray(pos),
            cp.zeros((len(radii), 3), dtype=cp.float32),
            cp.asarray(radii, dtype=cp.float32),
            cp.asarray(mat))


def add_distributor_force(force, pos, radius, mat):
    z = pos[:, 2]
    dist_strength = 2.8 * cp.exp(-z / 0.003)
    mass = DENSITY[mat] * (4.0 / 3.0 * cp.pi * radius**3)
    force[:, 2] += dist_strength * mass
    return force


def add_wall_forces(force, pos, radius, mat):
    """Sync-free (unconditional masked) wall forces."""
    k_wall = 120.0
    for ax in [0, 1]:
        p = pos[:, ax]
        pen = -p
        over = pen > 0.0
        # Always execute the kernel on the masked subset - CuPy handles it without host sync
        if cp.any(over):  # this one is acceptable (rare)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=8000, help="Total particles (reg + iron)")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--log-every", type=int, default=500)
    args = parser.parse_args()

    print(f"Generating N={args.n} particles (brute-force forces)...")
    pos, vel, radius, mat = generate_particles(args.n, with_iron=True)

    print(f"Starting {args.steps} steps...")
    t0 = time.time()
    for s in range(args.steps):
        f, tq = compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        eps = estimate_local_porosity(pos, radius, BOX)
        dr = compute_drag(vel, radius, mat, U_g=U_G, local_porosity=eps)
        f += dr
        f = add_distributor_force(f, pos, radius, mat)
        f = add_wall_forces(f, pos, radius, mat)
        f = add_floor_force(f, pos, vel, radius, mat)
        pos, vel, _ = integrate(pos, vel, cp.zeros_like(vel), f, tq, radius, mat, DT, DAMP)
        pos, vel = unconditional_hard_clips(pos, vel, BOX)   # optimized unconditional version

        if (s + 1) % args.log_every == 0:
            reg_mask = (mat == 0)
            bed = float(cp.mean(pos[reg_mask, 2]) * 1000)
            free, total = cp.cuda.runtime.memGetInfo()
            used_gb = (total - free) / 1e9
            print(f"  step {s+1:5d}  reg bed ~{bed:.1f} mm  (device ~{used_gb:.2f} / {total/1e9:.1f} GB)")

    elapsed = time.time() - t0
    free, total = cp.cuda.runtime.memGetInfo()
    used_gb = (total - free) / 1e9
    print(f"\nDone in {elapsed:.1f}s ({args.steps} steps, {args.steps/elapsed:.1f} steps/s)")
    print(f"Device memory at end: ~{used_gb:.2f} GB used / {total/1e9:.1f} GB total")
    print("Tip: increase --n until you hit OOM or desired VRAM usage. For N>~5k-8k switch to cell-list in real runs for scalability.")


if __name__ == "__main__":
    main()
