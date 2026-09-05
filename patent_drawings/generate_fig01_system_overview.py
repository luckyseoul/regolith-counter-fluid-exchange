#!/usr/bin/env python3
"""Readable FIG. 1 architecture from Rev 5.2 §§4.1, 4.5–4.6, 5.7.

Source: docs/RCFX_Complete_Specification_Rev52.pdf, PDF pages 7–8, 11–12, 17.
Cold regolith passes 1→5; hot spent regolith passes 5→1. Iron shot remains
stage thermal mass. Gas branches run in parallel between supply and return.
The lower panel repeats stage symbols to show the gas circuit separately; it
is not a second bank of beds. Stream-separation/transfer hardware is not drawn.
Later bundle text describing an iron return stream is a different arrangement.
"""
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "patent_drawings"
BUNDLE = ROOT / "patent_application/2026-06-05/patent_drawings"
STEM = "FIG_01_system_overview"
STAGE_X = [4, 6, 8, 10, 12]
BLUE = "#2475BA"
ORANGE = "#D76A32"
TEAL = "#287E79"
INK = "#24364B"
MUTED = "#5D7081"
BORDER = "#D7E1E9"


def arrow(ax, start, end, *, color, width=2.3, scale=13, gid=None):
    patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=scale,
                            linewidth=width, color=color, shrinkA=0, shrinkB=0,
                            zorder=5)
    patch.set_gid(gid)
    ax.add_patch(patch)
    return patch


def card(ax, xy, width, height, *, fill="white", edge=BORDER, radius=0.14, gid=None):
    patch = FancyBboxPatch(xy, width, height,
                           boxstyle=f"round,pad=0,rounding_size={radius}",
                           facecolor=fill, edgecolor=edge, lw=0.9, zorder=2)
    patch.set_gid(gid)
    ax.add_patch(patch)
    return patch


def build_figure():
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11,
                         "text.color": INK}):
        fig, ax = plt.subplots(figsize=(13.8, 8.4))
        fig.subplots_adjust(left=0.025, right=0.975, bottom=0.025, top=0.98)
        ax.set(xlim=(0, 16), ylim=(0, 10.6))
        ax.axis("off")
        ax.text(0.45, 10.05, "RCFX  /  FIVE-STAGE HEAT RECOVERY", fontsize=18,
                weight="bold", va="center")
        ax.text(0.45, 9.60, "Incoming regolith warms as spent regolith cools on its return.",
                fontsize=12, color=MUTED)

        # Quiet common envelope with five easily readable stage cards.
        card(ax, (2.78, 5.16), 10.44, 3.78, fill="#F4F7FA", edge="#E4EBF0", radius=0.22)
        ax.text(8, 8.64, "PRESSURIZED ENVELOPE", ha="center", fontsize=9, color=MUTED)
        ax.text(4, 8.18, "COLD END", ha="center", fontsize=9, color=BLUE, weight="bold")
        ax.text(12, 8.18, "HOT END", ha="center", fontsize=9, color=ORANGE, weight="bold")
        for i, x in enumerate(STAGE_X, 1):
            card(ax, (x - 0.82, 5.44), 1.64, 2.44, gid=f"stage-{i}")
            ax.text(x, 7.53, f"Stage {i}", ha="center", fontsize=13, weight="bold")
            # Two streams pass through each stage; only interstage paths have arrowheads.
            ax.plot([x - 0.82, x + 0.82], [7.04, 7.04], color=BLUE, lw=2.7,
                    zorder=4, gid=f"cold-stage-{i}")
            ax.plot([x - 0.82, x + 0.82], [6.25, 6.25], color=ORANGE, lw=2.7,
                    zorder=4, gid=f"hot-stage-{i}")
            # Iron dots and a distributor mark, explained once underneath.
            for dx in (-0.28, 0, 0.28):
                ax.add_patch(Circle((x + dx, 5.77), 0.055, facecolor="#7D8D9D",
                                    edgecolor="none", zorder=4))
            ax.plot([x - 0.51, x + 0.51], [5.58, 5.58], color="#A9BAC6", lw=2,
                    zorder=4)
        ports = [(x - 0.82, x + 0.82) for x in STAGE_X]
        starts = [0.52] + [right for _left, right in ports]
        ends = [left for left, _right in ports] + [15.48]
        for i, (start, end) in enumerate(zip(starts, ends)):
            arrow(ax, (start, 7.04), (end, 7.04), color=BLUE, gid=f"cold-transfer-{i}")
            arrow(ax, (end, 6.25), (start, 6.25), color=ORANGE, gid=f"hot-transfer-{i}")

        # Endpoint descriptions stay entirely outside the envelope.
        ax.text(0.52, 8.04, "COLD FEED", fontsize=10, color=BLUE, weight="bold")
        ax.text(0.52, 7.56, "200 K", fontsize=20, color=BLUE, weight="bold")
        ax.text(15.48, 8.04, "HEATED FEED", ha="right", fontsize=10, color=BLUE, weight="bold")
        ax.text(15.48, 7.56, "to reactor", ha="right", fontsize=13)
        ax.text(0.52, 5.79, "COOLED SPENT", fontsize=10, color=ORANGE, weight="bold")
        ax.text(0.52, 5.39, "regolith", fontsize=12)
        ax.text(15.48, 5.79, "HOT SPENT", ha="right", fontsize=10, color=ORANGE, weight="bold")
        ax.text(15.48, 5.30, "900 K", ha="right", fontsize=20, color=ORANGE, weight="bold")
        ax.text(8, 4.86, "Each stage: iron shot thermal mass  ·  gas distributor  ·  EDS wall electrodes",
                ha="center", fontsize=11, color=MUTED)

        # Show the same five stages again as parallel gas branches. Keeping this
        # circuit in its own panel avoids crossing either solids path.
        card(ax, (0.45, 0.92), 15.10, 3.43, fill="#F1F8F6", edge="#E0EEEA", radius=0.22)
        ax.text(0.78, 3.91, "GAS CIRCULATION", color=TEAL, fontsize=11, weight="bold")
        ax.text(0.78, 3.54, "The same five stages, connected in parallel", color=MUTED, fontsize=10)
        # Return collects from each bed; supply feeds each bed independently.
        ax.plot([4, 14.44], [3.05, 3.05], color=TEAL, lw=1.5, zorder=3)
        ax.plot([4, 14.44], [1.36, 1.36], color=TEAL, lw=1.5, zorder=3)
        ax.text(0.78, 3.05, "Gas return", va="center", fontsize=11, color=TEAL)
        ax.text(0.78, 1.36, "Gas supply", va="center", fontsize=11, color=TEAL)
        for i, x in enumerate(STAGE_X, 1):
            card(ax, (x - 0.57, 1.98), 1.14, 0.50, fill="white", edge="#B7D5CF", radius=0.10,
                 gid=f"gas-branch-stage-{i}")
            ax.text(x, 2.23, f"Stage {i}", ha="center", va="center", fontsize=10, color=TEAL)
            arrow(ax, (x, 1.36), (x, 1.96), color=TEAL, width=1.3, scale=10,
                  gid=f"gas-supply-stage-{i}")
            arrow(ax, (x, 2.50), (x, 3.05), color=TEAL, width=1.3, scale=10,
                  gid=f"gas-return-stage-{i}")
        arrow(ax, (12.70, 3.05), (14.44, 3.05), color=TEAL, width=1.5, scale=11)
        arrow(ax, (13.50, 1.36), (12.70, 1.36), color=TEAL, width=1.5, scale=11)
        # Equipment follows the loop: return → fines capture → blower → supply.
        ax.plot([14.44, 14.44], [3.05, 2.79], color=TEAL, lw=1.5, zorder=3)
        card(ax, (13.50, 1.63), 1.88, 1.16, fill="white", edge="#B7D5CF", radius=0.12)
        ax.text(14.44, 2.55, "Fines capture", ha="center", fontsize=9, color=TEAL)
        arrow(ax, (14.44, 2.43), (14.44, 2.23), color=TEAL, width=1.1, scale=9)
        ax.text(14.44, 2.05, "Blower", ha="center", fontsize=11, color=TEAL, weight="bold")
        ax.text(14.44, 1.80, "+ standby backup", ha="center", fontsize=8.5, color=MUTED)
        ax.plot([14.44, 14.44], [1.63, 1.36], color=TEAL, lw=1.5, zorder=3)

        ax.text(0.45, 0.45, "FIG. 1  ·  Rev 5.2 architecture  ·  Conceptual flow paths; transfer hardware not shown",
                fontsize=9, color=MUTED)
        ax.text(15.55, 0.45, "Not to scale", ha="right", fontsize=9, color=MUTED)
        return fig


def main():
    fig = build_figure()
    with plt.rc_context({"svg.fonttype": "none", "svg.hashsalt": "rcfx-system-overview-v3"}):
        for extension, metadata in [("svg", {"Date": None}),
                                    ("pdf", {"CreationDate": None, "ModDate": None})]:
            path = OUT / f"{STEM}.{extension}"
            fig.savefig(path, bbox_inches="tight", facecolor="white", metadata=metadata)
            shutil.copyfile(path, BUNDLE / path.name)
            print("wrote and synchronized", path.name)
    plt.close(fig)


if __name__ == "__main__":
    main()
