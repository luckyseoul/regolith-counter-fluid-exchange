#!/usr/bin/env python3
"""
Rung 4 Runner: Full 5-Stage Counterflow + Heat Transfer + Power
Using best current claim-compliant tuning.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "models"))
import five_stage_counterflow as m
import numpy as np

# Best current tuning (from full tuning sweeps + 5-stage refinement)
m.IRON_COLD_MM = 2.0
m.IRON_HOT_MM = 3.5
m.FILL_COLD = 0.32
m.FILL_HOT = 0.20
m.VEL_MULT_COLD = 5.5
m.VEL_MULT_HOT = 3.5
m.EDS_EFF = 0.97
m.PRECLASS_UM = 22

results = {}

for p in [0.12, 0.14, 0.15]:
    m.P = p
    res = m.run_5stage()
    results[p] = res
    print(f"=== Rung 4 at {p:.2f} bar ===")
    print(f"Overall effectiveness: {res['overall_eff']:.1%}")
    print(f"Recovered (100 kg/hr ref): {res['recovered_kW']:.2f} kW")
    print(f"Total blower power: {res['total_blower_W']:.0f} W")
    print(f"Stage effectivenesses: {[f'{e:.1%}' for e in res['stage_effs']]}")
    print(f"Parameters: {res['params']}")
    print()

# Save for later
out = Path(__file__).resolve().parent / "rung4_results.npy"
np.save(out, results)
print(f"Results saved to {out}")