#!/usr/bin/env python3
"""
Legacy five-step thermal recurrence, retained for numerical reproducibility.

This is NOT a validated counterflow energy balance: both stream temperatures
advance in the same loop direction, rather than satisfying opposite-end inlet
conditions. The default arithmetic returns 75.6%, but alternates the sign of
heat transfer. Empirical stage coefficients can also exceed unity. Neither
this number nor a blower/recovery ratio establishes exchanger performance.
"""

import numpy as np

# =============================================================================
# TUNED PARAMETERS (from full_tuning_sweep — all within Rev 5.2 claims)
# =============================================================================
P = 0.14                    # current working demonstration point (0.14 bar, 75.6%)
# Best parameters from cold-stage optimizer + hot stage tuning (within claims)
# VEL_MULT_COLD set for U_G ~0.066 m/s alignment with DEM Rung rep point + correct vol_flow power calc
IRON_COLD_MM = 2.0
IRON_HOT_MM = 3.5
FILL_COLD = 0.32
FILL_HOT = 0.20
VEL_MULT_COLD = 4.4
VEL_MULT_HOT = 3.5
EDS_EFF = 0.97
PRECLASS_UM = 22

# =============================================================================
# PHYSICS
# =============================================================================
RHO_REG = 3100.0
CP_REG = 800.0
G = 1.625
AREA = 0.10                 # m2 per stage

STAGE_INLET_T = [200, 340, 480, 620, 760]   # regolith entering each stage
HOT_INLET_T = 900                           # spent regolith entering Stage 5

def gas_at_T(T):
    if T < 550:
        mw = 7.8
    elif T < 750:
        mw = 9.5
    else:
        mw = 19.0
    rho = P * 1e5 * (mw / 1000) / (8.314 * T)
    mu = 2.28e-5 * (T/600)**0.68
    return rho, mu, mw

def stage(U, rho, mu, iron_d_mm, iron_fill, eds, pre_um, is_cold_stage=True):
    """
    Conservative stage model for robust, low-maintenance design.
    Cold stages penalized more for lighter gas + higher risk of cohesion/entrainment.
    """
    dp = 200e-6
    Ar = (dp**3 * rho * (RHO_REG - rho) * G) / (mu**2)
    Remf = np.sqrt(33.7**2 + 0.0408*Ar) - 33.7
    Umf = Remf * mu / (dp * rho)

    agitation = min(0.93, (iron_d_mm/3.2)**2.2 * (iron_fill/0.25) * (U/Umf / 4.0)**1.2)

    coh_factor = 1.30 if is_cold_stage else 0.82
    coh = (coh_factor / (P/0.1)**0.52) * (1 - 0.82*agitation) * (1 - 0.73*eds)

    entr_factor = 1.30 if is_cold_stage else 0.85
    entr = min(0.94, 0.21 + 2.9*(0.2/P)*coh * (pre_um/32) * entr_factor)

    # Make the mitigations count more strongly (iron agitation + EDS strongly improve effective heat transfer
    # by breaking agglomerates and keeping the bed well fluidized and de-agglomerated).
    htf = (rho/0.017)**0.38 * (1 - 0.42*coh) * (1 + 0.28*agitation)
    eff = 0.80 * htf / (1 + 1.05 * entr**1.4)

    dp_bed = 400 * (rho/0.018) * (U / 0.018)**1.65
    return eff, entr, dp_bed, Umf

def run_5stage():
    """
    Replay the legacy recurrence, with explicit validity diagnostics.

    Existing numeric result keys are preserved without clipping or calibration.
    ``valid_counterflow`` remains false because this recurrence does not solve
    the counterflow boundary-value problem, even when numeric bounds pass.
    """
    mdot = 100.0 / 3600.0   # kg/s  (reference throughput)

    # Initialize streams
    T_cold = 200.0          # Cold incoming regolith
    T_hot = 900.0           # Hot spent regolith entering Stage 5 (after any pre-cool)

    total_heat_recovered = 0.0
    stage_effs = []
    blower_powers = []
    stage_trace = []
    invalid_eff_stages = []
    negative_heat_stages = []
    reversed_inlet_stages = []

    for i in range(5):
        # Local gas properties at average temperature in this stage
        T_avg = (T_cold + T_hot) / 2
        rho, mu, _ = gas_at_T(T_avg)

        # Choose tuned parameters for this stage group
        if i < 2:  # Cold stages - hardest fluidization
            iron_d = IRON_COLD_MM
            iron_f = FILL_COLD
            vmult = VEL_MULT_COLD
        else:
            iron_d = IRON_HOT_MM
            iron_f = FILL_HOT
            vmult = VEL_MULT_HOT

        # Local stage performance
        is_cold = (i < 2)
        U = vmult * 0.015
        eff, entr, dp_bed, Umf = stage(U, rho, mu, iron_d, iron_f, EDS_EFF, PRECLASS_UM, is_cold)
        stage_effs.append(eff)

        # Legacy local heat-transfer arithmetic (not a counterflow network).
        # Maximum possible heat transfer limited by the smaller capacity rate stream
        # (both streams have same mdot * CP)
        max_possible_this_stage = mdot * CP_REG * (T_hot - T_cold)
        actual_heat_this_stage = max_possible_this_stage * eff
        cold_in, hot_in = T_cold, T_hot
        if not np.isfinite(eff) or not 0 <= eff <= 1:
            invalid_eff_stages.append(i + 1)
        if actual_heat_this_stage < 0:
            negative_heat_stages.append(i + 1)
        if T_hot < T_cold:
            reversed_inlet_stages.append(i + 1)

        total_heat_recovered += actual_heat_this_stage

        # Update both streams
        T_cold += actual_heat_this_stage / (mdot * CP_REG)
        T_hot  -= actual_heat_this_stage / (mdot * CP_REG)
        stage_trace.append({
            'stage': i + 1,
            'cold_in_K': cold_in,
            'hot_in_K': hot_in,
            'cold_out_K': T_cold,
            'hot_out_K': T_hot,
            'heat_W': actual_heat_this_stage,
            'effectiveness': eff,
        })

        # Blower power for this stage (parallel manifold)
        # vol_flow must use actual local U (was hardcoded 0.015*AREA — bug)
        vol_flow = U * AREA
        stage_blower = (vol_flow * dp_bed) / 0.60
        blower_powers.append(stage_blower)

    total_possible = mdot * CP_REG * (900 - 200)
    overall_eff = total_heat_recovered / total_possible
    total_blower = sum(blower_powers)

    return {
        'P_bar': P,
        'overall_eff': overall_eff,
        'recovered_kW': total_heat_recovered / 1000,
        'stage_effs': stage_effs,
        'total_blower_W': total_blower,
        'stage_trace': stage_trace,
        'valid_counterflow': False,
        'validity': {
            'reason': 'Both streams advance in the same direction; opposite-end counterflow boundary conditions are not solved.',
            'stage_effectiveness_out_of_bounds': invalid_eff_stages,
            'negative_heat_stages': negative_heat_stages,
            'reversed_inlet_stages': reversed_inlet_stages,
            'overall_effectiveness_out_of_bounds': not bool(np.isfinite(overall_eff) and 0 <= overall_eff <= 1),
        },
        'params': {
            'iron_cold_mm': IRON_COLD_MM,
            'iron_hot_mm': IRON_HOT_MM,
            'fill_cold': FILL_COLD,
            'fill_hot': FILL_HOT,
            'vel_cold': VEL_MULT_COLD,
            'vel_hot': VEL_MULT_HOT,
            'eds': EDS_EFF,
            'pre_um': PRECLASS_UM
        }
    }

if __name__ == "__main__":
    res = run_5stage()
    print("Legacy five-step thermal recurrence — numerical replay")
    print("WARNING: invalid counterflow interpretation; reported effectiveness and recovery are unvalidated arithmetic outputs.")
    print(res['validity']['reason'])
    print(f"Pressure: {res['P_bar']:.2f} bar")
    print(f"Overall effectiveness: {res['overall_eff']:.1%}")
    print(f"Recovered (100 kg/hr ref): {res['recovered_kW']:.2f} kW")
    print(f"Estimated blower power: {res['total_blower_W']:.0f} W")
    print(f"Stage effectivenesses: {[f'{e:.1%}' for e in res['stage_effs']]}")
    print("Stage trace (K; heat positive from labelled hot to cold stream):")
    for row in res['stage_trace']:
        print(f"  {row['stage']}: cold {row['cold_in_K']:.2f} -> {row['cold_out_K']:.2f}; "
              f"hot {row['hot_in_K']:.2f} -> {row['hot_out_K']:.2f}; Q={row['heat_W']:.2f} W")
    print(f"Validity diagnostics: {res['validity']}")
    print("\nParameters used (all within existing claims):")
    print(res['params'])
