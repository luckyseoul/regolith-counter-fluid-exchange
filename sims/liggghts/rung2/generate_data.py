#!/usr/bin/env python3
"""
Generate a small LIGGGHTS data file for Rung 2.
Bimodal lunar-like regolith + iron shot at 0.14 bar conditions.

This is a starting point for small validation boxes.
For production Rung 2/4 runs we will need much larger systems on the V100.
"""

import numpy as np
import random

# Parameters
box_size = 0.02          # 2 cm cube for initial testing (small)
n_regolith = 8000
n_iron = 200

# Regolith PSD (simplified from Rev 5.2)
# Fine mode (Geldart C, cohesive)
fine_diameters = np.random.lognormal(mean=np.log(25e-6), sigma=0.6, size=int(n_regolith*0.35))
fine_diameters = np.clip(fine_diameters, 5e-6, 60e-6)

# Coarse mode
coarse_diameters = np.random.lognormal(mean=np.log(180e-6), sigma=0.5, size=int(n_regolith*0.65))
coarse_diameters = np.clip(coarse_diameters, 80e-6, 600e-6)

regolith_diam = np.concatenate([fine_diameters, coarse_diameters])
np.random.shuffle(regolith_diam)

# Iron shot (1-5 mm, mostly 2-4 mm)
iron_diam = np.random.uniform(0.001, 0.004, n_iron)

# Densities
rho_reg = 3100.0
rho_iron = 7870.0

# Generate positions (simple random packing, will relax)
positions = []
radii = []

# Regolith
for d in regolith_diam:
    r = d / 2.0
    for _ in range(100):  # try to place
        x = random.uniform(r, box_size - r)
        y = random.uniform(r, box_size - r)
        z = random.uniform(r, box_size - r)
        if all(np.linalg.norm([x-px, y-py, z-pz]) > (r + pr + 1e-6) for px,py,pz,pr in positions):
            positions.append([x, y, z, r])
            break

# Iron
for d in iron_diam:
    r = d / 2.0
    for _ in range(100):
        x = random.uniform(r, box_size - r)
        y = random.uniform(r, box_size - r)
        z = random.uniform(r, box_size - r)
        if all(np.linalg.norm([x-px, y-py, z-pz]) > (r + pr + 1e-6) for px,py,pz,pr in positions):
            positions.append([x, y, z, r])
            break

# Write LIGGGHTS data file
with open("data/bimodal_regolith.data", "w") as f:
    f.write("LIGGGHTS data file for RCFX Rung 2\n\n")
    f.write(f"{len(positions)} atoms\n")
    f.write("2 atom types\n\n")
    f.write(f"0.0 {box_size} xlo xhi\n")
    f.write(f"0.0 {box_size} ylo yhi\n")
    f.write(f"0.0 {box_size} zlo zhi\n\n")
    f.write("Atoms\n\n")

    for i, (x, y, z, r) in enumerate(positions, 1):
        if r < 0.0003:  # regolith
            typ = 1
            density = rho_reg
        else:           # iron
            typ = 2
            density = rho_iron
        mass = (4/3)*np.pi*r**3 * density
        f.write(f"{i} {typ} {density} {r} {x} {y} {z} 0 0 0\n")

print(f"Generated data file with {len(positions)} particles")
print(f"Box size: {box_size} m")
print(f"Regolith particles: {sum(1 for _,_,_,r in positions if r < 0.0003)}")
print(f"Iron particles: {sum(1 for _,_,_,r in positions if r >= 0.0003)}")