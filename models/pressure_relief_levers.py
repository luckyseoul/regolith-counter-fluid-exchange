#!/usr/bin/env python3
"""
RCFX Pressure Relief Levers Analysis
Goal: Quantify how low we can push envelope pressure while still achieving acceptable performance,
by varying the three main mitigations the spec already provides:

1. Iron shot agitation strength (tumbling/collision energy that breaks cohesive agglomerates)
2. EDS charge dissipation effectiveness (reduces electrostatic component of cohesion)
3. Pre-classification cutoff (how aggressively we remove Geldart C fines upstream)

This is the core of "make it work off-world at low mbar without high-pressure vessel overhead".

All numbers anchored to Rev 5.2.
"""

import numpy as np
from pathlib import Path

# --- Core constants from spec ---
RHO_REG = 3100.0
G = 1.625
AREA = 0.1
L_BED = 0.3
EPS = 0.55
D_TARGET = 200e-6

# Rough calibration point from spec at 0.2 bar He-dominant
REF_RHO = 0.02
REF_UMF_TARGET = 0.006   # m/s for 200µm
REF_VEL = 0.018          # m/s operating

def gas_props(P_bar, T, co2_co_frac=0.0):
    """Simple MW scaling. co2_co_frac = 0 (light) to 1 (hot-end heavy)"""
    mw = 6.0 + 18.0 * co2_co_frac   # 6 (light) to ~24 (CO/CO2 rich)
    rho = P_bar * 1e5 * (mw / 1000.0) / (8.314 * T)
    mu = 2.2e-5 * (T/600)**0.65 * (mw/10)**0.25
    return rho, mu, mw

def base_umf(P_bar, T, co2_co_frac):
    rho, mu, _ = gas_props(P_bar, T, co2_co_frac)
    # Wen-Yu scaling from reference
    umf = REF_UMF_TARGET * (REF_RHO / rho)**0.5 * (mu / 2.5e-5)**0.8
    return umf

def effective_cohesion(P_bar, eds_effectiveness, iron_agitation):
    """
    Effective cohesion force on fines (arbitrary units, higher = worse).
    - Higher pressure helps via more ion discharge (even without EDS).
    - EDS adds controllable dissipation.
    - Iron shot agitation mechanically breaks agglomerates (very powerful per spec).
    """
    base = 1.0 / (P_bar / 0.1)**0.6          # pressure helps ionization
    base *= (1 - 0.7 * eds_effectiveness)    # EDS reduces electrostatic part
    base *= (1 - 0.85 * iron_agitation)      # iron shot is the hammer
    return max(0.05, base)

def entrainment(U, P_bar, cohesion, preclass_cutoff_um=40):
    """Fraction of problematic fines that get entrained or cause trouble."""
    # Higher cohesion + lower density → much higher effective entrainment/locking
    base_entrain = 0.3 + 2.5 * (0.2 / P_bar) * cohesion
    # Pre-classification removes the worst offenders
    preclass_benefit = max(0, (preclass_cutoff_um - 20) / 60.0)
    return min(0.98, base_entrain * (1 - 0.6 * preclass_benefit))

def stage_effectiveness(U, P_bar, cohesion, iron_agitation, preclass):
    """Very rough but directionally useful effectiveness for one stage."""
    htc = (P_bar / 0.2)**0.45 * (1 - 0.35 * cohesion) * (1 + 0.25 * iron_agitation)
    entr = entrainment(U, P_bar, cohesion, preclass)
    eff = 0.78 * htc / (1 + 0.8 * entr)   # entrainment hurts a lot
    return np.clip(eff, 0.35, 0.93)

def blower_power(P_bar, U, co2_co_frac):
    rho, mu, _ = gas_props(P_bar, 600, co2_co_frac)
    dp_dist = 6300 * (rho / REF_RHO) * (U / REF_VEL)**2
    dp_bed = 400 * (rho / REF_RHO) * (U / REF_VEL)**1.6
    dp = dp_dist + dp_bed
    vol = U * AREA * 5   # 5 stages in parallel
    return (vol * dp) / 0.60

# =============================================================================
# MAIN STUDY
# =============================================================================
def run_relief_study():
    pressures = np.array([0.08, 0.10, 0.12, 0.15, 0.20, 0.30])

    # Sweep the three real levers the architecture gives us
    iron_levels = [0.3, 0.6, 0.9]           # low / medium / high agitation
    eds_levels  = [0.4, 0.7, 0.95]          # low / good / excellent dissipation
    preclass    = [25, 40, 55]              # aggressive / moderate / none (cutoff in µm)

    results = []

    for P in pressures:
        for iron in iron_levels:
            for eds in eds_levels:
                for pre in preclass:
                    # Cold end is binding (lightest gas, first contact with fines)
                    rho_c, _, _ = gas_props(P, 450, 0.1)
                    U_c = 4.0 * base_umf(P, 450, 0.1)

                    coh_c = effective_cohesion(P, eds, iron)
                    eff_c = stage_effectiveness(U_c, P, coh_c, iron, pre)

                    # Hot end (heavier gas helps)
                    rho_h, _, _ = gas_props(P, 800, 0.6)
                    U_h = 4.0 * base_umf(P, 800, 0.6)
                    coh_h = effective_cohesion(P, eds, iron)
                    eff_h = stage_effectiveness(U_h, P, coh_h, iron, pre)

                    # Crude overall effectiveness (5 stages, weighted)
                    overall = 0.15*eff_c + 0.20*eff_c + 0.25*eff_h + 0.25*eff_h + 0.15*eff_h

                    power = blower_power(P, U_c, 0.3)   # conservative light gas power

                    results.append({
                        'P': P,
                        'iron': iron,
                        'eds': eds,
                        'preclass_um': pre,
                        'cold_eff': eff_c,
                        'hot_eff': eff_h,
                        'overall_eff': overall,
                        'blower_W': power,
                        'cohesion_cold': coh_c,
                    })

    return results

if __name__ == "__main__":
    data = run_relief_study()

    print("P(bar) | Iron | EDS  | Pre(µm) | ColdEff | HotEff | Overall | Blower(W) | CohCold")
    print("-" * 95)
    for r in data:
        if r['P'] in [0.10, 0.12, 0.15, 0.20]:
            print(f"{r['P']:.2f}  | {r['iron']:.1f}  | {r['eds']:.2f} | {r['preclass_um']:2d}    | "
                  f"{r['cold_eff']:.2f}   | {r['hot_eff']:.2f}  | {r['overall_eff']:.2f}   | "
                  f"{r['blower_W']:.0f}      | {r['cohesion_cold']:.2f}")

    outpath = Path(__file__).resolve().parents[1] / "analysis" / "pressure_relief_levers_v1.npy"
    np.save(outpath, data)
    print(f"\nSaved to {outpath}")
    print("This directly quantifies how much the existing mitigations buy us at low pressure.")