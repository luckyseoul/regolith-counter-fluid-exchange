# Operating point — 0.14 bar

Working demonstration point from the 5-stage counter-flow energy balance
(`models/five_stage_counterflow.py`), aligned with custom GPU DEM Rung 1.

## Pressure

**0.14 bar** (140 mbar). Lower than the 0.2–0.3 bar nominal in Rev 5.2 while
remaining inside the 0.1–0.5 bar claim envelope.

## Parameters (inside Rev 5.2)

**Cold stages (1–2)**
- Iron shot: 2.0 mm (good-var DEM also at 1.5 mm)
- Fill: 0.32
- 4.4× *U*<sub>mf</sub> (*U*<sub>G</sub> = 0.066 m/s in DEM)
- EDS: 0.97
- Pre-class cutoff: 22 µm

**Hot stages (3–5)**
- Iron shot: 3.5 mm
- Fill: 0.20
- 3.5× *U*<sub>mf</sub>
- EDS: 0.97

## Performance

- Overall effectiveness: **75.6%**
- Recovered heat (100 kg/h): **11.8 kW**
- Blower: **221 W** (1.88% parasitic; `vol_flow = U × AREA`)
- Cold-stage effectiveness ~86.3%; hot-stage ~99.5%

Rung 1 DEM (custom GPU, physical lid, BOX = 0.018 m): high-N EMI 8.04× at
1000 steps (peak 8.53×); good-variable 1.5 mm / 3.5 m/s EMI 3.58× vs no-iron;
100% inside x,y ∈ [0, 0.018] m. High-N with-iron mean speeds ~37–41 m/s.
