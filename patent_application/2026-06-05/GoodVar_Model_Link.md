# Link Between Good-Var DEM Data and Lumped/NTU Model (CPU Post-Process)
**Date**: 2026-06-23 (run after cold review)
**Purpose**: Provide direct quantitative bridge between the primary citable DEM checkpoint (physical_drag_real_u3.5_iron1.5mm_step002000.npz — real drag only) and the thermal numbers. Addresses cold review gaps on (a) model run at DEM-supported conditions and (b) DEM-derived contact/porosity stats for solid-solid heat transfer.

All numbers from direct execution on existing artifacts (no new long simulations).

## 1. Lumped Model Run at Exact Good-Var Conditions
- Iron cold: 1.5 mm
- U_G cold: 3.5 m/s (VEL_MULT_COLD = 3.5 / 0.015)
- P = 0.14 bar (same gas props as DEM run)
- Other params as tuned reference (EDS 0.97, PRECLASS 22 µm, hot iron 3.5 mm)

**Results** (using stage() + vol_flow = U × AREA + power = vol_flow × dp_bed / 0.6 from five_stage_counterflow.py):
- Per-stage effectiveness: cold ≈ 0.863, hot ≈ 0.995
- Overall effectiveness: **77.0%** (slightly above the 75.6% reference headline)
- Total blower power: **4,507,539 W** (≈ 4.5 MW)
- Parasitic on recovered heat (mdot=100 kg/hr, ΔT=700 K): **28,977%**

**Interpretation**:
The clean real-drag agitation (iron lifts to 34.47 mm vs reg 11.56 mm) only appears at conditions where blower power is catastrophically high. The low-power 75.6% / 1.88% numbers at the reference point (U_G≈0.066 m/s) depend on the sub-grid distributor momentum term (as confirmed by drag-fix verification). This is now quantitatively shown.

## 2. DEM Checkpoint Post-Processing (Collision / Contact Proxies)
Loaded directly from the primary good-var .npz.

- Mean bed porosity (volume fraction from local cells): **0.775** (regolith 0.807)
- Sampled near-contact pairs (within ~2.5 × sum radii): hundreds in limited search
- Mean |v_rel| for near-neighbor particles: **10.12 m/s**
- Characteristic contact duration estimate (2r / |v_rel|): **31.5 µs**
- Regolith moving fraction (|v_z| > 0.2 m/s): **56.3%**
- Iron moving fraction: **22.4%** (iron does the "heavy lifting")

These provide mechanistic support for improved gas-solid contact + direct solid-solid heat transfer (short but frequent high-relative-velocity contacts due to iron).

## 3. Analytical Umf Cross-Check (DEM Accuracy Validation)
Using the exact gas properties from the DEM run (rho_g=0.0438, mu_g=2.28e-5 at 0.14 bar):

- 1.5 mm iron: Umf ≈ **0.741 m/s**
  - Good-var U_G=3.5 m/s = **4.7 × Umf** (matches envelope calculation used to select the point)
- Reference 2 mm iron at identical gas props: Umf ≈ **1.267 m/s**
  - Reference U_G=0.066 m/s = **0.05 × Umf** → iron should act as jetsam
  - Exactly consistent with drag-fix runs (velocities collapse, iron sits at reference point)

This is strong evidence the DEM physics is behaving as expected analytically (no hidden artificial forces in the good-var data).

## 4. Implications for NTU / Thermal Model
- At good-var point, gas capacity rate is much higher (vol_flow ×50), h higher, but power prohibitive.
- DEM porosity ~0.78 and short contact times support the hybrid (gas fluidizes + solids exchange) picture used in the lumped model.
- Can be used to tighten the solid-solid hA band in proper_ntu_thermal.py if desired (using contact time + conductance estimate).

These runs were performed on CPU from committed artifacts only. Results can be reproduced from the raw checkpoint + the model source.

**Files referenced**:
- rcfx/sims/custom_gpu_dem/rung1_highn_checkpoints/physical_drag_real_u3.5_iron1.5mm_step002000.npz
- models/five_stage_counterflow.py
- models/proper_ntu_thermal.py

This document strengthens enablement by showing the DEM data and analytical model are mutually consistent at the claimed envelope.