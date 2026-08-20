# RCFX Full Tuning Sweep Results — 31 May 2026

**Scope**: Systematic optimization of parameters **already enabled by PERRY-RCFX-004 Rev 5.2**. No new subject matter.

**Tuned knobs** (all within current claims):
- Iron shot diameter (1.5–5.0 mm)
- Iron fill fraction in cold stages (0.18–0.38)
- Superficial velocity multiple in cold stages (3.5–5.5× Umf)
- EDS effectiveness (0.75–0.96)
- Pre-classification cutoff (28–48 µm)

**Model**: Low-fidelity but anchored multi-stage counter-flow effectiveness model using Rev 5.2 gas evolution, regolith properties, and mitigation physics.

## Key Results

| Pressure | Best Achievable Overall Effectiveness | Best Iron Shot (cold) | Fill (cold) | Vel. Mult (cold) | EDS   | Pre-class |
|----------|---------------------------------------|-----------------------|-------------|------------------|-------|-----------|
| 0.08 bar | 60.3%                                | 3.5 mm               | 0.38       | 4.5×            | 0.96 | 28 µm    |
| **0.10 bar** | **73.2%**                            | 3.5 mm               | 0.38       | 4.5×            | 0.96 | 28 µm    |
| **0.12 bar** | **83.8%**                            | 3.5 mm               | 0.38       | 4.5×            | 0.96 | 28 µm    |
| 0.15 bar | 93.6%                                | 3.5 mm               | 0.28       | 5.5×            | 0.96 | 28 µm    |
| 0.18 bar | 94.0%                                | 2.5 mm               | 0.38       | 5.5×            | 0.88 | 28 µm    |
| 0.22 bar | 94.0%                                | 2.5 mm               | 0.28       | 5.5×            | 0.96 | 28 µm    |

## Major Insights

1. **Aggressive but claim-compliant tuning buys enormous margin at low pressure.**
   - At 0.10 bar we reach 73% overall effectiveness (very close to the 70% minimum target).
   - At 0.12 bar we are comfortably above the design target range.

2. **The winning combination in the cold stages is consistently:**
   - Larger iron shot (3.5 mm) at high fill fraction (0.38)
   - Higher velocity multiple in the cold stages (4.5–5.5×)
   - Maximum practical EDS effectiveness
   - Aggressive pre-classification (removing down to ~28 µm)

3. **Hot stages are much more forgiving** due to higher gas density from CO/CO2 release. The binding constraint is almost entirely the cold end.

4. **0.10 bar now looks viable** with proper tuning of existing features. This is a major improvement over earlier untuned or lightly tuned runs.

5. Below ~0.09–0.10 bar we start falling off a cliff even with maximum tuning of current mitigations.

## Implications for the Patent

This directly supports the goal of operating at meaningfully lower pressure than the current 0.2–0.3 bar nominal without requiring new patentable subject matter.

By simply optimizing iron shot size distribution and loading (already claimed), EDS performance (already claimed), fines management aggressiveness (already claimed), and stage-wise velocity (enabled by the parallel manifold architecture), the system can achieve good performance at 0.10–0.12 bar.

This pressure range is low enough to provide substantial relief on vessel design, sealing, and certification burden compared to 0.2+ bar, while remaining well above the "real vacuum hardware" regime (~5–20 mbar) that would trigger entirely different technology and testing requirements.

## Next Steps (already in progress)

- Refine to a higher-fidelity 5-stage counter-flow energy/mass balance model using the best tuning parameters above.
- Generate clean figures and tables suitable for the patent application.
- Explore one additional safe dimension: differential iron shot sizing between cold vs hot stages (still within the staged deployment language of the claims).
- Document the exact parameter sets that achieve the reported performance for inclusion in the patent support file.

