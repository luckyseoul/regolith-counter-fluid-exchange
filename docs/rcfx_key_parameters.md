# RCFX Key Quantitative Parameters (Extracted from Rev 5.2)

## Core Performance Targets
- Thermal recovery efficiency: >70% (design target 80-90%)
- Pilot throughput: 50-100 kg/hr
- Parasitic power: 80-250 W total (goal <2% of recovered sensible heat)
- Number of stages: 5 (optimized)
- Temperature step per stage: ~140 K
- Operating temperature range in RCFX: 200-900 K

## Pressure Envelope (The Central Trade)
- Nominal operating pressure: 0.2 - 0.3 bar
- Design range: 0.1 - 0.5 bar
- Pre-charge gas: ~0.1 kg He or H2
- Self-sustaining gas inventory at 0.2 bar: ~15 grams (envelope volume ~0.2 m³ at 600 K avg)
- Gas generation rate (100 kg/hr): 20-30 g/hr total volatiles
- Gas leakage rate: ~0.4 g/hr (conservative)
- Generation-to-loss ratio: >50:1

## Regolith Properties (Lunar reference)
- Median particle diameter: 60-80 µm
- Bulk density: ~3100 kg/m³
- Specific heat: 800 J/kg/K (range 700-900)
- PSD (mass fractions):
  - <20 µm: 10-20%
  - 20-50 µm: 15-25%
  - 50-100 µm: 15-25%
  - 100-250 µm: 20-30%
  - 250-500 µm: 10-15%
  - >500 µm: small
- Cohesive fraction (Geldart C): significant below ~40-50 µm
- Entrainment cutoff (0.1 bar, He-dominant, 3×Umf of 200 µm fraction): ~37 µm

## Fluidization & Gas Conditions (at 0.2 bar reference)
- Gas at 0.2 bar, 600 K (He-dominant): density ≈ 0.02 kg/m³, viscosity ≈ 2.5e-5 Pa·s
- Umf examples (Wen-Yu, lunar g, He-dominant):
  - 30 µm: ~0.2 mm/s
  - 70 µm: ~0.9 mm/s
  - 200 µm: ~6 mm/s
- Operating velocity: 3-5 × Umf (for target size fraction ~200 µm)
- Per-stage pressure drop: ~7000 Pa total
  - Distributor (sintered Inconel 625, 20-30 µm pores, 3-5 mm thick): ~6300 Pa (dominant)
  - Bed: ~400 Pa
- Superficial velocity example: ~18 mm/s (0.1 m² cross-section per stage)

## Iron Shot Thermal Mass
- Size: 1-5 mm diameter spheres
- Initial seed stock: 50 kg (Earth-supplied, optimized 40-50 HRC)
- Annual consumption (100 kg/hr, pure iron): 26-53 kg/year
- In-situ hardening: CO carburization → surface 800-1000 HV (cementite)
- Functions: thermal buffer, agglomerate breaker, abrasion distributor, wear uniformizer

## Blower & Circulation
- 5 stages in parallel → blower only fights single-stage ΔP (~7000 Pa)
- Primary blower power: 70-150 W (ideal ~63 W at 70% efficiency for baseline)
- N+1 redundancy (primary + standby)
- Thermosiphon effect: negligible at these densities (5 orders of magnitude too weak)

## EDS (Electrodynamic Dust Shield)
- 8 m² total electrode area
- Operating voltage: 1-4 kV (must be validated vs Paschen at 0.2 bar + specific gas)
- Power: 5-15 W total (1-5 W per m² protected)
- High-purity alumina (>99.9%, no transition metals) for dielectric stability at 1000 K

## Fines Management (Section 5.8)
- Entrainment cutoff ~37 µm at baseline conditions
- Three approaches (used in combination):
  1. Cyclones (primary)
  2. Optional pre-classification (sieve upstream, removes <40-50 µm Geldart C)
  3. Acceptance of some fines loss (if economic impact low)

## Key Claims Relevant to Fluid Dynamics Work
- Pressurized envelope (0.05-1.0 bar) using self-generated gases
- Fluidized beds + iron thermal mass + EDS as integrated solution to vacuum + abrasion + electrostatic + cohesion + clogging
- CO-enriched gas for both better fluidization (higher MW) and in-situ iron hardening
- Forced circulation required (natural convection impossible)

Source: PERRY-RCFX-004 Rev 5.2 (full document ingested)
