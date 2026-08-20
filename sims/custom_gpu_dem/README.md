# Custom GPU DEM

Particle-scale simulator for every RCFX DEM number in this repository.

- Kernels: `common/dem_kernels.py` (Hertz + JKR-style cohesion, rolling, porosity-aware drag)
- Step / cell-list: `common/cell_list.py`, `common/optimized_step.py`
- Runners: `run_rung*.py`, `continue_*.py`, `migrate_rung1_highn.py`
- Checkpoints: `rung*_checkpoints/` — Rung 1 citations use `rung1_highn_checkpoints/`

See [DATA.md](../../DATA.md). Standalone extract: [luckyseoul/custom-gpu-dem](https://github.com/luckyseoul/custom-gpu-dem).
