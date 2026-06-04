#!/usr/bin/env python3
"""
Minimal smoke test for Rung 2 physics loop.
Tiny system (7k particles) + very short times so we can prove the full chain works:
- bimodal + iron
- correct CohFrict + 6D cohesion law
- Wen-Yu drag application via PyRunner
- stats collection (bed, entrainment, KE)
- .npz save
This must complete cleanly and produce usable output before we scale up.
"""

import numpy as np
from yade import pack, utils, O
import os

P_BAR = 0.14
G = 1.625
RHO_G = 0.085
MU_G = 2.3e-5
U_G = 0.055
eff_coh = 10500.0

BOX = 0.028
N_REG = 6800
N_IRON = 55

print("=== RCFX Rung2 SMOKE TEST ===")
print(f"Particles: {N_REG} reg + {N_IRON} iron")

O.materials.append(CohFrictMat(young=6e7, poisson=0.25, density=3100, frictionAngle=np.arctan(0.5), label='regolith'))
O.materials.append(CohFrictMat(young=1.8e11, poisson=0.29, density=7870, frictionAngle=np.arctan(0.3), label='iron'))

reg_sp = pack.SpherePack()
reg_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=22e-6, rRelFuzz=0.55, num=2700)
reg_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=115e-6, rRelFuzz=0.35, num=4100)
for c,r in reg_sp:
    O.bodies.append(utils.sphere(c, r, material='regolith'))

iron_sp = pack.SpherePack()
iron_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=0.002, rRelFuzz=0.2, num=N_IRON)
for c,r in iron_sp:
    O.bodies.append(utils.sphere(c, r, material='iron'))

print(f"Generated {len(O.bodies)} bodies")

O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(normalCohesion=eff_coh, shearCohesion=eff_coh*0.9)],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment()]
    ),
    NewtonIntegrator(damping=0.08, gravity=(0,0,-G)),
    PyRunner(command='apply_drag()', iterPeriod=8),
    PyRunner(command='log_stats()', iterPeriod=400),
]

O.dt = 0.2 * utils.PWaveTimeStep()

stats = {'t':[], 'bed':[], 'entr':[], 'ke_ratio':[]}
entr = 0
last_entr = 0
last_t = 0.0
TOP = BOX * 0.88

def wen_yu(vrel, d, eps=0.48):
    Re = RHO_G * abs(vrel) * d / MU_G
    Cd = 24.0/Re*(1+0.15*Re**0.687) if 1e-4 < Re < 700 else (0.44 if Re >= 700 else 300)
    Cd *= eps**(-3.4)
    return 0.5 * Cd * RHO_G * np.pi*(d/2)**2 * vrel**2

def apply_drag():
    global entr
    for b in O.bodies:
        if b.material.label != 'regolith': continue
        vrel = U_G - b.state.vel[2]
        Fd = wen_yu(vrel, 2*b.shape.radius)
        if abs(vrel) > 1e-6:
            O.forces.addF(b.id, (0,0, (1 if vrel>0 else -1)*Fd))
        if b.state.pos[2] > TOP and b.state.vel[2] > 0.01:
            entr += 1

def log_stats():
    global last_entr, last_t
    t = O.time
    z = [b.state.pos[2] for b in O.bodies if b.material.label == 'regolith']
    if not z: return
    bed = float(np.percentile(z, 88))
    rate = (entr - last_entr) / max(1e-4, t - last_t) if last_t > 0 else 0.0
    last_entr = entr
    last_t = t
    ke_r = sum(0.5*b.state.mass * np.dot(b.state.vel, b.state.vel) for b in O.bodies if b.material.label=='regolith')
    ke_i = sum(0.5*b.state.mass * np.dot(b.state.vel, b.state.vel) for b in O.bodies if b.material.label=='iron')
    ratio = ke_i / max(1e-9, ke_r)
    stats['t'].append(t)
    stats['bed'].append(bed)
    stats['entr'].append(entr)
    stats['ke_ratio'].append(ratio)
    print(f"SMOKE t={t:.3f} bed={bed*1000:.1f}mm entr={entr} rate={rate:.1f} ke_ratio={ratio:.3f}")

print("Short settle...")
O.run(1800, wait=True)
print("Fluidize (short)...")
O.run(6500, wait=True)
print("Smoke test finished.")

np.savez("/home/nick/rcfx/sims/yade/rung2/data/rung2_smoke_test.npz", **{k:np.array(v) for k,v in stats.items()})
print("Saved smoke .npz with", len(stats['t']), "samples")
print("Last values:", {k: (v[-1] if v else None) for k,v in stats.items()})
print("=== SMOKE COMPLETE ===")
