#!/usr/bin/env python3
"""CPU-only, reproducible measurements behind the DEM README figures.

Run from any directory. Configuration in source runners is explicitly separated
from checkpoint facts: the archives do not store gas velocity, timestep, seed,
force mode, start state, or source revision.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "sims/custom_gpu_dem"
HIGHN = BASE / "rung1_highn_checkpoints"
GOODVAR = HIGHN / "physical_drag_real_u3.5_iron1.5mm_step002000.npz"
BASELINE = HIGHN / "rung1_highn_no_iron_step000400.npz"
BOUNDS_M = np.array([0.018, 0.018, 0.060])


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkpoint_stats(path: Path) -> dict:
    """Validate array structure and measure centers, diameters, and velocities."""
    with np.load(path, allow_pickle=False) as d:
        required = {"pos", "vel", "radius", "mat", "step"}
        if not required.issubset(d.files):
            raise ValueError(f"{path}: missing {required - set(d.files)}")
        pos = np.asarray(d["pos"], dtype=np.float64)
        vel = np.asarray(d["vel"], dtype=np.float64)
        radius = np.asarray(d["radius"], dtype=np.float64)
        mat = d["mat"]
        step_array = d["step"]
        fields = sorted(d.files)
    n = len(pos)
    if pos.shape != (n, 3) or vel.shape != (n, 3) or radius.shape != (n,) or mat.shape != (n,):
        raise ValueError(f"{path}: inconsistent particle array shapes")
    if not all(np.isfinite(a).all() for a in (pos, vel, radius, mat)) or (radius <= 0).any():
        raise ValueError(f"{path}: nonfinite data or nonpositive radius")
    if not np.isin(mat, [0, 1]).all():
        raise ValueError(f"{path}: unknown material labels")
    if step_array.size != 1 or float(step_array.item()) != int(step_array.item()):
        raise ValueError(f"{path}: invalid checkpoint step")
    step = int(step_array.item())
    if "step" in path.stem and step != int(path.stem.rsplit("step", 1)[1]):
        raise ValueError(f"{path}: filename/internal step mismatch")
    centers_inside = ((pos >= 0) & (pos <= BOUNDS_M)).all(axis=1)
    spheres_inside = ((pos - radius[:, None] >= 0) & (pos + radius[:, None] <= BOUNDS_M)).all(axis=1)
    result = {
        "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "sha256": sha256(path), "stored_fields": fields, "step": step,
        "n_particles": n,
        "center_bounds_m": [pos.min(axis=0).tolist(), pos.max(axis=0).tolist()],
        "center_inside_count": int(centers_inside.sum()),
        "whole_sphere_inside_count": int(spheres_inside.sum()),
    }
    for label, mask in (("regolith", mat == 0), ("iron", mat == 1)):
        result[label] = {
            "count": int(mask.sum()),
            "mean_center_z_mm": float(pos[mask, 2].mean() * 1000) if mask.any() else None,
            "diameter_range_mm": [float(radius[mask].min() * 2000), float(radius[mask].max() * 2000)] if mask.any() else None,
            "mean_speed_m_s": float(np.linalg.norm(vel[mask], axis=1).mean()) if mask.any() else None,
        }
    return result


def checkpoint_inventory() -> dict:
    rows = []
    for folder in sorted(BASE.glob("*checkpoints")):
        files = sorted(folder.glob("*.npz"))
        rows.append({"directory": str(folder.relative_to(ROOT)), "files": len(files),
                     "bytes": sum(p.stat().st_size for p in files)})
    loose = sorted(BASE.glob("*.npz"))
    return {"directories": rows, "loose_files": len(loose),
            "loose_bytes": sum(p.stat().st_size for p in loose),
            "total_files": sum(r["files"] for r in rows) + len(loose),
            "total_bytes": sum(r["bytes"] for r in rows) + sum(p.stat().st_size for p in loose),
            "size_units": "decimal MB = bytes / 1,000,000"}


def source_constants(path: Path) -> dict:
    """Read simple top-level constants without importing GPU runners."""
    wanted = {"BOX", "U_G", "DAMP", "FREEBOARD_Z", "LID_Z", "DT"}
    constants = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in wanted:
                    constants[target.id] = ast.literal_eval(node.value)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "default_constants": constants}


def build_report() -> dict:
    patterns = {
        "highn_with_iron": "rung1_highn_with_iron_step*.npz",
        "highn_no_iron": "rung1_highn_no_iron_step*.npz",
        "real_drag_filename_u3_5_iron1_5mm": "physical_drag_real_u3.5_iron1.5mm_step*.npz",
    }
    series = {name: [checkpoint_stats(p) for p in sorted(HIGHN.glob(pattern))]
              for name, pattern in patterns.items()}
    if any(not rows for rows in series.values()):
        raise ValueError("Missing plotted checkpoint series")
    baseline = checkpoint_stats(BASELINE)
    good = checkpoint_stats(GOODVAR)
    peak = max(series["highn_with_iron"], key=lambda r: r["regolith"]["mean_center_z_mm"])
    baseline_z = baseline["regolith"]["mean_center_z_mm"]
    return {
        "schema_version": 1,
        "scope": "Archive measurement and source inspection; no GPU simulation or physical validation",
        "containment_test_bounds_m": BOUNDS_M.tolist(),
        "inventory": checkpoint_inventory(),
        "series": series,
        "reference_ratios": {
            "interpretation": "Descriptive ratios to an earlier no-iron checkpoint; not matched-condition causal effects",
            "denominator_path": baseline["path"], "denominator_step": baseline["step"],
            "denominator_mean_regolith_z_mm": baseline_z,
            "goodvar_to_baseline": good["regolith"]["mean_center_z_mm"] / baseline_z,
            "sampled_highn_peak_step": peak["step"],
            "sampled_highn_peak_mean_regolith_z_mm": peak["regolith"]["mean_center_z_mm"],
            "sampled_highn_peak_to_baseline": peak["regolith"]["mean_center_z_mm"] / baseline_z,
        },
        "current_source_runners": [source_constants(BASE / name) for name in (
            "migrate_rung1_highn.py", "continue_highn_rung1.py", "continue_physical_drag_fix.py")],
        "limitations": [
            "Step labels are stored checkpoint counters, not verified time since initialization; all inspected runners currently set DT=6.5e-7 seconds.",
            "Checkpoints store no run configuration or source revision; gas velocity 3.5 m/s is a filename label, not stored metadata.",
            "Current high-N runner defaults use U_G=0.066 m/s and distributor body forces; physical-drag runner can override velocity and disables those adders.",
            "Fresh high-N runner uses distributor strength 12; continuation uses 2.8, so filenames alone do not establish homogeneous forcing history.",
            "No-iron series ends at step 400; no matched no-iron step 2000 or matched physical-drag control is included in these plotted series.",
            "Current lid routine caps particle centers and damps velocity; whole-sphere containment is a separate stricter measurement.",
            "Mean particle-center height is neither bed surface height nor a direct measurement of thermal exchange or agitation.",
            "The sampled high-N peak is the maximum among archived plotted checkpoints, not a steady-state or full-trajectory maximum.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/figures/dem_validation.json")
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {args.output}; measured {sum(map(len, report['series'].values()))} plotted checkpoints")


if __name__ == "__main__":
    main()
