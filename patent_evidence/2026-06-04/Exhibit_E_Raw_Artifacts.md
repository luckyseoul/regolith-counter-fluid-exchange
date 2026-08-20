# Exhibit E — Raw Artifact Index (Reproducibility)

**Cover statement**: This exhibit lists primary data files, logs, and scripts needed to reproduce or audit every cited Rung 5 and related DEM number in the evidence package.

## Rung 5 GPU DEM (locked)
| Artifact | Description |
|----------|-------------|
| `sims/custom_gpu_dem/rung5_checkpoints/rung5_step500000.npz` | Final 500k lock (334th checkpoint slice) |
| `sims/custom_gpu_dem/rung5_checkpoints/rung5_step200000.npz` | Prior 200k lock |
| `sims/custom_gpu_dem/rung5_checkpoints/rung5_step*.npz` | Full series (334 files, 1500-step cadence) |
| `/tmp/rung5_slice.log` | Complete run log incl. `rung5 done...` and proxy lines |
| `/tmp/rung5_status.txt` | Last status bar snapshot |
| `sims/custom_gpu_dem/run_rung5_sensitivity_stub.py` | Runner (real DEM, not stub physics) |
| `sims/custom_gpu_dem/rung5_status.py` | Verification / progress utility |

## Related locked rungs (context)
| Rung | Final checkpoint | Steps |
|------|------------------|-------|
| 0 | `rung0_checkpoints/rung0_step500000.npz` | 500,000 |
| 1 | `rung1_checkpoints/` (locked EMI run) | per campaign MD |
| 4 | `rung4_checkpoints/` | per campaign MD |

## Lumped / analytical
| Artifact | Description |
|----------|-------------|
| `rung_results/rung5_sensitivity.npy` | Sensitivity + robustness dict |
| `models/five_stage_counterflow.py` | 5-stage counterflow model |
| `rung_results/RUNG_CAMPAIGN_RESULTS.md` | Campaign master log (search-replace locked numbers) |

## Patent outputs (this filing support set)
| Path | Role |
|------|------|
| `patent_evidence/2026-06-04/` | This package |
| `patent_drawings/FIG_*.svg/pdf` | Formal figures |
| `patent_specification_draft.md` | Specification support draft |

## Reproduction commands
```bash
python sims/custom_gpu_dem/rung5_status.py
cat /tmp/rung5_status.txt
python3 -c "import numpy as np; d=np.load('sims/custom_gpu_dem/rung5_checkpoints/rung5_step500000.npz'); print(list(d.files), d['step'])"
```

## Integrity note
Do not cite pre-containment or partial-escape checkpoints. The campaign explicitly invalidates any ckpt not meeting 100.0% inside + zmin ≥ 0.

**Batch audit (2026-06-04)**: All **334** files in `rung5_checkpoints/rung5_step*.npz` pass the inside mask (x,y ∈ [0, 0.016] m, z ≥ 0) with zmin ≥ 0 on every particle.