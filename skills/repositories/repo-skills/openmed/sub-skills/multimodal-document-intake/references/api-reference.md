# Multimodal API reference

This reference summarizes the public multimodal contracts a future agent should
use. It is intentionally selective and task-oriented.

## Shared document objects

### `SourceSpan`

`SourceSpan(start, end, page=0, bbox=None, metadata={})`

- `start`, `end`: character offsets into `ExtractedDocument.text`.
- `page`: 0-based page or source segment index.
- `bbox`: optional `(x0, y0, x1, y1)` source bounding box.
- `metadata`: adapter-specific provenance, confidence, source offsets, or block
  information.

### `ExtractedDocument`

`ExtractedDocument(text, spans=(), metadata={})`

Use this as the normal bridge into downstream text workflows. Helpful methods:

- `ExtractedDocument.from_blocks(blocks, separator="\n", metadata=None)` builds
  text and spans from ordered block dictionaries.
- `location_at(offset)` returns the span covering a normalized-text offset.
- `text_for(span)` returns the normalized text covered by a span.

## Markdown and source-text replacement

### `extract_markdown(source)`

Accepts a filesystem path, raw text string, or text file-like object and returns
an `ExtractedDocument`. Each span can carry source offsets so normalized-text
redactions can be mapped back to Markdown source.

### `redact_source_text(document, replacements)`

Applies replacements back to original source text. Each replacement is
`(start, end, replacement_text)` using offsets into `document.text`. Use this
only after validating offsets against the extracted document.

## PDF routes

### `extract_pdf(path)`

Returns normalized PDF text plus page/rectangle provenance. Requires PDF parser
optional dependencies. Treat missing dependencies as an installation issue, not
a malformed input issue.

### `project_text_spans(document, spans)`

Maps normalized text spans back to PDF rectangles when source mapping exists.
Use it before applying or verifying PDF redactions.

### `verify_redacted_pdf(original, redacted, spans)`

Compares expected redaction regions with the redacted PDF. Use it to catch
cases where a visible box was drawn but the hidden text layer still contains
identifiers, or where expected rectangles were not covered.

## OCR routes

### `OcrWord`

`OcrWord(text, bbox, confidence, page=0)` describes one recognized word.

### `OcrResult`

`OcrResult(words, metadata={})` exposes:

- `.text`: words joined into normalized text.
- `.to_document(separator=" ")`: bridges OCR words into `ExtractedDocument` with
  bounding boxes carried in spans.
- `.to_layout(...)`: reconstructs layout-aware reading order when needed.

### `FakeOcrEngine`

`FakeOcrEngine(words, **metadata)` is the deterministic test engine. Call
`recognize(image, languages=None)`; the `image` argument can be a placeholder in
synthetic tests. Use this in bundled smoke checks to avoid external OCR binaries
and downloads.

### Real OCR engine notes

- `TesseractEngine` requires both Python packages and a system Tesseract binary.
- `EasyOcrEngine`, `PaddleOcrEngine`, and `DocTrEngine` require heavier optional
  packages and may download model assets.
- `tesseract_language`, `paddle_language`, and `easyocr_languages` map OpenMed
  language codes to backend-specific identifiers.

## Image routes

Image redaction helpers expose reports for residual text and metadata. Use
`redact_image`, `verify_image_redaction`, `assert_no_residual_phi`, and
`verify_image_metadata` when an image may contain both visible text and embedded
metadata.

## DICOM routes

- `deidentify_dicom_headers(path)` reports header actions and safe replacements.
- `redact_dicom_pixels(path)` reports pixel findings and redaction results.

Use both on DICOM images when PHI might appear in tags and burned-in pixels.
DICOM-SR extraction is a separate structured-report path and should preserve
report provenance.

## Error classes and availability checks

- Missing optional parser/OCR dependencies should surface as a multimodal
  missing-dependency error with an install hint.
- Use availability checks before promising a real OCR or document backend.
- Parser-only Markdown/fake-OCR paths can be used for deterministic tests even
  when heavy document extras are absent.
