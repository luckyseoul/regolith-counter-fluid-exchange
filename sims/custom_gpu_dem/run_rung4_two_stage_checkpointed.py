#!/usr/bin/env python3
"""
Rung 4 Two-Stage Counter-Current with CHECKPOINTS (resume-safe).
Uses iron agitation (Rung 2) + EDS (Rung 3) at 0.14 bar target.
Saves state every 1000 steps so long runs survive the 300s harness limit.
Run this repeatedly to accumulate real multi-stage transfer + heat proxy data.

This is how we finish Rung 4 without stalling.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))
from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

DT = 7e-7
TARGET_STEPS = 15000
CHECKPOINT_EVERY = 1000
BOX = 0.011
U_G = 0.066
DAMP = 0.035
EDS_EFF = 0.97

CHECKPOINT_DIR = Path("rung4_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

def add_eds(f, pos, r, mat, eds):
    reg = (mat == 0)
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
    p[:, 2] = p[:, 2] * 0.45 + z0 + 0.0005
    p = np.clip(p, rad[:, None] + 1e-6, BOX + z0 - rad[:, None] - 1e-6)
    is_hot = cp.zeros(n, dtype=bool)
    if hot_iron_frac > 0:
        iron_idx = np.where(m == 1)[0]
        is_hot[iron_idx[:int(len(iron_idx)*hot_iron_frac)]] = True
    return cp.asarray(p), cp.zeros((n,3),cp.float32), cp.asarray(rad,cp.float32), cp.asarray(m), is_hot

def save_checkpoint(pos1, vel1, rad1, mat1, pos2, vel2, rad2, mat2, is_hot2, step, xfer, heat):
    cp.savez(CHECKPOINT_DIR / f"rung4_step{step:05d}.npz",
             pos1=cp.asnumpy(pos1), vel1=cp.asnumpy(vel1), rad1=cp.asnumpy(rad1), mat1=cp.asnumpy(mat1),
             pos2=cp.asnumpy(pos2), vel2=cp.asnumpy(vel2), rad2=cp.asnumpy(rad2), mat2=cp.asnumpy(mat2),
             is_hot2=cp.asnumpy(is_hot2), step=step, xfer=xfer, heat=heat)

def load_latest():
    files = sorted(CHECKPOINT_DIR.glob("rung4_step*.npz"))
    if not files:
        return None
    latest = files[-1]
    d = np.load(latest, allow_pickle=True)
    print(f"Resuming Rung 4 from {latest.name} (step {int(d['step'])}, xfer={int(d['xfer'])}, heat={int(d['heat'])})")
    return (cp.asarray(d['pos1']), cp.asarray(d['vel1']), cp.asarray(d['rad1']), cp.asarray(d['mat1']),
            cp.asarray(d['pos2']), cp.asarray(d['vel2']), cp.asarray(d['rad2']), cp.asarray(d['mat2']),
            cp.asarray(d['is_hot2']), int(d['step']), int(d['xfer']), int(d['heat']))

print("=== Rung 4 Checkpointed Two-Stage + Heat Proxy (0.14 bar) ===")

ck = load_latest()
if ck is not None:
    pos1, vel1, rad1, mat1, pos2, vel2, rad2, mat2, is_hot2, start_step, transfer_count, heating_events = ck
else:
    pos1, vel1, rad1, mat1, _ = make_stage(900, 0.032, 0.0, 0.0)
    pos2, vel2, rad2, mat2, is_hot2 = make_stage(900, 0.03, BOX+0.0008, 0.30)
    start_step = 0
    transfer_count = 0
    heating_events = 0

steps_to_do = TARGET_STEPS - start_step
if steps_to_do <= 0:
    print("Rung 4 already at target.")
    sys.exit(0)

print(f"Running additional {steps_to_do} steps from step {start_step}")

transfer_every = 600
t0 = time.time()

for s in range(steps_to_do):
    step = start_step + s

    f1, t1 = compute_forces(pos1, vel1, cp.zeros_like(vel1), rad1, mat1, DT)
    f1 = add_eds(f1, pos1, rad1, mat1, EDS_EFF)
    f1 += compute_drag(vel1, rad1, mat1, U_g=U_G, local_porosity=estimate_local_porosity(pos1, rad1, BOX))
    pos1, vel1, _ = integrate(pos1, vel1, cp.zeros_like(vel1), f1, t1, rad1, mat1, DT, DAMP)

    f2, t2 = compute_forces(pos2, vel2, cp.zeros_like(vel2), rad2, mat2, DT)
    f2 = add_eds(f2, pos2, rad2, mat2, EDS_EFF)
    f2 += compute_drag(vel2, rad2, mat2, U_g=U_G, local_porosity=estimate_local_porosity(pos2, rad2, BOX))
    pos2, vel2, _ = integrate(pos2, vel2, cp.zeros_like(vel2), f2, t2, rad2, mat2, DT, DAMP)

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

    if (s + 1) % 400 == 0:
        reg2 = (mat2 == 0)
        if cp.sum(reg2) > 0 and cp.sum(is_hot2) > 0:
            hot_pos = pos2[is_hot2]
            dx = pos2[reg2, None, :] - hot_pos[None, :, :]
            close = cp.any(cp.linalg.norm(dx, axis=2) < (rad2[reg2, None] + 0.001), axis=1)
            heating_events += int(cp.sum(close))

    if (s + 1) % 500 == 0:
        b1 = float(cp.mean(pos1[mat1==0, 2]) * 1000)
        b2 = float(cp.mean(pos2[mat2==0, 2]) * 1000)
        print(f"step {step+1:5d} | S1={b1:5.1f}mm S2={b2:5.1f}mm xfer={transfer_count} heat={heating_events}")

    if (s + 1) % CHECKPOINT_EVERY == 0:
        save_checkpoint(pos1, vel1, rad1, mat1, pos2, vel2, rad2, mat2, is_hot2, step+1, transfer_count, heating_events)
        print(f"  [checkpoint saved at step {step+1}]")

wall = time.time() - t0
print(f"\nRung 4 slice done in {wall:.1f}s. Total xfer={transfer_count}, heat_events={heating_events}")
save_checkpoint(pos1, vel1, rad1, mat1, pos2, vel2, rad2, mat2, is_hot2, start_step + steps_to_do, transfer_count, heating_events)
print("Final checkpoint saved. Re-run this script to continue Rung 4.")