# How to Run the RCFX Rungs on soulkiller (LIGGGHTS 3.8.0 full build)

**Status (31 May 2026)**: Proper full-featured LIGGGHTS-PUBLIC 3.8.0 is now installed at `/usr/local/bin/liggghts`.

The binary was built from the exact Ubuntu 3.8.0+repack1 source tree with all patches, VTK 9.5, Boost MPI, and complete granular + sjkr/sjkr2 cohesion support.

## One-time setup (already done)
- `/usr/local/bin/liggghts` is the working binary.
- All material + cohesion models for Rung 2/4 are available.

## Quick validation run (Rung 2 at 0.14 bar, small data)

```bash
cd /home/nick/rcfx/sims/liggghts/rung2
mkdir -p post
/usr/local/bin/liggghts < rung2_0.14_sjkr.in
```

This uses the corrected modern syntax (`pair_style gran model hertz tangential history cohesion sjkr` + proper `peratomtypepair` matrices for 2 atom types).

For MPI parallel (recommended on 88-core machine):

```bash
mpirun -np 16 /usr/local/bin/liggghts < rung2_0.14_sjkr.in
```

## Production runs
The current `bimodal_regolith.data` is a small toy system (box ~0.02 m) for fast validation only.

For real Rung 2/4/5 results you need larger systems (hundreds of thousands of particles). Use the generators in `rung2/`:

- `generate_realistic_data.py`
- `generate_rung2_data.py`

Then switch to the production .in files (e.g. `rung2_production_0.14bar.in` after adapting them the same way as the sjkr version).

## Custom GPU DEM (CuPy) alternative / complement
While LIGGGHTS runs, you can also launch the custom GPU DEM for faster iteration on Rung 2 physics:

```bash
cd /home/nick/rcfx/sims/custom_gpu_dem/rung2
python3 rung2_0.14bar.py
```

## Next after successful small runs
- Scale particle count + box size for production statistics.
- Add heat transfer / multi-stage coupling for Rung 4.
- Post-process dumps vs the Python 5-stage counterflow model.
- Update `rung_results/` and campaign docs with real DEM evidence for the patent.

All work stays strictly within PERRY-RCFX-004 Rev 5.2 claims.

Run the validation command above — it should now execute cleanly (neighbor/nsq or small-box tweaks may still be needed for the toy data). Let me know the output and we'll scale immediately.
## Rung 4 Setup (Single Stage Representative)

```bash
cd /home/nick/rcfx/sims/liggghts/rung4
./../launch_rung4.sh          # or set NPROCS=...
```

Input: `rung4_0.14_sjkr.in` (same modern sjkr + peratomtypepair syntax as Rung 2).

Note: The data file `data/rung4_stage.data` must be generated or provided before a meaningful run. Use the same data generation approach as Rung 2 but for a single-stage slice at operating conditions.

Once small validation passes, this becomes the template for the full 5-stage Rung 4 counterflow DEM.

## Reliable Command for First Real Data (after the MPI interface hell)

```bash
cd /home/nick/rcfx/sims/liggghts/rung2
NPROCS=12 ./run_packer_direct.sh
```

This uses the exact safe mpirun flags we discovered (`--mca btl_tcp_if_include lo,enp5s0 --mca btl ^openib,ofi --mca pml ob1`).

Once it finishes you will have `data/rung2_first_real.data` and can immediately launch real parallel Rung runs.

## Full Rung 4 (5-stage)

See `rung4/full_stages/run_full_rung4.sh` and the stage1..stage5 templates.

Use the same `run_packer_direct.sh` style (or the Python wrapper) to generate stage-specific packed data, then chain the stages with restarts.

This is now the proper path for the entire Rung campaign.
