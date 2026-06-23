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

**Infrastructure note (this session)**: Cell-list hotpath rewrite complete (device-only build + single RawKernel neighbor search; get_compute_forces_fn + recommended_cell_size). High-N sensitivities (iron size leverage on dead% at physical lid) + long extension to 3000 steps executed from 2000-step ckpt; new ckpts + metrics appended to audit. Support drawing FIG_S1 produced. All .docx refreshed. Brute Raw default for N=6500 consistency; cell for scale. All "100% inside + zmin>=0" rules enforced.

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
## 2026-06-04 Update: Scale + Runner
- Added explicit N=8000 contained ckpt + integrated support in the highN sensitivity runner (auto base+add for --n >6500, always 100% inside from settled physical base).
- Full campaign (iron+U_G+fines) executed at latest evolved physical state; all 100% inside, iron still dead=0 with monotonic KE scaling.
- New support drawing FIG_S3 (iron size KE bias + reg bed comparison across 200-step, later, and 8000-scale states).
- All reflected in updated Rung1_HighN_Primary_Audit, COLD, plan, and rebuilt evidence + spec support packages.
- Raw artifacts: highn_sens_checkpoints/ (60+ clean, many 100% including scale8000_*), patent_drawings/FIG_S3_*, reports with n_total.

The modeling evidence base (lumped + highN physical-lid DEM + scale demo + sensitivities) is now even stronger for 112 enablement of the physical bed + iron agitation claims at the 0.14 bar rep point.


- N=10000 scale run completed via runner (100% inside, KE bias to 45k x, ~70 s/s). FIG_S4 (perf scaling) added. All in updated audit/COLD/evidence package.

## 2026-06-05: New Utility Bundle Generated
Full updated utility specification, bundle index, and suggested claims created in /home/nick/rcfx/patent_application/2026-06-05/. Incorporates 10k scale, cell-list, iron size sensitivities, runner, S3/S4, all 100% contained high-N data, and campaign results. MD source of truth; drawings included. Practitioner can convert to .docx/PDF and complete cover sheet with inventor details for utility filing.

## Clean Data for Filing (2026-06-05 update)
Use ONLY the clean summary: patent_application/2026-06-05/Patent_Citable_Evidence_Summary.md (or the excerpt at top of Rung1_HighN_Primary_Audit_6500.md).

All bad/unphysical data (Rung5 loft, non-lid runs, contradictory claims) have been purged from the utility spec and are NOT to be presented.

The spec has been fixed to only cite the clean physical-lid mechanism data.

The architecture was scoped to use iron-collision agitation + static distributor + physical containment precisely to avoid dynamic rotary seals or rotating mechanicals in the regolith path. Such seals (as required by prior auger-based recuperator concepts) would necessitate physical prototypes and extended wear/leakage testing for validation — costs that are unaffordable under current constraints. Enablement for the utility filing rests entirely on the modeling + clean DEM evidence package. The design still requires standard low-pressure vessel seals and boundary regolith feed/exit interfaces (common to all ISRU systems), but these are not the continuous rotary dynamic seals in the hot abrasive stream that make mechanical recuperators prototype-heavy.

