# Multimodal troubleshooting

Use this when document extraction, OCR, DICOM handling, source redaction, or
redaction-fidelity checks fail.

## Missing optional dependency

**Symptoms**

- Import or runtime error naming a parser package such as `pdfplumber`, `docx`,
  `pptx`, `PIL`, `pikepdf`, `pydicom`, `openpyxl`, or `markdown_it`.
- Error message suggests installing `openmed[multimodal]` or `openmed[ocr-paddle]`.

**Likely causes**

- Base OpenMed was installed without heavy document/OCR extras.
- A system binary such as Tesseract is missing even though Python packages are
  installed.

**Recovery**

1. Choose only the backend needed for the input family.
2. Install the matching extra or system binary in the user's local environment.
3. Re-run a small synthetic or fixture-only parser check before processing PHI.
4. If the task only needs a smoke test, run `scripts/document_intake_smoke.py`
   instead of installing heavy extras.

## OCR language or model mismatch

**Symptoms**

- Words are missing, incorrectly ordered, or returned with low confidence.
- An OCR backend rejects a language code.
- EasyOCR/Paddle attempts a model download unexpectedly.

**Recovery**

- Map OpenMed language codes to backend-specific IDs with the OCR language
  helpers.
- Install the system Tesseract language pack or pre-stage OCR model assets.
- Use `FakeOcrEngine` for tests and examples; use real OCR only after the user
  accepts any model download boundary.
- Do not treat OCR output as exact clinical ground truth without review.

## Span projection mismatch

**Symptoms**

- A normalized PHI span maps to no source rectangle.
- Redaction boxes cover the wrong words.
- `location_at(offset)` returns `None` for a span that should be mapped.

**Likely causes**

- Text normalization changed offsets after extraction.
- The wrong document object was passed downstream.
- OCR reading order inserted or removed separators.

**Recovery**

1. Keep the original `ExtractedDocument` object with downstream predictions.
2. Use the exact normalized text from `document.text` for de-identification.
3. Verify start/end offsets before applying replacements.
4. For OCR, confirm the separator used by `OcrResult.to_document()`.

## Hidden PDF text remains after visual redaction

**Symptoms**

- The page looks redacted, but copied text or search still reveals identifiers.
- Fidelity report says a text-layer span remains.

**Recovery**

- Treat visual redaction and text-layer removal as separate requirements.
- Run a PDF fidelity check after redaction.
- If the PDF is scanned, document that the result is OCR-derived and verify
  pixels, not just text extraction.

## DICOM PHI in headers or burned-in pixels

**Symptoms**

- Header de-identification succeeds but visible labels remain on the image.
- Pixel redaction finds identifiers but metadata still contains patient/study
  fields.

**Recovery**

- Run both header and pixel workflows.
- Keep header action reports and pixel residual-text reports together.
- Do not release a DICOM artifact unless both channels have been reviewed.

## Corrupt, encrypted, or unsupported file

**Symptoms**

- Parser reports unsupported extension, encryption, malformed zip/container, or
  invalid object structure.

**Recovery**

- Confirm the file type independently rather than trusting the extension.
- Ask the user for decryption credentials or an export in a supported format;
  do not bypass access controls.
- If the file is too large, process pages/blocks in bounded chunks and keep
  provenance for each chunk.

## Metadata remnants

**Symptoms**

- Text is redacted, but author, title, comments, EXIF, calendar/contact fields,
  or document properties still contain identifiers.

**Recovery**

- Run the format-specific metadata scrub or verification route.
- Re-open the output through the extractor and search for synthetic test
  identifiers before release.
- Preserve a no-PHI audit summary, not raw identifiers.
