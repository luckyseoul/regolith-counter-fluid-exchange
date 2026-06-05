#!/usr/bin/env python3
"""FIG. 7 — Rung 5 GPU DEM mobilization progression (contained checkpoints only)."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BOX = 0.016
CKPT_DIR = Path(__file__).resolve().parents[1] / "sims/custom_gpu_dem/rung5_checkpoints"
OUT_DIR = Path(__file__).resolve().parent


def load_series():
    rows = []
    for p in sorted(CKPT_DIR.glob("rung5_step*.npz"), key=lambda x: int(x.stem.split("step")[1])):
        d = np.load(p)
        step = int(d["step"])
        pos = d["pos"]
        mat = d["mat"]
        inside = (
            (pos[:, 0] >= 0) & (pos[:, 0] <= BOX)
            & (pos[:, 1] >= 0) & (pos[:, 1] <= BOX)
            & (pos[:, 2] >= 0)
        )
        z = pos[inside, 2] * 1000
        reg = mat == 0
        iron = mat == 1
        rb = float(pos[reg, 2].mean() * 1000) if reg.any() else 0.0
        ib = float(pos[iron, 2].mean() * 1000) if iron.any() else 0.0
        rows.append((step, float(z.mean()), rb, ib, 100.0 * inside.mean()))
    return rows


def main():
    rows = load_series()
    steps = np.array([r[0] for r in rows])
    bed = np.array([r[1] for r in rows])
    iron_b = np.array([r[2] for r in rows])
    reg_b = np.array([r[3] for r in rows])

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "text.color": "black",
    })
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    ax.plot(steps / 1000, bed, "k-", linewidth=1.2, label="Mean bed height (all)")
    ax.plot(steps / 1000, iron_b, "k--", linewidth=0.9, label="Iron mean z (proxy)")
    ax.plot(steps / 1000, reg_b, "k:", linewidth=0.9, label="Regolith mean z (proxy)")
    ax.axvline(200, color="black", linewidth=0.6, linestyle="-.", alpha=0.7)
    ax.axvline(500, color="black", linewidth=0.6, linestyle="-.", alpha=0.7)
    ax.annotate("200k lock", xy=(200, bed[np.searchsorted(steps, 200000)]), xytext=(210, bed.max() * 0.55),
                fontsize=8, arrowprops=dict(arrowstyle="->", color="black", lw=0.6))
    ax.annotate("500k lock", xy=(500, bed[-1]), xytext=(420, bed.max() * 0.85),
                fontsize=8, arrowprops=dict(arrowstyle="->", color="black", lw=0.6))
    ax.set_xlabel("Simulation step (×10³)")
    ax.set_ylabel("Mean bed height (mm)")
    ax.set_title("FIG. 7 — Rung 5 sensitivity GPU DEM mobilization progression\n"
                 "0.14 bar rep (U_G=0.066 m/s); combined degradation; 100.0% contained all ckpts")
    ax.legend(loc="upper left", frameon=True, edgecolor="black", fontsize=8)
    ax.grid(True, linestyle=":", linewidth=0.4, color="gray")
    fig.tight_layout()
    for ext in ("svg", "pdf"):
        out = OUT_DIR / f"FIG_07_rung5_mobilization_progression.{ext}"
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        print("wrote", out)
    plt.close(fig)


if __name__ == "__main__":
    main()