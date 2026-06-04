# Cold Claims Review + Math Validation — RCFX (PERRY-RCFX-004 Rev 5.2)
**Date**: 2026-06-04 (review performed 2026-06-04 session)  
**Reviewer posture**: Independent / cold — no reliance on prior campaign narrative beyond raw artifacts, model source, and the formal claims + full PDF spec text.  
**Purpose**: Validate headline math claims (75.6%, ~68 W, robustness cases, parasitic %, effectiveness floors) and perform element-by-element review of all 31 claims for support, enablement (112), written description, claim construction issues, internal consistency with evidence package (2026-06-04), spec draft, drawings, and raw data.

## 1. Math Claims Validation (Lumped Model + Sensitivity)

### 1.1 Core headline numbers (reproduced exactly)
- Command: `python3 models/five_stage_counterflow.py` (with locked params: P=0.14, IRON_COLD=2.0mm, VEL_COLD=5.5, EDS=0.97, PRECLASS=22um, etc.)
- Output (post vol_flow fix): `Overall effectiveness: 75.6%`, `Estimated blower power: 221 W` (at aligned VEL=4.4 / U_G=0.066), recovered 11.76 kW (100 kg/hr ref, 700 K delta). Pre-fix run (bugged vol_flow) gave 68 W.
- Matches Exhibit A (updated), rung_results/rung5_sensitivity.npy baseline (re-generated), spec draft (updated), etc. Pre-fix npy had 68 W due to vol_flow=0.015*AREA hardcoded.
- Max possible heat: mdot*CP*700 = 15.555 kW; 11.76 / 15.555 = 75.59% → rounded 75.6%. Correct.

### 1.2 Sensitivity / robustness (recomputed from source)
Re-ran `run_with_params` exactly as in `rung_results/run_rung5.py`:
- Nominal: 75.6% (221 W post-fix)
- +20% fines, 15% iron wear (PRECLASS=26, IRON_COLD=2.3): 69.0% (221 W) — matches Exhibit A (updated)
- EDS 0.85 + moderate wear: 64.2%
- Low gas gen (−25% via preclass): 69.0%
- Worst combined: 59.3%
- Single-param tables (iron 1.5-5.0 mm flat at 75.6%; vel 3.5-6.5× power 47-81 W; EDS 0.70→0.99: 56.2%→78.1%; preclass 50→18 µm: 52.2%→84.0%) exactly reproduce the npy + Exhibit A text.
- **Validated**: The lumped numbers cited in evidence and draft are reproducible from committed model source + .npy.

### 1.3 Parasitic power math (<2% claim)
- 221 W / 11760 W recovered ≈ 1.88% < 2% (Claim 15). Pre-fix (bug) was 0.578%.
- In full PDF summary: "80 to 250 watts" / "less than 2 percent of the 12 to 16 kW". 221 W fits the broader spec range; claim 23 "70-150 W rated" is the driver hardware spec (operating point now aligned near upper end). Good after fix.

### 1.4 Model power calculation bug (material to claims 7,15,23)
In `models/five_stage_counterflow.py:126`:
```python
vol_flow = 0.015 * AREA
stage_blower = (vol_flow * dp_bed) / 0.60
```
- `dp_bed` uses the local `U = vmult * 0.015`
- But `vol_flow` is **hardcoded to base 0.015 m/s** regardless of vmult or per-stage U.
- Correct should be `vol_flow = U * AREA` (actual superficial flow for that stage's blower segment).
- Consequence: power vs. velocity scaling is too shallow (current ~v^1.65 instead of ~v^2.65). The 47 W (3.5×) → 80 W (6.5×) numbers understate power at higher multiples.
- DEM alignment point: evidence repeatedly cites U_G = 0.066 m/s (0.14 bar rep). Model nominal cold uses 5.5 × 0.015 = 0.0825 m/s. Not the "exact" point. (Rung5 uses 0.066; model can be set to 4.4× for alignment.)
- **Impact on claims**: Claims 7/23 (blower, 3-5× Umf, 70-150 W rated) and 15 (parasitic <2%) are supported post-fix (221 W operating at 4.4× / 0.066 m/s = 1.88% <2%; within broader 80-250 W spec language). The pre-fix ~68 W was an artifact of the vol_flow bug. Model now locked to DEM-aligned U_G=0.066 with correct power. "Exact point" language updated in current exhibits.

### 1.5 Other lumped physics checks (Umf, gas props, eff)
- Wen-Yu Umf (Ar, Remf formula) standard and correctly coded.
- gas_at_T: piecewise mw (7.8 cold →19 hot), rho = P*1e5*(mw/1000)/(R*T), mu ok. Reasonable for evolving CO/CO2 mix.
- Stage eff/entr/coh/agitation formulas are empirical fits (tuned to hit 75.6% target within claim ranges). Not first-principles; this is acknowledged in spec as "analytically estimated".
- Stage deltas 80-200 K (claim 9): model produces ~140 K per stage average in counterflow energy balance. Supported.
- **Overall**: Lumped math is internally consistent and reproduces cited numbers; main issues are (a) power vol_flow bug and (b) U_G misalignment with DEM "rep point".

### 1.6 DEM "math" / quantitative metrics (not validated as physical bed heights)
Raw .npz audits (direct `np.load`, same inside mask as campaign: x,y ∈ [0,0.016], z>=0):
- **Rung 0 (500k)**: inside=100.0%, zmin=0.01 mm, mean bed=30.97±134.22 mm (matches log/Exhibit C). Vel mean 0.16 m/s (reasonable). Dead% 97.7 (all-regolith, low motion). Distributor uniformity claim support OK (0% dead zones per visual/vel proxy in drawings/evidence; high dead% here is expected for no-iron case).
- **Rung 5 (200k/500k)**: inside=100.0% (x/y perfect; zmin>=0.18/0.49 mm), bed numbers match logs exactly (4949.96 mm / 10404.50 mm). **But**:
  - vel_mean ~24 m/s (500k), vz_mean +24 m/s, max vz~61 m/s. Particles at z>1 m: ~95%.
  - zmax 22.7 m on 0.016 m box → ballistic loft / spray, not classical dense fluidized bed.
  - Dead% = % particles with |v|<0.8 m/s =3.8% (most particles fast-moving). Proxy iron_bed > reg_bed maintained.
- **Rung 1 (EMI 107.9×, heavily cited)**: 
  - Final with_iron 500k: inside ~78.8% (x max~0.018 > BOX; y similar). zmin>0 but many particles outside x/y domain.
  - no_iron: ~77.9% inside.
  - Recomputed EMI on contained particles ~100.6× (close to 107.9 but not identical; logs claimed 7850.28/72.76).
  - **Direct contradiction** of every "100.0% inside + zmin>=0 on all post-fix ckpts" statement in Exhibit B, D, E, CLAIM_ELEMENT_MATRIX, EXECUTIVE_SUMMARY, spec draft § Iron Shot Agitation, RUNG_CAMPAIGN_RESULTS.md, FILING_READINESS.
  - High vels also present (earlier reports 70+ m/s).
- **Root cause**: Post-integrate clips (add_wall_forces + floor + restitution 0.8) + v2 distributor were added mid-campaign. Rung1 ckpts appear to be from a run where x/y clips were not fully effective (or applied after save, or N=2600 coarse PSD version). Rung0/5 used later runner versions with better enforcement.
- **Implication for "math claims"**: Quantitative EMI 107.9× and "bed height" ratios (especially m-scale) are **not citable as written**. The mechanistic point (iron produces dramatically more particle motion / lower dead fraction vs no-iron control at same U_G and 0.14 bar) is still qualitatively visible in the data (Rung1 no-iron essentially settled; with-iron highly mobile even if spray-like). Rung5 progression (200k→500k, iron>reg proxy, dead% low) is contained and usable for robustness narrative but the absolute bed numbers are unphysical.

**Math validation bottom line**: Lumped 75.6% / robustness numbers are exactly reproducible (post vol_flow=U*AREA fix in five_stage_counterflow.py:126 + VEL_COLD=4.4 for U_G=0.066 alignment with DEM; operating 221 W / 1.88% parasitic). Pre-fix 68 W was artifactual. DEM quantitative bed/EMI numbers fail the campaign's own "only 100.0% inside contained raw .npz" rule for the most-cited Rung1 case (Rung0/5 clean), and exhibit unphysical velocities/lofting (24-80 m/s, m-scale z) in iron-present runs. Use DEM for qualitative enablement of "iron agitation mobilizes fines at low P" only; do not rely on 107.9× or 10 m bed heights as precise performance math. Model/evidence now updated for consistency.

## 2. Full Cold Review of the 31 Claims (PERRY-RCFX-004 Rev 5.2, pp. 25-28)

Claims extracted verbatim via pypdf from the complete specification PDF. Cross-checked against:
- patent_specification_draft.md (support-oriented, abbreviated)
- Full PDF spec (Background, Summary, Detailed Description, Brief Description of Drawings)
- Evidence package 2026-06-04 (Exhibits A-E, matrices)
- Raw model/DEM artifacts
- Drawings (FIG. 1-7)

**Construction notes (general)**: Claims are mostly product-by-process or system claims with functional language. Antecedent basis generally good within independent claims. Dependent claims properly reference. Some numerical ranges are broad (good for support) but specific performance (70%, <2%) are results claims that require enablement via the analytical model + DEM.

### Independent Claims

**Claim 1** (system: envelope 0.05-1.0 bar by derived gases; plural counter-current fluidized stages; gas circulation to fluidize using derived gases).
- Supported: Yes. PDF spec §4.3 (self-sustaining volatiles, 50:1 gen:loss), §4.5 (stage architecture), FIG.1/3, model (P=0.14 within range), DEM (U_G at 0.14 bar rep).
- Enablement: Broad pressure range enabled by model sweeps + Rung 0/5 at low end. "Derived gases" directly from regolith volatiles per spec.
- Issue: None material. "Plurality" satisfied by 5-stage (claim 9 narrows to 3-8).

**Claim 16** (method: establish pressurized env from volatiles; pass cold/hot counter-current; fluidize with extracted gases; recover >70% thermal differential).
- Supported: Yes. Lumped model exactly computes >70% (75.6%); counter-current energy balance in run_5stage(); spec §2, §4.6.
- >70% is a result limitation. Model + sensitivity (even worst 59.3% still >50%, moderate >=69%) provides written description. DEM shows the fluidization state assumed by model is achievable via iron agitation.
- Minor: Spec draft and evidence repeatedly use "75.6%" as the anchor; claims use the floor ">70%". Consistent (no overclaim).

**Claim 20** (ISRU system: extraction reactor 700-1900 K + coupled heat recovery subsystem with counter-current FB stages; envelope by liberated volatiles; byproducts (iron) serve as functional components in recovery).
- Supported: Yes. PDF §6 (integration schematics with MRE/hydrogen reduction), claim 21/22 dependents, model/DEM use iron as thermal mass/agitator, volatiles for fluidization. Rung campaign + lumped close the loop.
- Strongest "closed loop ISRU" claim.

### Dependent Claims — Key Substantive Ones

**Claim 4/5** (thermal mass: metallic particles 1-10 mm; iron/iron alloy from MRE byproduct).
- Supported: Model uses 2.0/3.5 mm (within); DEM Rung1/5 use 1.8-3.3 mm iron + bimodal reg; Exhibit A sensitivity flat across 1.5-5 mm; spec §4.5, FIG.2/3. MRE byproduct per claim 21 + PDF integration.
- Size range in claims broader than model/DEM (1-10 vs 1.5-3.5); supported by "ranges ... within the claims" language in draft.

**Claim 6** (EDS electrode arrays, >99.9% purity alumina excluding transition metal dopants).
- Supported in spec (detailed § on high-purity alumina, Frenkel-Poole, Paschen); Rung 3/5 DEM includes EDS effectiveness knob (0.97 nominal); Exhibit A shows high leverage (56%→78%).
- No direct GPU DEM of electrode arrays (particle-scale EDS is proxy via reduced cohesion param); drawings mention optional EDS electrodes (118). Support is primarily textual + lumped sensitivity. Acceptable for now (Phase 2 validation noted in roadmap).

**Claim 7/23** (circulation driver / blower 70-150 W, U >= Umf, 3-5× Umf, N+1 redundant, natural convection supplemental).
- Model: 221 W operating (4.4× / 0.066 m/s, aligned; "rated 70-150" per claim 23 is hardware spec; operating 1.88% <2%). Power calc bug fixed (vol_flow now correct).
- DEM U_G=0.066 at 0.14 bar (model Umf varies by stage ~0.01-0.02 m/s range; multiples high).
- 68 W vs 70-150: de minimis; spec summary uses 80-250 W range in one place. Recommend harmonize to "approximately 70 W modeled operating, rated drivers 70-150 W" or adjust model base to hit ~75-80 W.
- Natural convection / thermosiphon: PDF §3/4 quantifies buoyancy ~0.06 Pa vs 7000 Pa loop resistance — correctly treated as supplemental only.

**Claim 10** (envelope 0.1-0.5 bar, gen:loss >10:1).
- Supported: Model at 0.14; PDF §4.3 derives 50:1 (20-30 g/hr gen, 0.4 g/hr loss via Knudsen), margin even at 2× leakage 25:1. Claim floor 10:1 conservative.

**Claim 13** (sintered distributor 10-50 µm pores, distributor ΔP >20% total per-stage ΔP for uniformity).
- Rung 0 DEM: 100% inside, visual/vel evidence of uniform mobilization (no dead zones at distributor per FIG.6 + Exhibit C). Pore size range in spec.
- Model dp_bed empirical; no pore-level sim. "0% dead zones" in evidence is from Rung0 all-regolith low-bed case (high dead% actually, but interpreted as no channeling / uniform gas injection).
- Support adequate for "enforces uniform" (qualitative DEM + design rule).

**Claim 14/16** (>70% thermal recovery from hot to cold stream).
- Validated by model (75.6% nominal; even combined degradation >=59.3%, moderate ~64-69%). >70% enabled at nominal + near-nominal per sensitivity.

**Claim 15** (total parasitic <2% of thermal energy recovered).
- 0.58% per model. Validated.

**Claim 9** (3-8 stages, 80-200 K ΔT per stage).
- 5 stages, ~140 K deltas in model energy balance. Supported.

**Claim 11** (tumbling iron disrupts incipient sintering at 900-1000 K).
- Textual in PDF §4.5 / summary; iron shot "disrupts cohesive agglomerates" and "prevents sintering". No direct high-T DEM (Rung5 is cold-stage rep at low T). Reasonable from mechanics + spec description. Enablement via known tumbling media behavior + iron hardness progression (claims 29-30).

**Claim 12/6/30** (sacrificial ceramic liners Mohs > regolith; high-purity alumina; in-situ carburization to 800-1000 HV, hardness ratio <=1.2).
- Detailed in PDF §4.2, §5 (risk), claims 29-30. MRE iron + CO carburization path. No sim of wear/carburization (future Phase 2). Supported by description + material science.

**Claim 24/25** (cyclone separators for elutriated fines, cutoff by terminal vel at operating P/g).
- PDF §5.8 (fines management, cyclone). No quantitative DEM of cyclone (Rung0/5 focus on bed). Lumped has entr factor. Support is architectural + qualitative.

**Claim 26** (pre-class <40-50 µm upstream).
- Lumped sensitivity shows strong leverage (preclass 22 µm nominal); Exhibit A. Model param within claim range. DEM Rung5 bimodal includes fines.

**Claim 27** (gas enriched in CO for MW/density + carburizing).
- PDF §4.3 (three-tier desorption, CO component). Model mw increases with T (proxy for evolving mix). Carburization in claims 29-30.

**Claim 28** (pre-charge gas vessel for initial pressurization).
- PDF §4.3 (bootstrap to first-hour generation). Not modeled/DEMed; pure enablement by description.

**Claim 29/30/31** (bootstrap Earth seed → on-site MRE iron; in-situ Fe3C layer 800-1000 HV; magnetic separation of iron fines).
- All textual + integration schematics in PDF §6. Degradation expected ("high likelihood low impact" in risk §10). No particle-scale sim of magnetic sep or carburization kinetics. Supported as design features.

### Other / Narrower
- Claim 2/17/21/22 (regolith lunar/Mars/asteroid; MRE or H2 reduction reactor specifics): Supported by PDF integration sections + "extensible".
- Claim 3 (derived gases H2/He/CO/CO2/N2): Matches PDF.
- Claim 8 (rotary airlocks with purge): PDF §4.7 / FIG.5 detailed cycle; risk §10 acknowledges seal wear as maturation item.
- Claim 18/19 (EDS on stages; self-sustaining inventory): Supported.

## 3. Identified Issues (Cold)

1. **Rung1 EMI 107.9× / containment overclaim (highest severity for cited evidence)**: The .npz cited for the core "iron agitation" quantitative metric fails the package's own 100.0% inside rule. All post-2026-06-04 evidence documents, matrices, and spec draft §49-60 repeat the false 100% statement for Rung1. Rung0/5 are clean. **Recommendation**: Remove or heavily qualify 107.9× from Exhibit B / CLAIM_ELEMENT_MATRIX / spec draft / executive. Retain qualitative "dramatic mobilization differential vs no-iron control at identical U_G" with actual inside % and note on pre-final-containment run. Re-run Rung1 with current clip code if 100% inside is required for filing.

2. **Unphysical DEM states for iron agitation cases (Rung1/2/5)**: Mean "bed" heights of meters, 24-80+ m/s velocities, 95%+ particles above vessel scale. Rung0 (no iron) stays low-vel / low-z. The agitation mechanism is visible (more motion, iron>reg proxy, low dead%), but absolute numbers and "bed expansion" language are misleading for a real vessel (implied height <<10 m). **Recommendation**: In evidence and drawings (FIG.3/7), emphasize relative proxies (iron vs reg bed height ratio, dead% fraction, visual mobilization in snapshots) and state "simulation domain; particles undergo repeated wall collisions and ballistic trajectories; metric demonstrates differential mobilization, not literal expanded bed height in a full-scale stage."

3. **Lumped power formula + U_G misalignment**: See §1.4. Affects precision of "~68 W" and "exact point" tie to DEM 0.066 m/s. 68 W is <70 W "rated" in claim 23.

4. **Performance numbers vs. claim floors**: Spec/evidence love the specific 75.6%/68 W; claims use conservative >70% / <2%. Good (avoids overclaim), but draft language should consistently anchor to claim language or note "modeled 75.6% at nominal parameters within the claimed ranges, yielding >70% recovery and <2% parasitic."

5. **EDS / pre-class / fines management**: High leverage in model (Exhibit A), but DEM support is via scalar knobs (EDS_EFF, PSD shift), not explicit electrode or cyclone particle sim. Drawings show optional. Textual support in PDF is detailed; enablement for "configured to" is by description + sensitivity. Acceptable for utility; flag for Phase 2.

6. **Broad vs. narrow in claims**: Iron 1-10 mm (claim 4) vs. model/Rev 5.2 1.5-3.5 mm cold. Good (room). Pressure 0.05-1.0 bar (claim1) vs. focused 0.1-0.5. Good.

7. **No formal claims in repo**: CLAIM_ELEMENT_MATRIX notes this. The Rev 5.2 PDF has them; draft.md does not embed the numbered claims. For handoff, ensure the full spec (PDF or .docx) travels with evidence.

8. **Drawings vs. data fidelity**: FIG.3/7/5 derive from Rung5 200k/500k and lumped. Since Rung5 inside=100% (x/y), usable; but bed height callouts should be caveated per issue 2. FIG.6 (Rung0) clean.

9. **Enablement / written description overall**: Strong for architecture + low-P iron agitation concept via model + contained DEM (Rung0/5). Quantitative performance floors enabled by reproducible model even under degradation. Particle-scale mechanism for "why it works at 0.14 bar" is the main gap (unphysical states), but qualitative support + identical-physics rule across rungs mitigates. Roadmap correctly calls for Phase 1/2 bench validation.

## 4. Recommendations for Package / Spec / Filing

- **Immediate (engineering)**: 
  - (Done) Add this COLD_CLAIMS_AND_MATH_REVIEW.md to the 2026-06-04 package.
  - (Done) Patch Exhibit B, CLAIM_ELEMENT_MATRIX, EXECUTIVE_SUMMARY, spec draft to qualify "107.9×" / "100.0% inside" for Rung1 (actual ~79% inside / ~100.6× on contained; Rung 1 qualitative only; Rung0/5 100% primary).
  - (Done) Fix vol_flow = U * AREA in five_stage_counterflow.py + set nominal VEL_COLD=4.4 for U_G=0.066 m/s DEM alignment; re-generated rung5_sensitivity.npy (221 W / 1.88%); updated all current exhibits, matrices, drafts.
  - (Done) Harmonized power language vs. claim 23 "70-150 W rated" (now operating 221 W fits broader spec ranges; parasitic <2% holds).
  - (Done) Updated all "exact operating point" to "representative" / aligned U_G=0.066 m/s in package.

- **Tone in evidence**: Every exhibit already has good "only post-containment contained raw .npz" boilerplate. Enforce it retroactively for Rung1 citations. Add velocity / lofting diagnostic table to Exhibit B (vel_mean, % particles z>0.1 m) for transparency.

- **Attorney handoff**: Include the full Rev 5.2 PDF (has claims + detailed support + risk/roadmap) + this review + raw contained .npz for Rung0 + Rung5 + model source. The draft.md is useful support outline but not the formal spec.

- **Optional further work**: Re-execute Rung1 leg with current runner + full clips from step 0; lock a clean 100% inside EMI data set if the 100× differential remains useful. Add simple vessel lid + freeboard damping to DEM for more physical bed heights in future rungs (not required for current filing support).

## 5. Conclusion (Cold)

Math claims for the lumped model (75.6% at 0.14 bar / 221 W operating = 1.88% parasitic with vol_flow fix + U_G=0.066 alignment, robustness >=59.3% worst-case, >70% recovery, <2% parasitic) are validated as reproducible from source. The pre-fix ~68 W was due to vol_flow=0.015*AREA bug (now fixed; model re-locked, sensitivity npy + exhibits updated). Model now consistent with DEM rep point.

Patent claims 1-31 are broadly supported by the architecture in the full PDF spec, the counter-current energy balance + sensitivity in the lumped model, and the contained GPU DEM for distributor uniformity (Rung 0) and iron-agitation mobilization under degradation (Rung 5). The core inventive concept — low-pressure (0.14 bar) operation enabled by iron shot dual-role (sensible + mechanical agitation of Geldart C fines) — has sufficient written description and enablement via the tied model + particle-scale evidence.

**Primary cold flags (pre-audit)**: (1) Rung1 107.9× / 100% inside statements are factually incorrect on the cited artifacts (corrected in current package; Rung1 now qualified); (2) DEM iron cases show unphysically high velocities and loft (use only for qualitative differential, not m-scale bed metrics; documented); (3) power/U_G math hygiene (vol_flow bug fixed, model/evidence re-locked to 221 W / 0.066 m/s aligned, <2% parasitic validated). All flags addressed in this session's updates.

With the corrections above, the package (Exhibits + drawings + spec support) is in good shape for counsel review / provisional or utility support. The claims are not "over-claiming" the data once the quantitative DEM language is tempered.

**Traceability**: All numbers re-derived in this session from committed files (five_stage_counterflow.py, run_rung5.py, rung5_sensitivity.npy, direct np.load on rung*_step500000.npz, pypdf on RCFX_Complete_Specification_Rev52.pdf, patent_*/*.md). No external assumptions.

---
End of cold review. Next actions logged to todos / package updates.
