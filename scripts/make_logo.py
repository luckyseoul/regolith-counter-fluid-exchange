#!/usr/bin/env python3
"""RCFX product mark: exactly five stages, closed envelope, counter-flow, parallel gas."""
from pathlib import Path

OUT_SVG = Path(__file__).resolve().parents[1] / "logo.svg"
W = H = 1024

# Stage 1 (cold) at TOP, Stage 5 (hot) at BOTTOM — same as FIG. 1
BED = [
    "#E7B56A",  # S1 cold
    "#E89A45",
    "#E07A32",
    "#D45A28",
    "#C43C22",  # S5 hot
]
BED_HI = [
    "#F3D39A",
    "#F0B56A",
    "#EE9350",
    "#E4723C",
    "#D35530",
]
IRON = "#8A9AAB"
REG = "#C4A574"


def svg() -> str:
    # vessel
    vx, vw = 300, 400
    shell_top, shell_bot = 118, 900
    n = 5
    gap = 10
    # beds live inside the straight wall, below/above the dishes
    top = shell_top + 52
    bot = shell_bot - 52
    usable = bot - top
    sh = (usable - gap * (n - 1)) / n

    parts = [
        f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1A2744"/>
      <stop offset="100%" stop-color="#121A2E"/>
    </linearGradient>
    <linearGradient id="shell" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#D7E4F4"/>
      <stop offset="45%" stop-color="#F4F8FC"/>
      <stop offset="100%" stop-color="#B7C8DC"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="18" flood-color="#000" flood-opacity="0.35"/>
    </filter>
  </defs>
  <rect width="{W}" height="{H}" rx="72" fill="url(#bg)"/>
'''
    ]

    # closed envelope: dish top + body + dish bottom (NO chimney / vent)
    body_top = shell_top + 40
    body_bot = shell_bot - 40
    cx = vx + vw / 2
    parts.append(f'''
  <g filter="url(#soft)">
    <path d="
      M {vx} {body_top}
      C {vx} {shell_top-8}, {vx+vw} {shell_top-8}, {vx+vw} {body_top}
      L {vx+vw} {body_bot}
      C {vx+vw} {shell_bot+8}, {vx} {shell_bot+8}, {vx} {body_bot}
      Z" fill="url(#shell)" stroke="#8EA3BC" stroke-width="5"/>
  </g>
  <path d="
    M {vx+16} {body_top+2}
    C {vx+16} {shell_top+22}, {vx+vw-16} {shell_top+22}, {vx+vw-16} {body_top+2}
    L {vx+vw-16} {body_bot-2}
    C {vx+vw-16} {shell_bot-22}, {vx+16} {shell_bot-22}, {vx+16} {body_bot-2}
    Z" fill="#152033" opacity="0.22"/>
''')

    # five stages
    particles = []
    for i in range(n):
        y0 = top + i * (sh + gap)
        y1 = y0 + sh
        # plenum + sintered distributor
        dist_y = y1 - 14
        bed_top = y0 + 10
        parts.append(f'''
  <!-- Stage {i+1} -->
  <rect x="{vx+22}" y="{bed_top}" width="{vw-44}" height="{dist_y-bed_top-2}" rx="10"
        fill="{BED[i]}"/>
  <path d="M {vx+22} {bed_top+8}
           C {cx-80} {bed_top-6}, {cx+90} {bed_top+18}, {vx+vw-22} {bed_top+6}
           L {vx+vw-22} {bed_top+22}
           C {cx+70} {bed_top+10}, {cx-60} {bed_top+2}, {vx+22} {bed_top+20} Z"
        fill="{BED_HI[i]}" opacity="0.85"/>
  <!-- sintered distributor -->
  <rect x="{vx+22}" y="{dist_y}" width="{vw-44}" height="10" fill="#2C3A52"/>
  <g stroke="#6E7F96" stroke-width="1.4">
''')
        for k in range(14):
            x = vx + 40 + k * ((vw - 80) / 13)
            parts.append(f'    <line x1="{x:.1f}" y1="{dist_y+1}" x2="{x:.1f}" y2="{dist_y+9}"/>\n')
        parts.append("  </g>\n")
        # overflow weir on right (regolith down)
        if i < n - 1:
            parts.append(
                f'  <rect x="{vx+vw-52}" y="{y1-6}" width="26" height="{gap+18}" rx="4" fill="#C5D4E8"/>\n'
            )
        # iron return port on left
        if i < n - 1:
            parts.append(
                f'  <rect x="{vx+26}" y="{y1-6}" width="22" height="{gap+18}" rx="4" fill="#A9B8C9"/>\n'
            )

        # particles: small regolith + larger iron
        rng_y = (bed_top + 18, dist_y - 8)
        # deterministic scatter
        seed = (i + 1) * 997
        for p in range(18):
            s = (seed * (p + 3) * 2654435761) & 0xFFFFFFFF
            px = vx + 50 + (s % int(vw - 100))
            py = rng_y[0] + ((s >> 8) % max(8, int(rng_y[1] - rng_y[0])))
            r = 3.2 + (s >> 16) % 3
            particles.append(
                f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{REG}" opacity="0.9"/>'
            )
        for p in range(7):
            s = (seed * (p + 11) * 2246822519) & 0xFFFFFFFF
            px = vx + 70 + (s % int(vw - 140))
            py = rng_y[0] + 8 + ((s >> 9) % max(8, int(rng_y[1] - rng_y[0] - 16)))
            particles.append(
                f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="7.5" fill="{IRON}" stroke="#D5DEE8" stroke-width="1.2"/>'
            )

    parts.append("\n".join(particles) + "\n")

    # parallel gas manifold to the RIGHT of the vessel (one header, five equal laterals)
    hx = vx + vw + 70
    y_first = top + sh - 18
    y_last = top + (n - 1) * (sh + gap) + sh - 18
    parts.append(f'''
  <line x1="{hx}" y1="{y_first}" x2="{hx}" y2="{y_last}"
        stroke="#7FB3D8" stroke-width="8" stroke-linecap="round"/>
''')
    for i in range(n):
        y0 = top + i * (sh + gap)
        gy = y0 + sh - 18
        parts.append(
            f'  <line x1="{vx+vw-16}" y1="{gy}" x2="{hx}" y2="{gy}" '
            f'stroke="#7FB3D8" stroke-width="5" stroke-linecap="round"/>\n'
            f'  <circle cx="{hx}" cy="{gy}" r="6" fill="#B9D7EE"/>\n'
        )
    # blower on the header, not a vent
    parts.append(f'''
  <rect x="{hx-22}" y="{y_last+16}" width="44" height="30" rx="7" fill="#7FB3D8"/>
  <circle cx="{hx}" cy="{y_last+31}" r="8" fill="#1A2744"/>
''')

    # counter-flow: iron/heat UP (left), regolith DOWN (far right of manifold)
    ax = vx - 48
    rx = hx + 36
    parts.append(f'''
  <path d="M {ax} {bot-20} L {ax} {top+20}" fill="none" stroke="#A8B8C8" stroke-width="6" stroke-linecap="round"/>
  <path d="M {ax-11} {top+42} L {ax} {top+16} L {ax+11} {top+42}" fill="none" stroke="#A8B8C8" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M {rx} {top+20} L {rx} {bot-20}" fill="none" stroke="#D4B48A" stroke-width="6" stroke-linecap="round"/>
  <path d="M {rx-11} {bot-44} L {rx} {bot-18} L {rx+11} {bot-44}" fill="none" stroke="#D4B48A" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
''')

    parts.append("</svg>\n")
    return "".join(parts)


def main():
    OUT_SVG.write_text(svg())
    print("wrote", OUT_SVG)


if __name__ == "__main__":
    main()
