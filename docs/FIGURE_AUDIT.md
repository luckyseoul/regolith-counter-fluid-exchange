# Figure and quantitative-claim audit — 2026-09-05

The current figures contain reproducible plotting errors and unsupported physical interpretations. Corrections distinguish checkpoint coordinates, model diagnostics, and design targets. No hardware performance is established. Dated `patent_application/2026-06-05` and `patent_evidence/2026-06-04` copies remain historical artifacts and do not inherit the numerical corrections. Their obsolete patent docket labeling is removed separately at the user’s request.

## README figure results

Audited from `main` at `e06389686af1717bbbb3d89a70fe45f8eeb744a2`.

| Figure | Correction |
|---|---|
| Pressure sweep | Removed the 100% display clamp: raw outputs at 0.16 / 0.18 / 0.20 bar are 108.068% / 158.781% / 230.316%. All points are labeled invalid legacy-model diagnostics, including the nominal 75.592% point. |
| Stage coefficients | Raw values 86.336% / 86.336% / 99.481% / 99.481% / 99.481% are identified as correlation outputs. They do not establish plant-stage performance. |
| EDS / cutoff sensitivity | Regenerated from live model parameters instead of loading the old pickled sweep. The baseline parameters are explicit and restored after every evaluation, including on failure. Curves retain the model-invalidity notice. |
| DEM snapshot | Corrected the inferred lid claim: observed maximum centre z is 40.1297 mm; the current source declares a 60 mm lid. Markers are illustrative and projection overlap is disclosed. |
| DEM height series | Isolated the different real-drag run in its own panel; removed the unsupported horizontal reference across all steps. Labels identify particle-centre height and checkpoint steps, not elapsed seconds. The 8.5323× maximum is among saved samples. |
| Inventory | Added 13 root dumps omitted from the former chart. Total 1467 files / 150,981,303 bytes; sizes use decimal MB. |

The source recurrence keeps the average of its stream temperatures at 550 K.
It yields −9.760 kW and −8.088 kW signed heat at steps 2 and 4, respectively.
Stage coefficients first exceed one among the checked pressure points at
0.15 bar. The model now exposes these diagnostics and `valid_counterflow=False`
without altering the archived arithmetic. No corrected physical performance
number can be inferred merely by clipping the coefficients.

The velocity inputs also need precise interpretation: 4.4 and 3.5 multiply
0.015 m/s in code, giving 0.066 and 0.0525 m/s. The computed Wen–Yu minimum
fluidization velocity at the invariant average is 0.005676 m/s, so actual
ratios are 11.63 and 9.25, not 4.4 and 3.5.

Reproducible evidence:

- [Plotted data, source hashes, and inventory paths/sizes](figures/figure_data.json).
- [Independent DEM measurements and runner-source provenance](figures/dem_validation.json): 26 plotted checkpoints; all 6500 centres fit the stated bounds at the cited samples, while only 6331 full spheres fit for the real-drag sample.
- [Data catalog](../DATA.md). Checkpoints lack configuration and time metadata; present runner constants are contextual evidence, not authenticated historical settings.

General heat-exchanger methodology distinguishes effectiveness–NTU and LMTD
analyses and the flow configuration; see the primary
[F-Chart heat-exchanger documentation](https://fchartsoftware.com/ees/heat_transfer_library/heat_exchangers/hs1.htm).
The defects above are established directly from this repository's equations
and data, without fitting a replacement heat-transfer correlation.

## Drawing results

| Current drawing | Finding and correction |
|---|---|
| FIG. 1 | System schematic. Removed the unvalidated “0% dead zones” caption; a particle-speed threshold in a no-lid model is not a distributor-uniformity measurement. |
| FIG. 2 | Conceptual cross-section; dimensions and 0.14 bar are representative design inputs, not measured validation. No numeric coordinate plot. |
| FIG. 3, Rung 5 at 200k and 500k | Raw checkpoint z coordinates were numerically plotted in metres under millimetre labels. Regenerated with x in mm and z in m and explicit no-lid limitation. Maximum z is 9.840985 m at 200k and 22.703933 m at 500k. |
| FIG. 3, good-variable | Regenerated a legible coordinate scatter and statistics panel. Mean heights reproduce; 100% refers only to particle centers, while 6331/6500 whole spheres fit the 18 × 18 × 60 mm source bounds. The 3.58x ratio is cross-run, not a matched control. Do not conflate its filename 3.5 m/s input with Rung 5 0.066 m/s. |
| FIG. 4 | Opposing material-flow arrows are conceptual. The 230-transfer callout comes from a two-stage DEM skeleton, not validation of five-stage counter-current thermal exchange; corrected caption. |
| FIG. 5 | Removed the performance curve and replaced it with an explicit withdrawal notice. The 75.6% recovery claim relies on an invalid thermal recurrence. The default point has raw stage effectiveness below one; other sweep points exceed one, and the README sweep clipped overall output above one. |
| FIG. 6 | Rung 0 raw z values reached 3.455635 m, although labeled mm. Regenerated from the checkpoint with z in metres; scatter is not a verified uniformity measurement. |
| FIG. 7 | Fixed swapped iron/regolith series. Removed the false full-containment assertion: the code checks only x/y limits and z ≥ 0, without any upper-z boundary. Relabeled means as particle-center z, not physical bed height. |

FIG. 7 reads 334 checkpoints. Its lateral-and-floor containment metric is 100% at each checkpoint; this does not bound height. At step 500000, mean z is 10404.501172 mm overall, 9781.750371 mm for regolith (`mat == 0`) and 12584.128974 mm for iron (`mat == 1`). These are historical lofting diagnostics, not confined-bed performance.

## Quantitative parameter arithmetic

Corrected `docs/rcfx_key_parameters.md` while retaining its distinction as an extracted design document:

- Ideal-gas inventory from `m = P V M / (R T)` at 20000 Pa, 0.2 m³, 600 K is 3.21 g He or 1.62 g H2. The former 15 g needs mean molar mass 18.7 g/mol; composition was unspecified.
- Pure-He density at the same P/T is 0.0160 kg/m³. The stated 3100 kg/m³ is particle material density, not bulk bed density.
- Five parallel stages at 0.1 m² × 0.018 m/s each give total flow 0.009 m³/s. At 7000 Pa, gas power is 63 W and electrical input is 90 W at 70% efficiency. The former caption conflated these powers.
- Distributor and bed drops total 6300 + 400 = 6700 Pa; the rounded 7000 Pa estimate leaves ~300 Pa unspecified.
- EDS estimates 5–15 W total over 8 m² and 1–5 W/m² are inconsistent; both are now identified explicitly with the correct conversions.

The 140 K per-stage temperature step, fluidization velocities, entrainment cutoffs, wear rates, gas-generation estimates and optimal stage count remain design assumptions or historical estimates; this audit does not establish their empirical validity. The original Rev 5.2 document is not independently verified by the extraction itself.

## Thermal and campaign status

Prominent notices in the parameter extraction, campaign summary, and campaign results mark the thermal values as historical. Both stream temperatures advance in the same loop direction; this is not the stated counter-current boundary-value problem. Stage coefficients can exceed one; the former README pressure plot hid overall outputs above 100% by clipping the display. Agreement with stored outputs is only replay consistency, not physical validation. Recovery percentages and parasitic fractions derived using that recovered heat are therefore unsupported. No replacement calibrated performance claim is supplied.

## Replay

From repository root:

```sh
python3 scripts/generate_readme_figures.py
python3 scripts/audit_dem_figures.py
python3 patent_drawings/generate_audited_figures.py
python3 patent_drawings/generate_fig07_rung5_progression.py
python3 patent_drawings/generate_fig02_fig04.py --fig04-only
python3 -m unittest discover -s tests -v
```

SVG/PDF pairs were regenerated together. FIG. 2 artifacts were preserved, since its schematic needs no numerical correction. FIG. 1's caption was corrected in both existing vector artifacts while preserving its schematic. Source checkpoint arrays were read directly; no GPU simulation or data mutation was needed. The generated FIG. 3 good-variable and FIG. 7 PDFs were rasterized and visually inspected for legible units and correct legend assignment.

The campaign velocity multipliers use an assumed 0.015 m/s reference, not the model-computed minimum-fluidization velocity. At the default model state, U_mf = 0.00567574 m/s; inputs 0.066/0.0525 m/s correspond to actual U/U_mf ≈ 11.6284/9.24989.

Validation environment: Python 3, NumPy 2.4.4, Matplotlib 3.10.9. Figure regeneration and the CPU audit need no GPU or checkpoint mutation.

The final CPU suite passes 25 tests, including plotted units, material legends, source hashes, archive measurements, and thermal invalidity diagnostics.

The obsolete patent docket label was removed from 32 text/source files (48 occurrences), two DOCX files (8 occurrences), and three PDFs (39 occurrences). DOCX XML structure and unchanged ZIP entries were verified; PDF reading-order text across all 37 changed-document pages matches the originals after only the intended label substitutions and whitespace normalization. All 24 repository PDFs and both DOCX files were scanned afterward. Unrelated decimal values and checkpoint step identifiers were preserved.
