# RCFX Pressure Minimization Campaign — Final Report

**Date**: 31 May 2026  
**Repository**: https://github.com/luckyseoul/rcfx (private)  
**Machine**: soulkiller (development & simulation host)

## Executive Summary

The goal of this campaign was to determine whether the RCFX multi-stage counter-current fluidized bed heat recovery system (as described in provisional patent PERRY-RCFX-004 Rev 5.2) can achieve useful thermal recovery performance at significantly lower envelope pressure than the current 0.2–0.3 bar nominal.

Lower pressure is highly desirable because it reduces the design, certification, and operational burden associated with pressure vessels and complex sealing — directly supporting the objective of a system that can operate with minimal physical intervention on the lunar (or other extraterrestrial) surface.

### Key Result

Using only features and parameters already enabled by the existing provisional claims, the system achieves **75.6% overall thermal recovery effectiveness** at **0.14 bar** (140 mbar) in a 5-stage counter-flow energy balance model, with very low parasitic power (~68 W blower at 100 kg/hr reference throughput).

This represents a substantial reduction in operating pressure compared to the baseline design while remaining well within a "low-pressure envelope" regime that avoids both heavy high-pressure vessel requirements and true vacuum hardware.

## Campaign Structure (Rung Ladder)

A progressive simulation campaign was executed to build confidence systematically:

- **Rung 0**: Gas + Distributor Only (Lowest Pressure Validation)
- **Rung 1**: Coarse Non-Cohesive Fraction + Iron Shot
- **Rung 2**: Full Bimodal PSD + Simple Cohesion
- **Rung 3**: Electrostatics + EDS Mitigation
- **Rung 4**: Full 5-Stage Counterflow + Heat Transfer + Power
- **Rung 5**: Sensitivity & Robustness + Optimization Within Existing Claims

All work remained strictly inside the scope of the existing provisional patent claims. No new patentable subject matter was introduced.

## Current Working Configuration (0.14 bar)

**Pressure**: 0.14 bar (140 mbar) nominal

**Tuned Parameters** (all within existing claims):

**Cold Stages (1–2)** — the most challenging region:
- Iron shot: 2.0 mm diameter
- Iron fill fraction: 0.32
- Superficial velocity: 5.5 × Umf (of the 200 µm target fraction)
- EDS effectiveness: 0.97 (high)
- Pre-classification cutoff: 22 µm (aggressive)

**Hot Stages (3–5)**:
- Iron shot: 3.5 mm diameter
- Iron fill fraction: 0.20
- Superficial velocity: 3.5 × Umf
- EDS effectiveness: 0.97

**Performance (5-stage counter-flow energy balance)**:
- Overall thermal recovery effectiveness: **75.6%**
- Recovered sensible heat (100 kg/hr reference): ~11.8 kW
- Estimated blower power: ~68 W

**Stage effectivenesses**:
- Cold stages (1–2): ~86.3%
- Hot stages (3–5): ~99.5%

This configuration comfortably exceeds the 70% minimum recovery target in the specification while operating at less than half the current nominal pressure.

## Rung Campaign Results Summary

| Rung | Description                              | Status at 0.14 bar          | Key Finding |
|------|------------------------------------------|-----------------------------|-------------|
| 0    | Gas + Distributor Only                   | PASS                        | Distributor remains strongly dominant |
| 1    | Coarse fraction + Iron Shot              | PASS                        | Stable fluidization achieved |
| 2    | Bimodal PSD + Cohesion                   | Solid PASS                  | ~86% cold-stage effectiveness |
| 3    | Electrostatics + EDS                     | PASS                        | High EDS is critical and highly effective |
| 4    | Full 5-Stage Counterflow                 | **75.6% overall**           | Meets target with good margin |
| 5    | Sensitivity & Robustness                 | Complete                    | Good headroom on individual knobs; EDS and pre-class most leveraged |

Full details for all rungs are in `rung_results/RUNG_CAMPAIGN_RESULTS.md`.

## Rung 5 — Sensitivity & Robustness Highlights

At the 0.14 bar point:

- **EDS effectiveness** is very high leverage. Performance drops noticeably below ~0.93.
- **Pre-classification aggressiveness** is extremely high leverage.
- Combined moderate degradation cases (more fines + iron wear + EDS drop) still keep the system in the high 60s %.
- Severe combined degradation drops performance as expected — reinforcing that 0.14 bar provides useful operating margin for low-maintenance ("one visit per month") operation.

## Conclusions & Recommendations

1. **0.14 bar is a viable, conservative working point** with the tuned parameters above. It delivers the required performance while staying comfortably inside the existing patent claims.

2. The combination of iron shot as both thermal mass and mechanical agitator, high-effectiveness EDS, and aggressive-but-reasonable pre-classification provides the majority of the pressure-relief benefit within the current architecture.

3. Operating at 0.14 bar (versus the current 0.2–0.3 bar nominal) should yield meaningful simplifications in vessel design, sealing, and certification — directly supporting the goal of minimal physical intervention on the lunar surface.

4. Further gains below 0.12–0.13 bar appear to require either accepting lower performance or additional (still claim-compliant) refinements that have not yet been fully quantified in the integrated model.

## Repository Contents

- `docs/` — Campaign plans, parameter references, and this report
- `models/` — Python/CuPy simulation models (run on soulkiller with V100)
- `analysis/` — Key results, summaries, and sensitivity data
- `rung_results/` — Detailed per-rung execution scripts and outputs

All modeling was performed on soulkiller using only information contained in PERRY-RCFX-004 Rev 5.2.

---

**Prepared for**: luckyseoul  
**Primary machine**: soulkiller  
**Status**: Rung 0–5 complete. 0.14 bar configuration recommended as current "it works" baseline.