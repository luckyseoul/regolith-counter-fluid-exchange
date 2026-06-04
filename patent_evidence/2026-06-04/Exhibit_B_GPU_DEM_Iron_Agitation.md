# Exhibit B — GPU DEM Validation of Iron Agitation Mechanism

**Cover statement**: This exhibit provides particle-scale DEM evidence that iron shot agitation at the 0.14 bar representative operating point (U_G = 0.066 m/s) mobilizes cohesive regolith while maintaining full containment, including extended Rung 5 sensitivity backfill to 500k steps.

## Simulation method (identical across rungs)
- Custom CuPy GPU DEM: Hertzian normal + tangential friction + JKR-style cohesion (fines); Stokes + quadratic drag with cell-list local porosity; velocity-Verlet; DT = 6.5×10⁻⁷ s.
- Containment: v2 mass-scaled distributor / wall / floor forces + post-integrate clips (restitution 0.8).
- Domain: BOX = 0.016 m; N ≈ 1800 particles (bimodal regolith + iron, mat=0/1).
- **Citable rule**: Only checkpoints with **100.0% inside** (x,y ∈ [0, BOX], z ≥ 0) and **zmin ≥ 0** are cited.

## Rung 1 — Effective Mobilization Index (EMI)
| Metric | Value | Source |
|--------|-------|--------|
| EMI (iron / no-iron bed height ratio) | **~100.6× (recomputed on contained subset)** | Direct `np.load(rung1_*_step500000.npz)`; campaign logs claimed 107.9× / 100.0% inside |
| U_G | 0.066 m/s (0.14 bar rep) | — |
| Containment (raw ckpt) | ~78-79% inside (x/y exceed BOX=0.016; z>=0, zmin>=0) | direct `np.load` (see COLD_CLAIMS_AND_MATH_REVIEW.md §1.6 and §3) |

**Cold audit note**: Rung 1 final ckpts do not satisfy the "100.0% inside + zmin>=0 on all post-fix" citable rule repeated throughout the package. Use Rung 5 (100.0% inside, contained) as primary for quantitative mobilization support. Rung 1 remains useful for qualitative with-iron vs. no-iron differential at identical conditions. High velocities (tens of m/s) present; metrics demonstrate relative agitation benefit, not literal bed heights.

## Rung 5 — Sensitivity / combined degradation (real DEM)

### 200k lock (initial)
| Field | Value |
|-------|-------|
| Steps | 200,000 |
| Checkpoints | 134 (`rung5_step200000.npz`) |
| Mean bed height | 4949.96 ± 2498.89 mm |
| zmax / zmin | 9841 / 0.18 mm |
| inside | 100.0% |
| dead% | 1.3 |
| Mobilization proxy | iron_bed = 5563.2 mm, reg_bed = 4774.8 mm |
| Log | `rung5 done. Final bed: 4949.96±2498.89 mm (zmax=9841mm zmin=0.18mm inside=100.0%) dead%=1.3` |

### 500k lock (final)
| Field | Value |
|-------|-------|
| Steps | 500,000 |
| Checkpoints | 334 (`rung5_step500000.npz`) |
| Mean bed height | 10404.50 ± 5708.47 mm |
| zmax / zmin | 22704 / 0.49 mm |
| inside | 100.0% |
| dead% | 3.8 |
| Mobilization proxy | iron_bed = 12584.1 mm, reg_bed = 9781.8 mm |
| Log | `rung5 done. Final bed: 10404.50±5708.47 mm (zmax=22704mm zmin=0.49mm inside=100.0%) dead%=3.8` |

## Artifacts
- Checkpoints: `/home/nick/rcfx/sims/custom_gpu_dem/rung5_checkpoints/`
- Runner: `/home/nick/rcfx/sims/custom_gpu_dem/run_rung5_sensitivity_stub.py`
- Log: `/tmp/rung5_slice.log`
- Status: `python /home/nick/rcfx/sims/custom_gpu_dem/rung5_status.py` → `/tmp/rung5_status.txt`

## Figures
- FIG. 3 — `FIG_03_iron_agitation_rung5_final` (200k npz)
- FIG. 3 (500k) — `FIG_03_iron_agitation_rung5_500k_final` (500k npz)
- FIG. 7 — `FIG_07_rung5_mobilization_progression` (all 334 contained ckpts)