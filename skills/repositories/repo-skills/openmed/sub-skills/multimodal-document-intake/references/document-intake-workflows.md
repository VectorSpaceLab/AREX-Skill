# Document intake workflows

Read this when a task begins with a clinical document, scan, image, DICOM file,
spreadsheet, message export, or mixed-format bundle. The goal is to normalize
content into text plus provenance before sending it to privacy or clinical NLP
workflows.

## Core contract

OpenMed multimodal ingesters share one pattern:

1. Extract normalized text.
2. Preserve source mapping through `SourceSpan` objects: normalized character
   offsets, page number, optional bounding box, and metadata.
3. Run downstream de-identification or clinical extraction against normalized
   text.
4. Map detected spans back to the source for redaction, review, or audit.
5. Verify that no hidden text, metadata, pixel, or layout remnant still carries
   identifiers.

The common return shape is `ExtractedDocument(text, spans, metadata)`. A span's
`start`/`end` offsets index the normalized text, while `page`/`bbox`/`metadata`
anchor that span in the source.

## Choose the route by input family

| Input family | OpenMed route | Output to preserve | Main optional dependencies |
| --- | --- | --- | --- |
| Markdown or AsciiDoc | `extract_markdown`, `extract_asciidoc`, `redact_source_text` | source byte ranges in span metadata | `markdown-it-py` for Markdown parsing |
| PDF | `extract_pdf`, `project_text_spans`, `verify_redacted_pdf` | page numbers, PDF rectangles, text-layer evidence | `pdfplumber`, `pikepdf`, optional OCR/image stack |
| DOCX / PPTX / ODT / RTF / EPUB | format-specific extractors | paragraph/run/slide/page provenance where available | `python-docx`, `python-pptx`, parser-specific libraries |
| Images and scans | OCR engine adapters and image redaction checks | word bounding boxes, confidence, page/image id | `pytesseract` + system Tesseract, DocTR, EasyOCR, PaddleOCR |
| DICOM and DICOM-SR | header de-id, pixel redaction, SR extraction | header action report, pixel findings, residual text report | `pydicom`, imaging stack |
| XLSX / CSV / tables | table redaction/intake helpers | cell, row, column, sheet provenance | `openpyxl`, pandas/polars depending workflow |
| SMS, chatlogs, calendar, contacts | format-specific extractors/redactors | message/event/contact field provenance | parser-specific lightweight dependencies |

## Safe end-to-end pattern

Use this pattern for document-to-de-id tasks:

```python
from openmed.multimodal.documents_markdown import extract_markdown
from openmed import deidentify

source = "# Visit note\nPatient Alice Example called from 555-0100."
document = extract_markdown(source)
result = deidentify(document.text, method="mask", loader=fixture_or_local_loader)
# Then apply replacements back to the source format only after checking offsets.
```

For model-backed de-identification, supply a local model or a configured loader;
do not trigger model downloads while handling PHI unless the user explicitly
accepted that boundary.

## OCR workflow

Use a fake engine for tests and examples. Use real OCR only when the user has
installed the chosen backend and language resources.

```python
from openmed.multimodal.ocr import FakeOcrEngine, OcrWord

engine = FakeOcrEngine([
    OcrWord("Patient", (0, 0, 50, 10), 0.99),
    OcrWord("Alice", (55, 0, 90, 10), 0.98),
])
ocr_result = engine.recognize(None, languages=["en"])
document = ocr_result.to_document()
```

Real OCR notes:

- Tesseract needs the system executable and language packs.
- EasyOCR and PaddleOCR can download recognition models on first use.
- DocTR/EasyOCR/Paddle stacks are heavier than parser-only document handling.
- OCR output should be reviewed for low confidence, bad reading order, and
  language-code mismatch before using it as ground truth.

## PDF redaction pattern

For PDFs, treat visual boxes and hidden text separately:

1. Extract text and source rectangles.
2. Run de-identification on normalized text.
3. Project PHI spans back to rectangles.
4. Apply redaction to the PDF page content and text layer.
5. Verify with a fidelity report that expected rectangles are covered and the
   redacted text layer no longer contains the PHI string.

If a PDF has no extractable text layer, use OCR and mark the result as OCR-derived
instead of born-digital.

## DICOM pattern

DICOM workflows have two channels:

- Header metadata: patient/study/acquisition tags may identify a person.
- Pixel data: names, MRNs, dates, or measurements can be burned into the image.

Run header de-identification and pixel redaction separately, then keep the
reports together. Do not assume a clean header means clean pixels.

## Handoff to sibling sub-skills

- Send normalized text to `deidentification-privacy` first when identifiers may
  be present.
- Send already de-identified or synthetic text to `clinical-extraction-grounding`
  for sections, clinical NER, relations, and grounding.
- Send structured tables to `structured-risk-evaluation` before release.
- Send validated FHIR/OMOP/HL7 handoff payloads to `interoperability-serving`.
