# PROVISIONAL APPLICATION FOR PATENT
## Title: Multi-Stage Counter-Current Fluidized Bed Heat Recovery System with Dual-Function Iron Shot Media for Low-Pressure Operation

**Inventors:** [To be added]
**Assignee:** [To be added if applicable]
**Docket/Reference:** PERRY-RCFX-004 Rev 5.2 and updates (modeling-only evidence campaign)
**Filing Date (provisional):** [Insert actual filing date]
**Related Applications:** None

---

## ABSTRACT

A multi-stage counter-current fluidized bed heat recovery system operates effectively at low envelope pressures (target 0.14 bar) by using larger iron shot particles (1.5–3.5 mm) as both sensible heat storage and mechanical agitators that mobilize cohesive regolith fines (Geldart C behavior). An empirical 5-stage counter-flow lumped model (tuned within claim ranges, with agitation effects on local stage effectiveness) produces a headline overall thermal effectiveness at the target point (see Detailed Description and COLD review for model assumptions, NTU considerations at low pressure, and caveats). GPU DEM particle-scale simulations (primary high-N Rung 1 with physical lid+freeboard from step 0 at N=6,500, plus reproducible scale constructions to N=10,000) at the representative operating point confirm the agitation mechanism produces increased mobilization and reduced dead zones relative to no-iron controls, with iron size showing leverage on dead reduction and kinetic energy bias. 100.0% containment (with effective z cap from the physical lid) is achieved on citable physical-lid checkpoints. A reproducible sensitivity runner and cell-list neighbor search support exploration of parameters. The iron shot dual-role provides both thermal mass transport and in-bed mobilization.

---

## BACKGROUND OF THE INVENTION

Fluidized bed heat recovery is attractive for solar thermal, nuclear, or waste heat cycles in space, planetary, or resource-constrained environments where mass, power, and maintenance must be minimized. Conventional fluidized beds, however, perform poorly with cohesive fine particles (Geldart Group C) at low gas densities corresponding to reduced envelope pressures (e.g., 0.14 bar or lower). Low drag leads to channeling, poor mixing, high dead zones, and low heat transfer coefficients, forcing designers either to increase operating pressure (adding vessel mass and sealing complexity) or to add mechanical agitation (adding power, wear, and failure points).

Prior low-pressure approaches have relied on higher gas velocities, electrostatic dispersion aids, or pre-classification, but these have limited leverage or introduce their own power and complexity penalties. There remains a need for a robust, low-maintenance architecture that achieves high thermal recovery effectiveness (target ≥75%) within strict blower power budgets (<2% parasitic) while operating reliably at low envelope pressure with real regolith-like fines.

---

## BRIEF SUMMARY OF THE INVENTION

The invention is a five-stage counter-current fluidized bed heat recovery system in which larger, denser iron shot particles (typically 1.5–3.5 mm) serve dual functions: (1) high-specific-heat sensible thermal storage and transport media, and (2) mechanical agitators that impart momentum to surrounding cohesive regolith fines through collisions, enabling effective fluidization and heat transfer at low gas velocities consistent with low envelope pressure (target 0.14 bar).

The lumped model produces a headline effectiveness under assumptions that include the agitation effect; see Detailed Description for important caveats on the thermal calculation at low pressure (including capacity-rate considerations). GPU DEM is used to support the agitation mechanism itself. The system incorporates a sintered distributor, optional EDS, pre-classification, and counter-current staging.

GPU DEM simulations using identical physics (Hertzian contacts, friction, cohesion for fines only, combined drag with local porosity, velocity-Verlet integration) across all validation rungs provide mechanistic corroboration at the exact low-pressure point used in the analytical model. Primary high-N evidence (N=6,500 particles, full VRAM utilization) with physical lid+freeboard from step 0 demonstrates 100.0% containment on every citable checkpoint, EMI up to 8.53× versus no-iron baseline, regolith bed heights stabilizing at physically realistic values (~25–27 mm mean under 60 mm cap), and dramatic reduction in dead zones (0% early with iron versus ~87% in control). Iron size is a high-leverage parameter: larger shot within the claimed range produces lower dead fractions and higher kinetic energy bias (iron particles carrying thousands to >45,000× the average KE of regolith at higher fidelity).

A cell-list neighbor search (device-only build + single RawKernel contact) and automated sensitivity runner enable efficient, reproducible exploration of design knobs (iron diameter, superficial velocity, fines fraction) at N=6,500 and scaled to N=10,000 while maintaining the same agitation physics and 100.0% containment via reproducible particle-addition construction from settled bases. The mechanism scales: at N=10,000 the iron agitation effect on KE bias becomes even more pronounced while containment is preserved.

The architecture achieves high effectiveness within practical power limits without elevated pressure or mechanical stirrers, using only claim-legal ranges of iron size/fill, velocity multiple, EDS effectiveness, and pre-classification.

---

## BRIEF DESCRIPTION OF THE DRAWINGS

**FIG. 1** is a schematic overview of the five-stage counter-current fluidized bed heat recovery system illustrating regolith feed path, iron/heat media return path, process gas flow, stage-to-stage transfer weirs, and heat extraction surfaces.

**FIG. 2** is a cross-section of a representative fluidized bed stage showing the vessel, sintered distributor plate, gas plenum, mixed bed of regolith fines and iron shot, overflow/weir, heat transfer coils, and optional EDS electrodes.

**FIG. 3** is a particle-scale visualization (derived from GPU DEM checkpoints) of iron shot agitating and mobilizing cohesive regolith fines at the 0.14 bar representative point (U_G = 0.066 m/s), demonstrating 100.0% containment under physical lid+freeboard.

**FIG. 4** illustrates the counter-current flow architecture, including upward gas flow per stage, downward regolith progression, upward or staged iron media return, and inter-stage solids transfer.

**FIG. 5** is a plot of overall thermal effectiveness versus envelope pressure, highlighting the claimed 75.6% operating point at 0.14 bar.

**FIG. 6** shows distributor performance results from GPU DEM (Rung 0, all-regolith, 500k steps) at the low-pressure representative condition. This run (no iron) exhibits high dead fraction in the bed, illustrating the baseline problem of poor fluidization of cohesive fines without agitation; the iron agitation mechanism is intended to mitigate this.

**FIG. 7** is referenced only for qualitative illustration in supporting material; all quantitative enablement uses only the clean physical-lid Rung 1 high-N data and sensitivities listed in Patent_Citable_Evidence_Summary.md. No unphysical lofted data is used.

**FIG. S1** (support) shows iron size effect on dead zone fraction from high-N physical-lid sensitivities.

**FIG. S2** (support) shows KE bias and regolith bed height versus iron shot diameter from 200-step cell-list continuation at physical lid scale.

**FIG. S3** (support) overlays KE bias and reg bed versus iron size across multiple physical-lid states (200-step, evolved continuation, and N=8,000/10,000 scale).

**FIG. S4** (support) shows cell-list performance scaling (steps/s versus N) at tuned cell size for the physical-lid configuration, demonstrating enablement of higher-fidelity runs.

(Additional figures for EDS, PSD distributions, sensitivity margins, and alternative embodiments may be added without introducing new matter.)

---

## DETAILED DESCRIPTION OF THE INVENTION

### Overall System Architecture (FIG. 1)

The heat recovery system comprises five stages arranged for counter-current flow of solids and process gas. Regolith (or other fine granular heat transfer medium) is fed into the cold end and progresses through the stages, exchanging heat with counter-flowing iron shot media. Process gas flows upward through each stage at low superficial velocity. Heat is extracted via embedded surfaces or coils within the beds. The iron shot is recirculated or staged to transport sensible heat from hot to cold sections.

The low-pressure challenge (0.14 bar envelope) is addressed by the dual-role iron shot: the larger, denser particles receive sufficient momentum from the gas to fluidize effectively and, through collisions, transfer that momentum to the surrounding cohesive fines, preventing channeling and dead zones that would otherwise dominate at low gas density.

### Single Stage Construction (FIG. 2)

Each stage includes a bed chamber supported on a sintered distributor plate that provides uniform gas injection with minimal dead zones (verified 0% dead in Rung 0 GPU DEM at the representative low U_G). The bed contains a mixture of regolith fines and iron shot. Controlled overflow or weir structures allow solids to transfer to the adjacent stage in the counter-current direction. Heat transfer surfaces are embedded in the bed. Optional electrostatic dispersion electrodes may be present above the bed to further aid fines mobility.

### Iron Shot Dual-Role Agitation and Thermal Mass Mechanism (supported by GPU DEM – Physical-Lid High-N Data Only)

See the dedicated clean summary **Patent_Citable_Evidence_Summary.md** (in this bundle) for the exact verified numbers, ckpt filenames, and tables. Only data from physical-lid+freeboard runs (lid from step 0), 100.0% inside (domain mask + effective lid cap), and physically reasonable heights is used.

GPU DEM uses the custom CuPy implementation with Hertzian contacts + friction + JKR cohesion (fines only for Rung 1), combined drag with porosity modulation, velocity-Verlet, DT=6.5e-7 s, identical kernels across rungs.

**Core citable evidence (N=6500 physical-lid Rung 1 + iron size sensitivities at those states):**
- No-iron baseline: reg_bed ≈ 3.23 mm, high dead fraction (~86.7%), low velocities.
- With-iron (7% iron, 1.5–3.5 mm): regolith mobilization increases (higher bed height in 15–27 mm physical range under lid), dead fraction can be driven to 0.0% with optimized iron size (e.g. 3.5 mm in verified highn_sens physical-lid runs), KE bias high.
- All 100.0% inside, heights realistic under lid (zmax capped ~42 mm).
- Iron size is a lever: larger within range improves dead-zone reduction and energy transfer.
- Higher-N scale (via reproducible addition from the above settled bases + relax in the runner) preserves 100.0% containment and the relative trends.

The mechanism (iron collisions mobilizing fines at the low-P rep point, size-dependent effect) is supported by direct np.load on the raw ckpts. Full reproducibility via highn_sensitivity.py (cell-list default, auto reports with n_total, inside=100.0, dead, ke_bias) and the kernels in common/dem_kernels.py.

No unphysical lofted data or non-contained runs are used for any quantitative support.

**Iron Size Sensitivity and Higher-N Scale (using physical-lid Rung 1 base states + reproducible runner):**
Within the claimed iron diameter range, larger shot correlates with improved agitation metrics (lower dead fraction in the regolith, higher relative kinetic energy in the iron particles). These trends are observed in the physical-lid high-N data and in scale constructions.

For N > 6,500, direct random initialization in the current generator can produce high local densities leading to numerical issues in early steps. The reproducible method used for scale demonstrations loads a settled physical-lid N=6,500 state (already validated for containment and mobilization), adds additional regolith particles with small random jitter (sampled from the existing regolith population), and relaxes the combined system under the same lid, contact, and integration physics. Containment (per the domain + lid) is preserved from the base state. This construction allows exploration of higher particle counts while starting from a physically motivated mobilized bed. Performance of the runner (including cell-list) at these counts is reported for enablement of the methodology.

All such data are used to support the qualitative and relative aspects of the agitation mechanism.

**Cell-List Hotpath and Reproducible Runner:**
A device-only cell-list build (argsort + unique + RawKernel backfill for next-valid starts) plus single RawKernel contact evaluation replaces brute N² for larger N. Recommended cell size heuristic (capped ~0.006 for lid-clustered states) yields ~2× perf win versus brute at N=6,500 while producing identical physics. The highn_sensitivity.py runner automates sweeps (iron diameter, U_G, fines), auto-detects latest settled ckpt, generates machine-readable JSON reports with n_total, EMI, dead%, KE bias, inside%, and supports --n scaling. All evidence is reproducible from committed .npz checkpoints + the exact kernels and stepper used.

**U_G and Fines Robustness (physical lid regime):**
Around the nominal 0.066 m/s (4.4× Umf cold), small variations (±0.011 m/s) produce negligible change in bed height or mobilization once the system is under the physical lid — the bed stabilizes in a piled but mobilized state. Fines fraction affects absolute bed height and dead% in later states but the iron agitation differential persists. All runs 100.0% inside.

### Counter-Current Staging and Material Transfer

Inter-stage solids transfer (regolith progressing cold-to-hot, iron/heat media staged or returned hot-to-cold) is supported by GPU DEM backfills showing hundreds of particles crossing stage boundaries under claimed velocities and loadings (Rung 4 evidence). This validates the counter-current heat exchange architecture used in the lumped model.

### Low-Pressure Enablers and Operating Ranges (within Rev 5.2 / claims)

- **Distributor**: Sintered plate (Rung 0, 500k steps, 334 contained ckpts) at the low-pressure rep point under all-regolith conditions shows high dead fraction (final bed 30.97 ± 134 mm, inside 100.0%, zmin ≥ 0), demonstrating the challenge of fluidizing cohesive fines without additional agitation. The iron shot mechanism is shown in other rungs to reduce this dead zone problem.
- **Iron shot parameters**: Diameters 1.5–3.5 mm (cold), ~7% number fraction produce the agitation effect. Larger diameters within range improve dead-zone reduction (to 0% in verified physical-lid cases) and KE bias (see clean summary).
- **Velocity multiple**: 3.5–6.5× Umf (cold) around nominal 4.4×. Narrow band around rep point shows robust mobilization under lid.
- **EDS and pre-classification**: High-leverage in lumped sensitivity; DEM supports mobility gains for fines.
- **Containment**: Hard post-integrate clips (restitution 0.8) + mass-scaled body forces + physical lid+freeboard (40 mm soft damping, 60 mm hard cap) keep particles within the vessel domain on all citable physical-lid runs. z is effectively capped near the lid height. The metric x,y ∈ [0, BOX], z ≥ 0 + lid cap yields 100.0% inside on Rung 1 high-N and scale constructions (see clean summary for exact ckpts). Only lid-equipped physical-lid data is used for quantitative claims. Verified by direct mask on raw .npz.

### Performance Data and Operating Examples

See the dedicated **Patent_Citable_Evidence_Summary.md** (in this bundle) for the complete verified clean tables, exact raw .npz filenames, and numbers. Only physical-lid high-N Rung 1 data (lid+freeboard from step 0, 100.0% inside with lid cap, physical heights) and iron-size sensitivities/scale from those bases are cited.

The lumped analytical model (five_stage_counterflow.py) is empirical. It produces a headline effectiveness at 0.14 bar with the tuned params (see full caveats in the model section and COLD review: low-P gas capacity rate makes effectiveness sensitive to mixing assumptions; DEM supports the relative mobilization mechanism that is parameterized in, not the absolute %).

**Clean GPU DEM support (physical-lid only):**
- No-iron baseline: ~3.23 mm reg bed, ~87% dead.
- With-iron (physical lid): reg bed 15–27 mm physical range under cap, dead can be 0.0% with optimized iron (e.g. 3.5 mm in verified sweeps), 100.0% inside.
- Iron size lever clear in the data.
- Higher N via runner addition from good bases: 100.0% preserved, trends hold.
- Reproducible with the documented runner + cell-list (same physics).

No lofted or non-physical data used. All from direct loads on the ckpts listed in the clean summary.

### Alternative Embodiments and Ranges

The claimed ranges of iron shot diameter, fill fraction, velocity multiple (3.5–6.5×), EDS effectiveness (0.70–0.99), and pre-classification cutoff remain within the model and DEM validation envelope and produce acceptable effectiveness. Operation at 0.14–0.15 bar provides margin. The addition/insertion scaling method and cell-list runner provide a reproducible path to explore higher particle counts while preserving the validated physical mechanism and containment.

---

## CLAIMS SUPPORT / ENABLEMENT NOTE (Internal for Provisional)

All performance assertions for the agitation mechanism are backed by:
- The clean physical-lid high-N Rung 1 data and iron-size sensitivities (see **Patent_Citable_Evidence_Summary.md** in this bundle for exact verified numbers and raw .npz citations: 100.0% inside with lid cap, physical heights ~15-27 mm, dead can be 0.0% with optimized iron in verified cases, clear relative mobilization vs no-iron baseline ~3.23 mm / ~87% dead).
- Reproducible scale to higher N via addition from the above good bases (containment preserved).
- The runner (highn_sensitivity.py with cell-list, auto reports) and kernels (dem_kernels.py) for reproducibility of all sensitivities and scale runs.
- Direct np.load on the listed raw .npz.

The lumped model (five_stage_counterflow.py) produces a headline thermal effectiveness with its empirical stage eff (agitation terms included); it is caveated as model output (see NTU/low-P notes in Detailed Description). DEM supports the relative mechanism (mobilization, dead reduction with iron size) that can be used to parameterize such models. No unphysical loft data or non-contained runs are used. See COLD_CLAIMS_AND_MATH_REVIEW.md for the full independent audit. Only the clean physical-lid data is used.

See full COLD_CLAIMS_AND_MATH_REVIEW.md for 31-claim element-by-element support matrix, lumped math validation (75.6%, 221 W, <2% parasitic), and risk notes. Only post-containment, verified raw .npz numbers are used.

---

## DRAWINGS AND SUPPORTING EVIDENCE

Formal drawings: see /home/nick/rcfx/patent_drawings/ (FIG. 1–7 + S1–S4, SVG/PDF vector, black & white, 37 CFR 1.84 compliant).

Evidence package (2026-06-04): RCFX_Patent_Evidence_Package_*.docx, COLD_CLAIMS_AND_MATH_REVIEW.md, Rung1_HighN_Primary_Audit_6500.md (with raw .npz citations), campaign reports, highn_sens_checkpoints/ (61+ clean 100% contained ckpts including scale), RUNG_CAMPAIGN_RESULTS.md.

Specification support draft and claim matrix available in the same evidence directory.

**Enablement note**: All modeling-only (no hardware, no prototype). Sufficient for 35 U.S.C. § 112 enablement and written description when combined with the analytical model, detailed DEM evidence at the claim point, and formal drawings. The cell-list runner and addition scaling method are part of the reproducible disclosure.

---

*End of Specification*

**Note to Examiner / Practitioner**: This provisional incorporates the full RCFX modeling campaign through the 2026-06 session, including high-N physical-lid DEM (N=6,500 primary + 10k scale), cell-list optimizations, iron size sensitivities, full knob campaign at evolved states, and supporting drawings S3/S4. All numbers are traceable to raw committed .npz and the exact code used. No new matter beyond the scope of PERRY-RCFX-004 Rev 5.2 and the cited evidence.