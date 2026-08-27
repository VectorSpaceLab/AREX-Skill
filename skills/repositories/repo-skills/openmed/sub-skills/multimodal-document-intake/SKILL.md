---
name: multimodal-document-intake
description: "Route OpenMed document, OCR, DICOM, image, table, and metadata
  intake workflows before de-identification or clinical extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Multimodal document intake

Use this sub-skill when a task starts from files, scans, images, DICOM studies,
messages, spreadsheets, or mixed document formats and needs normalized text,
source-offset provenance, layout coordinates, or redaction-fidelity checks before
passing text into OpenMed de-identification, clinical extraction, or interop
handoffs.

## Use when

- The input is PDF, DOCX, PPTX, RTF, ODT, EPUB, Markdown/AsciiDoc, CSV/XLSX,
  image, scan, OCR output, DICOM/DICOM-SR, SMS/chatlog, calendar, contact, or a
  community health worker form.
- You need `ExtractedDocument.text`, `SourceSpan` offsets, page/bounding-box
  provenance, or source-text replacement after redaction.
- You need to decide whether to install `openmed[multimodal]`, `openmed[ocr-paddle]`,
  a system OCR binary, or no optional document backend.
- You need `openmed verify-pdf`-style evidence that text-layer and visual
  redactions match.

## Route elsewhere

- Free-text PHI detection, masking, date shifting, mappings, and audit reports →
  `../deidentification-privacy/SKILL.md`.
- Clinical NER, assertions, sections, labs, medications, timelines, or grounding →
  `../clinical-extraction-grounding/SKILL.md`.
- FHIR/OMOP/HL7/OpenMRS/DHIS2/service handoffs →
  `../interoperability-serving/SKILL.md`.
- Mobile/browser model runtime deployment after document text is prepared →
  `../model-runtimes-mobile/SKILL.md`.

## Recommended workflow

1. Identify the input family and whether it is born-digital text, scanned image,
   mixed text+layout, or medical imaging metadata/pixels.
2. Read `references/document-intake-workflows.md` for the format-specific route,
   optional dependencies, and safe ordering.
3. If you only need a safe parser/OCR contract demonstration, run
   `scripts/document_intake_smoke.py --json`.
4. Keep real PHI out of prompts and logs. Use synthetic fixtures or already
   authorized local files; never paste source document text into an external
   agent message.
5. Preserve offsets and provenance when handing text to de-identification, then
   project final redactions back to the original source representation.
6. For PDFs, images, and DICOM, validate both visible pixels and hidden metadata
   or text layers before treating the output as scrubbed.

## Bundled references and scripts

- `references/document-intake-workflows.md` — read for format-specific recipes,
  data contracts, optional dependency choices, and handoff patterns.
- `references/api-reference.md` — read for verified public APIs and returned
  object shapes used by document, OCR, DICOM, and redaction-fidelity code.
- `references/troubleshooting.md` — read when a parser, OCR engine, hidden text
  layer, DICOM field, metadata scrub, or span projection behaves unexpectedly.
- `scripts/document_intake_smoke.py` — run for a deterministic Markdown plus
  fake-OCR smoke check that does not require external binaries or downloads.

## Safety reminders

- Treat extracted text and metadata as PHI until de-identification and fidelity
  verification complete.
- Prefer local, synthetic, or fixture data while developing. Do not send scans,
  image pixels, DICOM headers, or raw text to remote tools.
- OCR engines may download models or require system language packs. Make those
  network and installation boundaries explicit before use.
- DICOM PHI can live in both headers and burned-in pixels; verify both paths.
