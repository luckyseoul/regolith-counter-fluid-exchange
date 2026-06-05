# Suggested Independent/Dependent Claims (for utility patent application)
**Internal working draft only — not for direct filing. Aligns with PERRY-RCFX-004 Rev 5.2 and COLD review. Narrows to Option A envelope supported by good-variable real-drag physical-lid GPU DEM.**

## Independent Claim 1 (System + Iron Dual-Role at Low Pressure – Supported Envelope)
A multi-stage counter-current fluidized bed heat recovery system comprising:
a plurality of stages arranged for counter-current flow of a fine granular heat transfer medium and a process gas;
iron shot particles disposed within at least one stage, the iron shot particles having a diameter in the range of 1.5 mm to 2.0 mm and serving as both (i) sensible heat storage and transport media and (ii) mechanical agitators that impart momentum to the fine granular medium via collisions;
a distributor configured to introduce the process gas at a superficial velocity in the range of approximately 2.5–3.5 m/s or higher (corresponding to an envelope pressure in the range of 0.1–0.5 bar for effective fluidization of the iron shot); and
a physical lid or freeboard structure above the bed that maintains the granular medium in a contained, physically realistic height while permitting the iron shot agitation mechanism to operate.

## Independent Claim 2 (Method – Supported Envelope)
A method of recovering heat in a low-pressure environment, the method comprising:
operating a counter-current multi-stage fluidized bed at an envelope pressure in the range of 0.1–0.5 bar with a superficial gas velocity in the range of approximately 2.5–3.5 m/s (or higher) in cold stages;
introducing iron shot particles of 1.5–2.0 mm diameter at a number fraction of approximately 7% into the bed;
allowing the iron shot to collide with and mobilize cohesive fines under real gas drag, thereby increasing mean bed height, effective heat transfer, and reducing dead zones (as verified by GPU DEM at 1.5 mm iron, 3.5 m/s superficial velocity showing iron mean height 34.47 mm above regolith 11.56 mm, EMI 3.58× vs baseline, 100% containment under physical lid); and
achieving high overall thermal effectiveness while maintaining blower power parasitic within practical limits (as calculated from the supported envelope).

## Dependent Claims (examples, supported by evidence)
- The iron shot diameter is selected from the group consisting of 1.5 mm and 2.0 mm, wherein the agitation effect (reduced dead zone fraction and increased kinetic energy bias in the fine medium) is verified under real gas drag at the supported envelope points (e.g., 1.5 mm iron at 3.5 m/s superficial velocity producing iron mean height 34.47 mm, EMI 3.58× vs no-iron baseline in the good-variable DEM run physical_drag_real_u3.5_iron1.5mm_step002000.npz, 100% inside physical lid).
- The system further comprises a cell-list neighbor search and automated sensitivity runner that enables reproducible exploration of iron size, velocity, and fines parameters at particle counts of 6,500 and higher while preserving 100.0% containment.
- Containment is maintained at 100.0% (all particles with x,y coordinates strictly within the bed domain and z ≥ 0) on every checkpoint generated under the physical lid+freeboard boundary, as verified by direct loading of raw simulation files.
- The system achieves an Effective Mobilization Index (EMI) of at least 3.5× (mean regolith bed height with iron versus identical no-iron control at the same gas flow) at the supported envelope points, sustained under physical lid conditions (verified in the good-variable real-drag DEM at 1.5 mm iron, 3.5 m/s).
- At particle counts of 8,000–10,000, the iron agitation mechanism produces kinetic energy bias exceeding 14,000× to 45,000× (iron versus regolith average KE) while 100.0% containment is preserved via addition of jittered fines to a settled N=6,500 base state followed by relaxation under the same lid and contact physics (supporting scalability of the dual-role concept within the envelope).

(Additional dependents on EDS, pre-class, distributor design, velocity multiples 3.5–6.5×, etc., per the full claim matrix in COLD_CLAIMS_AND_MATH_REVIEW.md and the specification support matrix.)

**Note**: These are drafting suggestions derived from the evidence. Final claims should be prepared by qualified counsel after review of the complete file history and any prior art. All numbers are directly supported by the cited raw .npz and the reproducible runner.