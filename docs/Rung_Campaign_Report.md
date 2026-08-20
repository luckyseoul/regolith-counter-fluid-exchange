# RCFX pressure-minimization campaign

**Date**: 2026-06  
**Repository**: https://github.com/luckyseoul/regolith-counter-fluid-exchange

## Summary

The campaign asked whether the five-stage counter-current fluidized bed in
PERRY-RCFX-004 Rev 5.2 can meet thermal-recovery targets at a lower envelope
pressure than the 0.2–0.3 bar nominal.

**Result.** The lumped 5-stage model reaches **75.6% overall effectiveness** at
**0.14 bar**, with **221 W** blower power (1.88% parasitic) at 100 kg/h.
Rung 1 particle-scale evidence is from the custom GPU DEM: high-N physical-lid
EMI up to 8.53×, and a good-variable real-drag point at 1.5 mm iron / 3.5 m/s
with EMI 3.58×, 100% inside the lid.

## Operating point

| | Cold stages 1–2 | Hot stages 3–5 |
|--|--|--|
| Iron diameter | 2.0 mm (good-var DEM also at 1.5 mm) | 3.5 mm |
| Iron fill | 0.32 | 0.20 |
| Velocity | 4.4× *U*<sub>mf</sub> (*U*<sub>G</sub> = 0.066 m/s) | 3.5× *U*<sub>mf</sub> |
| EDS | 0.97 | 0.97 |
| Pre-class | 22 µm | 22 µm |

Stage effectiveness at 0.14 bar: cold ~86.3%, hot ~99.5%.

## Rungs

| Rung | Scope | Result |
|------|--------|--------|
| 0 | Distributor | PASS — ΔP still distributor-dominated |
| 1 | Coarse fraction + iron (custom DEM) | High-N physical-lid + good-variable real-drag |
| 2 | Bimodal PSD + cohesion | Iron agitation confirmed in DEM |
| 3 | EDS | High EDS required at this pressure |
| 4 | 5-stage counter-flow | 75.6% overall |
| 5 | Sensitivity | EDS and pre-class are the high-leverage knobs |

Detail: `rung_results/RUNG_CAMPAIGN_RESULTS.md`.

## Notes

These are model and DEM results. There is no hardware prototype. Quantitative
DEM citations use physical-lid checkpoints only.
