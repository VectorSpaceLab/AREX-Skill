# Image redaction troubleshooting

Use this guide when Presidio image or DICOM workflows fail, return empty bboxes, or produce unexpected masks.

## Quick triage order

1. Confirm package imports.
2. Confirm Tesseract binary availability for local OCR.
3. Inspect raw OCR words before redaction.
4. Check analyzer kwargs: `language`, `entities`, `score_threshold`, `allow_list`, `context`, and custom recognizers.
5. For DICOM, confirm readable `PixelData`, transfer syntax support, padding/fill/crop settings, and the pixel-versus-metadata caveat.

The bundled `scripts/image_ocr_smoke.py` exercises the first three steps without source checkout assumptions.

## Missing Tesseract

Symptoms:

- `pytesseract.pytesseract.TesseractNotFoundError`
- `tesseract is not installed or it's not in your PATH`
- Image workflows fail before analysis starts.

Checks:

```sh
tesseract --version
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

Fixes:

- Install the Tesseract OCR system package for the operating system.
- Ensure the `tesseract` executable is on `PATH` for the Python process.
- If Tesseract is installed in a non-standard location, set `pytesseract.pytesseract.tesseract_cmd` in application code before constructing/running `TesseractOCR`.
- Install required Tesseract language data before using `ocr_kwargs={"lang": "..."}`.
- Re-run `scripts/image_ocr_smoke.py` after installation.

## OCR runs but returns no text

Symptoms:

- `redact_and_return_bbox()` returns an empty bbox list.
- `ImagePiiVerifyEngine.verify()` shows no OCR or PII boxes.
- Raw OCR dictionary has empty or whitespace-only `text` entries.

Checks:

```python
from PIL import Image
from presidio_image_redactor import TesseractOCR

raw = TesseractOCR().perform_ocr(Image.open("input.png"), config="--psm 6")
print([w for w in raw.get("text", []) if w and not w.isspace()])
print(raw.get("conf", []))
```

Fixes:

- Increase image resolution or provide a clearer crop.
- Correct rotation/orientation before OCR.
- Improve contrast or thresholding before passing the image.
- Try Tesseract page segmentation settings such as `ocr_kwargs={"config": "--psm 6"}` for a block of text or `"--psm 11"` for sparse text.
- Lower or remove `ocr_threshold`; a high threshold can filter out all words.
- Confirm Tesseract language data and `ocr_kwargs={"lang": "..."}` match the image text.
- If local OCR remains poor and cloud processing is permitted, consider `DocumentIntelligenceOCR`.

## OCR finds text but no PII boxes are redacted

Symptoms:

- Raw OCR words include the expected text, but `ImageAnalyzerEngine.analyze()` or `redact_and_return_bbox()` returns no boxes.
- Boxes appear only after lowering the analyzer score threshold.

Likely causes and fixes:

- Wrong entity filter: remove `entities` or use supported entity names for the configured analyzer.
- Wrong language: pass the language supported by the analyzer and recognizers.
- Score threshold too strict: lower `score_threshold` or inspect analyzer decision process in a text-only run.
- Allow list filters the OCR word: remove or narrow `allow_list`; remember image bbox mapping skips allowed OCR words.
- Default analyzer model missing: install the default spaCy model, or inject a custom analyzer using `NoOpNlpEngine` plus explicit recognizers for deterministic regex/deny-list workflows.
- Custom recognizer not supplied correctly: `ad_hoc_recognizers` must be `None` or a non-empty list of `PatternRecognizer` objects.

For recognizer registry, NLP engine, supported entity, country/language, and analyzer-model tuning, use `../analyze-text/SKILL.md`.

## Missing spaCy model or analyzer model errors

Symptoms:

- Default `ImageRedactorEngine()` or `ImageAnalyzerEngine()` fails while constructing or analyzing.
- Error text mentions `en_core_web_lg`, spaCy model loading, model download, or an unsupported language/model.

Fixes:

- Install the documented default model in the current environment:

```sh
python -m spacy download en_core_web_lg
```

- For no-download tests or deterministic examples, build a custom `AnalyzerEngine` with `NoOpNlpEngine` and explicit `PatternRecognizer`/deny-list recognizers, then pass it to `ImageAnalyzerEngine(analyzer_engine=...)`.
- Confirm that `language` in the image call matches `supported_languages` on the injected analyzer.
- If using optional model backends such as transformers, GLiNER, Stanza, or cloud recognizers, treat them as analyzer-level optional integrations and route details to `../analyze-text/SKILL.md`.

## Document Intelligence credentials and Azure OCR failures

Symptoms:

- `ValueError("Endpoint and key must be specified")`
- `ValueError("Endpoint must be specified")`
- `ValueError("Only one of key or credential may be specified")`
- `ValueError("Unsupported model id: ...")`
- `ValueError("DocumentIntelligenceOCR only supports 1 page documents")`
- Azure client/network/authentication errors.

Fixes:

- Provide `endpoint` and `key`, or provide `endpoint` and an Azure SDK `credential` object.
- Do not pass both `key` and `credential`.
- If relying on environment variables, set `DOCUMENT_INTELLIGENCE_ENDPOINT` and `DOCUMENT_INTELLIGENCE_KEY` before constructing `DocumentIntelligenceOCR()`.
- Use a supported model id from `api-reference.md`.
- Ensure the document/image produces exactly one page in the service response.
- Confirm that sending the image to Azure is allowed for the data and environment; this is an external-cloud workflow with network, credential, privacy, and billing implications.

## DICOM pixel redaction versus metadata PHI

Critical caveat:

- `DicomImageRedactorEngine` changes pixel data only. It does not remove PHI from DICOM metadata tags.
- `use_metadata=True` uses metadata values to help detect matching burnt-in text in pixels. It is not metadata de-identification.

Recommended order:

1. Run pixel/burnt-in text redaction with `use_metadata=True` while metadata values are still available to help detection.
2. Review redacted pixels and bbox sidecars/verification overlays.
3. Run a separate DICOM metadata scrubber/de-identification workflow.
4. Re-check that both pixel text and metadata PHI are handled.

If a future task is specifically about DICOM metadata anonymization, do not claim this sub-skill solves it.

## pydicom, pixel data, and GDCM issues

Symptoms:

- `AttributeError("Provided DICOM instance lacks pixel data...")` or `AttributeError("Provided DICOM file lacks pixel data.")`
- Pixel data access errors from `pydicom`.
- Compression/recompression failures involving GDCM, transfer syntax, icon image sequence, or photometric interpretation.
- Redacted DICOM cannot be read by downstream DICOM tools.

Fixes:

- Confirm the input is a `pydicom` dataset with `PixelData` and not a metadata-only object.
- Confirm the file is a DICOM file, not a directory; use `redact_from_directory()` for directories.
- Install/repair `pydicom` and `python-gdcm` in the environment when compressed pixel data is involved.
- For compressed or icon-image-sequence datasets, expect the engine to decompress/recompress pixel data; validate outputs with the same downstream DICOM reader used by the project.
- If RGB DICOM behavior differs from grayscale, test a representative sample. Some helper calculations are grayscale-specific.
- Preserve original files and process copies; the file/directory helpers are designed to copy into the output directory before editing.

## Fill color and bbox expectations

Symptoms:

- Mask color is not what the user expected.
- Redaction boxes are offset, too large, or split over words.
- Multi-word entities produce several bbox entries.

Explanations and fixes:

- Standard images use PIL fill semantics: integer for grayscale, RGB tuple for color.
- DICOM fill is not an RGB tuple; use `"contrast"` or `"background"` plus aliases documented in `api-reference.md`.
- DICOM padding is added before OCR and removed from returned boxes. When manually labeling verification images, account for the padding used in that verification run.
- A multi-word entity maps to multiple OCR word boxes; that is expected.
- Overlapping analyzer results can create duplicate-looking boxes with different entity labels. For DICOM evaluation, duplicate removal keeps the highest-scoring nearby entity.
- Empty bboxes for blank/no-text images are expected and should leave the image unchanged.
- `crop_ratio` outside `(0, 1)` and `padding_width <= 0` or `>= 100` raise validation errors.

## Workflow failure quick table

| Symptom | Most likely layer | Action |
| --- | --- | --- |
| Import fails | Python package install | Install `presidio-image-redactor` in the active environment. |
| Tesseract not found | System OCR binary | Install Tesseract and expose it on `PATH`. |
| OCR words empty | Image/OCR quality | Inspect raw OCR, adjust resolution/contrast/orientation/`--psm`/language data. |
| OCR words present, no boxes | Analyzer config | Check entity names, language, threshold, allow list, model, and recognizers. |
| Default analyzer model error | spaCy model | Install `en_core_web_lg` or inject a no-op/custom analyzer. |
| Azure constructor fails | Document Intelligence config | Provide endpoint plus exactly one credential source and a supported model id. |
| DICOM lacks pixels | Input data | Use a DICOM instance/file with accessible `PixelData`. |
| DICOM compressed output fails | pydicom/GDCM | Verify `python-gdcm`, transfer syntax support, and downstream reader compatibility. |
| Metadata PHI remains | Scope limitation | Run a separate metadata de-identification workflow after pixel redaction. |
