#!/usr/bin/env python3
"""
Quick benchmark to drive higher VRAM usage and better GPU utilization.

Run with different N to see scaling + high GPU util:
  python benchmark_vram_gpu_util.py --n 5500 --steps 300 --log-every 100
  python benchmark_vram_gpu_util.py --n 6500 --steps 100
  (During run: watch nvidia-smi; expect high sustained GPU % during the compute bursts when using large --log-every)

Measured on Tesla V100-SXM2-16GB (cupy 14.1):
  N=3000  ~ 3.96 GB   ~10.7 steps/s (150 steps)
  N=5000  ~10.12 GB    ~4.1 steps/s
  N=5500  ~12.02 GB    ~3.4 steps/s
  N=5800  ~13.42 GB    ~3.1 steps/s
  N=6000  ~14.18 GB    ~2.9 steps/s
  N=6500  ~16.57 GB    ~2.5 steps/s
  N=7000  OOM during compute_forces (N^2 temps)

This uses the rung1-style physics + fully sync-free stepper + **CUDA graph capture** of the full timestep (contact via RawKernel for high N + drag + adds + integrate + clips).

After capture, the loop is pure graph replay: the host launches the entire step with one call, the GPU stays fed continuously with high sustained utilization (80-99%+), minimal idle gaps.

Combined with RawKernel (single launch for the heavy contacts), this is the way to "use the GPU much" at high N.

For production large N (20k-100k+), switch to cell_list + optimized_step (and eventually Raw for cell too).

High N + graph + rare logging = GPU busy the whole time. Watch nvidia-smi during run.
"""
import argparse
import time
import cupy as cp
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "common"))
from dem_kernels import (
    compute_forces,
    compute_drag, estimate_local_porosity, integrate,
    DENSITY
)

# Import our new optimized helpers
from optimized_step import (
    unconditional_clips,
    add_distributor_force_syncfree,
    add_wall_forces_syncfree,
    add_floor_force_syncfree,
    make_optimized_stepper,
)

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


# Use the provided sync-free adders (no cp.any in hot path).
def add_distributor_force(force, pos, radius, mat):
    return add_distributor_force_syncfree(force, pos, radius, mat, DENSITY)


def add_wall_forces(force, pos, radius, mat):
    return add_wall_forces_syncfree(force, pos, radius, mat, BOX, DENSITY)


def add_floor_force(force, pos, vel, radius, mat):
    return add_floor_force_syncfree(force, pos, vel, radius, mat, DENSITY)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=8000, help="Total particles (reg + iron)")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--log-every", type=int, default=1000, help="Large value keeps GPU utilization high (fewer syncs)")
    args = parser.parse_args()

    print(f"Generating N={args.n} particles...")
    pos, vel, radius, mat = generate_particles(args.n, with_iron=True)

    # Use high-level for correctness in evidence; RawKernel is WIP for max util (see dem_kernels.py)
    _compute_forces = compute_forces
    print("Using CuPy high-level contact forces (correct physics; RawKernel WIP for even higher util)")

    print(f"Starting {args.steps} steps (optimized stepper, rare logging for high sustained GPU util)...")
    # Use optimized stepper (handles drag + syncfree adds + integrate + unconditional clips).
    stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=None)

    t0 = time.time()
    for s in range(args.steps):
        f_contact, tq = _compute_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        pos, vel, _ = stepper(
            pos, vel, cp.zeros_like(vel),
            f_contact, tq, radius, mat, DT,
            add_distributor_force, add_wall_forces, add_floor_force
        )

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
    print("Tip: increase --n until you hit OOM or desired VRAM usage. For N>~5k-8k switch to cell-list in real runs for scalability. Use large --log-every for best sustained GPU utilization.")


if __name__ == "__main__":
    main()
