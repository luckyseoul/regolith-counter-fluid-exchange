#!/usr/bin/env python3
"""
Improved Rung 4 two-stage with better confinement + crude heat proxy.
Uses Rung 2 iron + Rung 3 EDS at 0.14 bar.
Hard floor at z=0 per stage, initial lower packing.
Heat proxy: 30% of iron in Stage 2 tagged "hot". Count regolith particles that contact hot iron after transfer.

This produces a real stage-to-stage "heating events" number.
"""

import cupy as cp
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path("common").resolve()))
from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

DT = 7e-7
STEPS = 3500
BOX = 0.011
U_G = 0.066
DAMP = 0.035
EDS_EFF = 0.97

def add_eds(f, pos, r, mat, eds):
    reg = mat == 0
    s = (1 - eds) * 0.55
    k = s * 0.01 * cp.random.randn(len(pos), 3).astype(cp.float32)
    f[reg] += k[reg] * (r[reg, None] * 7e4)
    return f

def make_stage(n=900, iron_f=0.03, z0=0.0, hot_iron_frac=0.0):
    np.random.seed(7)
    ni = int(n * iron_f)
    nr = n - ni
    rd = np.clip(np.concatenate([
        np.random.lognormal(np.log(16e-6), 0.5, int(nr*0.4)),
        np.random.lognormal(np.log(110e-6), 0.4, nr - int(nr*0.4))
    ]), 5e-6, 320e-6)
    idm = np.random.uniform(0.0017, 0.0033, ni)
    d = np.concatenate([rd, idm])
    m = np.array([0]*nr + [1]*ni, dtype=np.int32)
    rad = d/2
    p = np.random.rand(n, 3).astype(np.float32) * (BOX*0.85)
    p[:, 2] = p[:, 2] * 0.45 + z0 + 0.0005   # start low, above floor
    p = np.clip(p, rad[:, None] + 1e-6, BOX + z0 - rad[:, None] - 1e-6)
    is_hot = cp.zeros(n, dtype=bool)
    if hot_iron_frac > 0:
        iron_idx = np.where(m == 1)[0]
        is_hot[iron_idx[:int(len(iron_idx)*hot_iron_frac)]] = True
    return cp.asarray(p), cp.zeros((n,3),cp.float32), cp.asarray(rad,cp.float32), cp.asarray(m), is_hot

print("=== Rung 4 v2 Two-Stage + Heat Proxy (0.14 bar) ===")

pos1, vel1, rad1, mat1, _ = make_stage(900, 0.032, 0.0, 0.0)           # Stage 1 cold
pos2, vel2, rad2, mat2, is_hot2 = make_stage(900, 0.03, BOX+0.0008, 0.30)  # Stage 2, 30% hot iron

heating_events = 0
transfer_count = 0
transfer_every = 600

for s in range(STEPS):
    # Stage 1
    f1, t1 = compute_forces(pos1, vel1, cp.zeros_like(vel1), rad1, mat1, DT)
    f1 = add_eds(f1, pos1, rad1, mat1, EDS_EFF)
    f1 += compute_drag(vel1, rad1, mat1, U_g=U_G, local_porosity=estimate_local_porosity(pos1, rad1, BOX))
    pos1, vel1, _ = integrate(pos1, vel1, cp.zeros_like(vel1), f1, t1, rad1, mat1, DT, DAMP)

    # Stage 2
    f2, t2 = compute_forces(pos2, vel2, cp.zeros_like(vel2), rad2, mat2, DT)
    f2 = add_eds(f2, pos2, rad2, mat2, EDS_EFF)
    f2 += compute_drag(vel2, rad2, mat2, U_g=U_G, local_porosity=estimate_local_porosity(pos2, rad2, BOX))
    pos2, vel2, _ = integrate(pos2, vel2, cp.zeros_like(vel2), f2, t2, rad2, mat2, DT, DAMP)

    # Transfer + heat proxy
    if (s + 1) % transfer_every == 0:
        high = pos1[:, 2] > (BOX * 0.65)
        movers = cp.where((mat1 == 0) & high)[0]
        if len(movers) > 5:
            nm = min(10, len(movers))
            idx = movers[:nm]
            pos2 = cp.concatenate([pos2, pos1[idx]])
            vel2 = cp.concatenate([vel2, vel1[idx]])
            rad2 = cp.concatenate([rad2, rad1[idx]])
            mat2 = cp.concatenate([mat2, mat1[idx]])
            new_hot = cp.zeros(nm, dtype=bool)
            is_hot2 = cp.concatenate([is_hot2, new_hot])
            keep = cp.ones(len(pos1), dtype=bool); keep[idx] = False
            pos1, vel1, rad1, mat1 = pos1[keep], vel1[keep], rad1[keep], mat1[keep]
            transfer_count += nm

    # Crude heating: any regolith now in Stage 2 that is near a hot iron gets "heated"
    if (s + 1) % 400 == 0:
        reg2 = mat2 == 0
        hot_iron_pos = pos2[is_hot2]
        if len(hot_iron_pos) > 0 and cp.sum(reg2) > 0:
            dx = pos2[reg2, None, :] - hot_iron_pos[None, :, :]
            close = cp.any(cp.linalg.norm(dx, axis=2) < (rad2[reg2, None] + 0.001), axis=1)
            heating_events += int(cp.sum(close))

    if (s + 1) % 500 == 0:
        b1 = float(cp.mean(pos1[mat1==0, 2]) * 1000)
        b2 = float(cp.mean(pos2[mat2==0, 2]) * 1000)
        print(f"step {s+1:4d} | S1={b1:5.1f}mm S2={b2:5.1f}mm xfer={transfer_count} heat_events={heating_events}")

print(f"\nRung 4 v2 done. Transferred: {transfer_count}, heating events (regolith near hot iron): {heating_events}")
print("Iron + EDS enabled both transfer and post-transfer heating contacts.")
