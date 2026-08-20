# Exhibit D — Calibration & Traceability to Claims (PERRY-RCFX-004 Rev 5.2)

**Cover statement**: This exhibit maps the GPU DEM operating point and numerical method to the lumped-model inputs that produce 75.6% overall effectiveness at 0.14 bar, and documents the containment verification protocol used before any cited DEM number enters the specification or evidence package.

## Operating-point alignment
| Parameter | Lumped (Rev 5.2) | GPU DEM (all rungs) |
|-----------|------------------|---------------------|
| Envelope pressure (rep) | 0.14 bar | 0.14 bar rep |
| Cold U_G | 0.066 m/s | 0.066 m/s (Rung 1/5); 0.055 m/s (Rung 0 distributor case) |
| Iron size (cold) | 1.5–3.5 mm | Bimodal + iron mat=1 per runners |
| Timestep | analytical | DT = 6.5×10⁻⁷ s |
| Domain | stage-scale model | BOX = 0.018 m (current high-N / good-var citations) |

## Identical-physics rule
The same `dem_kernels` stack (forces, drag, integration), material densities, and containment implementation are used across Rung 0, 1, 2, and 5 for defensible cross-rung comparison at the claim point.

## Containment verification protocol (mandatory before citation)
1. `ps` / `nvidia-smi` — confirm run state when live.
2. Direct `numpy.load` on raw `.npz`:
   - inside mask: x,y ∈ [0, 0.018], z ≥ 0 → must be **100.0%**
     (older Rung 0/5 runners used 0.016 m; that mask is **not** the
     current high-N / good-var domain)
   - zmin ≥ 0 (mm scale in logs)
   - CONTAINED = True
3. Cross-check printed log line and `rung*_status.py` output.
4. Only then update `RUNG_CAMPAIGN_RESULTS.md` or patent documents.

## Claim support chain (summary)
| Claim theme | Primary evidence |
|-------------|------------------|
| Low-pressure operation with iron agitation | Exhibit B (good-var EMI 3.58×; high-N EMI 8.04× / peak 8.53× vs no-iron; Rung 5 qualitative only), Exhibit C |
| 75.6% effectiveness | Exhibit A + B (mechanistic corroboration at same rep point) |
| Robustness under degradation | Exhibit A (lumped margins) + C (Rung 5 500k contained DEM) |
| Distributor / low-P gas distribution | Exhibit C (Rung 0) |
| No particle escape in cited DEM | Exhibit D protocol + all cited ckpts 100.0% inside |

## Reference documents
- PERRY-RCFX-004 Rev 5.2 (claim-legal parameters)
- `rung_results/RUNG_CAMPAIGN_RESULTS.md`
- `docs/rcfx_key_parameters.md` (if present)