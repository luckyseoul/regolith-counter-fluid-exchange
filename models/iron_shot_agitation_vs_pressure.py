#!/usr/bin/env python3
"""
Iron Shot Agitation Effectiveness vs Pressure Study
Focused on cold stages (most difficult for fluidization).

This explores parameter space that is already covered by the existing claims
(Claims 4, 11, 29, 30, etc. on metallic thermal mass particles 1-10mm, staged
deployment, and the tumbling action for sinter/agglomerate disruption).

Goal: Quantify how much low-pressure performance can be recovered simply by
optimizing iron shot size distribution and fill fraction in the early stages,
within the ranges already described in Rev 5.2.

No new subject matter. Pure optimization and sensitivity within the provisional.
"""

import numpy as np
from pathlib import Path

# --- Anchored to Rev 5.2 ---
RHO_REG = 3100.0
RHO_IRON = 7870.0
G = 1.625
CP = 800.0

def effective_agitation(shot_diameter_mm, fill_frac, velocity_multiple):
    """
    Simple model of how effectively iron shot breaks cohesive agglomerates.
    Larger or faster-moving shot = more impact energy.
    Higher fill fraction = more collisions per unit time.
    """
    # Kinetic energy per collision scales with d^3 * v^2
    # Collision frequency scales with fill_frac and velocity
    impact_energy = (shot_diameter_mm / 3.0)**3 * (velocity_multiple / 4.0)**2
    collision_rate = fill_frac * (velocity_multiple / 4.0)
    return min(0.95, 0.3 * impact_energy * collision_rate)

def cold_stage_performance(P_bar, shot_d_mm=3.0, iron_fill=0.25, vel_mult=4.0, eds=0.9, preclass_um=35):
    """
    Simplified cold-stage (light gas + incoming fines) performance.
    Returns estimated stage effectiveness and effective cohesion.
    """
    # Gas at cold end (~400-500K, relatively light)
    mw = 8.0
    rho = P_bar * 1e5 * (mw / 1000.0) / (8.314 * 450)
    mu = 2.1e-5 * (450/600)**0.7

    # Target coarse fraction Umf
    dp = 200e-6
    Ar = (dp**3 * rho * (RHO_REG - rho) * G) / (mu**2)
    Remf = np.sqrt(33.7**2 + 0.0408 * Ar) - 33.7
    Umf = Remf * mu / (dp * rho)
    U = vel_mult * Umf

    # Base cohesion (higher at low P)
    base_coh = 1.0 / (P_bar / 0.1)**0.55

    # Agitation reduction from iron shot
    agitation = effective_agitation(shot_d_mm, iron_fill, vel_mult)
    coh_after_iron = base_coh * (1 - 0.80 * agitation)

    # EDS reduction
    coh = coh_after_iron * (1 - 0.70 * eds)

    # Entrainment / trouble from fines
    entrain = min(0.92, 0.20 + 2.6 * (0.2 / P_bar) * coh * (preclass_um / 40.0))

    # Stage effectiveness (cold stage is harder)
    eff = 0.78 * (1 - 0.45 * coh) / (1 + 1.1 * entrain)

    return eff, coh, entrain, agitation, U * 1000

def run_study():
    pressures = np.array([0.08, 0.10, 0.12, 0.15, 0.20])

    # Sweep iron shot parameters within spec ranges (1-5mm typical, up to 10mm allowed)
    shot_sizes = [1.5, 2.5, 3.5, 5.0]   # mm
    fills = [0.15, 0.25, 0.35]

    results = []

    for P in pressures:
        for d in shot_sizes:
            for f in fills:
                eff, coh, entr, agit, U = cold_stage_performance(
                    P, shot_d_mm=d, iron_fill=f, vel_mult=4.5, eds=0.92, preclass_um=30
                )
                results.append({
                    'P_bar': P,
                    'shot_mm': d,
                    'fill': f,
                    'agitation': agit,
                    'cold_eff': eff,
                    'entrain': entr,
                    'coh': coh,
                    'U_mm_s': U
                })

    return results

if __name__ == "__main__":
    data = run_study()

    print("Cold-stage effectiveness vs iron shot parameters (within existing claims)")
    print("P(bar) | Shot(mm) | Fill | Agit | Cold Eff | Entrain | U(mm/s)")
    print("-" * 80)
    for r in data:
        if r['P_bar'] in [0.10, 0.12, 0.15]:
            print(f"{r['P_bar']:.2f}   | {r['shot_mm']:4.1f}    | {r['fill']:.2f} | {r['agitation']:.2f} | "
                  f"{r['cold_eff']:.2f}    | {r['entrain']:.2f}   | {r['U_mm_s']:.1f}")

    out = Path("/home/nick/rcfx/analysis/iron_agitation_pressure_sweep.npy")
    np.save(out, data)
    print(f"\nSaved to {out}")
    print("This is optimization within the existing provisional claims (iron thermal mass + tumbling action).")