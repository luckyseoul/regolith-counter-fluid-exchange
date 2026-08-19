# Data catalog

All particle-scale results in this repository come from the **custom GPU DEM**
(`sims/custom_gpu_dem/`). Checkpoints are NumPy `.npz` archives with at least
`pos`, `vel`, `radius`, `mat`, `step`.

`mat == 0` is regolith; `mat != 0` is iron shot. Positions are metres.

## Checkpoint archive

| Directory | Files | Size | What it is |
|---|---:|---:|---|
| `sims/custom_gpu_dem/rung0_checkpoints/` | 334 | 26.9 MB | Distributor / gas-only backfill to 500k steps |
| `sims/custom_gpu_dem/rung1_checkpoints/` | 677 | 78.3 MB | Coarse fraction + iron, post-containment |
| `sims/custom_gpu_dem/rung1_checkpoints/v1_blastoff/` | 154 | 17.8 MB | **Invalid** pre-containment archive (kept for audit) |
| `sims/custom_gpu_dem/rung1_highn_checkpoints/` | 60 | 13.5 MB | Primary citable high-N + good-variable runs |
| `sims/custom_gpu_dem/rung2_checkpoints/` | 34 | 3.3 MB | Iron agitation production / controls |
| `sims/custom_gpu_dem/rung4_checkpoints/` | 15 | 1.2 MB | Two-stage transfer demos |
| `sims/custom_gpu_dem/rung5_checkpoints/` | 334 | 26.9 MB | Combined-degradation 500k backfill |
| `sims/custom_gpu_dem/*.npz` | 13 | 0.9 MB | Early Rung 2 calibration dumps |
| **Total** | **1621** | **168.8 MB** | |

## Primary citable DEM file

```
sims/custom_gpu_dem/rung1_highn_checkpoints/physical_drag_real_u3.5_iron1.5mm_step002000.npz
```

Good-variable point: 1.5 mm iron, real drag, 3.5 m/s, physical lid, 100% inside.
Source of the 3.58× EMI / 34.47 mm iron / 11.56 mm regolith numbers.

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
