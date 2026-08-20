# Data catalog

Particle-scale results are from the custom GPU DEM in `sims/custom_gpu_dem/`.
Checkpoints are NumPy `.npz` archives with `pos`, `vel`, `radius`, `mat`, `step`.

`mat == 0` is regolith; `mat != 0` is iron shot. Positions are metres.

Rung 1 citations use the high-N physical-lid series and the good-variable
real-drag point, not the older unbounded-freeboard slices.

## Checkpoint archive

| Directory | Files | Size | What it is |
|---|---:|---:|---|
| `sims/custom_gpu_dem/rung0_checkpoints/` | 334 | 26.9 MB | Distributor / gas-only series |
| `sims/custom_gpu_dem/rung1_checkpoints/` | 677 | 78.3 MB | Early contained Rung 1 slices |
| `sims/custom_gpu_dem/rung1_highn_checkpoints/` | 60 | 13.5 MB | Primary Rung 1: high-N + good-variable |
| `sims/custom_gpu_dem/rung2_checkpoints/` | 34 | 3.3 MB | Iron-agitation production / controls |
| `sims/custom_gpu_dem/rung4_checkpoints/` | 15 | 1.2 MB | Two-stage transfer |
| `sims/custom_gpu_dem/rung5_checkpoints/` | 334 | 26.9 MB | Combined-degradation series |
| `sims/custom_gpu_dem/*.npz` | 13 | 0.9 MB | Rung 2 calibration dumps |
| **Total** | **1467** | **151.0 MB** | |

## Primary citable DEM file

```
sims/custom_gpu_dem/rung1_highn_checkpoints/physical_drag_real_u3.5_iron1.5mm_step002000.npz
```

Good-variable point: 1.5 mm iron, real drag, 3.5 m/s, physical lid.
100% inside **x,y ∈ [0, 0.018] m** (not the older 0.016 m mask). Source of the
3.58× EMI (vs no-iron ⟨z⟩ = 3.2307 mm) / 34.47 mm iron / 11.56 mm regolith numbers.

## Lumped-model arrays

| File | Contents |
|------|----------|
| `rung_results/rung4_results.npy` | 5-stage effectiveness at 0.12 / 0.14 / 0.15 bar |
| `rung_results/rung5_sensitivity.npy` | Baseline 75.6% / 221 W plus one-at-a-time sweeps |
| `rung_results/rungs_0_to_3_summary.npy` | Locked parameter set |
| `analysis/*.npy` | Pressure, iron, and NTU sweeps used while tuning |

## How to load a checkpoint

```python
import numpy as np
d = np.load("sims/custom_gpu_dem/rung1_highn_checkpoints/physical_drag_real_u3.5_iron1.5mm_step002000.npz")
pos, vel, radius, mat, step = d["pos"], d["vel"], d["radius"], d["mat"], d["step"]
reg = pos[mat == 0]
iron = pos[mat != 0]
print(step, reg[:, 2].mean() * 1e3, iron[:, 2].mean() * 1e3)  # mm
```

Regenerate README charts with `python3 scripts/generate_readme_figures.py`.
