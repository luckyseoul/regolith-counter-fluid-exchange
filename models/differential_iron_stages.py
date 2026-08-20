#!/usr/bin/env python3
"""
Differential Iron Shot Sizing Study (Cold vs Hot Stages)
Explores a very natural optimization already supported by the staged deployment
and metallic thermal mass language in the existing claims.

Cold stages: larger/more aggressive shot for maximum agglomerate breaking.
Hot stages: smaller or optimized shot for thermal mass + carburization.

This is pure tuning within Rev 5.2.
"""

import numpy as np
from pathlib import Path

# Use the same core functions as the previous studies for consistency
# (lightweight re-implementation for speed)

RHO_REG = 3100.0
G = 1.625

def gas_props(P_bar, T, co_level=0.0):
    mw = 7.5 + 15.0 * co_level
    rho = P_bar * 1e5 * (mw / 1000) / (8.314 * T)
    mu = 2.25e-5 * (T/600)**0.7
    return rho, mu

def stage_eff(P, T, iron_cold_mm, iron_hot_mm, fill_cold, fill_hot, v_cold, v_hot, eds, pre):
    # Cold stage representative
    rho_c, mu_c = gas_props(P, 480, 0.12)
    dp = 200e-6
    Ar = (dp**3 * rho_c * (RHO_REG - rho_c) * G) / (mu_c**2)
    Umf_c = (np.sqrt(33.7**2 + 0.0408*Ar) - 33.7) * mu_c / (dp * rho_c)
    U_c = v_cold * Umf_c

    coh_base = 1.0 / (P / 0.1)**0.52
    agit_c = min(0.92, (iron_cold_mm/3.0)**2.1 * (fill_cold/0.25) * (v_cold/4.0)**1.2)
    coh_c = coh_base * (1 - 0.81*agit_c) * (1 - 0.71*eds)
    entr_c = min(0.94, 0.22 + 2.7*(0.2/P)*coh_c*(pre/38))
    htf_c = (rho_c/0.018)**0.37 * (1-0.47*coh_c) * (1+0.19*agit_c)
    eff_c = 0.79 * htf_c / (1 + 1.05*entr_c**1.35)

    # Hot stage representative
    rho_h, mu_h = gas_props(P, 820, 0.65)
    Umf_h = (np.sqrt(33.7**2 + 0.0408*Ar) - 33.7) * mu_h / (dp * rho_h)
    U_h = v_hot * Umf_h

    agit_h = min(0.90, (iron_hot_mm/3.0)**2.0 * (fill_hot/0.22) * (v_hot/4.0)**1.1)
    coh_h = coh_base * (1 - 0.80*agit_h) * (1 - 0.71*eds)   # lower base at hot end anyway
    entr_h = min(0.90, 0.15 + 2.2*(0.2/P)*coh_h*(pre/38))
    htf_h = (rho_h/0.018)**0.40 * (1-0.42*coh_h) * (1+0.17*agit_h)
    eff_h = 0.82 * htf_h / (1 + 0.95*entr_h**1.3)

    # Weighted overall (cold stages matter a lot for fines)
    overall = 0.22*eff_c + 0.20*eff_c + 0.20*eff_h + 0.20*eff_h + 0.18*eff_h
    return overall, eff_c, eff_h

def run_diff_study():
    pressures = [0.09, 0.10, 0.11, 0.12, 0.14, 0.16]
    results = []

    for P in pressures:
        best = 0.0
        best_params = None

        # Cold stages want aggressive shot
        for cold_d in [3.0, 3.5, 4.0, 5.0]:
            for hot_d in [1.5, 2.0, 2.5, 3.0]:   # can be smaller in hot stages
                for fill_c in [0.30, 0.38]:
                    for fill_h in [0.18, 0.25]:
                        for v_c in [4.5, 5.5]:
                            for v_h in [3.5, 4.5]:
                                eff, ec, eh = stage_eff(P, 480, cold_d, hot_d, fill_c, fill_h, v_c, v_h, 0.94, 30)
                                if eff > best:
                                    best = eff
                                    best_params = (cold_d, hot_d, fill_c, fill_h, v_c, v_h)

        results.append({
            'P': P,
            'best_eff': best,
            'cold_shot': best_params[0],
            'hot_shot': best_params[1],
            'fill_c': best_params[2],
            'fill_h': best_params[3],
            'v_cold': best_params[4],
            'v_hot': best_params[5]
        })

    return results

if __name__ == "__main__":
    data = run_diff_study()

    print("Effect of differential iron shot sizing (cold vs hot stages)")
    print("P(bar) | Overall | Cold Shot | Hot Shot | Fill C/H | Vel C/H")
    print("-" * 75)
    for r in data:
        print(f"{r['P']:.2f}   | {r['best_eff']:.1%} | {r['cold_shot']:.1f}mm    | {r['hot_shot']:.1f}mm    | "
              f"{r['fill_c']:.2f}/{r['fill_h']:.2f}  | {r['v_cold']:.1f}/{r['v_hot']:.1f}")

    np.save(Path(__file__).resolve().parents[1] / "analysis" / "differential_iron_v1.npy", data)
    print("\nSaved. This is still fully within the staged iron deployment and thermal mass claims.")