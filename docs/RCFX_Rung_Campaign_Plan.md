# RCFX Pressure-Minimization Simulation Campaign (My Plan)

**Objective**: Determine the lowest envelope pressure at which the 5-stage RCFX system can still achieve ≥75% thermal recovery effectiveness at 50-100 kg/hr pilot scale, with blower power <200 W and acceptable fines loss, **while staying strictly within the existing claims and architecture of PERRY-RCFX-004 Rev 5.2**.

**Critical Constraints (per user, 31 May 2026)**:
- Changes to the design are allowed.
- **Avoid any changes that would require a refiling or new patent filing.** All work must be supportable under the existing provisional claims.
- Simpler is strongly preferred.
- Primary deliverable right now is **the math / modeling evidence** needed to support issuance of the full patent.

This directly serves the economic goal: demonstrate that good performance is achievable at low enough pressure (targeting well below the current 0.2-0.3 bar nominal) that the system does not require heavy high-pressure vessel certification, extensive safety protocols, or complex sealing — without inventing new patentable subject matter.

## Guiding Principles
- All analysis and any proposed optimizations must remain fully supportable under the existing claims of PERRY-RCFX-004 Rev 5.2. No new patentable subject matter.
- Simplicity is strongly preferred.
- Start at the lowest credible pressure (targeting well below the current 0.2-0.3 bar nominal) and quantify exactly what is required (within existing features) to make performance acceptable.
- Focus on generating clear, documented math and sensitivity data suitable for supporting full patent issuance.
- Prioritize optimization and better exploitation of features already described (iron shot as agitator, EDS, fines management approaches, gas composition evolution, parallel forced circulation, etc.).

## Proposed Rung Ladder (Progressive)

### Rung 0 — Gas + Distributor Only (Lowest Pressure Validation)
- Goal: Prove we can even *distribute* gas uniformly at target low pressure.
- Physics: Pure gas flow through the sintered distributor at 0.08–0.15 bar with realistic gas compositions.
- Success: Distributor ΔP ≥ 20–30× bed ΔP (or absolute value matching spec ~6300 Pa at reference conditions). Velocity uniformity < ±15% across bed.
- Tools: 3D CFD (later) or detailed 1D network model of the plate.

### Rung 1 — Coarse Non-Cohesive Fraction + Iron Shot
- Add only the >50 µm fraction + iron shot (1-5 mm).
- No fines, no cohesion, no charge.
- Measure: Minimum fluidization, bubbling behavior, iron shot random motion as function of pressure and gas MW.
- Success: Stable bubbling fluidization at 3–5× Umf with <10% dead zones at P ≤ 0.12 bar with hot-end gas.

### Rung 2 — Full Bimodal PSD + Simple Cohesion
- Add the real Geldart C fraction (<40-50 µm).
- Introduce van der Waals + basic agglomeration model.
- Quantify how much extra gas velocity (or iron shot agitation energy) is needed to break "fairy castles" at different pressures.
- Success: <15% of bed mass locked in stable agglomerates at operating velocity, at P = 0.12–0.15 bar.

### Rung 3 — Electrostatics + EDS Mitigation
- Add triboelectric + UV charging model for the fines.
- Model EDS electrode arrays as a controllable charge dissipation rate (function of voltage, gas pressure, gas composition).
- Key question: How much does the pressurized envelope + EDS buy us versus pure vacuum?
- Success: Demonstrate that EDS + 0.12 bar envelope keeps effective cohesion below the threshold that defeats fluidization.

### Rung 4 — Full 5-Stage Counterflow + Heat Transfer + Power
- All physics + realistic axial temperature profile (200 → 900 K).
- Gas composition evolves stage-by-stage per the three-tier desorption in the spec.
- Include blower power, entrainment to cyclones, and first-order effectiveness per stage.
- Success: ≥75% overall recovery at P ≤ 0.15 bar with total parasitic < 180 W at 75 kg/hr.

### Rung 5 — Sensitivity & Robustness + Optimization Within Existing Claims
- While holding pressure at the lowest viable value identified in Rung 4, perform detailed sensitivity and optimization on parameters and features **already enabled by the existing claims** (no new subject matter):
  - Iron shot size distribution, fill fraction per stage, and agitation intensity (within the 1-10 mm metallic particles and staged bootstrap deployment of Claims 4, 11, 29, 30).
  - EDS electrode voltage, coverage, and duty cycle (within the integration described in Claims 6 and 18, including high-purity alumina constraints).
  - Pre-classification cutoff aggressiveness and fines routing strategy (within the three approaches of Claim 26 and Section 5.8).
  - Independent superficial gas velocity per stage (enabled by the parallel manifold + forced circulation architecture of Claim 7).
  - Exploitation of the natural temperature-dependent volatile release profile for gas composition management (directly supported by Claim 27 and Section 4.3).
- Deliverable: Clear, documented math and sensitivity curves showing how performance at low pressure (target << 0.2 bar) can be improved or maintained by intelligent tuning and optimization of features already present in the provisional application. Focus on producing evidence suitable for supporting the full patent issuance.

## Current Status (4 Jun 2026)

**Rung campaign (lumped + GPU DEM) is complete through Rung 5.**

Key result: At **0.14 bar** with claim-compliant tuning (2.0 mm iron at 0.32 fill + 5.5× velocity + max EDS in cold stages), the integrated 5-stage counterflow model achieves **75.6% overall effectiveness**.

Full rung-by-rung results and details: `rung_results/RUNG_CAMPAIGN_RESULTS.md`

- Rung 0: PASS (lumped); **GPU DEM locked 500k** (distributor uniformity, 334 contained ckpts)
- Rung 1 full migration to high-N: N=6500 particles (~16.5 GB VRAM), 100% inside. See **Rung1_HighN_Primary_Audit_6500.md/.json** (direct np.load; authoritative). ... Raw default (SURFACE=0 for Rung1 no-coh; single launch high util; unit-test validated; high-level N^2 unreliable at scale so Raw authoritative for ckpts). Primary: audit + migrate (Raw) + ckpts + COLD/Exhibit. Old low-N historical. (Post-audit low-effort polish: kernel SURFACE fix, coarse switch to Raw, cell rolling re-enabled, comments/validation updated.)
- What comes after (in progress): Cell-list hotpath rewrite (remove Python `for c in range` + neighbor loops; current ext was ~0.15 steps/s, too slow). Graph capture for full step (to minimize host gaps). High-N sensitivities (iron size, U_G, fines %). Further extension (2000+ steps) for stats near lid cap. Final package polish + claims re-sweep vs latest highN numbers. 
- Rung 2: Solid PASS at 0.14 bar (GPU DEM iron agitation evidence)
- Rung 3: PASS with high EDS
- Rung 4: **75.6% at 0.14 bar** (meets ≥75% target); transfer ~230 particles (GPU DEM)
- Rung 5: **Complete** (lumped sensitivity + **GPU DEM locked 500k**, combined degradation, 334 contained ckpts)

**Patent support package**: `patent_evidence/2026-06-04/`, `patent_drawings/` (FIG. 1–7), `patent_specification_draft.md`. See `patent_evidence/2026-06-04/FILING_READINESS.md`.

See `analysis/it_works_configuration.md` for the clean one-pager on the current working point.

## Next Immediate Work
1. Update audits/exhibits/plan/COLD with highN step1000 + RawKernel success (now default in migration/benchmark; bit-exact, high sustained util).
2. Re-assemble .docx evidence package + spec support.
3. Cell-list rewrite (vectorized/Raw neighbor search) for scale + util beyond brute N~7k.
4. Optional highN sensitivity runs + longer extension (to 1500-2000 steps).
All modeling-only, zero hardware. "Enough data to patent fully." (See updated COLD for enablement via reproducible model + contained physical-lid highN DEM.)

All work is in ~/rcfx/ on soulkiller and will be updated in place.

This modeling campaign (with Rung1 containment + lid fixes) is explicitly scoped to generate sufficient computational data (lumped model + GPU DEM + sensitivity + fixed contained Rung1 audit + lid demo for physical mechanism) + descriptive evidence to fully support the utility patent claims for enablement (35 USC 112) and written description, without any physical prototype or bench hardware work. No funds for prototypes or testing. The goal is "enough data to patent fully." The historical PDF roadmap is retained as background only. See updated COLD_CLAIMS_AND_MATH_REVIEW.md for scope and enablement analysis.
