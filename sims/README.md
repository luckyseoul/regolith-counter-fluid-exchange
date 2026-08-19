# Simulations

**Production particle physics lives in `custom_gpu_dem/`.** That is the custom single-GPU DEM (CuPy) written for this project: physical lid, cell-list, real gas drag with local porosity. All citable iron-agitation numbers come from those checkpoints.

| Path | Role |
|------|------|
| `custom_gpu_dem/` | Production DEM engine, runners, and `.npz` checkpoints (Rungs 0–5) |
| `legacy/liggghts/` | Historical LIGGGHTS 3.8 input decks (abandoned; packing/lost-atom issues) |
| `legacy/yade/` | Historical YADE scripts (abandoned) |
| `legacy/orin_openfoam/` | Orin CFDEM/OpenFOAM case *setup* recovered from backup. No solver time directories. Do not treat as production data. |

A standalone extraction of the DEM kernels is published at [luckyseoul/custom-gpu-dem](https://github.com/luckyseoul/custom-gpu-dem).
