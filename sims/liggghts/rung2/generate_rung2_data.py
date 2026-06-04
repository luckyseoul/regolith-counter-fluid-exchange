#!/usr/bin/env python3
"""
Generate particle data for Rung 2 at 0.14 bar.
Bimodal lunar regolith + iron shot with realistic numbers for initial validation runs.
"""

import numpy as np
import random

# Box size for validation run (small enough to run reasonably fast)
BOX = 0.025   # 2.5 cm

# Target particle count (start modest for validation)
N_REGOLITH = 45000
N_IRON = 350

# Regolith PSD (simplified from spec)
# ~35% fines (very cohesive), rest coarser
fine_diam = np.random.lognormal(np.log(20e-6), 0.7, int(N_REGOLITH * 0.35))
fine_diam = np.clip(fine_diam, 3e-6, 50e-6)

coarse_diam = np.random.lognormal(np.log(150e-6), 0.5, int(N_REGOLITH * 0.65))
coarse_diam = np.clip(coarse_diam, 60e-6, 500e-6)

reg_diam = np.concatenate([fine_diam, coarse_diam])
np.random.shuffle(reg_diam)

iron_diam = np.random.uniform(0.0012, 0.0045, N_IRON)

all_diam = np.concatenate([reg_diam, iron_diam])
types = np.array([1]*len(reg_diam) + [2]*len(iron_diam))

# Radii
radii = all_diam / 2.0

# Simple random sequential addition (will have some overlaps → LIGGGHTS will relax)
positions = []
print("Placing particles...")
for i, r in enumerate(radii):
    placed = False
    for _ in range(300):
        x = random.uniform(r, BOX - r)
        y = random.uniform(r, BOX - r)
        z = random.uniform(r, BOX - r)
        if all(np.linalg.norm(np.array([x,y,z]) - np.array(p[:3])) >= (r + p[3] + 1e-6) for p in positions):
            positions.append([x, y, z, r])
            placed = True
            break
    if not placed:
        # fallback
        positions.append([random.uniform(r, BOX-r), random.uniform(r, BOX-r), random.uniform(r, BOX-r), r])

print(f"Placed {len(positions)} particles")

# Write LIGGGHTS data file
with open("data/rung2_particles.data", "w") as f:
    f.write("LIGGGHTS data file for RCFX Rung 2 (0.14 bar validation)\n\n")
    f.write(f"{len(positions)} atoms\n")
    f.write("2 atom types\n\n")
    f.write(f"0.0 {BOX} xlo xhi\n0.0 {BOX} ylo yhi\n0.0 {BOX} zlo zhi\n\n")
    f.write("Atoms\n\n")

    for i, (x, y, z, r) in enumerate(positions, 1):
        typ = types[i-1]
        dens = 7870.0 if typ == 2 else 3100.0
        f.write(f"{i} {typ} {dens} {r} {x} {y} {z} 0 0 0\n")

print("Wrote data/rung2_particles.data")