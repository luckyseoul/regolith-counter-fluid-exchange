#!/usr/bin/env python3
"""
Rung 2 using custom GPU DEM (CuPy on V100)
Bimodal regolith + cohesion + iron shot at 0.14 bar target.

This is the actual particle-level simulation replacing LIGGGHTS for now.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parents[2] / "common"))

from dem_kernels import compute_forces, integrate, DENSITY, GRAVITY

# =============================================================================
# Simulation parameters
# =============================================================================
P = 0.14                    # bar
DT = 1e-6                   # s (will be adjusted)
N_STEPS = 200_000
DUMP_EVERY = 5000

BOX_SIZE = 0.025            # m

# =============================================================================
# Particle generation (bimodal + iron)
# =============================================================================
def generate_particles():
    np.random.seed(42)
    
    # Approximate PSD from Rev 5.2
    n_fine = 6000
    n_coarse = 4000
    n_iron = 150
    
    fine_d = np.random.lognormal(np.log(18e-6), 0.65, n_fine)
    fine_d = np.clip(fine_d, 4e-6, 45e-6)
    
    coarse_d = np.random.lognormal(np.log(140e-6), 0.5, n_coarse)
    coarse_d = np.clip(coarse_d, 70e-6, 450e-6)
    
    iron_d = np.random.uniform(1.2e-3, 4.0e-3, n_iron)
    
    diameters = np.concatenate([fine_d, coarse_d, iron_d])
    mat = np.array([0]* (n_fine + n_coarse) + [1]*n_iron, dtype=np.int32)
    
    radii = diameters / 2.0
    
    # Place particles
    positions = []
    for r in radii:
        for _ in range(500):
            p = np.random.uniform(r, BOX_SIZE - r, 3)
            if all(np.linalg.norm(p - np.array(q[:3])) >= r + qq[3] + 1e-6 for q in positions):
                positions.append((*p, r))
                break
        else:
            positions.append((r, r, r, r))
    
    pos = np.array([p[:3] for p in positions], dtype=np.float32)
    rad = np.array([p[3] for p in positions], dtype=np.float32)
    
    # Velocities and angular velocities
    vel = np.zeros_like(pos)
    omega = np.zeros_like(pos)
    
    return cp.asarray(pos), cp.asarray(vel), cp.asarray(omega), cp.asarray(rad), cp.asarray(mat)

# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    print("Generating particles for Rung 2 at 0.14 bar...")
    pos, vel, omega, radius, mat_type = generate_particles()
    print(f"Total particles: {len(pos)}")
    
    # Simple damping as gas drag proxy at low pressure
    damping = 0.05
    
    for step in range(N_STEPS):
        force, torque = compute_forces(pos, vel, omega, radius, mat_type, DT)
        pos, vel, omega = integrate(pos, vel, omega, force, torque, radius, mat_type, DT, damping)
        
        if step % DUMP_EVERY == 0:
            print(f"Step {step:6d} | max vel = {cp.max(cp.linalg.norm(vel, axis=1)):.3e}")
    
    print("Rung 2 simulation finished.")