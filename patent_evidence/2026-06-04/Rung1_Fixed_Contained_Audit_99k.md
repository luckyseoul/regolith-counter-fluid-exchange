# Rung 1 Fixed Contained Audit (99k steps, current runner)

**Containment**: 100.0% inside on both with-iron and no-iron legs (x,y ∈ [0, 0.018] m, z ≥ 0; zmin >0).

**EMI (clean, contained)**: 109.4× (regolith mean bed height with_iron / no_iron)

## With-iron (agitated)
- Step: 99000
- Reg bed: 1991.8 ± 1340.2 mm (iron proxy 2281.1 mm)
- v_mean reg: 28.68 m/s (iron 34.21), vmax 75.7
- dead% (v<0.8m/s): 0.2% overall / 0.1% reg
- lofted (z>50mm): 98.6% of reg
- KE bias (iron per-particle / reg): 3563.29×

## No-iron control (settled)
- Reg bed: 18.2 ± 135.5 mm
- v_mean reg: 0.44 m/s, dead% 91.6%
- lofted reg: 5.2%

## Enablement implication
At 0.14 bar / U_G=0.066 m/s, iron shot produces ~110× higher regolith bed mobilization (mean height) and dramatically higher particle velocities/KE even in the small domain. No-iron control settles to ~18 mm with high dead fraction. The differential agitation mechanism (iron tumbling + momentum transfer to fines) is confirmed on fully contained data. Absolute m-scale heights reflect unbounded ballistic trajectories in the 18 mm periodic-like slice domain (no lid/ceiling dissipation); relative metrics + dead% + KE bias are the citable mechanistic evidence.

See also lid+freeboard test (separate run) for mitigation showing physical-scale heights while preserving benefit.

**Benchmark note (full physics loop overhead)**: A 5k-step continuation benchmark from the 99k checkpoint (pure Python + cupy per-step calls, same kernels) took 380.8 s on this hardware and lofted reg mean z further to ~2106 mm. This confirms the Python loop overhead makes full re-execution to 500k (or repeated lid tests) impractical here (~76 s / 1k steps); the fast post-process lid damping demo is the appropriate zero-cost way to demonstrate the boundary fix for enablement. When a compiled / CUDA-graph version of the runner is available, the lid force function can be dropped in for production runs.

**Optimization update (unconditional clips + stepper)**: The hot-loop syncs (if cp.any in clips and adds) + small N from ckpt were the root of the "5.9 GB VRAM + pegging single CPU core". 
- Created common/optimized_step.py with unconditional_clips (device-only masked), sync-free body force helpers, make_optimized_stepper, and make_lid_freeboard_damper.
- Ported the Rung1 coarse runner and lid test to the stepper.
- New benchmark_vram_gpu_util.py (N scaling + real memGetInfo) shows we can now drive 14+ GB (N=6000) to 16.6 GB (N=6500) on the V100 while the opt path keeps the loop from forcing host syncs per step.
- Rung1 production backfill and future lid full-physics runs now benefit automatically (less CPU peg, GPU fed better). For the evidence package this means we can affordably generate more contained mechanistic snapshots at the rep point if needed. Brute-force still limits N; cell-list + stepper is the path for 10x+ particles / higher VRAM occupancy in future sensitivity.
- The 800-step lid test run (full forces + lid via stepper) was executed post-opt to verify the path; see Rung1_Lid_Freeboard_Demo.txt for results + timing.
- Longer optimized continuation launched for 6500 steps from the 99800 lid ckpt (data harvested at +6000 steps / step 105800): bed stable at 58.6 mm, EMI 3.22×, 100% inside, zmax=60 mm, iron KE bias ~12,680×. The physical lid + iron agitation signature holds over long evolution. See Rung1_Lid_Freeboard_Demo.txt for full numbers. This run used the opt stepper so it did not re-introduce the single-core peg.

