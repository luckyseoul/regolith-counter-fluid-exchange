# Data catalog

Particle-scale results are from the custom GPU DEM in `sims/custom_gpu_dem/`.
Checkpoints are NumPy `.npz` archives with `pos`, `vel`, `radius`, `mat`, `step`.

`mat == 0` is regolith; `mat != 0` is iron shot. Positions are metres.

Rung 1 statistics use the high-N series and the separate real-drag point.
Their particle centres satisfy the documented bounds, but neither whole-sphere
containment nor physical validity follows from this. Checkpoints contain no
elapsed-time, timestep, gas-speed, force-mode, or lid metadata. Runner source
is contextual evidence; step labels must not be interpreted as seconds.

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

Real-drag point: 1.5 mm iron; source runner uses 3.5 m/s gas.
All 6500 particle centres are inside x,y ∈ [0, 0.018] m, z ∈ [0, 0.060] m.
Only 6331 full spheres fit inside those bounds when radii are included.
Maximum centre z is 40.1297 mm, not evidence of a 41 mm lid.
The 3.58× ratio uses the separate no-iron step-400 reference (3.2307 mm), with
different forcing and no matched-time control. Means are 34.4689 mm iron and
11.5609 mm regolith. These are reproducible statistics, not a controlled
mobilization gain.

## Lumped-model arrays

**Historical invalid-model outputs.** These arrays reproduce the old recurrence,
which does not solve counter-flow boundary conditions. They do not validate
75.6% recovery, 11.8 kW heat duty, or a 1.88% blower fraction. The corrected
README figures regenerate sensitivity directly from source and show thermal
outputs as diagnostics; the archived arrays are preserved.

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

## Validation evidence

- [Figure audit](docs/FIGURE_AUDIT.md): corrections and physical limits.
- [Figure data and source hashes](docs/figures/figure_data.json).
- [Independent DEM audit](docs/figures/dem_validation.json), regenerated with
  `python3 scripts/audit_dem_figures.py`.

Inventory uses decimal MB (1,000,000 bytes); exact total: 150,981,303 bytes.
