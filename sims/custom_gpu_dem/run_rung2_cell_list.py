#!/usr/bin/env python3
"""
Rung 2 production runner using cell-list accelerated custom GPU DEM.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path("common").resolve()))

import cupy as cp
import numpy as np
import time

from cell_list import compute_forces_cell_list
from dem_kernels import integrate  # reuse the integrator

print("=== Rung 2 Cell-List GPU DEM ===")

N = 4200
BOX = 0.018
DT = 1.2e-9
STEPS = 1200
DAMP = 0.25
CELL_SIZE = 0.0022   # tuned for ~20-3500um particles + iron

np.random.seed(99)

# Bimodal regolith + iron (Rung 2 0.14 bar conditions)
n_fine = 3000
n_coarse = 1000
n_iron = 200
diam = np.concatenate([
    np.random.lognormal(np.log(19e-6), 0.52, n_fine),
    np.random.lognormal(np.log(82e-6), 0.39, n_coarse),
    np.random.uniform(0.0018, 0.0033, n_iron)
])
mat = np.array([0] * (n_fine + n_coarse) + [1] * n_iron, dtype=np.int32)
r = diam / 2.0

# Simple placement
pos = np.random.rand(N, 3).astype(np.float32) * BOX
pos = np.clip(pos, r[:, None] + 1e-6, BOX - r[:, None] - 1e-6)

vel = np.zeros((N, 3), dtype=np.float32)
omega = np.zeros((N, 3), dtype=np.float32)

pos = cp.asarray(pos)
vel = cp.asarray(vel)
omega = cp.asarray(omega)
radius = cp.asarray(r, dtype=cp.float32)
mat_type = cp.asarray(mat)

print(f"Running {N} particles ({n_iron} iron) for {STEPS} steps...")

start = time.time()
for step in range(STEPS):
    f, t = compute_forces_cell_list(pos, vel, omega, radius, mat_type, DT, CELL_SIZE, BOX)
    pos, vel, omega = integrate(pos, vel, omega, f, t, radius, mat_type, DT, DAMP)

    if step % 200 == 0:
        v = cp.linalg.norm(vel, axis=1)
        iron_v = v[mat_type == 1]
        reg_v = v[mat_type == 0]
        print(f"step {step:4d} | max={float(cp.max(v)):7.1f} | iron_mean={float(cp.mean(iron_v)):6.1f} | reg_mean={float(cp.mean(reg_v)):.2f}")

print(f"\nCompleted in {time.time() - start:.1f} s")

final_v = cp.linalg.norm(vel, axis=1)
print(f"Final max |v| = {float(cp.max(final_v)):.1f} m/s")
print(f"Iron mean |v| = {float(cp.mean(final_v[mat_type==1])):.1f} m/s")

cp.savez("rung2_cell_list_8500p.npz",
         pos=cp.asnumpy(pos),
         vel=cp.asnumpy(vel),
         radius=cp.asnumpy(radius),
         mat=cp.asnumpy(mat_type))
print("Saved rung2_cell_list_8500p.npz")