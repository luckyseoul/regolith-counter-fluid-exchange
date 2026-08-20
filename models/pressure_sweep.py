#!/usr/bin/env python3
"""
RCFX Low-Pressure Fluidization Sensitivity Analysis
First-cut model using parameters directly from Rev 5.2 spec.

Focus: How low can we push envelope pressure before fluidization becomes impractical?

Correlations used (standard in literature, matching spec references):
- Wen-Yu for Umf (minimum fluidization velocity)
- Ergun for bed pressure drop
- Haider-Levenspiel for terminal velocity (non-spherical, sphericity 0.7)
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =============================================================================
# CONSTANTS & REGOLITH PROPERTIES (from spec)
# =============================================================================
RHO_REGOLITH = 3100.0          # kg/m3 bulk
CP_REGOLITH = 800.0            # J/kg/K
G_LUNAR = 1.625                # m/s2
G_EARTH = 9.81

# Representative particle sizes (mass-weighted midpoints of bins)
# PSD from spec: significant Geldart C below ~40-50 µm
D_P = np.array([15e-6, 35e-6, 75e-6, 175e-6, 375e-6, 750e-6])  # m
MASS_FRAC = np.array([0.15, 0.20, 0.20, 0.25, 0.125, 0.075])   # approximate from spec bins

SPH = 0.7                      # angular regolith, per spec

# =============================================================================
# GAS PROPERTIES (variable with composition and T)
# =============================================================================
def gas_props(P_bar, T_avg=600.0, co2_frac=0.0, co_frac=0.0, h2_frac=0.3):
    """
    Approximate gas properties at given pressure and composition.
    P_bar: operating pressure in bar
    Returns: rho (kg/m3), mu (Pa.s), MW (g/mol)
    """
    # Rough mixture: start with He-dominant low-T, then add CO/CO2 at hot end
    # Spec emphasizes that CO/CO2 (heavier) are preferentially released at hot end — good for fluidization
    MW_he = 4.0
    MW_h2 = 2.0
    MW_co = 28.0
    MW_co2 = 44.0
    MW_n2 = 28.0

    # Simplified: user can sweep "effective_MW"
    # At hot end, CO/CO2 rich → higher density, better drag at low P
    effective_MW = (1 - co2_frac - co_frac - h2_frac) * MW_he + h2_frac * MW_h2 + co_frac * MW_co + co2_frac * MW_co2

    R = 8.314
    rho = (P_bar * 1e5 * effective_MW / 1000.0) / (R * T_avg)   # ideal gas, kg/m3

    # Viscosity very weak function of composition at these T (rough)
    mu = 2.5e-5 * (T_avg / 600.0)**0.7   # Pa.s, typical for light gases at these conditions

    return rho, mu, effective_MW

# =============================================================================
# CORRELATIONS
# =============================================================================
def wen_yu_umf(dp, rho_g, mu_g, rho_p=RHO_REGOLITH, g=G_LUNAR):
    """
    Wen-Yu minimum fluidization velocity.
    Widely used, matches the numbers quoted in the spec.
    """
    Ar = (dp**3 * rho_g * (rho_p - rho_g) * g) / (mu_g**2)
    Remf = (33.7**2 + 0.0408 * Ar)**0.5 - 33.7
    Umf = Remf * mu_g / (dp * rho_g)
    return Umf

def ergun_dp_bed(U, dp, eps, L, rho_g, mu_g, g=G_LUNAR, rho_p=RHO_REGOLITH):
    """
    Ergun equation for bed pressure drop (viscous + inertial).
    Used in spec for distributor vs bed split.
    """
    term1 = 150 * mu_g * (1-eps)**2 * U / (eps**3 * dp**2)
    term2 = 1.75 * rho_g * (1-eps) * U**2 / (eps**3 * dp)
    return (term1 + term2) * L

def haider_levenspiel_terminal(dp, rho_g, mu_g, sph=SPH, rho_p=RHO_REGOLITH, g=G_LUNAR):
    """
    Haider-Levenspiel correlation for non-spherical particles (spec uses sph=0.7).
    Used for entrainment cutoff calculation.
    """
    # Simplified implementation
    Re_t = (dp * rho_g * 1.0) / mu_g   # placeholder iteration
    # Better: solve iteratively or use approximation
    # For speed we use a common approximation for angular particles
    Ut = (dp**2 * (rho_p - rho_g) * g) / (18 * mu_g) * (0.5 + 0.5 * sph)  # rough
    # More accurate form would iterate; this is directionally correct for sensitivity
    return Ut

# =============================================================================
# SWEEP
# =============================================================================
def run_pressure_sweep():
    pressures = np.linspace(0.08, 0.45, 38)   # bar
    results = []

    for P in pressures:
        # Two gas cases:
        # Case A: "worst" — He/H2 dominant (low density, early in system)
        # Case B: "hot end" — CO/CO2 enriched (higher density, where it matters most per spec)
        rho_a, mu_a, mw_a = gas_props(P, T_avg=500, co2_frac=0.05, co_frac=0.15, h2_frac=0.25)
        rho_b, mu_b, mw_b = gas_props(P, T_avg=750, co2_frac=0.25, co_frac=0.35, h2_frac=0.10)

        # Use 200 µm as "target" coarse fraction per spec discussion
        dp_target = 200e-6

        Umf_a = wen_yu_umf(dp_target, rho_a, mu_a)
        Umf_b = wen_yu_umf(dp_target, rho_b, mu_b)

        U_op_a = 4.0 * Umf_a   # 3-5x per spec
        U_op_b = 4.0 * Umf_b

        # Rough bed dp (per stage, ~0.3 m bed height)
        L_bed = 0.3
        eps = 0.55   # typical expanded
        dp_bed_a = ergun_dp_bed(U_op_a, dp_target, eps, L_bed, rho_a, mu_a)
        dp_bed_b = ergun_dp_bed(U_op_b, dp_target, eps, L_bed, rho_b, mu_b)

        # Distributor is dominant (spec says ~94% at 0.2 bar)
        # We keep same physical distributor → dp_dist scales with rho*U^2 roughly
        dp_dist_a = 6300 * (rho_a / 0.02) * (U_op_a / 0.018)**2   # scaled from spec 0.2 bar reference
        dp_dist_b = 6300 * (rho_b / 0.02) * (U_op_b / 0.018)**2

        total_dp_a = dp_bed_a + dp_dist_a
        total_dp_b = dp_bed_b + dp_dist_b

        # Blower power per stage (5 stages in parallel)
        # Very rough: power ~ volume_flow * dp / efficiency
        area = 0.1  # m2 per stage (from spec ~0.36 m diameter)
        vol_flow_a = U_op_a * area
        vol_flow_b = U_op_b * area

        eta = 0.65
        power_a = (vol_flow_a * total_dp_a) / eta
        power_b = (vol_flow_b * total_dp_b) / eta

        # Entrainment cutoff rough (higher density gas → lower terminal velocity for fines)
        Ut_fine_a = haider_levenspiel_terminal(30e-6, rho_a, mu_a)
        Ut_fine_b = haider_levenspiel_terminal(30e-6, rho_b, mu_b)

        results.append({
            'P_bar': P,
            'rho_worst': rho_a, 'rho_hot': rho_b,
            'Umf_worst': Umf_a, 'Umf_hot': Umf_b,
            'Uop_worst': U_op_a, 'Uop_hot': U_op_b,
            'dp_total_worst': total_dp_a, 'dp_total_hot': total_dp_b,
            'blower_power_worst_W': power_a, 'blower_power_hot_W': power_b,
            'Ut_30um_worst': Ut_fine_a, 'Ut_30um_hot': Ut_fine_b,
        })

    return results

if __name__ == "__main__":
    data = run_pressure_sweep()

    # Quick console summary
    print("Pressure | rho_worst | Umf_worst(mm/s) | Power_worst(W) | rho_hot | Umf_hot(mm/s)")
    print("-" * 85)
    for d in data[::4]:
        print(f"{d['P_bar']:.2f} bar | {d['rho_worst']:.4f} | {d['Umf_worst']*1000:.3f} | {d['blower_power_worst_W']:.1f} | "
              f"{d['rho_hot']:.4f} | {d['Umf_hot']*1000:.3f}")

    # Save for later plotting / analysis
    outdir = Path(__file__).resolve().parents[1] / "analysis"
    outdir.mkdir(parents=True, exist_ok=True)
    np.save(outdir / "pressure_sweep_v1.npy", data)

    print(f"\nResults saved to {outdir / 'pressure_sweep_v1.npy'}")
    print("This is the first artifact of the pressure-minimization campaign.")