#!/usr/bin/env python3
"""
RCFX Rung 4 starter - Single stage representative DEM (Yade)
This is a stepping stone before full 5-stage counterflow.

Uses the same tuned parameters as the 0.14 bar working point.
"""
from yade import pack, utils, O
import numpy as np

P = 0.14
g = 1.625

O.materials.append(CohFrictMat(young=1e8, poisson=0.25, density=3100, frictionAngle=np.arctan(0.55), label='regolith'))
O.materials.append(CohFrictMat(young=2.1e11, poisson=0.29, density=7870, frictionAngle=np.arctan(0.35), label='iron'))

box = 0.03
n_reg = 12000
n_iron = 90

sp = pack.SpherePack()
sp.makeCloud((0,0,0),(box,box,box), rMean=20e-6, rRelFuzz=0.7, num=n_reg//2)
sp.makeCloud((0,0,0),(box,box,box), rMean=130e-6, rRelFuzz=0.4, num=n_reg//2)
sp.makeCloud((0,0,0),(box,box,box), rMean=2.8e-3, rRelFuzz=0.3, num=n_iron)

for c,r in sp:
    O.bodies.append(utils.sphere(c, r, material='regolith' if r < 0.0005 else 'iron'))

O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(normalCohesion=7e4, shearCohesion=7e4)],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment()]
    ),
    NewtonIntegrator(damping=0.1, gravity=(0,0,-g)),
]

O.dt = 0.2 * utils.PWaveTimeStep()
print(f"Rung 4 single-stage validation: {len(O.bodies)} particles at {P} bar")
O.run(100000, wait=True)
print("Rung 4 single-stage run finished.")
