#!/usr/bin/env python3
"""Build README figures from the lumped model and custom GPU DEM checkpoints."""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models"))
import five_stage_counterflow as fsc  # noqa: E402

OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE = {}
SOURCES = {Path(__file__).resolve(), ROOT / "models/five_stage_counterflow.py"}
THERMAL_WARNING = "Legacy recurrence: invalid counter-flow model; diagnostic values only"
BASE_PARAMS = dict(P=0.14, IRON_COLD_MM=2.0, IRON_HOT_MM=3.5,
                   FILL_COLD=0.32, FILL_HOT=0.20, VEL_MULT_COLD=4.4,
                   VEL_MULT_HOT=3.5, EDS_EFF=0.97, PRECLASS_UM=22)


@contextmanager
def model_parameters(**overrides):
    """Use the documented point and restore every global even on failure."""
    saved = {key: getattr(fsc, key) for key in BASE_PARAMS}
    try:
        for key, value in (BASE_PARAMS | overrides).items():
            setattr(fsc, key, value)
        yield
    finally:
        for key, value in saved.items():
            setattr(fsc, key, value)


def evaluate_model(**overrides):
    with model_parameters(**overrides):
        return fsc.run_5stage()


def thermal_warning(fig):
    fig.text(0.5, -0.10, THERMAL_WARNING, ha="center", fontsize=9, color="#a52714")


def write_manifest():
    EVIDENCE["sources_sha256"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(SOURCES)
    }
    (OUT / "figure_data.json").write_text(json.dumps(EVIDENCE, indent=2, allow_nan=False) + "\n")

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 10,
        "figure.dpi": 140,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "svg.hashsalt": "rcfx-validated-figures",
    }
)


def save(fig, name: str) -> Path:
    p = OUT / name
    fig.savefig(p)
    fig.savefig(p.with_suffix(".svg"), metadata={"Date": None})
    plt.close(fig)
    print("wrote", p)
    return p


def fig_effectiveness_vs_pressure():
    pressures = np.array([0.10, 0.12, 0.14, 0.16, 0.18, 0.20])
    effs, powers = [], []
    for p in pressures:
        r = evaluate_model(P=float(p))
        effs.append(r["overall_eff"] * 100)
        powers.append(r["total_blower_W"])
    EVIDENCE["pressure"] = dict(pressure_bar=pressures.tolist(),
                                legacy_output_percent=effs, legacy_blower_W=powers)

    fig, ax1 = plt.subplots(figsize=(7.2, 4.0))
    ax1.plot(pressures, effs, "o-", color="#1f4e79", lw=2, ms=7, label="Legacy thermal output (unclipped)")
    ax1.axhline(100, color="#c0392b", ls="--", lw=1.2, label="Physical effectiveness ceiling")
    ax1.axvline(0.14, color="#7f8c8d", ls=":", lw=1.2)
    ax1.set_xlabel("Envelope pressure (bar)")
    ax1.set_ylabel("Legacy thermal output (%)")
    ax1.set_ylim(0, max(effs) * 1.12)
    ax2 = ax1.twinx()
    ax2.plot(pressures, powers, "s--", color="#d35400", lw=1.6, ms=6, label="Legacy blower calculation")
    ax2.set_ylabel("Legacy blower calculation (W)")
    ax2.grid(False)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9)
    ax1.set_title("Thermal-model audit — pressure sweep")
    ax1.annotate(
        "0.14 bar reference input",
        xy=(0.14, effs[list(pressures).index(0.14)]),
        xytext=(0.145, 30),
        arrowprops=dict(arrowstyle="->", color="#7f8c8d"),
        fontsize=9,
        color="#555",
    )
    thermal_warning(fig)
    save(fig, "effectiveness_vs_pressure.png")


def fig_stage_breakdown():
    r = evaluate_model()
    labels = [f"Stage {i+1}\n{'cold' if i < 2 else 'hot'}" for i in range(5)]
    vals = [e * 100 for e in r["stage_effs"]]
    EVIDENCE["stages"] = dict(raw_stage_coefficients=r["stage_effs"], legacy_output_percent=r["overall_eff"] * 100,
                              stage_trace=r["stage_trace"], validity=r["validity"],
                              valid_counterflow=r["valid_counterflow"])
    colors = ["#2e86ab"] * 2 + ["#e94f37"] * 3
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.bar(labels, vals, color=colors, edgecolor="none")
    ax.axhline(r["overall_eff"] * 100, color="#1f4e79", ls="--", lw=1.3, label=f"Legacy overall output {r['overall_eff']*100:.1f}%")
    ax.set_ylabel("Raw stage correlation × 100 (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Thermal-model audit — stage coefficients at 0.14 bar")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.legend(loc="lower right")
    thermal_warning(fig)
    save(fig, "stage_effectiveness.png")


def fig_sensitivity():
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.8))
    sweeps = {
        "EDS": ("EDS_EFF", [0.70, 0.80, 0.88, 0.93, 0.97, 0.99]),
        "Preclass": ("PRECLASS_UM", [18, 22, 26, 30, 35, 40, 50]),
    }
    EVIDENCE["sensitivity"] = {}

    def take(key):
        parameter, xs = sweeps[key]
        ys = [evaluate_model(**{parameter: x})["overall_eff"] * 100 for x in xs]
        EVIDENCE["sensitivity"][key] = dict(parameter=parameter, x=xs, legacy_output_percent=ys)
        return xs, ys

    for ax, key, xlabel, title in (
        (axes[0], "EDS", "EDS effectiveness", "Sensitivity to EDS"),
        (axes[1], "Preclass", "Pre-class cutoff (µm)", "Sensitivity to fines cutoff"),
    ):
        xs, ys = take(key)
        ax.plot(xs, ys, "o-", color="#1f4e79", lw=2, ms=6)
        ax.axvline(0.97 if key == "EDS" else 22, color="#7f8c8d", ls=":", lw=1.1)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Legacy thermal output (%)")
        ax.set_title(title)
        ax.set_ylim(45, 90)
    fig.suptitle("Thermal-model audit — parameter sweeps at 0.14 bar", y=1.02)
    fig.tight_layout()
    thermal_warning(fig)
    save(fig, "sensitivity_eds_preclass.png")


def _reg_iron_z(path: Path):
    SOURCES.add(path)
    with np.load(path) as d:
        z = d["pos"][:, 2] * 1e3
        mat = d["mat"]
    reg = z[mat == 0]
    iron = z[mat != 0]
    return reg, iron


def fig_dem_snapshot():
    ckpt = (
        ROOT
        / "sims"
        / "custom_gpu_dem"
        / "rung1_highn_checkpoints"
        / "physical_drag_real_u3.5_iron1.5mm_step002000.npz"
    )
    SOURCES.add(ckpt)
    with np.load(ckpt) as d:
        pos, mat = d["pos"], d["mat"]
    EVIDENCE["snapshot"] = dict(source=str(ckpt.relative_to(ROOT)),
                               regolith_mean_z_mm=float(pos[mat == 0, 2].mean() * 1e3),
                               iron_mean_z_mm=float(pos[mat != 0, 2].mean() * 1e3))
    fig, ax = plt.subplots(figsize=(6.0, 5.6))
    reg = mat == 0
    iron = ~reg
    ax.scatter(pos[reg, 0] * 1e3, pos[reg, 2] * 1e3, s=4, c="#8d6e63", alpha=0.55, linewidths=0, label="Regolith")
    ax.scatter(pos[iron, 0] * 1e3, pos[iron, 2] * 1e3, s=22, c="#546e7a", alpha=0.9, linewidths=0, label="Iron shot")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("z (mm)")
    ax.set_title("DEM checkpoint: x–z projection\n1.5 mm iron, 3.5 m/s gas, step 2000")
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 44)
    ax.axhline(pos[:, 2].max() * 1e3, color="#a52714", ls="--", lw=1,
               label=f"Maximum centre z: {pos[:, 2].max() * 1e3:.2f} mm")
    fig.text(0.5, 0.01, "Marker sizes are illustrative; particles overlap in projection.",
             ha="center", fontsize=9)
    ax.set_aspect("equal", adjustable="box")
    ax.legend(markerscale=2, loc="center left", bbox_to_anchor=(1.03, 0.5))
    save(fig, "dem_goodvar_snapshot.png")


def fig_dem_emi():
    """Bed-height contrast from the primary good-var checkpoint vs high-N series."""
    good = (
        ROOT
        / "sims"
        / "custom_gpu_dem"
        / "rung1_highn_checkpoints"
        / "physical_drag_real_u3.5_iron1.5mm_step002000.npz"
    )
    highn_dir = ROOT / "sims" / "custom_gpu_dem" / "rung1_highn_checkpoints"
    series = []
    for p in sorted(highn_dir.glob("rung1_highn_with_iron_step*.npz")):
        step = int(p.stem.split("step")[-1])
        reg, iron = _reg_iron_z(p)
        series.append((step, float(reg.mean()) if len(reg) else np.nan, float(iron.mean()) if len(iron) else np.nan))
    no_iron = []
    for p in sorted(highn_dir.glob("rung1_highn_no_iron_step*.npz")):
        step = int(p.stem.split("step")[-1])
        reg, _ = _reg_iron_z(p)
        no_iron.append((step, float(reg.mean()) if len(reg) else np.nan))

    EVIDENCE["dem_height"] = dict(with_iron=series, no_iron=no_iron,
                                 columns={"with_iron": ["step", "regolith_mean_z_mm", "iron_mean_z_mm"],
                                          "no_iron": ["step", "regolith_mean_z_mm"]})
    fig, (ax, separate) = plt.subplots(1, 2, figsize=(9.0, 4.3),
                                       gridspec_kw={"width_ratios": [2.8, 1]}, sharey=True)
    if series:
        st, zr, zi = zip(*series)
        ax.plot(st, zr, "o-", color="#8d6e63", lw=2, label="High-N with iron — regolith ⟨z⟩")
        ax.plot(st, zi, "s-", color="#546e7a", lw=2, label="High-N with iron — iron ⟨z⟩")
    if no_iron:
        stn, zn = zip(*no_iron)
        ax.plot(stn, zn, "o--", color="#c0392b", lw=1.6, label="High-N no iron — regolith ⟨z⟩")
    if good.exists():
        reg, iron = _reg_iron_z(good)
        means = [float(reg.mean()), float(iron.mean())]
        EVIDENCE["dem_height"]["separate_real_drag_step2000_mm"] = means
        separate.bar(["Regolith", "Iron"], means, color=["#8d6e63", "#546e7a"])
        for x, y in enumerate(means):
            separate.text(x, y + 0.6, f"{y:.2f}", ha="center", fontsize=9)
        separate.set_title("Separate real-drag run\n3.5 m/s, step 2000", fontsize=10)
        separate.tick_params(axis="x", labelsize=9)
    ax.set_xlabel("Checkpoint step (not seconds; separate runs)")
    ax.set_ylabel("Mean height (mm)")
    ax.set_title("High-N archive: particle-centre heights", fontsize=11)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.20), fontsize=9)
    fig.text(0.5, -0.24, "Different runs and saved steps; curves do not establish a controlled iron effect.",
             ha="center", fontsize=9)
    save(fig, "dem_bed_height.png")


def fig_checkpoint_inventory():
    base = ROOT / "sims" / "custom_gpu_dem"
    rows = []
    inventory_files = []
    for d in sorted(base.glob("*checkpoints")):
        files = list(d.glob("*.npz"))
        if not files:
            continue
        inventory_files.extend(files)
        bytes_ = sum(f.stat().st_size for f in files)
        rows.append((d.name.replace("_checkpoints", ""), len(files), bytes_ / 1e6))
    loose = list(base.glob("*.npz"))
    inventory_files.extend(loose)
    rows.append(("root dumps", len(loose), sum(f.stat().st_size for f in loose) / 1e6))
    EVIDENCE["inventory"] = dict(rows=rows, columns=["directory", "files", "decimal_MB"],
                                total_files=sum(r[1] for r in rows),
                                total_MB=sum(r[2] for r in rows),
                                files=[{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size}
                                       for p in sorted(inventory_files)])
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    names = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    bars = ax.bar(names, counts, color="#1f4e79")
    ax.set_ylabel("Checkpoint files")
    ax.set_title(f"DEM archive — {sum(counts):,} files (includes root dumps)")
    ax.tick_params(axis="x", labelsize=9)
    for b, (_, n, mb) in zip(bars, rows):
        ax.text(b.get_x() + b.get_width() / 2, n + 8, f"{n}\n{mb:.0f} MB", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, max(counts) * 1.28)
    save(fig, "checkpoint_inventory.png")


if __name__ == "__main__":
    fig_effectiveness_vs_pressure()
    fig_stage_breakdown()
    fig_sensitivity()
    fig_dem_snapshot()
    fig_dem_emi()
    fig_checkpoint_inventory()
    write_manifest()
    print("done", OUT)
