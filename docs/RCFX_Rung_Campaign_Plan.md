# RCFX pressure-minimization campaign plan

**Objective.** Find the lowest envelope pressure at which the 5-stage system still
reaches ≥75% thermal recovery at 50–100 kg/h pilot scale, with blower power
under ~250 W, **inside PERRY-RCFX-004 Rev 5.2**.

Constraints: stay supportable under the existing claims; prefer simpler
operating points; produce documented model and DEM evidence.

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
- Tools: custom GPU DEM plus the lumped distributor ΔP model.

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
- Deliverable: Clear, documented math and sensitivity curves showing how performance at low pressure (target << 0.2 bar) can be improved or maintained by intelligent tuning and optimization of features already present in PERRY-RCFX-004 Rev 5.2. Focus on producing evidence suitable for supporting the full patent issuance.

## Status

The lumped + custom GPU DEM campaign is complete through Rung 5.

At **0.14 bar** the 5-stage model reaches **75.6% overall effectiveness**
(221 W blower). Rung 1 is the custom-DEM high-N physical-lid series
(N = 6500, EMI 8.04× at 1000 steps, peak 8.53×) and the good-variable
real-drag point (1.5 mm iron, 3.5 m/s, EMI 3.58×).

| Rung | Result |
|------|--------|
| 0 | PASS — distributor DEM, 500k steps |
| 1 | Custom DEM high-N + good-variable (physical lid) |
| 2 | Iron agitation confirmed |
| 3 | High EDS required |
| 4 | 75.6% at 0.14 bar |
| 5 | Sensitivity complete |

See `rung_results/RUNG_CAMPAIGN_RESULTS.md` and `analysis/it_works_configuration.md`.
Patent package: `patent_evidence/2026-06-04/`, `patent_drawings/`,
`patent_specification_draft.md`.
