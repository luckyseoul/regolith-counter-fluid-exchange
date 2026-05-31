# RCFX Rung Campaign Results — Current Status (31 May 2026)

**Campaign Goal**: Find the lowest practical envelope pressure (within existing claims) at which the 5-stage RCFX system can achieve ≥70-75% thermal recovery at pilot scale with conservative, defensible margins and low maintenance burden.

**Working Configuration (from Rung 4)**:
- Pressure: 0.14 bar
- Cold stages: 2.0 mm iron @ 0.32 fill, 5.5× Umf, EDS=0.97, pre-class 22 µm
- Hot stages: 3.5 mm iron @ 0.20 fill, 3.5× Umf, EDS=0.97
- 5-stage counterflow result: **75.6% overall effectiveness**, ~68 W blower power

---

## Rung 0 — Gas + Distributor Only

**Tested at**: 0.12, 0.14, 0.15 bar (using current best velocity multiples)

**Result**:
- Distributor remains strongly dominant (~94% of per-stage ΔP) at all tested pressures.
- Ratio well above the 20-30× minimum for uniformity.
- **Status**: PASS across the board. The sintered distributor design from the spec works as intended even at low pressure.

**Key takeaway**: No fundamental distributor problem at 0.12+ bar.

---

## Rung 1 — Coarse Non-Cohesive Fraction + Iron Shot

**Tested at**: 0.12–0.15 bar using iron shot agitation models.

**Result**:
- With 3.5 mm iron at moderate-to-high fill and 4–5.5× velocity: stable fluidization of the >50 µm fraction with low dead zones.
- At 0.12 bar: requires the upper end of iron size/fill/velocity to stay comfortable.
- At 0.14 bar+: very comfortable with the recommended tuning.

**Status**: PASS at 0.14 bar with current tuning. Marginal but workable at 0.12 bar if we accept less margin.

---

## Rung 2 — Full Bimodal PSD + Simple Cohesion

**Tested via**: pressure_relief_levers and cold-stage focused models (cohesion + entrainment).

**Result**:
- 0.12 bar: Cold-stage effectiveness drops to ~76-80% even with max tuning. Entrainment and agglomeration risk are noticeable.
- 0.14 bar: Cold-stage reaches ~86% with recommended parameters. Good margin.
- 0.15 bar: Excellent (~90%+ in cold stages).

**Status**:
- Marginal at 0.12 bar.
- **Solid PASS at 0.14 bar** with the tuned iron shot + high EDS + pre-class combination.

---

## Rung 3 — Electrostatics + EDS Mitigation

**Tested via**: Direct parameterization of EDS effectiveness across all models + sensitivity runs.

**Result**:
- EDS at 0.97 is a major stabilizer at low pressure.
- Dropping EDS effectiveness to 0.5 costs 15–25 percentage points in cold-stage performance.
- At 0.14 bar with high EDS: cohesion is kept under control.
- At 0.12 bar: EDS becomes almost mandatory at maximum effectiveness.

**Status**: PASS at 0.14 bar with high EDS. EDS is one of the highest-leverage existing mitigations for low-pressure operation.

---

## Rung 4 — Full 5-Stage Counterflow + Heat Transfer + Power

**Full integrated model results** (five_stage_counterflow.py):

| Pressure | Overall Effectiveness | Cold Stages | Hot Stages | Blower Power |
|----------|-----------------------|-------------|------------|--------------|
| 0.12 bar | 58.1%                | 76.6%      | 91.5%     | 58 W        |
| **0.14 bar** | **75.6%**            | **86.3%**  | **99.5%** | **68 W**    |
| 0.15 bar | 89.7%                | 90.7%      | ~100%     | 73 W        |

**Success criteria** (from plan): ≥75% overall at P ≤ 0.15 bar with <180 W parasitic.

- **0.14 bar**: Meets the 75% target with the current tuning. Clear working point.
- **0.12 bar**: Falls short of 75% in the current model. Would require further improvements or acceptance of lower performance.

**Status**: **PASS at 0.14 bar**. This is the current "it works" configuration.

---

## Rung 5 — Sensitivity & Robustness + Optimization Within Existing Claims

**Pressure fixed at**: 0.14 bar (the Rung 4 working point)

**Baseline** (current best tuning): **75.6%** overall effectiveness, 68 W blower power.

### Single-Parameter Sensitivity (selected results)

| Parameter (range)              | Effect on Overall Effectiveness          | Notes |
|--------------------------------|------------------------------------------|-------|
| Iron shot diameter (cold) 1.5–5.0 mm | Very flat (~75.6% across range)         | Model shows limited additional gain from larger shot in this regime |
| Iron fill (cold) 0.18–0.42     | Very flat                                | — |
| Velocity multiple (cold) 3.5–6.5× | 75.6% → 75.6% (power 47 W → 81 W)       | Clear power vs. (modeled) performance trade-off |
| EDS effectiveness 0.70–0.99    | 56.2% → 78.1%                            | **Very high leverage** |
| Pre-class cutoff 50 µm → 18 µm | 52.2% → 84.0%                            | **Extremely high leverage** |

### Combined Robustness Cases (simultaneous degradation)

- Nominal: 75.6%
- +20% fines + 15% iron wear: **69.0%**
- EDS degraded to 0.85 + moderate wear: **64.2%**
- Low gas generation (-25%): **69.0%**
- Worst combined (more fines + EDS 0.85 + wear): **59.3%**

### Rung 5 Conclusions

- The 0.14 bar configuration has **good headroom on most individual parameters**.
- EDS effectiveness and pre-classification aggressiveness are the two highest-leverage single knobs within the current claims.
- Moderate combined degradation still keeps the system above ~69%.
- Severe simultaneous degradation drops performance significantly (as expected). This suggests that for true "one visit per month" reliability, we want to operate with some margin above the minimum (i.e. 0.14–0.15 bar rather than right at the edge).
- Iron shot size/fill showed less sensitivity than expected in the current model — this is an area for model refinement rather than a physical conclusion.

**Status**: **Complete for current model fidelity.**

Full data saved to `rung_results/rung5_sensitivity.npy`.

---

## Overall Campaign Conclusion (Current)

With the architecture and mitigations described in PERRY-RCFX-004 Rev 5.2, and with intelligent (claim-compliant) tuning of:
- Iron shot size and loading (especially in cold stages)
- Stage-wise velocity
- EDS performance
- Pre-classification aggressiveness

...the system can achieve **>75% thermal recovery at 0.14 bar** in the current 5-stage counterflow model.

This is:
- Well below the current 0.2–0.3 bar nominal → meaningful reduction in pressure vessel/seal complexity.
- High enough to maintain good fluidization margins with the existing mitigations.
- Achieved without introducing new patentable subject matter.

**Current recommended "make it work" point for further development and patent support**: **0.14 bar** with the parameter set listed above.

Lower pressures (0.12 bar and below) are marginal in the current models and would likely require either accepting lower performance or additional (still within-claims) refinements that have not yet been fully quantified.

---

## Files

- Detailed Rung 4 runs: `rung_results/rung4_results.npy` + `run_rung4.py`
- Rung 0-3 summary: `run_rungs_0_to_3.py`
- Full 5-stage model: `models/five_stage_counterflow.py`
- Supporting tuning data: `analysis/` directory

All work on soulkiller, within existing claims only.