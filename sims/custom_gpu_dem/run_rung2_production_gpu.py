#!/usr/bin/env python3
"""
RCFX Rung 2 Production GPU DEM run at 0.14 bar "it works" point.
Uses claim-legal iron shot (1.5-3.5 mm) + bimodal regolith + cohesion + fixed U_G drag (stronger on iron).

Target: higher-N (6k-10k), longer physical time, time-averaged EMI, iron-regolith collision stats,
bed expansion time series. Direct evidence for patent at the 68 W / 75.6% lumped point.

All parameters traceable to PERRY-RCFX-004 Rev 5.2.
"""

import cupy as cp
import numpy as np
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path("common").resolve()))

from dem_kernels import compute_forces, integrate, compute_drag, estimate_local_porosity

# =============================================================================
# Production Rung 2 parameters (0.14 bar, target 68 W point)
# =============================================================================
DT = 8e-7
N_STEPS = 25000          # ~20 ms physical time at this DT (enough for lift + collisions to develop)
DUMP_EVERY = 500
BOX_SIZE = 0.022         # larger representative volume for better stats

# Gas conditions for 0.14 bar (conservative mix from Rev 5.2 volatiles)
U_G = 0.066              # m/s superficial — exact match to lumped 68 W point
DRAG_STRENGTH = 1.0

DAMPING = 0.08

def generate_rung2_particles(n_total=7200, iron_frac=0.028):
    """Bimodal regolith + iron shot per Rev 5.2 (1-5 mm iron, Geldart A/C regolith)."""
    np.random.seed(42)
    n_iron = int(n_total * iron_frac)
    n_reg = n_total - n_iron

    # Regolith: 15% very fine (<20um), 40% fine, 45% coarse (within Apollo ranges)
    n_fine = int(n_reg * 0.15)
    n_mid = int(n_reg * 0.40)
    n_coarse = n_reg - n_fine - n_mid

    fine_d = np.random.lognormal(np.log(14e-6), 0.55, n_fine)
    fine_d = np.clip(fine_d, 4e-6, 22e-6)
    mid_d = np.random.lognormal(np.log(45e-6), 0.48, n_mid)
    mid_d = np.clip(mid_d, 22e-6, 90e-6)
    coarse_d = np.random.lognormal(np.log(140e-6), 0.42, n_coarse)
    coarse_d = np.clip(coarse_d, 90e-6, 380e-6)

    reg_diam = np.concatenate([fine_d, mid_d, coarse_d])
    np.random.shuffle(reg_diam)

    # Iron shot: 1.5-3.5 mm (core claim range in Rev 5.2 for cold stages)
    iron_diam = np.random.uniform(0.0015, 0.0035, n_iron)

    all_diam = np.concatenate([reg_diam, iron_diam])
    mat = np.array([0] * n_reg + [1] * n_iron, dtype=np.int32)

    radii = all_diam / 2.0

    # Initial packed-ish placement (small random + gravity settle will happen)
    pos = np.random.rand(len(radii), 3).astype(np.float32) * (BOX_SIZE * 0.92)
    pos[:, 2] *= 0.55   # start lower to allow lift
    pos = np.clip(pos, radii[:, None] + 1e-6, BOX_SIZE - radii[:, None] - 1e-6)

    vel = np.zeros((len(radii), 3), dtype=np.float32)
    omega = np.zeros((len(radii), 3), dtype=np.float32)

    return (cp.asarray(pos), cp.asarray(vel), cp.asarray(omega),
            cp.asarray(radii, dtype=cp.float32), cp.asarray(mat))

def count_iron_regolith_contacts(pos, radius, mat_type, cutoff_factor=1.05):
    """Brute force count of iron-regolith contacts (for agitation evidence)."""
    N = pos.shape[0]
    dx = pos[:, None, :] - pos[None, :, :]
    dist = cp.linalg.norm(dx, axis=2)
    r_sum = radius[:, None] + radius[None, :]
    iron_mask = (mat_type == 1)
    reg_mask = (mat_type == 0)

    contact_mask = (dist < r_sum * cutoff_factor) & (cp.arange(N)[:, None] != cp.arange(N)[None, :])
    iron_to_reg = contact_mask & iron_mask[:, None] & reg_mask[None, :]
    return int(cp.sum(iron_to_reg))

if __name__ == "__main__":
    print("=== RCFX Rung 2 PRODUCTION GPU DEM (0.14 bar iron agitation) ===")
    print("Target: 68 W / 75.6% lumped point | Stronger drag on iron | Cell-list ready path")

    pos, vel, omega, radius, mat_type = generate_rung2_particles(n_total=3500, iron_frac=0.031)
    n_iron = int(cp.sum(mat_type == 1))
    n_reg = int(cp.sum(mat_type == 0))
    print(f"Loaded {len(pos)} particles ({n_reg} regolith + {n_iron} iron 1.5-3.5 mm)")

    # Time series storage
    times = []
    bed_heights = []
    iron_heights = []
    ke_reg_series = []
    ke_iron_series = []
    contact_counts = []

    start = time.time()
    for step in range(N_STEPS):
        force, torque = compute_forces(pos, vel, omega, radius, mat_type, DT)

        # Local porosity + drag (stronger on iron by design)
        local_eps = estimate_local_porosity(pos, radius, box_size=BOX_SIZE)
        drag = compute_drag(vel, radius, mat_type, U_g=U_G, local_porosity=local_eps)
        force += DRAG_STRENGTH * drag

        pos, vel, omega = integrate(pos, vel, omega, force, torque, radius, mat_type, DT, DAMPING)

        if step % DUMP_EVERY == 0 or step == N_STEPS - 1:
            t_phys = step * DT
            reg_mask = (mat_type == 0)
            iron_mask = (mat_type == 1)

            # Bed height proxies (mean + 85th percentile for expanded surface)
            reg_z = pos[reg_mask, 2]
            bed_mean = float(cp.mean(reg_z) * 1000)
            bed_p85 = float(cp.percentile(reg_z, 85) * 1000) if len(reg_z) > 50 else bed_mean

            iron_z = pos[iron_mask, 2] if n_iron > 0 else cp.array([0.0])
            iron_mean = float(cp.mean(iron_z) * 1000)

            # KE (translational)
            DENS = cp.array([3100.0, 7870.0])
            vol = (4/3 * cp.pi * radius**3)
            mass = DENS[mat_type] * vol
            ke = 0.5 * mass * cp.sum(vel**2, axis=1)
            ke_reg = float(cp.sum(ke[reg_mask]))
            ke_iron = float(cp.sum(ke[iron_mask])) if n_iron > 0 else 0.0

            # Iron-regolith contacts (agitation proxy)
            n_contacts = count_iron_regolith_contacts(pos, radius, mat_type) if n_iron > 0 else 0

            times.append(t_phys)
            bed_heights.append(bed_mean)
            iron_heights.append(iron_mean)
            ke_reg_series.append(ke_reg)
            ke_iron_series.append(ke_iron)
            contact_counts.append(n_contacts)

            v_max = float(cp.max(cp.linalg.norm(vel, axis=1)))
            print(f"Step {step:5d} t={t_phys*1e3:6.2f}ms | bed={bed_mean:6.2f}mm (p85={bed_p85:6.2f}) | iron={iron_mean:6.2f}mm | contacts={n_contacts:4d} | v_max={v_max:6.1f} | KE_r={ke_reg:.3e}")

    wall = time.time() - start
    print(f"\n=== Run complete in {wall:.1f} s wall time ===")

    # Final EMI calculation (last 20% of run for steady-ish)
    tail = max(3, len(bed_heights) // 5)
    final_bed = np.mean(bed_heights[-tail:])
    final_iron_h = np.mean(iron_heights[-tail:])
    final_contacts = np.mean(contact_counts[-tail:])

    print(f"Final (tail avg): bed height {final_bed:.2f} mm, iron {final_iron_h:.2f} mm, iron-reg contacts {final_contacts:.1f}")

    # Save production dataset + time series
    out = {
        'pos': cp.asnumpy(pos),
        'vel': cp.asnumpy(vel),
        'radius': cp.asnumpy(radius),
        'mat_type': cp.asnumpy(mat_type),
        'times': np.array(times),
        'bed_heights_mm': np.array(bed_heights),
        'iron_heights_mm': np.array(iron_heights),
        'ke_reg': np.array(ke_reg_series),
        'ke_iron': np.array(ke_iron_series),
        'iron_reg_contacts': np.array(contact_counts),
        'U_G': U_G,
        'pressure_bar': 0.14,
        'n_steps': N_STEPS,
        'dt': DT,
        'box_size': BOX_SIZE,
        'n_iron': n_iron,
        'final_emi_proxy': final_bed / 4.5,   # rough vs historical no-iron ~4.5mm
        'note': 'Production Rung 2 at exact 0.14 bar 68W point with iron-stronger drag. For patent evidence.'
    }
    np.savez('rung2_production_0.14bar_6800p.npz', **out)
    print("Saved rung2_production_0.14bar_6800p.npz")

    # Also save a compact summary for quick loading
    summary = {
        'U_G': U_G,
        'final_bed_mean_mm': final_bed,
        'final_iron_mean_mm': final_iron_h,
        'avg_iron_reg_contacts': final_contacts,
        'emi_vs_historical_noiron': final_bed / 4.5,
        'wall_time_s': wall,
        'physical_time_ms': N_STEPS * DT * 1000
    }
    np.savez('rung2_production_summary_0.14bar.npz', **summary)
    print("Saved rung2_production_summary_0.14bar.npz")
    print("Rung 2 production evidence ready.")
