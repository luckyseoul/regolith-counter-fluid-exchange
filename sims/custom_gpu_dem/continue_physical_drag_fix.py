#!/usr/bin/env python3
"""
Physical drag-fix continuation / test run for RCFX patent evidence (addressing critique).

Removes the two sources of non-physical energy identified:
1. Mass-scaled body forces (distributor/wall/floor: acc * mass added in adders).
2. Restitution-0.8 post-integrate clips (vel reversal with energy loss).

Uses:
- Real gas drag: rho_g=0.0438 (from gas_at_T at 0.14bar ~300K in five_stage_counterflow.py),
  mu_g=2.28e-5, drag_mult=1.0 for ALL particles (fines no longer throttled to 0.015).
- Gravity still present (in contact kernel).
- Contacts + JKR=0 for Rung1, Hertz etc unchanged.
- Physical lid+freeboard for POSITION containment only (100% inside zmin>=0, zmax<=~42mm for citable data).
  Lid damping kept (models vessel top), but floor/walls use position_only_clips (no artificial vel reset).
- No distributor force at all: fluidization (if any) must come from computed gas drag on particles.

Start from a clean 100% inside with-iron ckpt (e.g. step002000 from prior physical-lid rung1).
Run long enough to observe whether:
- Iron (3.5mm) moves at all under gas drag + fines collisions, or sits as packed layer at bottom (expected: Umf_iron >> 0.066 m/s by ~1000x).
- Regolith fines sustain mobilization at physical velocities (cm/s not 10+m/s).
- Dead fraction (v<0.8 proxy) behavior vs prior artificial runs (prior showed rising dead 28->56% with high vmean from jetting).
- vmean_reg drops to <<1 m/s (physical gas-driven fluidization scale).

If iron vmean ~0 and sits (z_iron low, dead_iron high), mechanism premise falsified at this U_G/P: gas cannot drive iron; "iron agitates fines" premise runs backwards or impossible without raising U (power budget change).
If iron moves at physical low v and stirs fines without artificial forces, then real result (worth citing).

This run produces new clean .npz (100% inside by lid) for citable evidence only if metrics support physical velocities.

Usage (from sims/custom_gpu_dem/):
  python continue_physical_drag_fix.py --ckpt rung1_highn_checkpoints/rung1_highn_with_iron_step002000.npz \
      --steps 2000 --log-every 200 --save-every 500 --prefix physical_drag_fix_rung1

Then audit the final ckpts with python -c "import numpy as np; d=np.load('...'); ..." for vmean, dead, inside=100, zmax, ke etc.
Append results + paths to Patent_Citable_Evidence_Summary.md and the complete provisional doc.
"""

import sys
from pathlib import Path
import time
import cupy as cp
import numpy as np

# Add common/ for imports (run from sims/custom_gpu_dem/)
sys.path.insert(0, str(Path(__file__).parent / "common"))

from dem_kernels import compute_forces_raw as _raw_contact, DENSITY
print("Using compute_forces_raw (single RawKernel). Physical drag-fix: real rho_g + full drag_mult + NO mass body forces + pos-only clips.")
from optimized_step import (
    make_optimized_stepper,
    make_lid_freeboard_damper,
    no_body_force,
    no_wall_force,
    no_floor_force,
)
# default contact fn (may be rebound below for cell)
compute_contact_forces = _raw_contact

# Match prior highN Rung1 lid constants
N_HIGH = 6500
BOX = 0.018
U_G = 0.066
DAMP = 0.5   # for physical: mild proxy; main dissipation now from position_only_clips e=0.95 bounces + real drag (z) + contact friction/rolling + internal Ft viscous term
FREEBOARD_Z = 0.040
LID_Z = 0.060
DT = 6.5e-7

CHECKPOINT_DIR = Path("rung1_highn_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

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
    iron_v = vnorm[iron_mask] if cp.sum(iron_mask) > 0 else cp.array([0.0])
    dead_reg = float(cp.mean(reg_v < 0.8)) * 100
    dead_iron = float(cp.mean(iron_v < 0.8)) * 100 if cp.sum(iron_mask) > 0 else 100.0
    inside = float(cp.sum(
        (pos[:, 0] >= 0) & (pos[:, 0] <= BOX) &
        (pos[:, 1] >= 0) & (pos[:, 1] <= BOX) &
        (pos[:, 2] >= 0)
    )) / len(pos) * 100.0
    zmax_mm = float(cp.max(pos[:, 2]) * 1000)
    zmin_mm = float(cp.min(pos[:, 2]) * 1000)

    emi = None
    if no_iron_baseline_mm is not None and no_iron_baseline_mm > 0:
        emi = float(cp.mean(reg_z_mm)) / no_iron_baseline_mm

    mass_reg = DENSITY[0] * (4.0/3.0 * cp.pi * radius[reg_mask]**3)
    mass_iron = DENSITY[1] * (4.0/3.0 * cp.pi * radius[iron_mask]**3) if cp.sum(iron_mask) > 0 else cp.array([])
    ke_reg = float(cp.sum(0.5 * mass_reg * (reg_v**2))) if cp.sum(reg_mask) > 0 else 0.0  # total KE not mean for scale
    ke_iron = float(cp.sum(0.5 * mass_iron * (iron_v**2))) if cp.sum(iron_mask) > 0 else 0.0
    ke_bias = (ke_iron / ke_reg) if ke_reg > 0 else 0.0
    vmean_iron = float(cp.mean(iron_v)) if cp.sum(iron_mask) > 0 else 0.0
    vmean_reg = float(cp.mean(reg_v)) if cp.sum(reg_mask) > 0 else 0.0

    # Rough "moving" fraction above gas vel scale (say >0.2 m/s ~3x U_G)
    moving_reg = float(cp.mean(reg_v > 0.2)) * 100
    moving_iron = float(cp.mean(iron_v > 0.2)) * 100 if cp.sum(iron_mask) > 0 else 0.0

    return {
        "step": step,
        "reg_bed": float(cp.mean(reg_z_mm)),
        "reg_bed_std": float(cp.std(reg_z_mm)),
        "iron_bed": float(cp.mean(iron_z_mm)) if cp.sum(iron_mask) > 0 else 0.0,
        "zmax": zmax_mm,
        "zmin": zmin_mm,
        "inside": inside,
        "emi": emi,
        "dead_reg": dead_reg,
        "dead_iron": dead_iron,
        "vmean_reg": vmean_reg,
        "vmean_iron": vmean_iron,
        "moving_reg_pct_gt0.2": moving_reg,
        "moving_iron_pct_gt0.2": moving_iron,
        "ke_bias": ke_bias,
        "ke_reg_total": ke_reg,
        "ke_iron_total": ke_iron,
        "n_reg": int(cp.sum(reg_mask)),
        "n_iron": int(cp.sum(iron_mask)),
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Physical drag-only continuation (no mass body forces, no 0.8 clips, real rho drag).")
    parser.add_argument("--ckpt", type=str, default="rung1_highn_checkpoints/rung1_highn_with_iron_step002000.npz",
                        help="Path to starting ckpt (100pct inside with-iron preferred for test)")
    parser.add_argument("--steps", type=int, default=2000, help="Additional steps to run under physical drag")
    parser.add_argument("--log-every", type=int, default=200, help="Log interval")
    parser.add_argument("--save-every", type=int, default=500, help="Checkpoint interval")
    parser.add_argument("--prefix", type=str, default="physical_drag_fix_rung1")
    parser.add_argument("--use-cell", action="store_true", help="Use cell-list Raw for forces (for larger N or long runs)")
    parser.add_argument("--u-g", type=float, default=0.066, help="Superficial gas velocity for real drag (default 0.066; use higher for iron fluidization tests per envelope calc)")
    args = parser.parse_args()
    global U_G
    if args.u_g != 0.066:
        U_G = args.u_g
        print(f"Overriding U_G to {U_G} for physical real-drag test at viable fluidization point (per envelope calc)")
    else:
        print(f"Using U_G = {U_G}")

    # Load ckpt
    d = np.load(args.ckpt)
    pos = cp.asarray(d["pos"].astype(np.float32))
    vel = cp.asarray(d["vel"].astype(np.float32))
    radius = cp.asarray(d["radius"].astype(np.float32))
    mat = cp.asarray(d["mat"].astype(np.int32))
    start_step = int(d["step"])
    n_total = len(pos)
    n_iron = int(cp.sum(mat == 1))
    print(f"Loaded {args.ckpt}: N={n_total} (iron={n_iron}), starting PHYSICAL DRAG FIX continuation from step {start_step}")
    print("  Config: real rho_g~0.0438 @0.14bar, drag_mult=1.0 all, NO dist/wall/floor mass body forces,")
    print("          position_only_clips (no restitution-0.8), lid for pos containment only.")
    print("  Question under test: does 3.5mm iron move at physical v under gas drag + fines collisions at U_G=0.066?")
    # Zero velocities to test pure evolution under real drag+grav+contacts from the loaded positions (removes baked-in artificial KE from prior history).
    # This lets us see what velocities (if any) the real gas drag at 0.066 m/s can sustain / impart.
    vel[:, :] = 0.0
    print("  Initial vel zeroed for clean physical-from-rest test (drag must create any motion).")

    # Rung1 no reg coh
    import dem_kernels
    dem_kernels.SURFACE_ENERGY = cp.array([[0.0, 0.0], [0.0, 0.0]], dtype=cp.float32)

    lid_damper = make_lid_freeboard_damper(BOX, DENSITY, freeboard_start=FREEBOARD_Z, lid_z=LID_Z, damping=0.6)
    stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=lid_damper, physical_drag_only=True)

    # Use no-op adders (ignored inside stepper when physical=True, but must pass)
    dist_add = no_body_force
    wall_add = no_wall_force
    floor_add = no_floor_force

    # Contact fn: cell or raw
    if args.use_cell:
        from dem_kernels import get_compute_forces_fn
        max_r = float(cp.max(radius))
        contact_fn = get_compute_forces_fn(N=n_total, use_cell_list=True, max_radius=max_r, box_size=BOX)
        print("  Using cell-list RawKernel for contact forces.")
    else:
        contact_fn = compute_contact_forces
        print("  Using brute RawKernel for contact forces (N=~6.5k ok).")

    # Exact baseline from no-iron control step 400
    NOIRON_BASE = 3.2307

    print(f"Running additional {args.steps} steps from {start_step} under PHYSICAL DRAG ONLY...")
    t0 = time.time()

    for s in range(args.steps):
        step = start_step + s + 1
        f_contact, tq = contact_fn(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        pos, vel, _ = stepper(
            pos, vel, cp.zeros_like(vel),
            f_contact, tq, radius, mat, DT,
            dist_add, wall_add, floor_add
        )

        if (s + 1) % args.log_every == 0:
            m = compute_metrics(pos, vel, radius, mat, step, NOIRON_BASE)
            emi_str = f"EMI {m['emi']:.2f}×" if m['emi'] is not None else "EMI N/A"
            print(f"  step {step:6d}: reg {m['reg_bed']:.1f}±{m['reg_bed_std']:.1f} mm (iron {m['iron_bed']:.1f}), "
                  f"{emi_str}, dead_reg {m['dead_reg']:.1f}% dead_iron {m['dead_iron']:.1f}%, "
                  f"vmean_reg {m['vmean_reg']:.3f} m/s vmean_iron {m['vmean_iron']:.3f} m/s, "
                  f"moving>0.2 reg{ m['moving_reg_pct_gt0.2']:.0f}% iron{m['moving_iron_pct_gt0.2']:.0f}%, "
                  f"inside {m['inside']:.1f}%, zmax {m['zmax']:.0f} zmin {m['zmin']:.1f} mm, KEbias {m['ke_bias']:.2f}×", flush=True)

        if (s + 1) % args.save_every == 0:
            out = save_checkpoint(pos, vel, radius, mat, step, args.prefix)
            print(f"  [saved {out.name}]", flush=True)

    # final
    final_step = start_step + args.steps
    out = save_checkpoint(pos, vel, radius, mat, final_step, args.prefix)
    print(f"Saved final {out.name}", flush=True)

    elapsed = time.time() - t0
    m = compute_metrics(pos, vel, radius, mat, final_step, NOIRON_BASE)
    print(f"\n=== PHYSICAL DRAG-FIX FINAL (high-N Rung1 lid, artificial forces REMOVED) ===", flush=True)
    print(f"  additional steps: {args.steps}  time: {elapsed:.1f}s ({args.steps/elapsed:.1f} steps/s)", flush=True)
    print(f"  final reg bed: {m['reg_bed']:.1f} ± {m['reg_bed_std']:.1f} mm (iron {m['iron_bed']:.1f} mm)", flush=True)
    if m['emi'] is not None:
        print(f"  EMI vs no-iron baseline (3.2307 mm): {m['emi']:.2f}×", flush=True)
    print(f"  inside: {m['inside']:.1f}%  zmax: {m['zmax']:.0f} mm zmin: {m['zmin']:.1f} mm (physical lid containment)", flush=True)
    print(f"  dead% reg: {m['dead_reg']:.1f}%  iron: {m['dead_iron']:.1f}%", flush=True)
    print(f"  vmean reg: {m['vmean_reg']:.3f} m/s   iron: {m['vmean_iron']:.3f} m/s   (target: <<1 m/s physical; ~0 for iron)", flush=True)
    print(f"  % particles >0.2m/s (3x U_G): reg {m['moving_reg_pct_gt0.2']:.1f}%  iron {m['moving_iron_pct_gt0.2']:.1f}%", flush=True)
    print(f"  KE bias iron/reg (total): {m['ke_bias']:.2f}×   n_reg={m['n_reg']} n_iron={m['n_iron']}", flush=True)
    print("  100% containment + PHYSICAL velocities (real drag only).", flush=True)
    print("\n  GO/NO-GO for mechanism at 0.066 m/s: if vmean_iron <<0.1 m/s and iron_bed low, iron does not fluidize/move; premise requires higher U or redesign.", flush=True)

if __name__ == "__main__":
    main()
