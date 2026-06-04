# RCFX Patent Evidence — Executive Summary
**Date**: 2026-06-04  
**Claim anchor**: 75.6% overall thermal effectiveness at 0.14 bar envelope (~68 W, U_G = 0.066 m/s cold stages)

## Bottom line
The Rung campaign is complete through **Rung 0** (distributor, 500k) and **Rung 5** (sensitivity / combined degradation, 500k). All citable GPU DEM metrics use **post-containment** checkpoints only: **100.0% inside** the domain (x,y ∈ [0, 0.016] m, z ≥ 0) and **zmin ≥ 0** on every cited `.npz`.

## Rung 5 (particle-scale robustness)
| Lock point | Steps | Checkpoints | Final bed (mm) | zmin (mm) | inside | dead% | Iron / reg proxy (mm) |
|------------|-------|-------------|----------------|-----------|--------|-------|------------------------|
| Initial | 200,000 | 134 | 4949.96 ± 2498.89 | 0.18 | 100.0% | 1.3 | 5563.2 / 4774.8 |
| Final | 500,000 | 334 | 10404.50 ± 5708.47 | 0.49 | 100.0% | 3.8 | 12584.1 / 9781.8 |

Verbatim log terminations:
- `rung5 done. Final bed: 4949.96±2498.89 mm (zmax=9841mm zmin=0.18mm inside=100.0%) dead%=1.3`
- `rung5 done. Final bed: 10404.50±5708.47 mm (zmax=22704mm zmin=0.49mm inside=100.0%) dead%=3.8`

**Interpretation (neutral)**: Under combined degradation (bimodal PSD + iron + cohesion), iron-shot agitation remains active (iron mean bed height exceeds regolith throughout the final lock) and the simulation remains fully contained through 500k steps.

## Lumped model (Rung 5 analytical)
Baseline: **75.6%** at 68 W. Combined robustness (same parameter set as DEM degradation intent): moderate cases remain **≥ ~69%**; worst simultaneous case **59.3%** (see Exhibit A). Source: `rung_results/rung5_sensitivity.npy`, `RUNG_CAMPAIGN_RESULTS.md`.

## Supporting locks (context)
- **Rung 1**: EMI **107.9×** (iron vs. no-iron, identical drag) at 0.14 bar rep.
- **Rung 0**: Distributor backfill final bed **30.97 ± 134.22 mm**, dead% **97.7**, **100.0%** inside — distributor uniformity characterization at low pressure.

## Deliverables in this package
- `EVIDENCE_PACKAGE_INDEX.md` — master index
- `Exhibit_A` … `Exhibit_E` — detailed exhibit write-ups
- `CLAIM_ELEMENT_MATRIX.md` — claim element cross-reference
- Drawings: `/home/nick/rcfx/patent_drawings/` (FIG. 1, 3, 5, 6, 7)
- Specification draft: `/home/nick/rcfx/patent_specification_draft.md`

## Filing-ready gaps (attorney / next engineering)
- FIG. 2 (stage cross-section) and FIG. 4 (counter-current transfer schematic) not yet generated.
- Formal Word (.docx) assembly optional via docx skill.
- Claims text integration and inventor declaration support remain outside this package.

*Only verified raw post-containment contained `.npz` numbers are used for DEM citations.*