#!/usr/bin/env python3
"""
High-N (6500) physical-lid sensitivity sweeps for RCFX patent evidence.
Uses the exact same lid+freeboard, SURFACE=0 (Rung1 no-coh), generate, stepper, and contact path
as the primary highN audit runs for direct comparability.

Sweeps (one at a time, around the nominal 2.0-3.5mm iron, 0.066 U_G):
- iron_diam (mm): 1.5, 2.0, 2.5, 3.0, 3.5
- vel_multiple / U_G (nominal 0.066): 0.055, 0.066, 0.077 (approx 3.7x-5.1x)
- fines_fraction (by adjusting n_fine in bimodal, keeping total N): higher/lower fines

Each sweep point: 400 steps (quick, ~10s), record EMI, reg_bed, iron_bed, dead_reg, ke_bias, inside, zmax.
Optionally --long for 1500 steps on interesting points.

Output: highn_sens_*.npz + summary print + appendable metrics for audit.

Usage (from sims/custom_gpu_dem/):
  python highn_sensitivity.py --sweep iron_diam --steps 400
  python highn_sensitivity.py --sweep ug --long   # 1500 steps on U_G sweep

After: direct np.load the outputs, update Rung1_HighN_Primary_Audit_6500.md + .json,
Exhibit B, COLD, etc. Then re-assemble package.

Cell-list available with --use-cell-list (default ON; for larger N experiments/scale-up). DEM knob tuning: for N=6500 lid-clustered, cs~0.0055-0.006 makes cell faster than brute Raw (~58 vs 27 steps/s). Use --n 8000+ to exercise scale-up (cell enables). Script uses recommended_cell_size via get_compute_forces_fn. Core patent evidence at N=6500.
"""
import argparse
import time
import os
from pathlib import Path
import cupy as cp
import numpy as np
import sys

sys.path.insert(0, str(Path(__file__).parent / "common"))

from dem_kernels import get_compute_forces_fn, DENSITY, SURFACE_ENERGY
from optimized_step import (
    make_optimized_stepper,
    make_lid_freeboard_damper,
    add_distributor_force_syncfree,
    add_wall_forces_syncfree,
    add_floor_force_syncfree,
)

# Import the proven generator from the primary highN migration (guarantees 100% inside states matching audit)
from migrate_rung1_highn import generate_highn_particles as proven_generate_highn, add_distributor_force as migrate_add_dist  # for fresh or continuation choice

# Match primary highN Rung1 setup exactly
N_HIGH = 6500
IRON_FRAC = 0.07
BOX = 0.018
U_G_NOM = 0.066
DAMP = 0.08
FREEBOARD_Z = 0.040
LID_Z = 0.060
DT = 6.5e-7
CHECKPOINT_DIR = Path("highn_sens_checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)

def generate_highn_particles(n_total=N_HIGH, with_iron=True, seed=42, fines_boost=0.0):
    """Wrapper around the proven generate from migrate_rung1_highn.
    Adds optional fines_boost for sensitivity (more small regolith particles) while preserving exact
    initial placement logic and 100% containment properties used in the primary audit.
    """
    pos, vel, radius, mat = proven_generate_highn(n_total=n_total, with_iron=with_iron, seed=seed)
    if fines_boost != 0.0 and with_iron:
        reg_mask = (mat == 0).get() if hasattr(mat, 'get') else (mat == 0)
        n_reg = int(np.sum(reg_mask))
        n_change = max(0, int(abs(fines_boost) * n_reg))
        if n_change > 0:
            idx = np.where(reg_mask)[0][:n_change]
            if fines_boost > 0:
                # more fines: smaller radii for first n_change reg
                new_r = np.random.uniform(10e-6, 50e-6, n_change).astype(np.float32)
                radius[idx] = cp.asarray(new_r) if hasattr(radius, 'get') else new_r
                # slightly lower starting z
                # re-place slightly lower for small particles
                low_z = cp.random.rand(n_change).astype(cp.float32) * 0.008 + new_r + 1e-6
                pos[idx, 2] = low_z if hasattr(pos, 'get') else low_z
            else:
                # negative: more coarse, larger radii
                new_r = np.random.uniform(150e-6, 350e-6, n_change).astype(np.float32)
                radius[idx] = cp.asarray(new_r) if hasattr(radius, 'get') else new_r
    return pos, vel, radius, mat

def save_checkpoint(pos, vel, radius, mat, step, prefix):
    out = CHECKPOINT_DIR / f"{prefix}_step{step:06d}.npz"
    np.savez(out, pos=cp.asnumpy(pos), vel=cp.asnumpy(vel),
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

def run_sweep_point(iron_diam_mm=None, ug=None, fines_boost=0.0, total_steps=400, log_every=100,
                    use_cell_list=True, prefix="sens", start_from_ckpt=None, no_iron_baseline_mm=3.2307, n_total=6500):
    """Run one sensitivity point (optimized, robust).
    - Starts fresh with proven generator (or from a previous highN ckpt for continuation-style sens).
    - Supports overriding iron diameter (re-clips positions after radius change).
    - Uses recommended cell_size when cell-list selected via get_compute_forces_fn.
    - Computes EMI internally using the provided no_iron_baseline_mm.
    - n_total: particle count; for scale-up (cell-list enables higher N); for ckpt continuation, N is taken from the ckpt.
    """
    # Force Rung1 no-coh
    SURFACE_ENERGY[:] = 0.0

    if start_from_ckpt:
        d = np.load(start_from_ckpt)
        pos = cp.asarray(d["pos"])
        vel = cp.asarray(d.get("vel", np.zeros_like(d["pos"])))
        radius = cp.asarray(d["radius"])
        mat = cp.asarray(d["mat"])
        start_step = int(d.get("step", 0))
        n_total = len(pos)  # dynamic from ckpt for continuation
        print(f"  Continuing from {start_from_ckpt} at step {start_step} (N={n_total})")
    else:
        if n_total > 6500:
            # For scale-up N>6500, ALWAYS start from a settled physical-lid ckpt (auto latest good one) then add reg particles.
            # Direct generate (even tall z) at high N leads to initial density blowup/nan/50% inside.
            # Addition to proven contained state + relaxation during steps preserves 100% inside (see audit + manual construction that produced the scale8000 ckpt).
            import glob
            cands = sorted(glob.glob(str(CHECKPOINT_DIR / "*step*.npz")))
            base_ckpt = cands[-1] if cands else "rung1_highn_with_iron_step003000.npz"
            d = np.load(base_ckpt)
            pos = cp.asarray(d["pos"])
            vel = cp.asarray(d.get("vel", np.zeros_like(d["pos"])))
            radius = cp.asarray(d["radius"])
            mat = cp.asarray(d["mat"])
            start_step = int(d.get("step", 0))
            base_n = len(pos)
            print(f"  Scale base from settled ckpt {os.path.basename(base_ckpt)} (N={base_n})")
            n_add = n_total - base_n
            if n_add > 0:
                reg_idx = cp.where(mat == 0)[0].get()
                np.random.seed(42)
                add_idx = np.random.choice(reg_idx, n_add, replace=True)
                pos_add = pos[add_idx].copy() + cp.random.randn(n_add, 3).astype(cp.float32) * (radius[add_idx, None] * 2.0)
                pos_add[:, 2] = cp.clip(pos_add[:, 2], 0.003, 0.045)
                pos_add = cp.clip(pos_add, radius[add_idx, None] + 1e-6, BOX - radius[add_idx, None] - 1e-6)
                vel_add = cp.zeros((n_add, 3), dtype=cp.float32)
                pos = cp.concatenate([pos, pos_add])
                vel = cp.concatenate([vel, vel_add])
                radius = cp.concatenate([radius, radius[add_idx].copy()])
                mat = cp.concatenate([mat, mat[add_idx].copy()])
                print(f"  Added +{n_add} jittered reg for N={n_total} (inside 100% from base; relaxes in run)")
        else:
            pos, vel, radius, mat = generate_highn_particles(n_total=n_total, with_iron=True, fines_boost=fines_boost)
            start_step = 0
            print(f"  Fresh generate N={n_total}")

    # Override iron size if requested (scale + re-clip)
    if iron_diam_mm is not None:
        iron_mask = (mat == 1)
        if cp.sum(iron_mask) > 0:
            target_r = iron_diam_mm / 2000.0
            current_mean_r = float(cp.mean(radius[iron_mask]))
            if current_mean_r > 1e-9:
                scale = target_r / current_mean_r
                radius[iron_mask] *= scale
            r_host = cp.asnumpy(radius) if hasattr(radius, 'get') else np.asarray(radius)
            pos_host = cp.asnumpy(pos) if hasattr(pos, 'get') else np.asarray(pos)
            pos_host = np.clip(pos_host, r_host[:, None] + 1e-6, BOX - r_host[:, None] - 1e-6)
            pos = cp.asarray(pos_host)
            radius = cp.asarray(r_host) if hasattr(radius, 'get') else r_host

    current_ug = ug if ug is not None else U_G_NOM

    lid_damper = make_lid_freeboard_damper(BOX, DENSITY, freeboard_start=FREEBOARD_Z, lid_z=LID_Z, damping=0.6)
    stepper = make_optimized_stepper(BOX, current_ug, DAMP, add_lid_func=lid_damper)

    max_r = float(cp.max(radius)) if hasattr(radius, 'max') else float(np.max(np.asarray(radius)))
    contact_fn = get_compute_forces_fn(N=n_total, use_cell_list=use_cell_list,
                                       cell_size=None, box_size=BOX, max_radius=max_r)

    # Use boosted distributor (from migrate) for fresh starts to match primary audit bed-build behavior and keep 100% inside.
    # Standard for --start-from-ckpt continuations.
    if start_from_ckpt is None:
        def add_dist(f, p, r, m): return migrate_add_dist(f, p, r, m)
    else:
        def add_dist(f, p, r, m): return add_distributor_force_syncfree(f, p, r, m, DENSITY)
    def add_wall(f, p, r, m): return add_wall_forces_syncfree(f, p, r, m, BOX, DENSITY)
    def add_floor(f, p, v, r, m): return add_floor_force_syncfree(f, p, v, r, m, DENSITY)

    print(f"  Running {total_steps} steps (iron_diam={iron_diam_mm or 'nominal'}, UG={current_ug:.3f}, fines_boost={fines_boost}, cell={use_cell_list}) ...")
    t0 = time.time()

    for s in range(total_steps):
        step = start_step + s + 1
        f_contact, tq = contact_fn(pos, vel, cp.zeros_like(vel), radius, mat, DT)
        pos, vel, _ = stepper(
            pos, vel, cp.zeros_like(vel),
            f_contact, tq, radius, mat, DT,
            add_dist, add_wall, add_floor
        )

        if (s + 1) % log_every == 0 or s == total_steps-1:
            m = compute_metrics(pos, vel, radius, mat, step, no_iron_baseline_mm)
            emi_str = f"EMI {m['emi']:.2f}×" if m.get('emi') else "EMI N/A"
            print(f"    step {step:4d}: reg {m['reg_bed']:.1f}±{m['reg_bed_std']:.1f} mm (iron {m['iron_bed']:.1f}), "
                  f"{emi_str}, dead% {m['dead_reg']:.1f}, vmean {m['vmean_reg']:.1f} m/s, "
                  f"inside {m['inside']:.1f}%, zmax {m['zmax']:.0f} mm, KE {m['ke_bias']:.0f}×", flush=True)

    elapsed = time.time() - t0
    final_step = start_step + total_steps
    m = compute_metrics(pos, vel, radius, mat, final_step, no_iron_baseline_mm)
    print(f"  Done in {elapsed:.1f}s ({total_steps/elapsed:.1f} steps/s)")

    out = save_checkpoint(pos, vel, radius, mat, final_step, prefix)
    print(f"  Saved {out.name}")

    return m, out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", choices=["iron_diam", "ug", "fines", "all"], default="iron_diam",
                        help="Which parameter to sweep")
    parser.add_argument("--steps", type=int, default=400, help="Steps per point (400 fast, 1500+ for stats)")
    parser.add_argument("--long", action="store_true", help="Use 1500 steps instead of default")
    parser.add_argument("--use-cell-list", action="store_true", default=True, help="Use cell-list hotpath with tuned cell_size (~0.006 for perf win at N=6500 lid; default ON after knob tuning)")
    parser.add_argument("--log-every", type=int, default=200, help="Logging interval (larger = better sustained GPU util, less host sync)")
    parser.add_argument("--no-iron-baseline-mm", type=float, default=3.2307, help="Reference no-iron reg bed mm from audit for EMI calc")
    parser.add_argument("--run-control", action="store_true", help="First run a pure no-iron control (fresh generate) to establish fresh baseline")
    parser.add_argument("--start-from-ckpt", type=str, default=None, help="Path to existing highN .npz to continue from (for delta sens around operating point). Auto-detects latest *step*.npz in highn_sens_checkpoints/ or falls back to the 3000-step physical state.")
    parser.add_argument("--campaign", action="store_true", help="Run comprehensive optimized campaign: iron_diam + ug + fines sweeps with tuned knobs (cell-list, 500 steps, good logging)")
    parser.add_argument("--n", type=int, default=6500, help="Total particles N (default 6500 for core claim-legal evidence; use higher e.g. 8000-10000 for scale-up tests enabled by cell-list hotpath)")
    args = parser.parse_args()

    steps = 1500 if args.long else args.steps
    log_every = getattr(args, 'log_every', 200) or max(200, steps // 5)

    # Auto-detect best starting ckpt for continuation (keeps everything in physical lid regime)
    if args.start_from_ckpt is None:
        import glob
        cands = sorted(glob.glob(str(CHECKPOINT_DIR / "*step*.npz")))
        if cands:
            args.start_from_ckpt = cands[-1]
            print(f"Auto-selected start ckpt: {args.start_from_ckpt}")
        else:
            args.start_from_ckpt = "rung1_highn_with_iron_step003000.npz"
            print("Falling back to known 3000-step state")

    # For explicit higher/lower N (scale-up or test), force fresh generate (ckpt continuation would have wrong N)
    if args.n != 6500:
        if args.start_from_ckpt is not None:
            print(f"Note: --n {args.n} != 6500; forcing fresh generate (scale-up test, ignoring auto ckpt {args.start_from_ckpt})")
        args.start_from_ckpt = None

    N = args.n
    print("=== High-N Rung1 Physical-Lid Sensitivity Sweeps (optimized) ===")
    print(f"N={N}, lid physical, Rung1 no-coh, contact via get_compute_forces_fn (cell-list default with tuned cs~0.006 for perf)")
    print(f"Steps per point: {steps}, log_every={log_every}")
    print(f"Using no-iron baseline {args.no_iron_baseline_mm:.4f} mm for EMI")

    baseline = args.no_iron_baseline_mm

    if args.run_control:
        print("\n=== Running no-iron control first ===")
        m_ctrl, _ = run_sweep_point(iron_diam_mm=None, total_steps=steps, log_every=log_every,
                                    use_cell_list=args.use_cell_list, prefix="no_iron_ctrl",
                                    start_from_ckpt=None, no_iron_baseline_mm=baseline, n_total=args.n)
        baseline = m_ctrl["reg_bed"]
        print(f"Control established fresh baseline: {baseline:.2f} mm")

    results = []

    if args.campaign or args.sweep in ("iron_diam", "all"):
        print("\n--- Iron diameter sweep (core knob for agitation) ---")
        for dmm in [1.5, 2.0, 2.5, 3.0, 3.5]:
            m, out = run_sweep_point(iron_diam_mm=dmm, total_steps=steps, log_every=log_every,
                                     use_cell_list=args.use_cell_list, prefix=f"iron{dmm*10:.0f}",
                                     start_from_ckpt=args.start_from_ckpt, no_iron_baseline_mm=baseline, n_total=args.n)
            results.append(("iron_diam_mm", dmm, m))

    if args.campaign or args.sweep in ("ug", "all"):
        print("\n--- U_G sweep ---")
        for ug in [0.055, 0.066, 0.077]:
            m, out = run_sweep_point(ug=ug, total_steps=steps, log_every=log_every,
                                     use_cell_list=args.use_cell_list, prefix=f"ug{ug*1000:.0f}",
                                     start_from_ckpt=args.start_from_ckpt, no_iron_baseline_mm=baseline, n_total=args.n)
            results.append(("ug", ug, m))

    if args.campaign or args.sweep in ("fines", "all"):
        print("\n--- Fines boost sweep ---")
        for fb in [0.0, 0.15, -0.15]:
            m, out = run_sweep_point(fines_boost=fb, total_steps=steps, log_every=log_every,
                                     use_cell_list=args.use_cell_list, prefix=f"fines{fb*100:.0f}",
                                     start_from_ckpt=args.start_from_ckpt, no_iron_baseline_mm=baseline, n_total=args.n)
            results.append(("fines_boost", fb, m))

    print("\n=== CAMPAIGN / SWEEP SUMMARY (EMI vs baseline " + f"{baseline:.2f} mm) ===")
    for key, val, m in results:
        emi = m.get("emi") or 0.0
        print(f"{key}={val}: reg_bed={m['reg_bed']:.1f} mm, EMI={emi:.2f}x, dead%={m['dead_reg']:.1f}, KEbias={m['ke_bias']:.0f}x, inside={m['inside']:.1f}%")

    print("\nOptimized run complete. Data in highn_sens_checkpoints/. Load .npz, append to audit, rebuild package.")
    print("For scale-up use --n 8000+ + --use-cell-list: runner auto base+add for contained 100% from settled ckpt (see audit scale sections + scale8000_* and new 10k+ ckpts).")

    # Auto tiny report for audit ingestion
    try:
        import json, time as _t
        report = {"sweep": getattr(args, "sweep", "unknown"), "steps_per_point": steps, "used_cell_list": bool(getattr(args, "use_cell_list", False)), "baseline_mm": float(baseline), "n_total": int(N), "results": []}
        for key, val, m in results:
            report["results"].append({"param": key, "value": val, "reg_bed": float(m.get("reg_bed", 0)), "emi": float(m.get("emi", 0) or 0), "dead_pct": float(m.get("dead_reg", 0)), "inside_pct": float(m.get("inside", 0)), "ke_bias": float(m.get("ke_bias", 0))})
        rpath = CHECKPOINT_DIR / f"report_{getattr(args, 'sweep', 'run')}_{int(_t.time())}.json"
        with open(rpath, "w") as f: json.dump(report, f, indent=2)
        print(f"Auto-report saved: {rpath}")
    except Exception:
        pass

if __name__ == "__main__":
    main()
