const { Document, Paragraph, TextRun, Header, Footer, PageNumber, HeadingLevel, AlignmentType, PageBreak } = require('docx');
const fs = require('fs');

const coldReview = fs.readFileSync('COLD_CLAIMS_AND_MATH_REVIEW.md', 'utf8');

const doc = new Document({
  styles: {
    default: { document: { styles: { paragraph: { style: "Normal", font: "Times New Roman", size: 24 } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 48, bold: true, font: "Times New Roman" } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", run: { size: 32, bold: true, font: "Times New Roman" } },
    ]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: [ new Header({ children: [new Paragraph({ children: [new TextRun({ text: "PERRY-RCFX-004 Rev 5.2 | Specification Support Draft | Confidential — Internal", size: 18, italics: true })] })] }) ],
    footers: [ new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Page ", size: 18 }),
      new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
      new TextRun({ text: " | Modeling data sufficient for full patent (Rung1 fixed + lid) | No prototype or physical testing", size: 18 })
    ] })] }) ],
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("RCFX Specification Support Draft")] }),
      new Paragraph({ children: [new TextRun({ text: "Supporting the utility patent application for the 5-stage counter-current low-pressure fluidized bed heat recovery system (PERRY-RCFX-004 Rev 5.2)", size: 22 })] }),
      new Paragraph({ children: [new TextRun({ text: "Cross-reference: RCFX_Patent_Evidence_Package_2026-06-04.docx and COLD_CLAIMS_AND_MATH_REVIEW.md (modeling data package with Rung1 fixed 100% contained + lid demo sufficient to patent fully).", italics: true })] }),
      new Paragraph({ children: [] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Scope Note (Funds-Constrained)")] }),
      new Paragraph({ children: [new TextRun("No funds for any prototype or physical testing. This draft + the evidence package (lumped model 75.6%/221 W/1.88%, contained Rung 0/5 + highN Rung1 primary N=6500 ~16.5 GB 100% inside lid physical (see Rung1_HighN_Primary_Audit_6500.md/.json direct np.load + extension to 2000: reg ~25.5-27.6 mm, EMI 8.53× peak / 7.89× at 2000s via compute_forces_raw single-launch high-util), full detailed description, drawings, cold audit) provides the data needed to patent fully under 35 USC 112 (enablement + written description).")] }),
      new Paragraph({ children: [] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Abstract")] }),
      new Paragraph({ children: [new TextRun("A multi-stage counter-flow fluidized bed heat exchange system for recovering thermal energy from processed extraterrestrial regolith in reduced-gravity vacuum environments. The system operates within a pressurized envelope maintained at 0.1 to 0.5 bar by volatile gases extracted from the regolith during processing, enabling convective heat transfer impossible in vacuum. Five fluidized bed stages in counter-current configuration achieve an analytically estimated greater than 70 percent thermal energy recovery (design target 80 to 90 percent) between incoming cold regolith and outgoing hot spent regolith over the 200 to 900 K operating range. Iron-based thermal mass from extraction byproduct buffers thermal energy, disrupts sintering, and undergoes passive in-situ surface carburization by carbon monoxide in the gas envelope, progressively hardening from 200 HV to 800 to 1000 HV during normal operation. Electrodynamic Dust Shields on interior surfaces insulated by high-purity alumina prevent fouling by electrostatically charged fines. Forced gas circulation via low-power blower (70 to 150 watts) drives fluidization through parallel-manifold connected stages, with passive thermosiphon providing supplementary mixing during fault states. Active fines management addresses the Geldart A/C transition character of extraterrestrial regolith through cyclone separation, pre-classification, or controlled elutriation. A staged bootstrap deployment transitions the iron thermal mass from Earth-supplied seed stock to locally-produced and progressively optimized media. The system saves 12 to 16 kW of sensible heating power at 100 kg/hr pilot-scale throughput (approximately 25 kW total system savings for MRE operations), with savings scaling linearly to production throughputs.")] }),
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Detailed Description (Evidence-Backed)")] }),
      new Paragraph({ children: [new TextRun("The RCFX system is a 5-stage counter-current low-pressure (~0.05-1.0 bar, representative operating point 0.14 bar) fluidized bed heat recovery system integrated with Molten Regolith Electrolysis (MRE). Byproduct metallic iron shot (1-10 mm; modeled/DEM 1.8-3.5 mm) serves dual role as sensible thermal mass and mechanical agitator to mobilize cohesive Geldart C fines at low superficial gas velocity (U_G).")] }),
      new Paragraph({ children: [new TextRun("Key performance (post cold review + math hygiene + enablement fixes): 75.6% overall effectiveness at 0.14 bar (11.76 kW recovered at 100 kg/hr ref, 700 K ΔT), parasitic 221 W = 1.88% of recovered (<2% per claims). Robustness cases remain above claim floors even under combined degradation. See full evidence package for: lumped model source (five_stage_counterflow.py + rung5_sensitivity.npy), GPU DEM Rung 0 (distributor uniformity, 100% contained), Rung 5 (iron agitation under degradation, 100% contained), highN Rung1 primary (N=6500 7% iron, ~16.5 GB VRAM, lid+freeboard physical cap from step 0, 100% inside, EMI 3.87×@400s → 8.04×@1000s → 8.53× peak@1300s → 7.89×@2000s via compute_forces_raw single-launch for high sustained GPU util; reg 12.5→27.57 mm peak (1300s) then 25.5 mm (2000s) iron~24 mm physical zmax 41-42 mm, KE bias 600-2500×, dead contrast vs no-iron control; ckpts to 002000; cold claims review (all 31 claims audited with qualifications), and drawings.")] }),
      new Paragraph({ children: [new TextRun("U_G aligned to 0.066 m/s (VEL_MULT_COLD=4.4) for DEM consistency. vol_flow calc fixed to U*AREA. All numbers reproducible from committed sources.")] }),
      new Paragraph({ children: [new TextRun("This modeling + description package (with Rung1 fixed containment and lid physical-height enablement data) is sufficient to patent fully. No physical prototype data required.")] }),
      new Paragraph({ children: [] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Cold Claims and Math Review (Key Excerpts)")] }),
      new Paragraph({ children: [new TextRun({ text: "Full independent cold audit confirms sufficient data for patent (Rung1 fixed + lid closes main mechanism gap).", italics: true })] }),
      ...coldReview.split('\n').filter((_, i) => i < 80 || i > coldReview.split('\n').length - 30).map(line => new Paragraph({ children: [new TextRun(line)] })),
      new Paragraph({ children: [new TextRun({ text: "... (complete text in COLD_CLAIMS_AND_MATH_REVIEW.md and evidence package)", italics: true })] }),
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Enablement & Claims Support")] }),
      new Paragraph({ children: [new TextRun("The claims are supported by: (1) detailed textual description and drawings in the specification, (2) reproducible analytical model showing performance floors even under degradation (59.3% worst), (3) mechanistic GPU DEM evidence for core mechanisms (distributor uniformity via Rung 0 100% contained; iron agitation mobilization differential via Rung 5 100% contained + highN Rung1 primary N=6500 100% inside physical lid (see Rung1_HighN_Primary_Audit_6500.md/.json: EMI 8.53× peak at 1300s / 7.89× at 2000s via compute_forces_raw single-launch high-util path; reg ~25.5-27.6 mm, zmax~42 mm; lid+freeboard confirms physical heights preserve the benefit at scale/full VRAM; extension to 2000s). Quantitative citations limited to 100% contained checkpoints. This combination provides written description and enablement for a person of ordinary skill without need for physical prototype validation.")] }),
      new Paragraph({ children: [new TextRun("See CLAIM_ELEMENT_MATRIX.md and full evidence package for element-by-element mapping.")] }),

      new Paragraph({ children: [] }),
      new Paragraph({ children: [new TextRun({ text: "— End of Specification Support Draft (modeling data with enablement fixes sufficient to patent fully) —", italics: true })] }),
    ]
  }]
});

require('docx').Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('RCFX_Specification_Support_Draft_2026-06-04.docx', buffer);
  console.log('Spec support draft .docx updated (clean, Rung1 fixed + lid).');
});
