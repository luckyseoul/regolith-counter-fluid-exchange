# Custom GPU DEM (production)

This is the particle-scale simulator used for every citable RCFX DEM number.

- Kernels: `common/dem_kernels.py` (Hertz + JKR-style cohesion, rolling, porosity-aware drag)
- Step / cell-list: `common/cell_list.py`, `common/optimized_step.py`
- Runners: `run_rung*.py`, `continue_*.py`
- Checkpoints: `rung*_checkpoints/` (see [DATA.md](../../DATA.md))

Do not use `rung1_checkpoints/v1_blastoff/` for EMI — those runs predate the containment fix.

A slimmer, standalone extraction of the engine is [luckyseoul/custom-gpu-dem](https://github.com/luckyseoul/custom-gpu-dem).
