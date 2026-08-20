# RCFX Patent Evidence — Executive Summary
**Date**: 2026-06-04  
**Claim anchor**: 75.6% overall thermal effectiveness at 0.14 bar envelope (~221 W operating / 1.88% parasitic with corrected vol_flow, U_G = 0.066 m/s cold stages; see COLD_CLAIMS_AND_MATH_REVIEW.md for model hygiene fixes)

## Bottom line
The Rung campaign is complete through **Rung 0** (distributor, 500k) and **Rung 5** (sensitivity / combined degradation, 500k). All **current** GPU DEM citations use **physical-lid** checkpoints: **100.0% inside** x,y ∈ **[0, 0.018] m**, z ≥ 0. EMI = with-iron regolith ⟨z⟩ / no-iron-control regolith ⟨z⟩. Unbounded 107.9× / 109.4× and the pre-fix 68 W blower are historical. Rung 5 metre-scale beds are **not** quantitative EMI.

## Rung 5 (particle-scale robustness — qualitative only)

Rung 5 used the older unbounded-freeboard runner (BOX = 0.016 m). Final
logs report metre-scale beds (~5 m at 200k, ~10 m at 500k). Those absolute
heights are **not** quantitative EMI and are **not** current performance
numbers. Iron stayed above regolith in the proxy (agitation still active);
cite high-N / good-var for numbers.

## Lumped model (Rung 5 analytical)
Baseline: **75.6%** at 221 W (1.88% of recovered; post vol_flow= U*AREA fix + VEL=4.4 for 0.066 m/s DEM alignment). Combined robustness (same parameter set as DEM degradation intent): moderate cases remain **≥ ~69%**; worst simultaneous case **59.3%** (see Exhibit A). Source: `rung_results/rung5_sensitivity.npy`, `RUNG_CAMPAIGN_RESULTS.md`.

## Supporting locks (context)
- **Rung 1 highN (primary citable)**: N=6500 particles (~16.5 GB VRAM), lid+freeboard physical cap from step 0, 100% inside. See **Rung1_HighN_Primary_Audit_6500.md/.json** (direct np.load + extension to 2000): no-iron baseline reg 3.2307 mm @400s (86.66% dead); with-iron EMI 3.8657× (400s) → 6.3805× (700s) → **8.0445×** (1000s) → **8.53× peak (1300s)** → 7.89× (2000s, RawKernel), reg 12.4889→27.57 mm peak (1300s) then 25.48 mm (2000s, iron ~24 mm), zmax 41.3-41.8 mm (lid cap), dead contrast 0→11% (1000s)→29% (2000s, lid pile) vs 86.66% control, KE bias 1085–2551× (sustained 600+×). Full migration + extension + compute_forces_raw (single-launch high util; SURFACE=0 Rung1; unit tests dF~1e-9; highN high-level N^2 mem-unreliable so Raw authoritative). Old low-N 99k/109.4× historical. Rung 0/5 + highN Rung1 physical-lid audit (extended) = core mechanistic support.
- **Rung 0**: Distributor backfill final bed **30.97 ± 134.22 mm**, dead% **97.7**, **100.0%** inside — distributor uniformity characterization at low pressure.

## Deliverables in this package
- `EVIDENCE_PACKAGE_INDEX.md` — master index
- `Exhibit_A` … `Exhibit_E` — detailed exhibit write-ups
- `CLAIM_ELEMENT_MATRIX.md` — claim element cross-reference
- Drawings: `patent_drawings/` (FIG. 1, 3, 5, 6, 7)
- Specification draft: `patent_specification_draft.md`

## Filing package notes (internal)
- Formal Word (.docx) assembly optional via docx skill.
- FIG. 1–7 complete (including FIG. 2 stage cross-section and FIG. 4 counter-current schematic).
- Claims text integration and inventor declaration support remain outside this package.

**Scope note (funds-constrained)**: No prototype or physical testing (bench or otherwise) planned or funded. Objective is strictly to generate sufficient modeling + descriptive data (including Rung1 fixed contained + lid demo) for full patent support (enablement + written description). See COLD_CLAIMS_AND_MATH_REVIEW.md for details. Modeling campaign provides the data needed to patent fully.

*Only verified raw post-containment contained `.npz` numbers are used for DEM citations.*