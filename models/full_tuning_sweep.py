#!/usr/bin/env python3
"""
Full Tuning Sweep for RCFX Low-Pressure Optimization
Within existing claims only (Rev 5.2 parameters and features).

Tunes the following (all already enabled by Rev 5.2):
- Iron shot diameter (1-5 mm range, staged)
- Iron fill fraction in cold stages
- Superficial velocity multiple (3x-6x Umf, independent per stage group)
- EDS effectiveness (0.5-0.98)
- Pre-classification cutoff (20-55 µm)

Goal: Find the lowest pressure at which we can still hit ~70%+ overall effectiveness
with reasonable parasitic power, using only existing architecture + tuning.

This is the core "tune everything" run for the patent math.
"""

import numpy as np
from pathlib import Path
from itertools import product

# =============================================================================
# ANCHORED PHYSICS (Rev 5.2)
# =============================================================================
RHO_REG = 3100.0
CP = 800.0
G = 1.625
AREA = 0.1  # m2 per stage

def gas_props(P_bar, T, co2_co_level=0.0):
    """co2_co_level 0=light early, 1=heavy hot-end"""
    mw = 7.0 + 16.0 * co2_co_level
    rho = P_bar * 1e5 * (mw / 1000.0) / (8.314 * T)
    mu = 2.3e-5 * (T / 600)**0.7 * (mw / 10)**0.25
    return rho, mu, mw

def wen_yu_umf(dp, rho_g, mu_g):
    Ar = (dp**3 * rho_g * (RHO_REG - rho_g) * G) / (mu_g**2)
    Remf = np.sqrt(33.7**2 + 0.0408 * Ar) - 33.7
    return Remf * mu_g / (dp * rho_g)

def stage_effectiveness(P_bar, T, iron_d_mm, iron_fill, vel_mult, eds_eff, preclass_um, co2_co_level):
    rho, mu, _ = gas_props(P_bar, T, co2_co_level)

    dp_target = 200e-6
    Umf = wen_yu_umf(dp_target, rho, mu)
    U = vel_mult * Umf

    # Effective cohesion after iron + EDS
    base_coh = 1.0 / (P_bar / 0.1)**0.52
    agitation = min(0.92, (iron_d_mm / 3.0)**2.2 * (iron_fill / 0.25) * (vel_mult / 4.0)**1.3)
    coh = base_coh * (1 - 0.82 * agitation) * (1 - 0.72 * eds_eff)

    # Entrainment / loss
    entrain = min(0.96, 0.18 + 2.9 * (0.2 / P_bar) * coh * (preclass_um / 38.0))

    # Heat transfer factor (density + reduced cohesion + agitation help)
    htf = (rho / 0.018)**0.38 * (1 - 0.48 * coh) * (1 + 0.20 * agitation)

    eff = 0.80 * htf / (1 + 1.05 * entrain**1.4)
    return np.clip(eff, 0.28, 0.94), U, coh, entrain

def run_full_tune():
    pressures = np.array([0.08, 0.10, 0.12, 0.15, 0.18, 0.22])

    # Tunable ranges (within claims)
    iron_diams = [1.5, 2.5, 3.5, 5.0]          # mm
    iron_fills = [0.18, 0.28, 0.38]
    vel_mults = [3.5, 4.5, 5.5]
    eds_levels = [0.75, 0.88, 0.96]
    preclass_cuts = [28, 38, 48]               # µm

    best_results = []

    for P in pressures:
        best_eff = 0.0
        best_combo = None

        for iron_d, iron_f, vmult, eds, pre in product(iron_diams, iron_fills, vel_mults, eds_levels, preclass_cuts):
            # Cold stages (1-2) — binding
            eff1, _, _, _ = stage_effectiveness(P, 420, iron_d, iron_f, vmult, eds, pre, co2_co_level=0.08)
            eff2, _, _, _ = stage_effectiveness(P, 560, iron_d, iron_f, vmult, eds, pre, co2_co_level=0.18)

            # Hot stages (3-5) — easier due to heavier gas + hotter
            eff3, _, _, _ = stage_effectiveness(P, 700, iron_d, max(0.12, iron_f-0.08), vmult-0.5, eds, pre, co2_co_level=0.45)
            eff4, _, _, _ = stage_effectiveness(P, 820, iron_d, max(0.10, iron_f-0.12), vmult-0.8, eds, pre, co2_co_level=0.65)
            eff5, _, _, _ = stage_effectiveness(P, 880, iron_d, max(0.08, iron_f-0.15), vmult-1.0, eds, pre, co2_co_level=0.82)

            overall = 0.12*eff1 + 0.18*eff2 + 0.25*eff3 + 0.28*eff4 + 0.17*eff5

            if overall > best_eff:
                best_eff = overall
                best_combo = (iron_d, iron_f, vmult, eds, pre)

        best_results.append({
            'P_bar': P,
            'best_overall_eff': best_eff,
            'best_iron_mm': best_combo[0],
            'best_iron_fill': best_combo[1],
            'best_vel_mult_cold': best_combo[2],
            'best_eds': best_combo[3],
            'best_preclass_um': best_combo[4]
        })

    return best_results

if __name__ == "__main__":
    results = run_full_tune()

    print("Best achievable overall effectiveness vs pressure (tuned within existing claims)")
    print("P(bar) | Max Eff | Best Iron(mm) | Fill | VelMult(cold) | EDS  | Pre(um)")
    print("-" * 95)
    for r in results:
        print(f"{r['P_bar']:.2f}   | {r['best_overall_eff']:.1%}  | {r['best_iron_mm']:4.1f}         | {r['best_iron_fill']:.2f} | "
              f"{r['best_vel_mult_cold']:.1f}          | {r['best_eds']:.2f} | {r['best_preclass_um']:2d}")

    out = Path(__file__).resolve().parents[1] / "analysis" / "full_tuning_sweep_v1.npy"
    np.save(out, results)
    print(f"\nSaved to {out}")
    print("This is systematic tuning of existing architecture parameters only.")