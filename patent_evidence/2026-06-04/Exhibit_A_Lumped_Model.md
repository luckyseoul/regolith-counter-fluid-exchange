# Exhibit A — Lumped Analytical Model Baseline

**Cover statement**: This exhibit summarizes the five-stage counter-current lumped model results at the claimed 0.14 bar operating point and documents single-parameter and combined robustness sweeps used for Rung 5 analytical sensitivity.

## Nominal operating point
| Quantity | Value | Source |
|----------|-------|--------|
| Envelope pressure | 0.14 bar | PERRY-RCFX-004 Rev 5.2 |
| Overall effectiveness | **75.6%** | `rung_results/rung5_sensitivity.npy` → `baseline` |
| Blower power | **221 W** (post vol_flow fix; 1.88% of recovered) | same |
| Cold-stage U_G (rep) | 0.066 m/s (VEL_MULT_COLD=4.4) | Rev 5.2 / DEM alignment (model/DEM now consistent) |

## Single-parameter sensitivity (selected)
From `RUNG_CAMPAIGN_RESULTS.md` § Rung 5, source `rung_results/rung5_sensitivity.npy` (recomputed post vol_flow fix in five_stage_counterflow.py:126):

| Parameter | Range tested | Effect on overall effectiveness |
|-----------|--------------|----------------------------------|
| Iron shot diameter (cold) | 1.5–5.0 mm | Very flat (~75.6%) |
| Iron fill (cold) | 0.18–0.42 | Very flat |
| Velocity multiple (cold) | 3.5–6.5× | 75.6% (power 165 W → 440 W; nominal 4.4× / 0.066 m/s = 221 W, 1.88% parasitic) |
| EDS effectiveness | 0.70–0.99 | 56.2% → 78.1% |
| Pre-class cutoff | 50 µm → 18 µm | 52.2% → 84.0% |

## Combined robustness cases (0.14 bar fixed)
| Case | Overall effectiveness |
|------|----------------------|
| Nominal | 75.6% (221 W) |
| +20% fines, 15% iron wear | 69.0% (221 W) |
| EDS 0.85 + moderate wear | 64.2% (221 W) |
| Low gas generation (−25%) | 69.0% (221 W) |
| Worst combined (more fines + EDS 0.85 + wear) | 59.3% (221 W) |

## Model artifact
- **Primary**: `/home/nick/rcfx/rung_results/rung5_sensitivity.npy`
- **Implementation**: `/home/nick/rcfx/models/five_stage_counterflow.py` (and related tuning scripts)

## Relation to GPU DEM (Rung 5)
The lumped worst-combined case motivates the particle-scale Rung 5 GPU DEM backfill (bimodal PSD + iron + cohesion). DEM does not recompute 75.6%; it provides mechanistic corroboration that iron agitation and containment hold under degradation at the same pressure representative point.