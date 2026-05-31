# RCFX "It Works" Configuration
## 0.14 bar Operating Point (Claim-Compliant)

**Date**: 31 May 2026  
**Status**: Current working demonstration point from 5-stage counter-flow energy balance modeling on soulkiller.

### Operating Pressure
**0.14 bar (140 mbar) nominal**

This is substantially lower than the current 0.2–0.3 bar nominal in the provisional while still delivering strong performance with conservative modeling assumptions.

### Tuned Parameters (All Within Existing Claims)

**Cold Stages (1–2)** — the difficult region:
- Iron shot: 2.0 mm diameter
- Iron fill fraction: 0.32
- Superficial velocity: 5.5 × Umf of the 200 µm target fraction
- EDS effectiveness: 0.97 (high)
- Pre-classification cutoff: 22 µm (aggressive)

**Hot Stages (3–5)**:
- Iron shot: 3.5 mm diameter
- Iron fill fraction: 0.20
- Superficial velocity: 3.5 × Umf
- EDS effectiveness: 0.97

### Performance (5-Stage Counter-Flow Energy Balance)

- Overall thermal recovery effectiveness: **75.6%**
- Recovered sensible heat (100 kg/hr reference): ~11.8 kW
- Estimated blower power: ~68 W (well under 2% parasitic target)

**Stage breakdown**:
- Stages 1–2 (cold): ~86.3%
- Stages 3–5 (hot): ~99.5% (limited only by remaining temperature difference)

### Why This "Makes It Work"

- Hits the >70% recovery target with clear margin.
- Operates at ~half the current nominal pressure → major simplification opportunity for vessel and sealing design.
- Uses only parameters and features already described in PERRY-RCFX-004 Rev 5.2 (iron shot as thermal mass + agitator, EDS integration, fines management approaches, parallel forced circulation, staged iron deployment, etc.).
- Blower power is low and the architecture already includes N+1 redundancy + passive backup.

### Next (when ready to fine-tune)

- Sensitivity analysis around this point (regolith variation, gas generation, wear).
- Further optimization within claims to see if we can comfortably push to 0.12 bar while keeping >70%.
- Higher-fidelity heat transfer correlations.

All source models and data in `~/rcfx/models/` and `~/rcfx/analysis/` on soulkiller.
