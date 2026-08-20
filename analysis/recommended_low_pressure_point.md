# Recommended Low-Pressure Operating Point for RCFX
## Supporting Math for Patent Filing (within existing claims)

**Date**: 31 May 2026  
**Basis**: Systematic tuning using parameters and features from PERRY-RCFX-004 Rev 5.2.

### Target
Demonstrate that the RCFX architecture can achieve strong thermal recovery performance at significantly lower envelope pressure than the current 0.2–0.3 bar nominal, while remaining fully supportable under the existing provisional claims.

### Recommended Tuned Point (Claim-Compliant)

**Operating Pressure**: 0.10 – 0.12 bar (100–120 mbar)

This is low enough to provide substantial engineering and economic relief on vessel design, sealing, and certification compared to 0.2+ bar, while still being high enough to avoid crossing into regimes that require true vacuum hardware and associated extreme testing.

### Tuned Parameters (All Within Existing Claims)

**Cold Stages (1–2)** — where the problem is hardest:
- Iron shot: 3.5 mm diameter at 0.35–0.38 fill fraction
- Superficial velocity: 4.5–5.5 × Umf of the target 200 µm fraction
- EDS: operated at high effectiveness (0.92–0.96)

**Hot Stages (3–5)**:
- Iron shot: 2.5–3.5 mm at slightly lower fill (0.22–0.28)
- Lower velocity multiple (3.5–4.5×) is acceptable due to higher gas density

**Fines Management**:
- Pre-classification cutoff at ~28–35 µm (aggressive but within the pre-classification approach already described in Section 5.8 and Claim 26)

**Gas Management**:
- Rely on the natural temperature-dependent volatile release profile (Claim 27 and Section 4.3) — heavier CO/CO2 species preferentially available in the hotter stages where they provide the most fluidization benefit.

### Expected Performance (from tuned models)

- At **0.10 bar**: ~71–73% overall thermal recovery effectiveness (100 kg/hr reference)
- At **0.12 bar**: ~82–84% overall thermal recovery effectiveness

Blower power remains in the 80–150 W range (well under the 2% parasitic target in the spec) because the parallel manifold architecture means the blower only fights single-stage pressure drop.

### Why This Matters for the Patent

These results were obtained **without introducing any new hardware, new subsystems, or new patentable subject matter**. All improvements come from:

- Better exploitation of the iron shot thermal mass / agitator already claimed (Claims 4, 11, 29, 30).
- Full use of the EDS integration already claimed (Claims 6, 18).
- Intelligent use of the three fines management approaches already described (Claim 26 + Section 5.8).
- Stage-wise velocity optimization (enabled by the parallel forced circulation design in Claim 7).
- Natural gas composition evolution (Claim 27).

This provides clear mathematical support that the invention as disclosed can operate effectively at pressures low enough to avoid the major cost and complexity drivers associated with higher-pressure vessels, while staying entirely inside the scope of the existing provisional application.

### Files
- Raw sweep data: `analysis/full_tuning_sweep_v1.npy`
- Supporting scripts: `models/full_tuning_sweep.py`, `pressure_relief_levers.py`, `iron_shot_agitation_vs_pressure.py`
- Campaign plan: `docs/RCFX_Rung_Campaign_Plan.md`

