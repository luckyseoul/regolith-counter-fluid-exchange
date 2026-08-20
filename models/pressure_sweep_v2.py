#!/usr/bin/env python3
"""
RCFX Pressure & Gas Composition Sensitivity — v2
Improved model using detailed parameters and gas evolution from Rev 5.2.

Key additions:
- Three-tier volatile desorption profile (low-T H2O/H2, mid-T solar wind, high-T CO/CO2)
- Rough cohesion model for Geldart C fines
- Entrainment estimate
- First-order per-stage heat transfer / effectiveness sketch
"""

import numpy as np
from pathlib import Path

# =============================================================================
# SPEC-DERIVED CONSTANTS
# =============================================================================
RHO_REG = 3100.0          # kg/m3
CP_REG = 800.0            # J/kg/K
G = 1.625                 # lunar m/s2
SPH = 0.7

# Target coarse fraction for fluidization velocity (spec discussion)
D_TARGET = 200e-6         # m

# Bed geometry (per stage, pilot scale)
AREA = 0.1                # m2 (~0.36m diameter)
L_BED = 0.3               # m active bed height
EPS = 0.55                # expanded void fraction

# Distributor (dominant ΔP source at low density)
DIST_PORE = 25e-6
DIST_THICK = 4e-3
DIST_POROSITY = 0.30

# =============================================================================
# GAS EVOLUTION MODEL (from spec Section 4.3)
# =============================================================================
def gas_at_stage(stage_temp, P_bar):
    """
    Approximate local gas properties at a given stage temperature.
    Returns rho, mu, MW, name for reporting.
    Heavier gases (CO/CO2) dominate at hot end — big win for low-P fluidization.
    """
    T = stage_temp

    if T < 600:
        # Low-T: adsorbed H2O, H2, trace N2
        mw = 8.0   # light mix
        name = "light (H2/He/N2)"
    elif T < 900:
        # Mid: solar wind H/He release
        mw = 6.5
        name = "mid (H/He rich)"
    else:
        # High-T (Stages 4-5 + reactor): CO/CO2 + more H2O from decomposition/reduction
        mw = 22.0   # significantly heavier — key for low pressure
        name = "hot (CO/CO2 enriched)"

    R = 8.314462618
    rho = (P_bar * 1e5 * mw / 1000.0) / (R * T)

    # Viscosity scaling (very approximate)
    mu = 1.8e-5 * (T / 300)**0.7 * (mw / 20)**0.3   # rough

    return rho, mu, mw, name

# =============================================================================
# CORE MODELS
# =============================================================================
def wen_yu_umf(dp, rho_g, mu_g, g=G):
    Ar = (dp**3 * rho_g * (RHO_REG - rho_g) * g) / (mu_g**2)
    Remf = np.sqrt(33.7**2 + 0.0408 * Ar) - 33.7
    return Remf * mu_g / (dp * rho_g)

def ergun_bed_dp(U, dp, eps, L, rho_g, mu_g, g=G):
    term1 = 150 * mu_g * (1-eps)**2 * U / (eps**3 * dp**2)
    term2 = 1.75 * rho_g * (1-eps) * U**2 / (eps**3 * dp)
    return (term1 + term2) * L

def distributor_dp(U, rho_g, mu_g):
    # Ergun through the sintered plate (dominant term at low density)
    return ergun_bed_dp(U, DIST_PORE, DIST_POROSITY, DIST_THICK, rho_g, mu_g)

def approx_cohesion_force(dp_fine=30e-6, Hamaker=1e-19, charge_density=1e-6):
    """Very rough effective extra force on fines (van der Waals + residual electrostatic)."""
    # This is order-of-magnitude only. Real model would be much more sophisticated.
    F_vdw = Hamaker * dp_fine / (12 * 0.4e-9**2)   # at ~0.4 nm separation
    F_elec = (charge_density * np.pi * dp_fine**2)**2 / (4 * np.pi * 8.85e-12 * 1e-3)  # rough
    return F_vdw + 0.3 * F_elec   # pressure + EDS reduce the electrostatic part

def entrainment_fraction(U, dp_fines=30e-6, rho_g=0.03, mu_g=2.5e-5):
    """Crude estimate of % of fines that will be entrained."""
    Ut = (dp_fines**2 * (RHO_REG - rho_g) * 1.625) / (18 * mu_g) * 0.6  # sph corrected
    if U > Ut:
        return min(1.0, (U / Ut - 1.0) * 0.6 + 0.1)
    return 0.05

# =============================================================================
# MAIN SWEEP
# =============================================================================
def run_v2():
    pressures = np.array([0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.40])
    stages = [300, 500, 700, 850]   # representative stage temps

    rows = []

    for P in pressures:
        for T in stages:
            rho, mu, mw, gname = gas_at_stage(T, P)

            Umf = wen_yu_umf(D_TARGET, rho, mu)
            U = 4.0 * Umf   # operating point per spec guidance

            dp_bed = ergun_bed_dp(U, D_TARGET, EPS, L_BED, rho, mu)
            dp_dist = distributor_dp(U, rho, mu)
            dp_total = dp_bed + dp_dist

            # Blower power (5 stages in parallel)
            vol_flow_per_stage = U * AREA
            eta = 0.60
            power_per_stage = (vol_flow_per_stage * dp_total) / eta
            total_blower = 5 * power_per_stage

            # Fines behavior
            entrain = entrainment_fraction(U, 30e-6, rho, mu)
            Fcoh = approx_cohesion_force()

            # Extremely rough effectiveness sketch (higher density + better mixing helps)
            # This is placeholder — real model needs proper two-phase heat transfer
            htc_factor = (rho / 0.02) ** 0.4 * (1 - 0.4 * entrain)
            effectiveness_stage = min(0.92, 0.55 + 0.12 * np.log10(htc_factor + 0.1))

            rows.append({
                'P_bar': P,
                'T': T,
                'gas': gname,
                'rho': rho,
                'mw': mw,
                'Umf_mm/s': Umf * 1000,
                'U_mm/s': U * 1000,
                'dp_total_Pa': dp_total,
                'blower_total_W': total_blower,
                'entrain_frac': entrain,
                'eff_stage': effectiveness_stage,
                'cohesion_force_nN': Fcoh * 1e9,
            })

    return rows

if __name__ == "__main__":
    data = run_v2()

    print("P(bar) | T(K) | Gas                  | rho     | Umf(mm/s) | Blower(W) | Entrain | Eff")
    print("-" * 95)
    for r in data:
        print(f"{r['P_bar']:.2f}   | {r['T']:3d}  | {r['gas']:20s} | {r['rho']:.4f} | "
              f"{r['Umf_mm/s']:.2f}     | {r['blower_total_W']:.0f}      | "
              f"{r['entrain_frac']:.2f}    | {r['eff_stage']:.2f}")

    out = Path(__file__).resolve().parents[1] / "analysis" / "pressure_sweep_v2.npy"
    np.save(out, data)
    print(f"\nSaved to {out}")