#!/usr/bin/env python3
"""
RCFX Rung 2 - Small drag demo (2500-3000 particles)
Goal: Demonstrate iron shot getting fluidized by gas drag and transferring energy
to regolith via collisions at 0.14 bar conditions.

Drag model (simple, physically reasonable):
- Fixed superficial gas velocity U_G corresponding to ~68 W blower power (~0.066 m/s)
- Per-particle force: Stokes (viscous) + quadratic (inertial)
- Naturally stronger on larger iron particles (A ~ d^2, d~2mm vs ~0.1mm for fines)
- Applied to BOTH regolith and iron (unlike some earlier scripts)

This is a minimal demo to see the mechanism before scaling up.
"""

import numpy as np
from yade import pack, utils, O
import time

# ---------------- Parameters (small for speed + visibility) ----------------
G = 1.625
BOX = 0.026          # ~2.6 cm box
N_REG = 2700
N_IRON = 180         # total ~2880 particles

# Gas props at cold stage ~0.14 bar
RHO_G = 0.085
MU_G = 2.3e-5
U_G = 0.066          # m/s superficial, tied to ~68 W point from lumped model

# Materials (softened for dt on small particles)
Y_REG = 5e6
P_REG = 0.25
D_REG = 3100.0
F_REG = 0.5

Y_IRON = 1.5e11
P_IRON = 0.29
D_IRON = 7870.0
F_IRON = 0.3

# Cohesion (EDS reduced, only regolith-regolith)
EFF_COH = 1.1e4      # Pa effective

# Simulation control
STEPS_SETTLE = 3000
STEPS_FLUID = 18000
DRAG_EVERY = 8
STATS_EVERY = 400
TOP_Z = BOX * 0.88

print("=== RCFX Rung 2 Drag Demo (~3000 particles) ===")
print(f"Box: {BOX*1000:.1f} mm | N_reg={N_REG} + N_iron={N_IRON}")
print(f"U_G = {U_G:.4f} m/s (tied to ~68 W lumped model)")
print(f"Drag: Stokes + quadratic, applied to ALL particles (stronger on iron by size)")

# ---------------- Materials ----------------
O.materials.append(CohFrictMat(
    young=Y_REG, poisson=P_REG, density=D_REG,
    frictionAngle=np.arctan(F_REG),
    label='regolith'
))
O.materials.append(CohFrictMat(
    young=Y_IRON, poisson=P_IRON, density=D_IRON,
    frictionAngle=np.arctan(F_IRON),
    label='iron'
))

# ---------------- Particles ----------------
print("Generating particles...")
reg_sp = pack.SpherePack()
reg_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=22e-6, rRelFuzz=0.55, num=int(N_REG*0.42))
reg_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=120e-6, rRelFuzz=0.32, num=int(N_REG*0.58))
for c, r in reg_sp:
    O.bodies.append(utils.sphere(c, r, material='regolith'))

iron_sp = pack.SpherePack()
iron_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=0.0018, rRelFuzz=0.2, num=N_IRON)
for c, r in iron_sp:
    O.bodies.append(utils.sphere(c, r, material='iron'))

print(f"Generated {len(O.bodies)} bodies")

# ---------------- Engines ----------------
O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(
            normalCohesion=EFF_COH, shearCohesion=EFF_COH*0.9
        )],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment()]
    ),
    NewtonIntegrator(damping=0.05, gravity=(0,0,-G)),
    PyRunner(command='apply_drag()', iterPeriod=DRAG_EVERY),
    PyRunner(command='log_stats()', iterPeriod=STATS_EVERY),
]

O.dt = 0.2 * utils.PWaveTimeStep()

# ---------------- Stats ----------------
stats = {'t':[], 'bed_h':[], 'iron_z_avg':[], 'ke_iron':[], 'ke_reg':[], 'coll_iron_reg':[]}
prev_entr = 0
last_t = 0.0
TOP_ENTR = BOX * 0.87

def apply_drag():
    """Stokes + quadratic drag. Fixed U_G for simplicity.
    Force naturally much larger on iron (d~2mm vs ~0.1mm) because area ~ d^2.
    """
    for b in O.bodies:
        r = b.shape.radius
        d = 2.0 * r
        v_rel = U_G - b.state.vel[2]          # positive when gas is pushing particle up

        # Stokes (viscous)
        F_stokes = 3.0 * np.pi * MU_G * d * v_rel

        # Quadratic (inertial) - Cd approx
        Re = RHO_G * abs(v_rel) * d / MU_G
        if Re < 1e-4:
            Cd = 2000.0
        elif Re < 600:
            Cd = 24.0 / Re * (1.0 + 0.15 * Re**0.687)
        else:
            Cd = 0.45
        A = np.pi * (d/2.0)**2
        F_quad = 0.5 * Cd * RHO_G * A * v_rel * abs(v_rel)

        F_total = F_stokes + F_quad
        direction = 1.0 if v_rel > 0 else -1.0
        O.forces.addF(b.id, (0, 0, direction * F_total))

def log_stats():
    global last_t
    t = O.time
    z_reg = [b.state.pos[2] for b in O.bodies if b.material.label == 'regolith']
    z_iron = [b.state.pos[2] for b in O.bodies if b.material.label == 'iron']

    if not z_reg:
        return

    bed_h = float(np.percentile(z_reg, 88))
    iron_z = float(np.mean(z_iron)) if z_iron else 0.0

    ke_reg = sum(0.5 * b.state.mass * np.dot(b.state.vel, b.state.vel)
                 for b in O.bodies if b.material.label == 'regolith')
    ke_iron = sum(0.5 * b.state.mass * np.dot(b.state.vel, b.state.vel)
                  for b in O.bodies if b.material.label == 'iron')

    # Very rough collision proxy (number of iron-regolith interactions this step)
    coll = 0
    for i in O.interactions:
        if i.phys:
            b1 = O.bodies[i.id1]
            b2 = O.bodies[i.id2]
            if {b1.material.label, b2.material.label} == {'regolith', 'iron'}:
                coll += 1

    stats['t'].append(t)
    stats['bed_h'].append(bed_h)
    stats['iron_z_avg'].append(iron_z)
    stats['ke_iron'].append(ke_iron)
    stats['ke_reg'].append(ke_reg)
    stats['coll_iron_reg'].append(coll)

    if O.iter % 1200 < 5:
        print(f"t={t*1000:.2f}ms  bed={bed_h*1000:.2f}mm  iron_z={iron_z*1000:.2f}mm  "
              f"KEi/KEr={ke_iron/max(1e-12,ke_reg):.3f}  iron-reg_coll~{coll}")

# ---------------- Run ----------------
print("Settling (no drag)...")
O.run(STEPS_SETTLE, wait=True)

print(f"Starting fluidization with drag (U_G={U_G:.4f} m/s)...")
t0 = time.time()
O.run(STEPS_FLUID, wait=True)
print(f"Done in {time.time()-t0:.1f}s wall time")

# Save
import numpy as np
np.savez("/home/nick/rcfx/sims/yade/rung2/data/rung2_drag_demo_0.14.npz",
         **{k: np.array(v) for k,v in stats.items()})
print("Saved rung2_drag_demo_0.14.npz")

# Quick summary
if stats['iron_z_avg']:
    print(f"Final iron avg height: {stats['iron_z_avg'][-1]*1000:.2f} mm")
    print(f"Final KE_iron / KE_reg: {stats['ke_iron'][-1] / max(1e-12, stats['ke_reg'][-1]):.4f}")
print("=== Drag demo complete ===")