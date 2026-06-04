# RCFX Filing Readiness Checklist
**Date**: 2026-06-04  
**Campaign status**: Rung 0 and Rung 5 GPU DEM **locked at 500k**; lumped Rung 5 analytical **complete + math hygiene fixed (vol_flow, U_G alignment)**; **cold claims/math review complete** (COLD_CLAIMS_AND_MATH_REVIEW.md)

## Simulation locks (verified this session)
| Rung | Final checkpoint | Steps | Checkpoints | Containment audit |
|------|------------------|-------|-------------|-------------------|
| 0 | `rung0_step500000.npz` | 500,000 | 334 | Locked prior session |
| 5 | `rung5_step500000.npz` | 500,000 | 334 | **334/334** pass inside mask (x,y ∈ [0, 0.016] m, z ≥ 0), zmin ≥ 0 |

**Rung 5 final metrics** (citable only):
- 200k: bed 4949.96±2498.89 mm, inside 100.0%, dead 1.3%, proxy iron/reg 5563.2 / 4774.8 mm
- 500k: bed 10404.50±5708.47 mm, inside 100.0%, dead 3.8%, proxy iron/reg 12584.1 / 9781.8 mm

**Lumped post-audit (fixed)**: 75.6% at 221 W (U_G=0.066 m/s cold, 1.88% parasitic). Rung1 high-N primary (6500 particles, ~16.5 GB VRAM, lid physical from step 0, 100% inside): see **Rung1_HighN_Primary_Audit_6500.md/.json** (direct np.load + extension to 2000) — no-iron baseline 3.2307 mm (86.66% dead); with-iron EMI 3.8657×@400s → 6.3805×@700s → **8.0445×**@1000s → **8.53× peak (1300s)** → 7.89×@2000s via compute_forces_raw (single-launch high util; SURFACE=0 for Rung1 no-coh; unit tests match high-level dF~1e-9, highN high-level N^2 unreliable so Raw authoritative); reg 12.4889→27.57 mm peak (1300s) then 25.48 mm (2000s, iron ~24 mm), physical zmax 41.3-41.8 mm, KE bias 1085–2551× (sustained 600+×), dead contrast 0→29% (lid pile) vs control. Rung0/5 100% citable contained. See dedicated audit + COLD + Exhibit B + ckpts to 002000.

Process: not running. Log: `/tmp/rung5_slice.log`. Status: `python /home/nick/rcfx/sims/custom_gpu_dem/rung5_status.py`

## Patent support package (ready)
| Deliverable | Path | Status |
|-------------|------|--------|
| Evidence index + Exhibits A–E | `patent_evidence/2026-06-04/` | Complete |
| Claim element matrix | `CLAIM_ELEMENT_MATRIX.md` | Complete |
| Executive summary | `EXECUTIVE_SUMMARY.md` | Complete |
| Specification draft | `patent_specification_draft.md` | Complete (internal support) |
| Drawings FIG. 1–7 (SVG/PDF) | `patent_drawings/` | Complete |
| Cold claims + math validation review | `COLD_CLAIMS_AND_MATH_REVIEW.md` | **Added this session** (independent audit) |
| Assembled evidence package (.docx) | `RCFX_Patent_Evidence_Package_2026-06-04.docx` | **Generated this session** (US Letter, TOC, headers/footers, tables, full content + cold review) |
| Assembled spec support draft (.docx) | `RCFX_Specification_Support_Draft_2026-06-04.docx` | **Generated this session** (formatted support text, cross-refs to evidence package) |

## Outstanding (outside engineering)
1. Formal independent/dependent **claims** text integration (not in repo).
2. **Inventor declaration** (outside this repo).
3. Optional **Word (.docx)** assembly of exhibits + spec.
4. Optional FIG. 2B/2C embodiment series (not required for current support set).

**Scope note (funds-constrained)**: No prototype, no bench-scale testing, no physical hardware work planned or funded at any phase. All work is modeling + analysis to generate enough data to patent fully (enablement via reproducible model + mechanistic DEM + detailed spec + Rung1 fixed audit + lid demo). See COLD_CLAIMS_AND_MATH_REVIEW.md and updated Rung Campaign Plan.

## Recommended filing package bundle
Copy or zip these paths:
```
/home/nick/rcfx/patent_evidence/2026-06-04/RCFX_Patent_Evidence_Package_2026-06-04.docx
/home/nick/rcfx/patent_evidence/2026-06-04/RCFX_Specification_Support_Draft_2026-06-04.docx
/home/nick/rcfx/patent_evidence/2026-06-04/  (source MDs + COLD_CLAIMS_AND_MATH_REVIEW.md + Rung1_Fixed_Contained_Audit_99k.* + Rung1_Lid_Freeboard_Demo.txt + raw exhibits for reference)
/home/nick/rcfx/patent_drawings/FIG_*.pdf
/home/nick/rcfx/patent_specification_draft.md
/home/nick/rcfx/rung_results/RUNG_CAMPAIGN_RESULTS.md
/home/nick/rcfx/sims/custom_gpu_dem/rung5_checkpoints/rung5_step500000.npz
/home/nick/rcfx/sims/custom_gpu_dem/rung0_checkpoints/rung0_step500000.npz
/home/nick/rcfx/models/five_stage_counterflow.py
/home/nick/rcfx/rung_results/rung5_sensitivity.npy
```

## Enablement note
DEM evidence is framed as **mechanistic corroboration** at the lumped-model operating point (0.14 bar, U_G = 0.066 m/s), not as a standalone proof of full-scale 75.6%. All cited DEM numbers are from post-containment checkpoints only.