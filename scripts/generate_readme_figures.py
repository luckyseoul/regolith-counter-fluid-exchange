#!/usr/bin/env python3
"""Build README figures from the lumped model and custom GPU DEM checkpoints."""
from __future__ import annotations

import os
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
    }
)


def save(fig, name: str) -> Path:
    p = OUT / name
    fig.savefig(p)
    fig.savefig(p.with_suffix(".svg"))
    plt.close(fig)
    print("wrote", p)
    return p


def fig_effectiveness_vs_pressure():
    pressures = np.array([0.10, 0.12, 0.14, 0.16, 0.18, 0.20])
    effs, powers = [], []
    saved_p = fsc.P
    for p in pressures:
        fsc.P = float(p)
        r = fsc.run_5stage()
        # Stage correlation is not bounded at 1; clip display and note saturation.
        effs.append(min(r["overall_eff"] * 100, 100.0))
        powers.append(r["total_blower_W"])
    fsc.P = saved_p

    fig, ax1 = plt.subplots(figsize=(7.2, 4.0))
    ax1.plot(pressures, effs, "o-", color="#1f4e79", lw=2, ms=7, label="Overall effectiveness")
    ax1.axhline(70, color="#c0392b", ls="--", lw=1.2, label="70% target")
    ax1.axvline(0.14, color="#7f8c8d", ls=":", lw=1.2)
    ax1.set_xlabel("Envelope pressure (bar)")
    ax1.set_ylabel("Overall thermal effectiveness (%)")
    ax1.set_ylim(40, 105)
    ax2 = ax1.twinx()
    ax2.plot(pressures, powers, "s--", color="#d35400", lw=1.6, ms=6, label="Blower power")
    ax2.set_ylabel("Blower power (W)")
    ax2.grid(False)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="lower right")
    ax1.set_title("5-stage lumped model — effectiveness and blower vs pressure")
    ax1.annotate(
        "0.14 bar working point",
        xy=(0.14, effs[list(pressures).index(0.14)]),
        xytext=(0.17, 62),
        arrowprops=dict(arrowstyle="->", color="#7f8c8d"),
        fontsize=9,
        color="#555",
    )
    save(fig, "effectiveness_vs_pressure.png")


def fig_stage_breakdown():
    fsc.P = 0.14
    r = fsc.run_5stage()
    labels = [f"Stage {i+1}\n{'cold' if i < 2 else 'hot'}" for i in range(5)]
    vals = [e * 100 for e in r["stage_effs"]]
    colors = ["#2e86ab"] * 2 + ["#e94f37"] * 3
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.bar(labels, vals, color=colors, edgecolor="none")
    ax.axhline(r["overall_eff"] * 100, color="#1f4e79", ls="--", lw=1.3, label=f"Overall {r['overall_eff']*100:.1f}%")
    ax.set_ylabel("Stage effectiveness (%)")
    ax.set_ylim(0, 110)
    ax.set_title(f"Stage effectiveness at 0.14 bar  ·  blower {r['total_blower_W']:.0f} W")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.legend(loc="lower right")
    save(fig, "stage_effectiveness.png")


def fig_sensitivity():
    data = np.load(ROOT / "rung_results" / "rung5_sensitivity.npy", allow_pickle=True).item()
    sweeps = data["single_param_sweeps"]
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.8))

    def take(prefix):
        xs, ys = [], []
        for name, x, eff, _pwr in sweeps:
            if name == prefix:
                xs.append(float(x))
                ys.append(float(eff) * 100)
        return xs, ys

    for ax, key, xlabel, title in (
        (axes[0], "EDS", "EDS effectiveness", "Sensitivity to EDS"),
        (axes[1], "Preclass", "Pre-class cutoff (µm)", "Sensitivity to fines cutoff"),
    ):
        xs, ys = take(key)
        ax.plot(xs, ys, "o-", color="#1f4e79", lw=2, ms=6)
        ax.axhline(70, color="#c0392b", ls="--", lw=1.1)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Overall effectiveness (%)")
        ax.set_title(title)
        ax.set_ylim(45, 90)
    fig.suptitle("Lumped-model robustness at the 0.14 bar point", y=1.02)
    fig.tight_layout()
    save(fig, "sensitivity_eds_preclass.png")


def _reg_iron_z(path: Path):
    d = np.load(path)
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
    d = np.load(ckpt)
    pos = d["pos"]
    mat = d["mat"]
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    reg = mat == 0
    iron = ~reg
    ax.scatter(pos[reg, 0] * 1e3, pos[reg, 2] * 1e3, s=4, c="#8d6e63", alpha=0.55, linewidths=0, label="Regolith")
    ax.scatter(pos[iron, 0] * 1e3, pos[iron, 2] * 1e3, s=22, c="#546e7a", alpha=0.9, linewidths=0, label="Iron shot")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("z (mm)")
    ax.set_title("Custom GPU DEM — good-variable point (1.5 mm iron, 3.5 m/s, step 2000)")
    ax.set_aspect("equal", adjustable="box")
    ax.legend(markerscale=2, loc="upper right")
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

    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    if series:
        st, zr, zi = zip(*series)
        ax.plot(st, zr, "o-", color="#8d6e63", lw=2, label="High-N with iron — regolith ⟨z⟩")
        ax.plot(st, zi, "s-", color="#546e7a", lw=2, label="High-N with iron — iron ⟨z⟩")
    if no_iron:
        stn, zn = zip(*no_iron)
        ax.plot(stn, zn, "o--", color="#c0392b", lw=1.6, label="High-N no iron — regolith ⟨z⟩")
    if good.exists():
        reg, iron = _reg_iron_z(good)
        ax.axhline(reg.mean(), color="#27ae60", ls=":", lw=1.4, label=f"Good-var iron 1.5 mm  ⟨z⟩_reg={reg.mean():.1f} mm")
    ax.set_xlabel("Checkpoint step")
    ax.set_ylabel("Mean height (mm)")
    ax.set_title("Custom GPU DEM — iron agitation vs no-iron control")
    ax.legend(loc="best")
    save(fig, "dem_bed_height.png")


def fig_checkpoint_inventory():
    base = ROOT / "sims" / "custom_gpu_dem"
    rows = []
    for d in sorted(base.glob("*checkpoints")):
        files = list(d.glob("*.npz"))
        if not files:
            continue
        bytes_ = sum(f.stat().st_size for f in files)
        rows.append((d.name.replace("_checkpoints", ""), len(files), bytes_ / 1e6))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    names = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    bars = ax.bar(names, counts, color="#1f4e79")
    ax.set_ylabel("Checkpoint files")
    ax.set_title("Custom GPU DEM checkpoint archive in this repo")
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
    print("done", OUT)
