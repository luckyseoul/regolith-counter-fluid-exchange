#!/usr/bin/env python3
"""
Continue Rung 2 production from existing drag-enabled states.
Loads rung2_3000p_with_drag.npz (iron + drag at 0.14 bar target) or the no-iron equivalent,
then runs additional physical time with the improved stronger-on-iron drag scaling.
Collects time-averaged EMI, collision counts, bed expansion stats for patent evidence.

This is the practical way to get longer-duration, higher-statistics Rung 2 data at the 68 W point
without OOM on brute-force pairwise at higher N.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

DT = 7e-7
EXTRA_STEPS = 5500
DUMP_EVERY = 400
BOX_SIZE = 0.015   # match the state that was saved

U_G = 0.066
DRAG_STRENGTH = 1.0
DAMPING = 0.06

def count_iron_reg_contacts(pos, radius, mat_type):
    N = pos.shape[0]
    dx = pos[:, None, :] - pos[None, :, :]
    dist = cp.linalg.norm(dx, axis=2) + 1e-12
    r_sum = radius[:, None] + radius[None, :]
    iron = (mat_type == 1)
    reg = (mat_type == 0)
    mask = (dist < r_sum * 1.04) & (cp.arange(N)[:, None] != cp.arange(N)[None, :])
    iron_reg = mask & iron[:, None] & reg[None, :]
    return int(cp.sum(iron_reg))

def run_continuation(state_file, out_prefix, is_iron_case=True):
    print(f"=== Continuing Rung 2 from {state_file} ===")
    data = np.load(state_file, allow_pickle=True)
    pos = cp.asarray(data['pos'], dtype=cp.float32)
    vel = cp.asarray(data['vel'], dtype=cp.float32)
    radius = cp.asarray(data['radius'], dtype=cp.float32)
    mat_type = cp.asarray(data.get('mat_type', data.get('mat')), dtype=cp.int32)

    n_iron = int(cp.sum(mat_type == 1))
    n_reg = int(cp.sum(mat_type == 0))
    print(f"  {len(pos)} particles ({n_reg} reg + {n_iron} iron) | extra {EXTRA_STEPS} steps")

    times = []
    bed_h = []
    iron_h = []
    contacts = []
    ke_r = []
    ke_i = []

    t0 = time.time()
    for step in range(EXTRA_STEPS):
        force, torque = compute_forces(pos, vel, omega=cp.zeros_like(vel), radius=radius, mat_type=mat_type, dt=DT)

        local_eps = estimate_local_porosity(pos, radius, box_size=BOX_SIZE)
        drag = compute_drag(vel, radius, mat_type, U_g=U_G, local_porosity=local_eps)
        force += DRAG_STRENGTH * drag

        # dummy omega for integrate (we zeroed it)
        omega = cp.zeros_like(vel)
        pos, vel, _ = integrate(pos, vel, omega, force, cp.zeros_like(vel), radius, mat_type, DT, DAMPING)

        if step % DUMP_EVERY == 0 or step == EXTRA_STEPS-1:
            t_phys = step * DT
            reg_z = pos[mat_type == 0, 2]
            bed_mean = float(cp.mean(reg_z) * 1000.0)
            iron_mean = float(cp.mean(pos[mat_type == 1, 2]) * 1000.0) if n_iron > 0 else 0.0

            DENS = cp.array([3100., 7870.])
            vol = 4/3 * cp.pi * radius**3
            mass = DENS[mat_type] * vol
            ke = 0.5 * mass * cp.sum(vel**2, axis=1)
            ke_reg = float(cp.sum(ke[mat_type==0]))
            ke_iron = float(cp.sum(ke[mat_type==1])) if n_iron > 0 else 0.0

            n_c = count_iron_reg_contacts(pos, radius, mat_type) if n_iron > 0 else 0

            times.append(t_phys)
            bed_h.append(bed_mean)
            iron_h.append(iron_mean)
            contacts.append(n_c)
            ke_r.append(ke_reg)
            ke_i.append(ke_iron)

            print(f"  +{step:5d} t={t_phys*1e3:5.2f}ms bed={bed_mean:6.2f}mm iron={iron_mean:6.2f}mm contacts={n_c:4d} KE_r={ke_reg:.2e}")

    wall = time.time() - t0
    print(f"Continuation done in {wall:.1f}s wall")

    tail = max(4, len(bed_h)//4)
    avg_bed = float(np.mean(bed_h[-tail:]))
    avg_iron = float(np.mean(iron_h[-tail:]))
    avg_contacts = float(np.mean(contacts[-tail:]))

    print(f"Tail avg: bed {avg_bed:.2f} mm, iron {avg_iron:.2f} mm, contacts {avg_contacts:.1f}")

    out = {
        'pos': cp.asnumpy(pos),
        'vel': cp.asnumpy(vel),
        'radius': cp.asnumpy(radius),
        'mat_type': cp.asnumpy(mat_type),
        'times': np.array(times),
        'bed_heights_mm': np.array(bed_h),
        'iron_heights_mm': np.array(iron_h),
        'iron_reg_contacts': np.array(contacts),
        'ke_reg': np.array(ke_r),
        'ke_iron': np.array(ke_i),
        'U_G': U_G,
        'pressure': 0.14,
        'extra_steps': EXTRA_STEPS,
        'avg_bed_tail': avg_bed,
        'avg_iron_tail': avg_iron,
        'avg_contacts_tail': avg_contacts,
        'source_state': state_file,
    }
    np.savez(f'{out_prefix}_continued.npz', **out)
    print(f"Saved {out_prefix}_continued.npz")

    return avg_bed, avg_iron, avg_contacts

if __name__ == "__main__":
    print("RCFX Rung 2 — Production continuation (longer time at 0.14 bar target)\n")

    # With iron (main evidence)
    bed_iron, iron_h, c_iron = run_continuation(
        'rung2_3000p_with_drag.npz',
        'rung2_prod_with_iron',
        is_iron_case=True
    )

    # No-iron control (for clean EMI)
    bed_no, _, _ = run_continuation(
        'rung2_3000p_noiron_with_drag.npz',
        'rung2_prod_no_iron',
        is_iron_case=False
    )

    emi = bed_iron / bed_no if bed_no > 0 else 0.0
    print("\n=== PRODUCTION EMI FROM CONTINUATION ===")
    print(f"With iron (tail): {bed_iron:.2f} mm")
    print(f"No iron  (tail): {bed_no:.2f} mm")
    print(f"EMI = {emi:.2f}× at extended physical time, U_G=0.066 m/s, 0.14 bar")
    print("Artifacts ready for patent update.")
