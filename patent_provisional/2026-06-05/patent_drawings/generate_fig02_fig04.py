#!/usr/bin/env python3
"""Generate FIG. 2 (single-stage cross-section) and FIG. 4 (counter-current transfer)."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Rectangle, Circle, FancyArrowPatch, Polygon, Arc, Wedge
)
from matplotlib import patheffects as pe

OUT = Path(__file__).resolve().parent


def patent_style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 9,
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "text.color": "black",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def label_num(ax, xy, num, offset=(0.02, 0.02), ha="left", va="bottom"):
    ax.annotate(
        str(num), xy=xy, xytext=(xy[0] + offset[0], xy[1] + offset[1]),
        fontsize=8, fontweight="bold", ha=ha, va=va,
        arrowprops=dict(arrowstyle="-", color="black", lw=0.5, shrinkA=2, shrinkB=2),
    )


def hatch_regolith(ax, x0, y0, w, h):
    """Stippled regolith region."""
    rect = Rectangle((x0, y0), w, h, fill=False, edgecolor="black", lw=0.8)
    ax.add_patch(rect)
    rng = np.random.default_rng(42)
    for _ in range(int(w * h * 1200)):
        px = x0 + rng.uniform(0.05, 0.95) * w
        py = y0 + rng.uniform(0.1, 0.9) * h
        ax.plot(px, py, "k.", markersize=0.6)


def draw_iron_particles(ax, x0, y0, w, h, n=18):
    rng = np.random.default_rng(7)
    for _ in range(n):
        cx = x0 + rng.uniform(0.1, 0.9) * w
        cy = y0 + rng.uniform(0.15, 0.85) * h
        r = rng.uniform(0.012, 0.022)
        c = Circle((cx, cy), r, fc="black", ec="black", lw=0.5)
        ax.add_patch(c)


def fig02_stage_cross_section():
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    # Vessel walls (100)
    wall_l = Rectangle((0.08, 0.12), 0.04, 0.76, fc="white", ec="black", lw=1.2)
    wall_r = Rectangle((0.88, 0.12), 0.04, 0.76, fc="white", ec="black", lw=1.2)
    ax.add_patch(wall_l)
    ax.add_patch(wall_r)

    # Bed chamber interior (102)
    chamber = Rectangle((0.12, 0.18), 0.76, 0.62, fill=False, ec="black", lw=0.6, ls="--")
    ax.add_patch(chamber)

    # Gas plenum (106)
    plenum = Rectangle((0.12, 0.12), 0.76, 0.06, fc="white", ec="black", lw=0.8)
    ax.add_patch(plenum)
    ax.text(0.5, 0.145, "Gas plenum", ha="center", va="center", fontsize=7)

    # Distributor plate (104) — sintered, hatched
    dist = Rectangle((0.12, 0.175), 0.76, 0.025, fc="white", ec="black", lw=1.0)
    ax.add_patch(dist)
    for x in np.linspace(0.14, 0.86, 25):
        ax.plot([x, x], [0.175, 0.20], "k-", lw=0.4)

    # Fluidized bed — regolith (110) + iron (112)
    hatch_regolith(ax, 0.14, 0.22, 0.72, 0.48)
    draw_iron_particles(ax, 0.14, 0.22, 0.72, 0.48)

    # Gas flow arrows (108)
    for x in np.linspace(0.2, 0.8, 6):
        ax.annotate("", xy=(x, 0.55), xytext=(x, 0.21),
                    arrowprops=dict(arrowstyle="->", color="black", lw=0.7))
    ax.text(0.92, 0.42, "U_G\n(0.14 bar rep)", fontsize=7, ha="left")

    # Heat transfer coil (116)
    coil_y = 0.35
    for i in range(5):
        x = 0.18 + i * 0.14
        ax.add_patch(Arc((x, coil_y), 0.12, 0.25, angle=0, theta1=0, theta2=180,
                         edgecolor="black", lw=1.0, fill=False))
    ax.plot([0.15, 0.85], [coil_y, coil_y], "k-", lw=0.8)

    # EDS electrodes (118)
    ax.plot([0.16, 0.16], [0.72, 0.82], "k--", lw=0.8)
    ax.plot([0.84, 0.84], [0.72, 0.82], "k--", lw=0.8)
    ax.text(0.5, 0.86, "EDS electrodes (optional)", ha="center", fontsize=7)

    # Overflow / weir (114)
    weir_x = 0.86
    ax.plot([weir_x, weir_x], [0.55, 0.78], "k-", lw=1.2)
    ax.plot([weir_x, 0.94], [0.78, 0.78], "k-", lw=1.2)
    ax.annotate("", xy=(0.97, 0.78), xytext=(0.88, 0.65),
                arrowprops=dict(arrowstyle="->", color="black", lw=0.8))

    # Solids transfer opening (120)
    ax.annotate("", xy=(0.97, 0.5), xytext=(0.88, 0.45),
                arrowprops=dict(arrowstyle="->", color="black", lw=0.8, ls="--"))
    ax.text(0.97, 0.48, "Solids\ntransfer", fontsize=7, ha="left")

    # Legend keys (material)
    ax.add_patch(Circle((0.2, 0.05), 0.015, fc="black", ec="black"))
    ax.text(0.23, 0.05, "112  Iron shot (1.5–3.5 mm)", fontsize=7, va="center")
    ax.plot(0.55, 0.05, "k.", markersize=4)
    ax.text(0.58, 0.05, "110  Regolith fines (bimodal PSD)", fontsize=7, va="center")

    # Reference numerals
    label_num(ax, (0.10, 0.5), 100, offset=(-0.06, 0))
    label_num(ax, (0.5, 0.5), 102, offset=(0, 0.05))
    label_num(ax, (0.5, 0.19), 104, offset=(0, -0.06))
    label_num(ax, (0.5, 0.14), 106, offset=(0, -0.05))
    label_num(ax, (0.35, 0.45), 108, offset=(-0.04, 0.04))
    label_num(ax, (0.5, 0.35), 110, offset=(0, -0.05))
    label_num(ax, (0.3, 0.55), 112, offset=(-0.05, 0))
    label_num(ax, (0.88, 0.72), 114, offset=(0.02, 0))
    label_num(ax, (0.5, 0.35), 116, offset=(0.12, 0.08))
    label_num(ax, (0.16, 0.78), 118, offset=(-0.05, 0.02))
    label_num(ax, (0.95, 0.5), 120, offset=(0.02, 0))

    ax.set_title(
        "FIG. 2 — Cross-section of a single fluidized bed stage\n"
        "(0.14 bar envelope representative point; iron shot agitation of cohesive fines)",
        fontsize=10, pad=12,
    )
    fig.tight_layout()
    return fig


def fig04_countercurrent():
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_aspect("equal")
    ax.axis("off")

    stages = ["Stage 1\n(cold)", "Stage 2", "Stage 3", "Stage 4", "Stage 5\n(hot)"]
    xs = np.linspace(1.2, 8.2, 5)
    w, h = 1.35, 2.2
    y0 = 1.4

    for i, (x, name) in enumerate(zip(xs, stages)):
        rect = Rectangle((x, y0), w, h, fc="white", ec="black", lw=1.0)
        ax.add_patch(rect)
        # Distributor line at bottom
        ax.plot([x + 0.05, x + w - 0.05], [y0 + 0.15, y0 + 0.15], "k-", lw=0.8)
        # Bed zone
        ax.add_patch(Rectangle((x + 0.08, y0 + 0.2), w - 0.16, h - 0.45,
                               fill=False, ec="black", lw=0.5, ls=":"))
        ax.text(x + w / 2, y0 + h / 2, name, ha="center", va="center", fontsize=8)
        # Gas up arrows (208)
        gx = x + w / 2
        ax.annotate("", xy=(gx, y0 + h - 0.25), xytext=(gx, y0 + 0.25),
                    arrowprops=dict(arrowstyle="->", color="black", lw=0.6))
        if i == 2:
            ax.text(gx + 0.15, y0 + h / 2, "208", fontsize=8, fontweight="bold")

        # Inter-stage weir (214)
        if i < 4:
            wx = x + w
            ax.plot([wx, wx + 0.15], [y0 + h * 0.65, y0 + h * 0.65], "k-", lw=0.9)

    # Regolith flow (210) — left to right (cold → hot)
    ry = y0 - 0.35
    ax.annotate(
        "", xy=(8.8, ry), xytext=(1.0, ry),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.4,
                        connectionstyle="arc3,rad=0"),
    )
    ax.text(5, ry - 0.25, "210  Regolith feed → discharge (counter-current)", ha="center", fontsize=9)
    ax.text(1.0, ry + 0.15, "Feed", fontsize=7)
    ax.text(8.5, ry + 0.15, "Discharge", fontsize=7)

    # Iron / heat media (212) — right to left
    iy = y0 + h + 0.45
    ax.annotate(
        "", xy=(1.2, iy), xytext=(8.5, iy),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.4, ls="--"),
    )
    ax.text(5, iy + 0.25, "212  Iron shot / heat media (counter-current)", ha="center", fontsize=9)

    # Process gas circuit (206)
    ax.annotate(
        "", xy=(0.5, 3.8), xytext=(0.5, 0.6),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0),
    )
    ax.text(0.35, 2.2, "206\nGas\ncirc.", ha="center", fontsize=7, rotation=90)
    ax.annotate(
        "", xy=(9.5, 0.6), xytext=(9.5, 3.8),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0),
    )

    # Rung 4 evidence callout
    ax.add_patch(Rectangle((6.8, 0.15), 2.9, 0.85, fill=False, ec="black", lw=0.8))
    ax.text(8.25, 0.58,
            "Rung 4 GPU DEM:\n~230 particles transferred\nacross stage boundaries",
            ha="center", va="center", fontsize=7)

    # System envelope (204)
    ax.add_patch(Rectangle((0.55, 0.35), 9.0, 4.0, fill=False, ec="black", lw=1.2, ls="-."))
    label_num(ax, (0.55, 4.2), 204, offset=(-0.15, 0), ha="left")
    label_num(ax, (5, 0.9), 210, offset=(0, -0.35))
    label_num(ax, (5, 3.5), 212, offset=(0, 0.15))

    ax.set_title(
        "FIG. 4 — Counter-current material and gas flow in the five-stage system\n"
        "(regolith and iron/heat media in opposite directions; gas upward per stage)",
        fontsize=10, pad=10,
    )
    fig.tight_layout()
    return fig


def save(fig, stem):
    for ext in ("svg", "pdf"):
        out = OUT / f"{stem}.{ext}"
        fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=300 if ext == "pdf" else None)
        print("wrote", out)


def main():
    patent_style()
    save(fig02_stage_cross_section(), "FIG_02_stage_cross_section")
    plt.close()
    save(fig04_countercurrent(), "FIG_04_countercurrent_transfer")
    plt.close()


if __name__ == "__main__":
    main()