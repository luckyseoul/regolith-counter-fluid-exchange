#!/usr/bin/env python3
"""
Cold-Stage Focused Optimizer
Goal: Maximize cold-stage effectiveness at low pressure (0.10-0.12 bar)
using only parameters within the existing claims.

This is the binding constraint for overall system performance.
"""

import numpy as np
from itertools import product

# Use the improved stage function from five_stage_counterflow
# (lightweight copy for standalone running)

RHO_REG = 3100.0
G = 1.625

def gas_props(P_bar, T, co_level=0.0):
    mw = 7.8 + 11.2 * co_level
    rho = P_bar * 1e5 * (mw / 1000.0) / (8.314 * T)
    mu = 2.25e-5 * (T/600)**0.68
    return rho, mu

def stage_cold(U, rho, mu, iron_d_mm, iron_fill, eds, pre_um):
    dp = 200e-6
    Ar = (dp**3 * rho * (RHO_REG - rho) * G) / (mu**2)
    Remf = np.sqrt(33.7**2 + 0.0408*Ar) - 33.7
    Umf = Remf * mu / (dp * rho)

    agitation = min(0.94, (iron_d_mm/3.2)**2.2 * (iron_fill/0.25) * (U/Umf / 4.0)**1.2)
    coh = (1.15 / (P/0.1)**0.53) * (1 - 0.82*agitation) * (1 - 0.73*eds)

    entr = min(0.94, 0.21 + 2.8*(0.2/P)*coh * (pre_um/35))

    htf = (rho/0.017)**0.38 * (1 - 0.48*coh) * (1 + 0.19*agitation)
    eff = 0.80 * htf / (1 + 1.08 * entr**1.4)
    return eff

def optimize_cold_stage(P_bar):
    best_eff = 0.0
    best_params = None

    # Search space (within claims)
    iron_sizes = [2.5, 3.0, 3.5, 4.0, 5.0]
    fills = [0.25, 0.30, 0.35, 0.40]
    vels = [4.0, 4.5, 5.0, 5.5, 6.0]
    eds = [0.88, 0.93, 0.97]
    pres = [25, 30, 35]

    for iron, fill, v, e, pr in product(iron_sizes, fills, vels, eds, pres):
        rho, mu = gas_props(P_bar, 480, 0.10)
        eff = stage_cold(v * 0.015, rho, mu, iron, fill, e, pr)
        if eff > best_eff:
            best_eff = eff
            best_params = (iron, fill, v, e, pr)

    return best_eff, best_params

if __name__ == "__main__":
    for P in [0.10, 0.11, 0.12, 0.15]:
        eff, params = optimize_cold_stage(P)
        print(f"P={P:.2f} bar → Cold stage eff = {eff:.1%} with "
              f"iron={params[0]}mm, fill={params[1]}, vel={params[2]}x, eds={params[3]}, pre={params[4]}um")