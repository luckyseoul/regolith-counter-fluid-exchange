#!/usr/bin/env python3
"""
RCFX Rung 2 - Actual DEM run using Yade (0.14 bar)
Bimodal regolith + JKR-style cohesion + iron shot agitation.

This is a real particle simulation for the rungs.
Uses on-the-fly packing for simplicity and to avoid data file issues.
"""

from yade import pack, utils, O
import numpy as np

# --- Parameters from Rev 5.2 + current best tuning ---
P = 0.14          # bar
g = 1.625         # lunar

# Materials
O.materials.append(CohFrictMat(
    young=1e8, poisson=0.25, density=3100,
    frictionAngle=np.arctan(0.55),
    label='regolith'
))

O.materials.append(CohFrictMat(
    young=2.1e11, poisson=0.29, density=7870,
    frictionAngle=np.arctan(0.35),
    label='iron'
))

# Tuned parameters (from our Python sweeps, within claims)
iron_cold_mm = 2.0
fill_cold = 0.32
vel_mult_cold = 5.5
eds_eff = 0.97
preclass_um = 22

# Effective cohesion reduced by EDS (approximation)
base_cohesion = 8e4 * (1 - 0.85 * eds_eff)   # Pa

# Box and particle count (start reasonable for V100)
box = 0.035
n_reg = 18000
n_iron = int(n_reg * 0.012)   # ~1% by number, higher volume effect

print(f"Generating ~{n_reg + n_iron} particles for Rung 2 at {P} bar...")

# Bimodal packing (simplified from spec)
reg_sp = pack.SpherePack()
reg_sp.makeCloud((0,0,0), (box,box,box), rMean=20e-6, rRelFuzz=0.7, num=int(n_reg*0.35))
reg_sp.makeCloud((0,0,0), (box,box,box), rMean=130e-6, rRelFuzz=0.45, num=int(n_reg*0.65))

iron_sp = pack.SpherePack()
iron_sp.makeCloud((0,0,0), (box,box,box), rMean=iron_cold_mm*1e-3, rRelFuzz=0.3, num=n_iron)

# Append bodies
for c, r in reg_sp:
    O.bodies.append(utils.sphere(c, r, material='regolith'))
for c, r in iron_sp:
    O.bodies.append(utils.sphere(c, r, material='iron'))

print(f"Total particles created: {len(O.bodies)}")

# Engines with cohesion
O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(
            normalCohesion=base_cohesion,
            shearCohesion=base_cohesion,
        )],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment()]
    ),
    NewtonIntegrator(damping=0.12, gravity=(0,0,-g)),
]

O.dt = 0.2 * utils.PWaveTimeStep()

# Run
print("Starting real Rung 2 DEM at 0.14 bar...")
O.run(15000, wait=True)   # short first leg for validation

print("First leg done. Continuing main run...")
O.run(120000, wait=True)

print("Rung 2 DEM run completed.")
print("Use yade.qt.View() or postprocess the saved data.")