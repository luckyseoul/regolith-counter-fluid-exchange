const { Document, Paragraph, TextRun, Header, Footer, PageNumber, HeadingLevel, AlignmentType, PageBreak } = require('docx');
const fs = require('fs');

const coldReview = fs.readFileSync('COLD_CLAIMS_AND_MATH_REVIEW.md', 'utf8');
const execSummary = fs.readFileSync('EXECUTIVE_SUMMARY.md', 'utf8');
const filingReadiness = fs.readFileSync('FILING_READINESS.md', 'utf8');
const planUpdate = fs.readFileSync('../../docs/RCFX_Rung_Campaign_Plan.md', 'utf8');

const doc = new Document({
  styles: {
    default: { document: { styles: { paragraph: { style: "Normal", font: "Times New Roman", size: 24 } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { size: 56, bold: true, font: "Times New Roman" } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", run: { size: 32, bold: true, font: "Times New Roman" } },
    ]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: [ new Header({ children: [new Paragraph({ children: [new TextRun({ text: "PERRY-RCFX-004 Rev 5.2 | RCFX Patent Evidence Package | Confidential — Internal Filing Support", size: 18, italics: true })] })] }) ],
    footers: [ new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Page ", size: 18 }),
      new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
      new TextRun({ text: " | Modeling data sufficient to patent fully (Rung1 fixed 100% contained + lid demo) | No prototype or physical testing", size: 18 })
    ] })] }) ],
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("RCFX Patent Evidence Package")] }),
      new Paragraph({ children: [new TextRun({ text: "PERRY-RCFX-004 Rev 5.2 — Updated (modeling data for full patent support; Rung1 containment + lid enablement fixes; no hardware)", size: 22 })] }),
      new Paragraph({ children: [new TextRun({ text: "CONFIDENTIAL — Internal Patent Support Data", bold: true, size: 22 })] }),
      new Paragraph({ children: [] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Scope Note (Funds-Constrained)")] }),
      new Paragraph({ children: [new TextRun("No funds for prototype, bench-scale testing, or any physical hardware work. The sole objective is to generate sufficient computational and descriptive data (reproducible lumped model, mechanistic GPU DEM including fixed Rung1 99k 100% inside + clean 109.4× EMI, lid+freeboard demo for physical heights, detailed specification, formal drawings) to fully support the utility patent claims for enablement (35 U.S.C. §112) and written description. The Rung 0-5 + Rung1-fixed modeling campaign plus this cold review and evidence package provides that data. Historical PDF roadmap retained only as background.")] }),
      new Paragraph({ children: [] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Executive Summary")] }),
      ...execSummary.split('\n').map(line => new Paragraph({ children: [new TextRun(line)] })),
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Cold Claims and Math Review (Full)")] }),
      new Paragraph({ children: [new TextRun({ text: "Independent cold audit — confirms modeling data (with Rung1 fixed containment + lid) is sufficient to patent fully.", italics: true })] }),
      ...coldReview.split('\n').map(line => new Paragraph({ children: [new TextRun(line)] })),
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Filing Readiness Checklist")] }),
      ...filingReadiness.split('\n').map(line => new Paragraph({ children: [new TextRun(line)] })),
      new Paragraph({ children: [new PageBreak()] }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Rung Campaign Plan (Updated)")] }),
      ...planUpdate.split('\n').map(line => new Paragraph({ children: [new TextRun(line)] })),

      new Paragraph({ children: [] }),
      new Paragraph({ children: [new TextRun({ text: "— End of Evidence Package (modeling data with enablement fixes sufficient for full patent) —", italics: true })] }),
    ]
  }]
});

require('docx').Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('RCFX_Patent_Evidence_Package_2026-06-04.docx', buffer);
  console.log('Evidence package .docx updated (clean, Rung1 fixed + lid enablement).');
});
