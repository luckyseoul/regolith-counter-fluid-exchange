#!/usr/bin/env python3
"""Quick validation of the contact kernel on the V100."""

import cupy as cp
import numpy as np
import sys
sys.path.append(str(__import__('pathlib').Path(__file__).parents[2] / "common"))
from dem_kernels import compute_forces, integrate

# Simple two-particle test (one regolith, one iron)
pos = cp.array([[0.0, 0.0, 0.0], [0.001, 0.0, 0.0]], dtype=cp.float32)
vel = cp.zeros((2, 3), dtype=cp.float32)
omega = cp.zeros((2, 3), dtype=cp.float32)
radius = cp.array([50e-6, 0.002], dtype=cp.float32)
mat = cp.array([0, 1], dtype=cp.int32)

for i in range(500):
    f, t = compute_forces(pos, vel, omega, radius, mat, 1e-6)
    pos, vel, omega = integrate(pos, vel, omega, f, t, radius, mat, 1e-6, damping=0.0)
    
    if i % 100 == 0:
        print(f"Step {i}: dist = {cp.linalg.norm(pos[1]-pos[0]):.6e} m")

print("Contact kernel test finished.")