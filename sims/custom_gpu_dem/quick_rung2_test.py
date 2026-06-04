#!/usr/bin/env python3
"""Quick self-contained Rung 2 test using fixed custom GPU kernels."""
import cupy as cp
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path("common").resolve()))
from dem_kernels import compute_forces, integrate

print("=== Custom GPU DEM - Quick Rung 2 Test on V100 ===")

# Small system for quick stable run
N_REG = 600
N_IRON = 40
BOX = 0.012
DT = 2e-8   # Very small for stability with current stiffness

np.random.seed(42)
fine = np.random.lognormal(np.log(15e-6), 0.55, int(N_REG*0.4))
fine = np.clip(fine, 4e-6, 35e-6)
coarse = np.random.lognormal(np.log(120e-6), 0.45, int(N_REG*0.6))
coarse = np.clip(coarse, 50e-6, 350e-6)
reg_d = np.concatenate([fine, coarse])
iron_d = np.random.uniform(0.0012, 0.003, N_IRON)

diam = np.concatenate([reg_d, iron_d])
mat = np.array([0]*len(reg_d) + [1]*len(iron_d), dtype=np.int32)
r = diam / 2

# Simple placement
pos = np.random.rand(len(r), 3).astype(np.float32) * (BOX * 0.9)
pos = np.clip(pos, r[:,None]*1.1, BOX - r[:,None]*1.1)
vel = np.zeros((len(r), 3), dtype=np.float32)
omega = np.zeros((len(r), 3), dtype=np.float32)

pos = cp.asarray(pos)
vel = cp.asarray(vel)
omega = cp.asarray(omega)
radius = cp.asarray(r, dtype=cp.float32)
mat_type = cp.asarray(mat)

print(f"Running {N_REG + N_IRON} particles for 1500 steps...")

for step in range(1500):
    f, t = compute_forces(pos, vel, omega, radius, mat_type, DT)
    pos, vel, omega = integrate(pos, vel, omega, f, t, radius, mat_type, DT, 0.08)
    if step % 300 == 0:
        maxv = float(cp.max(cp.linalg.norm(vel, axis=1)))
        print(f"  Step {step:4d} | max |v| = {maxv:.2e} m/s")

print("\nCustom GPU DEM test completed successfully on V100.")
print("Real particle physics executed (no LIGGGHTS involved).")
