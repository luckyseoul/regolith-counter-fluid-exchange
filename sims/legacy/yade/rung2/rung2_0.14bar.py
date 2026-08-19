#!/usr/bin/env python3
"""
RCFX Rung 2 using Yade (Python DEM)
Bimodal lunar regolith + JKR cohesion + iron shot agitation at 0.14 bar.

This is the high-fidelity particle simulation for the rungs.
"""

from yade import pack, qt, utils, plot, O
import numpy as np

# Parameters from Rev 5.2 + current working point
P = 0.14  # bar target
g = 1.625  # lunar

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

# Generate particles (simplified for now)
print("Generating particles for Rung 2 at 0.14 bar...")

# Small validation box first
box = 0.03
n_reg = 8000
n_iron = 80

reg = pack.SpherePack()
reg.makeCloud((0,0,0),(box,box,box), rMean=25e-6, rRelFuzz=0.8, num=n_reg//2)
reg.makeCloud((0,0,0),(box,box,box), rMean=140e-6, rRelFuzz=0.4, num=n_reg//2)

iron = pack.SpherePack()
iron.makeCloud((0,0,0),(box,box,box), rMean=2.5e-3, rRelFuzz=0.3, num=n_iron)

sp = reg + iron
sp.toSimulation()

# Add cohesion (only regolith)
for i in O.bodies:
    if i.material.name == 'regolith':
        i.material.cohesionEnergyDensity = 0.05  # J/m2 equivalent for JKR

# Engines
O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(cohesion=True)],
        [Law2_ScGeom_CohFrictPhys_CundallStrack()]
    ),
    NewtonIntegrator(damping=0.2, gravity=(0,0,-g)),
]

O.dt = 0.2 * utils.PWaveTimeStep()

print(f"Particles: {len(O.bodies)}")
print("Starting Rung 2 simulation...")

# Run
O.run(50000, wait=True)

print("Rung 2 basic run completed.")
print("Use yade.qt.View() or post-process the simulation for quantitative results.")

