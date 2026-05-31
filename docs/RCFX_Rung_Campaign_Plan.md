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

## Current Status (31 May 2026)

**Rung Campaign has been executed through Rung 4 with current models.**

Key result: At **0.14 bar** with claim-compliant tuning (2.0 mm iron at 0.32 fill + 5.5× velocity + max EDS in cold stages), the integrated 5-stage counterflow model achieves **75.6% overall effectiveness**.

Full rung-by-rung results and details: `rung_results/RUNG_CAMPAIGN_RESULTS.md`

- Rung 0: PASS (distributor strongly dominant)
- Rung 1: PASS
- Rung 2: Solid PASS at 0.14 bar
- Rung 3: PASS with high EDS
- Rung 4: **75.6% at 0.14 bar** (meets ≥75% target)
- Rung 5: **Complete**. Good headroom on individual knobs at 0.14 bar. EDS and pre-classification are highest-leverage. Moderate combined degradation still viable; severe combined degradation drops performance as expected. See `rung_results/RUNG_CAMPAIGN_RESULTS.md` for details.

See `analysis/it_works_configuration.md` for the clean one-pager on the current working point.

## Next Immediate Work
1. Build and run focused sensitivity studies on parameters and features already present in the claims (starting with iron shot size distribution and agitation effectiveness vs pressure in the cold stages — squarely within Claims 4, 11, 29, etc.).
2. Refine the multi-stage counter-flow effectiveness model with accurate energy accounting.
3. Execute Rung 0–3 prototypes, with all "design levers" restricted to optimization within the existing provisional application.
4. Produce clean, documented mathematical results and sensitivity data suitable for direct use in supporting the full patent prosecution.

All work is in ~/rcfx/ on soulkiller and will be updated in place.

This campaign is now explicitly scoped to generate the supporting math/evidence for the existing provisional (PERRY-RCFX-004) while exploring how low the operating pressure can realistically go without requiring new patent filings or heavy high-pressure/vacuum hardware.
