# RCFX campaign results

Particle-scale numbers are from the custom GPU DEM in `sims/custom_gpu_dem/`.
Plant-level numbers are from `models/five_stage_counterflow.py`. Quantitative DEM
citations use physical-lid checkpoints (100% of particles inside
**x,y ∈ [0, 0.018] m**, z ≥ 0). EMI is with-iron regolith ⟨z⟩ / no-iron-control
regolith ⟨z⟩. Unbounded EMI 107.9× / 109.4× and the pre-fix 68 W blower are historical.

## Working point

| | |
|--|--:|
| Envelope pressure | 0.14 bar |
| Overall thermal effectiveness | 75.6% |
| Recovered heat (100 kg/h) | 11.8 kW |
| Blower power | 221 W (1.88% parasitic) |
| Cold stages 1–2 | 2.0 mm iron, fill 0.32, 4.4× *U*<sub>mf</sub>, EDS 0.97, pre-class 22 µm |
| Hot stages 3–5 | 3.5 mm iron, fill 0.20, 3.5× *U*<sub>mf</sub>, EDS 0.97 |

Blower power uses `vol_flow = U × AREA` at the DEM-aligned cold *U*<sub>G</sub> = 0.066 m/s.

## Rung 0 — distributor

Gas + sintered distributor at the 0.14 bar representative velocity. Custom DEM,
N = 1800, *U*<sub>G</sub> = 0.055 m/s, 500k steps, 334 checkpoints.

Final `rung0_step500000.npz`: mean bed 31.0 mm, 100% inside. Distributor ΔP remains
the dominant per-stage drop in the lumped model (~94%).

## Rung 1 — coarse fraction + iron (custom DEM)

Official Rung 1 is the **high-N physical-lid** series plus the **good-variable
real-drag** point. Both were run with the custom GPU DEM.

### High-N (N = 6500)

Physical lid and freeboard from step 0. Direct loads of
`rung1_highn_checkpoints/`:

| Checkpoint | Regolith ⟨z⟩ | Iron ⟨z⟩ | EMI vs no-iron baseline |
|------------|-------------:|---------:|------------------------:|
| no-iron step 400 | 3.23 mm | — | 1.0× (baseline) |
| with-iron step 400 | 12.49 mm | — | 3.87× |
| with-iron step 1000 | 25.99 mm | — | 8.04× |
| with-iron step 1300 | 27.57 mm | 27.25 mm | 8.53× (peak) |
| with-iron step 2000 | 25.48 mm | 23.92 mm | 7.89× |

No-iron control remains packed (~3.2 mm, ~87% dead, ~0.4 m/s). With iron, the bed
expands under the lid (zmax ~41–42 mm) with 100% containment on **BOX = 0.018 m**.
Mean regolith speed at peak EMI is ~40 m/s (vmax ~130 m/s) — lid-capped agitation,
not a calm expanded bed. Audit:
`patent_evidence/2026-06-04/Rung1_HighN_Primary_Audit_6500.md`.

### Good-variable real-drag point

`physical_drag_real_u3.5_iron1.5mm_step002000.npz` — 1.5 mm iron, real drag only,
3.5 m/s, physical lid:

| | |
|--|--:|
| Iron bed | 34.47 mm |
| Regolith bed | 11.56 mm |
| EMI vs no-iron | 3.58× |
| Inside (BOX = 0.018 m) | 100% |

This is the primary mechanistic checkpoint for the 1.5–2.0 mm / 0.1–0.5 bar envelope.

## Rung 2 — iron agitation

Custom DEM production and no-iron controls at 0.14 bar. See
`sims/custom_gpu_dem/Rung2_*` summaries and `rung2_checkpoints/`.

## Rung 3 — EDS

Lumped-model EDS lever: overall effectiveness is a strong function of EDS (0.97
at the working point). Demo runners: `run_rung3_eds_*.py`.

## Rung 4 — five-stage counter-flow

Lumped 5-stage energy balance at 0.12 / 0.14 / 0.15 bar
(`rung_results/rung4_results.npy`). Two-stage DEM transfer demo in
`rung4_checkpoints/` (230 particle transfers in the skeleton run).

## Rung 5 — sensitivity

Lumped one-at-a-time sweeps in `rung5_sensitivity.npy`:

- Baseline: 75.6% at 221 W
- EDS and pre-class cutoff are the high-leverage knobs
- Combined moderate degradation remains near 70%; worst simultaneous case ~59%

DEM combined-degradation series: `rung5_checkpoints/` (500k steps). Absolute
heights from that series are not used for EMI; Rung 1 high-N / good-variable
are the quantitative DEM citations.

## Sources

| Artifact | Path |
|----------|------|
| Lumped model | `models/five_stage_counterflow.py` |
| Rung 1 high-N | `sims/custom_gpu_dem/rung1_highn_checkpoints/` |
| Good-variable | `.../physical_drag_real_u3.5_iron1.5mm_step002000.npz` |
| Rung 0 / 2 / 4 / 5 | `sims/custom_gpu_dem/rung*_checkpoints/` |
| Parameter table | `docs/rcfx_key_parameters.md` |
