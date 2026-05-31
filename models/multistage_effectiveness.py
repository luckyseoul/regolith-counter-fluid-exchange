#!/usr/bin/env python3
"""
5-Stage Counter-Flow Effectiveness Model (low-fidelity but anchored)
Uses the exact stage count, temperature steps, gas evolution, and mitigation effects from Rev 5.2.

This is the core model for the Rung campaign.
"""

import numpy as np
from pathlib import Path

# From spec
STAGE_TEMPS = [200, 340, 480, 620, 760, 900]   # inlet + 5 stages (hot spent enters at ~900 K after pre-cool)
G = 1.625
RHO_REG = 3100.0
CP = 800.0

def gas_mw_at_temp(T):
    """Three-tier desorption from spec 4.3"""
    if T < 600:
        return 7.5   # light
    elif T < 900:
        return 8.5
    else:
        return 20.0  # CO/CO2 rich — important

def stage(U, P, T, iron_agitation=0.8, eds=0.9, preclass_um=40):
    """Effectiveness of one stage at given conditions + mitigation levels"""
    mw = gas_mw_at_temp(T)
    rho = P * 1e5 * (mw / 1000) / (8.314 * T)
    mu = 2.3e-5 * (T/600)**0.7

    # Base Umf for target fraction
    dp = 200e-6
    Ar = (dp**3 * rho * (RHO_REG - rho) * G) / (mu**2)
    Remf = np.sqrt(33.7**2 + 0.0408*Ar) - 33.7
    Umf = Remf * mu / (dp * rho)

    # Operating velocity (we can choose to run higher if needed)
    U_used = max(U, 3.5 * Umf)

    # Effective cohesion after all mitigations
    base_coh = 1.0 / (P / 0.1)**0.55
    coh = base_coh * (1 - 0.75*eds) * (1 - 0.82*iron_agitation)

    # Entrainment / loss of fines
    entrain = min(0.95, 0.25 + 2.8*(0.2/P)*coh * (40 / max(preclass_um, 15)))

    # Heat transfer factor
    htf = (rho / 0.018)**0.42 * (1 - 0.45*coh) * (1 + 0.22*iron_agitation) / (1 + 1.2*entrain)

    eff = 0.82 * htf / (1 + 0.9 * entrain**1.3)
    return np.clip(eff, 0.30, 0.94), U_used, coh, entrain, rho

def run_full_system(P_bar, iron=0.85, eds=0.92, preclass=38):
    """Run all 5 stages in counterflow with evolving gas."""
    overall_recovered = 0.0
    total_in = 100.0   # kg/hr reference
    stage_effs = []

    # Cold incoming regolith starts at 200 K
    # Hot spent comes in at ~900 K (after any pre-cool dump)

    for i in range(5):
        T = STAGE_TEMPS[i+1]
        eff, U, coh, entr, rho = stage(0.015, P_bar, T, iron, eds, preclass)
        stage_effs.append(eff)

        # Very rough recovered energy this stage (placeholder — will be refined)
        delta_T_this_stage = 140
        recovered_this_stage = total_in * CP * delta_T_this_stage * eff / 3600   # kW
        overall_recovered += recovered_this_stage

    # Overall effectiveness (total sensible recovered vs theoretical max from 200→900 K)
    theoretical_max = total_in * CP * 700 / 3600   # kW
    overall_eff = overall_recovered / theoretical_max

    return {
        'P': P_bar,
        'iron': iron,
        'eds': eds,
        'preclass': preclass,
        'stage_effs': stage_effs,
        'overall_eff': overall_eff,
        'overall_recovered_kW': overall_recovered
    }

if __name__ == "__main__":
    cases = []
    for P in [0.10, 0.12, 0.15, 0.18, 0.20]:
        res = run_full_system(P, iron=0.88, eds=0.93, preclass=35)
        cases.append(res)
        print(f"P={P:.2f} bar | Overall eff = {res['overall_eff']:.1%} | Recovered ~{res['overall_recovered_kW']:.1f} kW (ref 100 kg/hr)")

    np.save("/home/nick/rcfx/analysis/multistage_v1.npy", cases)
    print("\nSaved multistage_v1.npy")