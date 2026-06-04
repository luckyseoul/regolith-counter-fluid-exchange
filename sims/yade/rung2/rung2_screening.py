#!/usr/bin/env python3
"""
RCFX Rung 2 SCREENING DEM (fast turnaround)
Bimodal regolith + cohesion (EDS) + iron shot agitation at target low pressure.

Smaller particle count (22k reg) for multiple runs in reasonable wall time on V100/88c.
Still 5-10x larger than the earlier validation toys, with full Wen-Yu drag fluidization.

Use this family for:
- 0.12 / 0.14 / 0.15 bar points
- with-iron vs no-iron (quantify agitation value)
- high vs low EDS (Rung 5 "bad day")

All numbers feed the conservative/defensible operating point claim (0.14 bar floor).
"""

import numpy as np
from yade import pack, utils, O
import os
import time

# ---------- CONFIG (override via env or edit for variants) ----------
P_BAR = float(os.environ.get("RCFX_P", "0.14"))
IRON_MM = float(os.environ.get("RCFX_IRON_MM", "2.0"))
VEL_MULT = 5.5
EDS = float(os.environ.get("RCFX_EDS", "0.97"))
HAS_IRON = os.environ.get("RCFX_NO_IRON", "0") != "1"

RUN_NAME = os.environ.get("RCFX_RUN", f"rung2_screen_p{P_BAR:.2f}_iron{IRON_MM:.1f}_eds{EDS:.2f}")
OUT_DIR = "/home/nick/rcfx/sims/yade/rung2/data"
os.makedirs(OUT_DIR, exist_ok=True)

G = 1.625
RHO_G = 0.085
MU_G = 2.3e-5
# Umf approx at this P for the pre-classed PSD; scale
U_G = 0.012 * (0.14 / P_BAR) * VEL_MULT   # rough scaling with density

COH_BASE = 7.2e4
eff_coh = COH_BASE * (1.0 - 0.88 * EDS)

Y_REG, P_REG, D_REG, F_REG = 6e6, 0.25, 3100.0, 0.5   # softened for usable dt on fines (standard screening practice)
Y_IRON, P_IRON, D_IRON, F_IRON = 1.8e11, 0.29, 7870.0, 0.3

BOX = 0.042
N_REG = 22000
N_IRON = 165 if HAS_IRON else 0

STEPS_SETTLE = 5500
STEPS_FLUID = 135000   # more steps now that contacts are softened for usable physical time
DRAG_EVERY = 10
STATS_EVERY = 600
TOP_Z = BOX * 0.90

print(f"=== RCFX SCREENING RUN: {RUN_NAME} ===")
print(f"P={P_BAR}bar  iron={IRON_MM}mm  Vx={VEL_MULT}  EDS={EDS}  no_iron={not HAS_IRON}")
print(f"Target U_g ~{U_G:.4f} m/s   eff_coh={eff_coh:.0f} Pa   particles={N_REG}+{N_IRON}")

# Materials
O.materials.append(CohFrictMat(young=Y_REG, poisson=P_REG, density=D_REG, frictionAngle=np.arctan(F_REG), label='regolith'))
O.materials.append(CohFrictMat(young=Y_IRON, poisson=P_IRON, density=D_IRON, frictionAngle=np.arctan(F_IRON), label='iron'))

# Particles
reg_sp = pack.SpherePack()
reg_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=24e-6, rRelFuzz=0.6, num=int(N_REG*0.40))
reg_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=128e-6, rRelFuzz=0.38, num=int(N_REG*0.60))
for c,r in reg_sp:
    O.bodies.append(utils.sphere(c, r, material='regolith'))

if HAS_IRON:
    iron_sp = pack.SpherePack()
    iron_sp.makeCloud((0,0,0), (BOX,BOX,BOX), rMean=IRON_MM*1e-3, rRelFuzz=0.25, num=N_IRON)
    for c,r in iron_sp:
        O.bodies.append(utils.sphere(c, r, material='iron'))

print(f"Generated {len(O.bodies)} bodies")

# Engines with correct cohesion on phys
O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(normalCohesion=eff_coh, shearCohesion=eff_coh*0.88)],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment()]
    ),
    NewtonIntegrator(damping=0.07, gravity=(0,0,-G)),
    PyRunner(command='apply_drag()', iterPeriod=DRAG_EVERY),
    PyRunner(command='log_stats()', iterPeriod=STATS_EVERY),
]

O.dt = 0.16 * utils.PWaveTimeStep()

# State
stats = {'t':[], 'bed_h':[], 'entr_current':[], 'entr_delta':[], 'ke_ratio':[], 'ke_iron':[]}
prev_entr = 0
last_t = 0.0

def wen_yu(vrel, d, eps=0.50):
    Re = RHO_G * abs(vrel) * d / MU_G
    Cd = (24.0/Re*(1+0.15*Re**0.687) if Re > 1e-5 else 2000) if Re < 800 else 0.44
    Cd *= eps**(-3.5)
    return 0.5 * Cd * RHO_G * np.pi*(d/2)**2 * vrel**2

def apply_drag():
    for b in O.bodies:
        if b.material.label != 'regolith': continue
        vrel = U_G - b.state.vel[2]
        Fd = wen_yu(vrel, 2*b.shape.radius)
        O.forces.addF(b.id, (0,0, (1 if vrel>0 else -1)*Fd if abs(vrel)>1e-6 else 0))

def count_entrained():
    return sum(1 for b in O.bodies 
               if b.material.label=='regolith' and b.state.pos[2] > TOP_Z and b.state.vel[2] > 0.008)

def log_stats():
    global prev_entr, last_t
    t = O.time
    z = [b.state.pos[2] for b in O.bodies if b.material.label=='regolith']
    if not z: return
    bed = float(np.percentile(z, 90))
    entr_now = count_entrained()
    delta = entr_now - prev_entr
    prev_entr = entr_now
    last_t = t

    ke_r = sum(0.5*b.state.mass*np.dot(b.state.vel,b.state.vel) for b in O.bodies if b.material.label=='regolith')
    ke_i = sum(0.5*b.state.mass*np.dot(b.state.vel,b.state.vel) for b in O.bodies if b.material.label=='iron')
    ratio = ke_i / max(1e-9, ke_r)

    stats['t'].append(t)
    stats['bed_h'].append(bed)
    stats['entr_current'].append(entr_now)
    stats['entr_delta'].append(delta)
    stats['ke_ratio'].append(ratio)
    stats['ke_iron'].append(ke_i)

    if O.iter % 2500 < 10:
        print(f"t={t:.4f}s bed={bed*1000:.1f}mm entr_now={entr_now} delta={delta} ke_i/ke_r={ratio:.3f}")

# Run
print("Settling...")
O.run(STEPS_SETTLE, wait=True)
print(f"Fluidizing at {U_G:.3f} m/s ...")
t0 = time.time()
O.run(STEPS_FLUID, wait=True)
print(f"Done in {time.time()-t0:.1f}s real")

np.savez(f"{OUT_DIR}/{RUN_NAME}.npz", **{k:np.asarray(v) for k,v in stats.items()})
print(f"Saved {OUT_DIR}/{RUN_NAME}.npz")
print("FINAL:", {k: (v[-1] if v else 0) for k,v in stats.items()})
print("dt_final ~", O.dt)
print("=== SCREEN RUN COMPLETE ===")
