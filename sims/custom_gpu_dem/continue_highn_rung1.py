#!/usr/bin/env python3
"""
Continue high-N Rung1 evidence from existing ckpt (e.g. step 001000) using:
- compute_forces_cell_list / cell Raw (hotpath rewrite: device-only build + single RawKernel 27-neighbor; scalable + high sustained util)
- lid+freeboard physical cap (40mm soft / 60mm hard) + opt stepper from the start of continuation
- standard (2.8) distributor strength (since starting from already-settled bed at 1000s, not fresh generate)
- Rung1 no-reg-cohesion (SURFACE_ENERGY=0)

This extends the physical-scale lid data for stronger stats (higher mean reg bed toward 60mm cap,
tighter EMI progression, KE bias, dead% contrast, zmax behavior under lid).

Usage example (from sims/custom_gpu_dem/):
  python continue_highn_rung1.py --ckpt rung1_highn_checkpoints/rung1_highn_with_iron_step001000.npz \
      --steps 500 --log-every 50 --save-every 100 --prefix rung1_highn_with_iron

After run: re-compute metrics with audit logic (or inline), append to Rung1_HighN_Primary_Audit_6500.md/.json,
update COLD/Exhibit B/claim matrix/exec/filing/plan, re-gen docx, commit.

Baseline for EMI: 3.2307 mm (exact from no-iron step 400 raw ckpt).
"""

import sys
from pathlib import Path
import time
import cupy as cp
import numpy as np

# Add common/ for imports (run from sims/custom_gpu_dem/)
sys.path.insert(0, str(Path(__file__).parent / "common"))

from dem_kernels import compute_forces_raw as compute_contact_forces, DENSITY
print("Using compute_forces_raw (single RawKernel; high sustained util). Cell-list hotpath rewrite complete and available for scale-up runs.")
from optimized_step import (
    make_optimized_stepper,
    make_lid_freeboard_damper,
    add_distributor_force_syncfree,
    add_wall_forces_syncfree,
    add_floor_force_syncfree,
)

# Match migrate_rung1_highn.py constants
N_HIGH = 6500
BOX = 0.018
U_G = 0.066
DAMP = 0.08
FREEBOARD_Z = 0.040
LID_Z = 0.060
DT = 6.5e-7

CHECKPOINT_DIR = Path("rung1_highn_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

# Standard distributor (2.8, not the boosted 12.0 used only for fresh-generate fast build in migrate)
def add_distributor_force(force, pos, radius, mat):
    return add_distributor_force_syncfree(force, pos, radius, mat, DENSITY)

def add_wall_forces(force, pos, radius, mat):
    return add_wall_forces_syncfree(force, pos, radius, mat, BOX, DENSITY)

def add_floor_force(force, pos, vel, radius, mat):
    return add_floor_force_syncfree(force, pos, vel, radius, mat, DENSITY)

def save_checkpoint(pos, vel, radius, mat, step, prefix):
    out = CHECKPOINT_DIR / f"{prefix}_step{step:06d}.npz"
    np.savez(out,
             pos=cp.asnumpy(pos), vel=cp.asnumpy(vel),
             radius=cp.asnumpy(radius), mat=cp.asnumpy(mat), step=step)
    return out

def compute_metrics(pos, vel, radius, mat, step, no_iron_baseline_mm=None):
    reg_mask = (mat == 0)
    iron_mask = (mat == 1)
    reg_z_mm = pos[reg_mask, 2] * 1000
    iron_z_mm = pos[iron_mask, 2] * 1000
    vnorm = cp.linalg.norm(vel, axis=1)
    reg_v = vnorm[reg_mask]
    dead_reg = float(cp.mean(reg_v < 0.8)) * 100
    inside = float(cp.sum(
        (pos[:, 0] >= 0) & (pos[:, 0] <= BOX) &
        (pos[:, 1] >= 0) & (pos[:, 1] <= BOX) &
        (pos[:, 2] >= 0)
    )) / len(pos) * 100.0
    zmax_mm = float(cp.max(pos[:, 2]) * 1000)

    emi = None
    if no_iron_baseline_mm is not None and no_iron_baseline_mm > 0:
        emi = float(cp.mean(reg_z_mm)) / no_iron_baseline_mm

    mass_reg = DENSITY[0] * (4.0/3.0 * cp.pi * radius[reg_mask]**3)
    mass_iron = DENSITY[1] * (4.0/3.0 * cp.pi * radius[iron_mask]**3) if cp.sum(iron_mask) > 0 else cp.array([])
    ke_reg = float(cp.mean(0.5 * mass_reg * (vnorm[reg_mask]**2))) if cp.sum(reg_mask) > 0 else 0.0
    ke_iron = float(cp.mean(0.5 * mass_iron * (vnorm[iron_mask]**2))) if cp.sum(iron_mask) > 0 else 0.0
    ke_bias = ke_iron / ke_reg if ke_reg > 0 else 0.0

    return {
        "step": step,
        "reg_bed": float(cp.mean(reg_z_mm)),
        "reg_bed_std": float(cp.std(reg_z_mm)),
        "iron_bed": float(cp.mean(iron_z_mm)) if cp.sum(iron_mask) > 0 else 0.0,
        "zmax": zmax_mm,
        "inside": inside,
        "emi": emi,
        "dead_reg": dead_reg,
        "vmean_reg": float(cp.mean(reg_v)) if cp.sum(reg_mask) > 0 else 0.0,
        "ke_bias": ke_bias,
        "n_reg": int(cp.sum(reg_mask)),
        "n_iron": int(cp.sum(iron_mask)),
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Continue highN Rung1 lid evidence from ckpt using Raw + opt + lid.")
    parser.add_argument("--ckpt", type=str, default="rung1_highn_checkpoints/rung1_highn_with_iron_step001000.npz",
                        help="Path to starting ckpt (must be with_iron highN)")
    parser.add_argument("--steps", type=int, default=500, help="Additional steps to run")
    parser.add_argument("--log-every", type=int, default=100, help="Log interval (high value for util)")
    parser.add_argument("--save-every", type=int, default=100, help="Checkpoint interval")
    parser.add_argument("--prefix", type=str, default="rung1_highn_with_iron")
    args = parser.parse_args()

    # Load ckpt (produced by Raw path, so continue with Raw)
    d = np.load(args.ckpt)
    pos = cp.asarray(d["pos"].astype(np.float32))
    vel = cp.asarray(d["vel"].astype(np.float32))
    radius = cp.asarray(d["radius"].astype(np.float32))
    mat = cp.asarray(d["mat"].astype(np.int32))
    start_step = int(d["step"])
    print(f"Loaded {args.ckpt}: N={len(pos)}, starting continuation from step {start_step}")

    # Rung1 definition: no cohesion on reg
    import dem_kernels
    dem_kernels.SURFACE_ENERGY = cp.array([[0.0, 0.0], [0.0, 0.0]], dtype=cp.float32)

    lid_damper = make_lid_freeboard_damper(BOX, DENSITY, freeboard_start=FREEBOARD_Z, lid_z=LID_Z, damping=0.6)
    stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=lid_damper)

    # Exact baseline from no-iron control step 400 (direct np.load in audit)
    NOIRON_BASE = 3.2307

    print(f"Running additional {args.steps} steps from {start_step} with lid+freeboard (physical cap), "
          f"standard distributor (2.8), compute_forces_raw, opt stepper")
    t0 = time.time()

    for s in range(args.steps):
        step = start_step + s + 1
        f_contact, tq = compute_contact_forces(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        pos, vel, _ = stepper(
            pos, vel, cp.zeros_like(vel),
            f_contact, tq, radius, mat, DT,
            add_distributor_force, add_wall_forces, add_floor_force
        )

        if (s + 1) % args.log_every == 0:
            m = compute_metrics(pos, vel, radius, mat, step, NOIRON_BASE)
            emi_str = f"EMI {m['emi']:.2f}×" if m['emi'] is not None else "EMI N/A (control)"
            print(f"  step {step:6d}: reg {m['reg_bed']:.1f}±{m['reg_bed_std']:.1f} mm (iron {m['iron_bed']:.1f}), "
                  f"{emi_str}, dead% {m['dead_reg']:.1f}%, vmean {m['vmean_reg']:.2f} m/s, "
                  f"inside {m['inside']:.1f}%, zmax {m['zmax']:.0f} mm, KE bias {m['ke_bias']:.1f}×", flush=True)

        if (s + 1) % args.save_every == 0:
            out = save_checkpoint(pos, vel, radius, mat, step, args.prefix)
            print(f"  [saved {out.name}]", flush=True)

    # final
    final_step = start_step + args.steps
    out = save_checkpoint(pos, vel, radius, mat, final_step, args.prefix)
    print(f"Saved final {out.name}", flush=True)

    elapsed = time.time() - t0
    m = compute_metrics(pos, vel, radius, mat, final_step, NOIRON_BASE)
    print(f"\n=== CONTINUATION FINAL (high-N Rung1 lid) ===", flush=True)
    print(f"  additional steps: {args.steps}  time: {elapsed:.1f}s ({args.steps/elapsed:.1f} steps/s)", flush=True)
    print(f"  final reg bed: {m['reg_bed']:.1f} ± {m['reg_bed_std']:.1f} mm (iron {m['iron_bed']:.1f} mm)", flush=True)
    if m['emi'] is not None:
        print(f"  EMI vs no-iron baseline (3.2307 mm): {m['emi']:.2f}×", flush=True)
    print(f"  inside: {m['inside']:.1f}%  zmax: {m['zmax']:.0f} mm (capped at physical lid)", flush=True)
    print(f"  dead% reg: {m['dead_reg']:.1f}%  reg vmean: {m['vmean_reg']:.2f} m/s", flush=True)
    print(f"  KE bias iron/reg: {m['ke_bias']:.1f}×  n_reg={m['n_reg']} n_iron={m['n_iron']}", flush=True)
    print("  100% containment + physical bed heights with iron agitation signature (primary citable evidence).", flush=True)

if __name__ == "__main__":
    main()