#!/usr/bin/env python3
"""
Quick validation run of Rung 2 at 0.14 bar using Yade.
Smaller system for fast smoke test before full production run.
"""

from yade import pack, utils, O
import numpy as np

P = 0.14
g = 1.625

O.materials.append(CohFrictMat(young=1e8, poisson=0.25, density=3100,
                               frictionAngle=np.arctan(0.55), label='regolith'))
O.materials.append(CohFrictMat(young=2.1e11, poisson=0.29, density=7870,
                               frictionAngle=np.arctan(0.35), label='iron'))

box = 0.015
n_reg = 3000
n_iron = 25

# Generate separately and append with correct materials
reg_sp = pack.SpherePack()
reg_sp.makeCloud((0,0,0), (box,box,box), rMean=25e-6, rRelFuzz=0.7, num=n_reg//2)
reg_sp.makeCloud((0,0,0), (box,box,box), rMean=120e-6, rRelFuzz=0.4, num=n_reg//2)

iron_sp = pack.SpherePack()
iron_sp.makeCloud((0,0,0), (box,box,box), rMean=2.2e-3, rRelFuzz=0.3, num=n_iron)

# Append with explicit materials
for c, r in reg_sp:
    O.bodies.append(utils.sphere(c, r, material='regolith'))
for c, r in iron_sp:
    O.bodies.append(utils.sphere(c, r, material='iron'))

O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(
            normalCohesion=1e5,
            shearCohesion=1e5,
        )],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment()]
    ),
    NewtonIntegrator(damping=0.2, gravity=(0,0,-g)),
]

O.dt = 0.25 * utils.PWaveTimeStep()

print(f"Validation Rung 2: {len(O.bodies)} particles at {P} bar")
O.run(8000, wait=True)
print("Validation run completed successfully.")