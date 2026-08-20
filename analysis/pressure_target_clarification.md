# Pressure target

The design goal is a plant that can run off-world without the vessel class,
safety protocol, and sealing burden of a high-pressure envelope.

An early low-fidelity estimate had placed “it only works” near ~5 mbar. That
is near-vacuum fluidization and would require space-grade vacuum sealing.
The campaign does **not** target that regime.

The custom GPU DEM and the 5-stage lumped model were used to find the lowest
pressure at which the existing architecture still performs.

## Engineering target

We are **not** trying to push all the way to hard vacuum (few mbar).

We are trying to find the **lowest pressure at which the existing architecture + its built-in mitigations can still deliver acceptable performance**, while staying comfortably inside a "slightly pressurized envelope" regime.

### Current Spec Envelope
- Nominal: 0.2–0.3 bar (200–300 mbar)
- Design range: 0.1–0.5 bar (100–500 mbar)

### Desired Operating Band (for cost avoidance)
Roughly **50–150 mbar** (0.05–0.15 bar).

Why this band?
- High enough gas density that fluidization + heat transfer is still feasible with the help of:
  - Iron shot mechanical agitation
  - EDS for electrostatic control
  - Active fines management (cyclones + optional pre-classification)
  - Self-generated heavier gases (CO/CO2) at the hot end
- Low enough that the vessel remains in a "low-pressure" category that avoids heavy ASME-style pressure vessel rules, extensive safety certification, and the associated physical prototype testing burden.

This is the classic "sweet spot" for this kind of ISRU hardware: low enough pressure to be cheap and light, high enough to make the gas-solid physics tractable without heroic measures.

## Modeling status

- At **0.10 bar (100 mbar)** with maximum use of existing mitigations (high iron agitation + strong EDS + aggressive pre-classification): effectiveness is still poor (~35-50% in current models). Fines loss in the cold stages dominates.

- At **0.12–0.15 bar**: Getting better, but still below the 70% floor in conservative runs when using realistic gas compositions.

- At **0.18–0.20 bar**: Approaches usable performance with strong mitigations.

Preliminary conclusion:
With the architecture exactly as described in Rev 5.2, the practical floor using only the built-in mitigations appears to be roughly **140–160 mbar** for good effectiveness. Below ~120 mbar the cold-stage cohesive fines problem becomes very hard to solve without either:
  a) Accepting significant performance loss, or
  b) Adding something new that is still "low-pressure friendly."

## Next Focus
The campaign is now explicitly targeting the 80–150 mbar band.

We will quantify:
- How much performance we can recover in that band by optimizing the existing levers (iron shot design per stage, EDS optimization, gas composition routing, pre-classification aggressiveness).
- What small, low-pressure-compatible additions would buy another 30–50 mbar of margin without crossing into "needs real vacuum seals" territory.

Sources: `models/`, `analysis/`, `rung_results/RUNG_CAMPAIGN_RESULTS.md`.
The locked working point is **0.14 bar / 75.6% / 221 W**.
