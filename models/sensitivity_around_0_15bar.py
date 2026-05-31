#!/usr/bin/env python3
"""
Sensitivity / Robustness around 0.15 bar
Tests performance variation with key uncertainties for minimal-intervention design.

Uncertainties tested (conservative ranges):
- Incoming fines fraction ±30%
- Gas generation rate ±25%
- Iron shot wear (effective agitation reduction)
- EDS effectiveness degradation

All within existing claims.
"""

import numpy as np

# Base case at 0.15 bar with good tuning (from previous runs)
BASE_P = 0.15
BASE_COLD_EFF = 0.78
BASE_HOT_EFF = 0.91
BASE_OVERALL = 0.65   # approximate from trends

def sensitivity():
    cases = []

    # Fines variation
    for factor in [0.7, 1.0, 1.3]:
        cold = BASE_COLD_EFF * (1 - 0.25*(factor-1))   # more fines hurts cold stages
        hot = BASE_HOT_EFF * 0.98
        overall = 0.22*cold + 0.20*cold + 0.20*hot + 0.20*hot + 0.18*hot
        cases.append(("Fines x{:.1f}".format(factor), overall))

    # Gas generation variation (affects envelope pressure stability and composition)
    for factor in [0.75, 1.0, 1.25]:
        # Lower gas gen → slightly lower effective density in cold stages
        penalty = 0.08 * (1 - factor)
        cold = BASE_COLD_EFF * (1 - penalty)
        hot = BASE_HOT_EFF
        overall = 0.22*cold + 0.20*cold + 0.20*hot + 0.20*hot + 0.18*hot
        cases.append(("Gas gen x{:.2f}".format(factor), overall))

    # Iron wear (reduces agitation)
    for wear in [0.0, 0.15, 0.30]:   # 0% = new, 30% = significantly worn
        cold = BASE_COLD_EFF * (1 - 0.35*wear)
        hot = BASE_HOT_EFF * (1 - 0.15*wear)
        overall = 0.22*cold + 0.20*cold + 0.20*hot + 0.20*hot + 0.18*hot
        cases.append(("Iron wear {}%".format(int(wear*100)), overall))

    # EDS degradation
    for deg in [0.0, 0.10, 0.20]:
        cold = BASE_COLD_EFF * (1 - 0.28*deg)
        hot = BASE_HOT_EFF * (1 - 0.12*deg)
        overall = 0.22*cold + 0.20*cold + 0.20*hot + 0.20*hot + 0.18*hot
        cases.append(("EDS deg {}%".format(int(deg*100)), overall))

    return cases

if __name__ == "__main__":
    results = sensitivity()
    print("Sensitivity around 0.15 bar (conservative tuning)")
    print("-" * 50)
    for name, eff in results:
        print(f"{name:20s} → Overall eff ≈ {eff:.1%}")
    print("\nNote: These are directional estimates from the current model family.")