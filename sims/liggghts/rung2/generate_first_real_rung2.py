#!/usr/bin/env python3
"""
Generate a more realistic (but still manageable) data file for Rung 2 on the V100.
Target: ~150k-300k particles for initial production Rung 2 runs.
"""

import numpy as np
import random

box_size = 0.06           # 8 cm box (reasonable for V100 with ~200k particles)
target_particles = 75000

# Regolith PSD (from Rev 5.2, simplified)
fine_frac = 0.35
n_fine = int(target_particles * fine_frac)
n_coarse = target_particles - n_fine

# Diameters
fine_d = np.random.lognormal(np.log(22e-6), 0.65, n_fine)
fine_d = np.clip(fine_d, 4e-6, 55e-6)

coarse_d = np.random.lognormal(np.log(160e-6), 0.55, n_coarse)
coarse_d = np.clip(coarse_d, 70e-6, 550e-6)

diameters = np.concatenate([fine_d, coarse_d])
np.random.shuffle(diameters)

# Iron shot (roughly 1-2% by volume for agitation)
n_iron = int(target_particles * 0.012)
iron_d = np.random.uniform(0.0015, 0.004, n_iron)

all_diam = np.concatenate([diameters, iron_d])
types = [1]*len(diameters) + [2]*len(iron_d)

# Simple insertion (will need relaxation)
positions = []
radii = list(all_diam / 2)

print("Generating positions (this can take a minute for large N)...")
for i, r in enumerate(radii):
    placed = False
    for attempt in range(200):
        x = random.uniform(r, box_size - r)
        y = random.uniform(r, box_size - r)
        z = random.uniform(r, box_size - r)
        if all(np.linalg.norm([x-px, y-py, z-pz]) >= (r + pr + 5e-7) for px,py,pz,pr in positions):
            positions.append((x, y, z, r))
            placed = True
            break
    if not placed:
        # If we can't place, just put it somewhere (will overlap, LIGGGHTS will relax)
        positions.append((random.uniform(r, box_size-r), random.uniform(r, box_size-r), random.uniform(r, box_size-r), r))

print(f"Generated {len(positions)} particles in {box_size}m box")

# Write data file
with open("data/realistic_rung2.data", "w") as f:
    f.write("LIGGGHTS data for RCFX Rung 2 (realistic size)\n\n")
    f.write(f"{len(positions)} atoms\n2 atom types\n\n")
    f.write(f"0 {box_size} xlo xhi\n0 {box_size} ylo yhi\n0 {box_size} zlo zhi\n\n")
    f.write("Atoms\n\n")
    for i, (x,y,z,r) in enumerate(positions, 1):
        typ = types[i-1]
        dens = 7870.0 if typ == 2 else 3100.0
        f.write(f"{i} {typ} {dens} {r} {x} {y} {z} 0 0 0\n")

print("Wrote data/realistic_rung2.data")