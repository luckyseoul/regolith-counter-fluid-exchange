# Claim Element → Evidence Matrix (Internal Working Document)

**Date**: 2026-06-04 | **Status**: Rung 0 and Rung 5 locked; DEM citations containment-verified

| Claim element (paraphrased) | Specification § | Drawings | Evidence | Status |
|-----------------------------|-------------------|----------|----------|--------|
| 5-stage counter-current fluidized bed heat recovery | Detailed Description — Architecture | FIG. 1 | Exhibit A (lumped architecture) | Supported |
| Operation at low envelope pressure (~0.14 bar) | Summary; Performance | FIG. 5 | Exhibit A (75.6% point); Exhibit D | Supported |
| Iron shot as sensible heat media | Detailed Description | FIG. 1, 2 | Exhibit A parameters | Supported |
| Iron shot mechanical agitation of cohesive fines | Iron agitation § | FIG. 3, 3 (500k), 7 | Exhibit B + **Rung1_HighN_Primary_Audit_6500.md/.json** (direct np.load + extension to 2000): Rung 5 200k/500k 100% contained proxies; Rung 1 highN primary N=6500 ~16.5 GB, 100% inside lid+opt from step 0, exact EMI 3.8657×@400s → 6.3805×@700s → **8.0445×**@1000s → **8.53× peak (1300s)** → 7.89×@2000s (RawKernel), reg 12.4889→27.5656 mm peak (1300s, iron 27.25) then 25.48 mm (2000s); zmax 41.3-41.8 mm (lid cap); dead% 0 early → 11% (1000s) → 29% (2000s, lid pile) vs 86.66% no-iron control (baseline 3.2307 mm); KE bias 1085–2551× (sustained 600+×); see dedicated audit + COLD + Exhibit B + ckpts to 002000; compute_forces_raw primary for util) | Supported (Rung0/5 contained + highN Rung1 physical-lid differential + Raw high-util path; all from raw ckpt re-compute; extension confirms sustained ~8x at physical heights) |
| Iron size range 1.5–3.5 mm (cold) | Low-pressure enablers | — | Exhibit A sensitivity (flat); Rev 5.2 | Supported |
| ~75.6% overall effectiveness at 221 W (1.88% parasitic) | Abstract; Performance | FIG. 5 | Exhibit A baseline (post vol_flow fix) | Supported |
| Sintered distributor / uniform gas injection | Low-pressure enablers | FIG. 6 | Exhibit C (Rung 0) | Supported |
| Counter-current solids transfer | Staging § | FIG. 4 | Exhibit C (Rung 4 ~230 particles) | Supported |
| EDS / pre-class within claims | Alternatives | — | Exhibit A (high leverage sweeps) | Supported (lumped) |
| Robustness under combined degradation | Performance; Rung 5 § | FIG. 7 | Exhibit A (69% moderate); Exhibit C (Rung 5 DEM 500k contained) | Supported |
| Particle-scale enablement (not overclaiming proof) | Iron agitation § | FIG. 3 series | Exhibit B, D (identical physics) | Supported |
| Containment / no escape in cited DEM | Enablement note | — | Exhibit D protocol; all cited .npz 100.0% inside | Supported |

## Thin or pending areas
1. **Formal claims text** — matrix maps to functional elements; independent/dependent claim wording not in repo.
2. **Optional** — FIG. 2B/2C series for alternative embodiments (not required for current support set).

## Rung 5-specific citations (quick reference)
- **200k**: `rung5_step200000.npz` — bed 4949.96±2498.89 mm, inside 100.0%, dead 1.3%
- **500k**: `rung5_step500000.npz` — bed 10404.50±5708.47 mm, inside 100.0%, dead 3.8%
- **Progression**: FIG. 7 + Exhibit C table (334 ckpts, all contained)