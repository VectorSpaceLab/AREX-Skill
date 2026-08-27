---
name: image-redaction
description: "Operate Presidio image OCR redaction for standard images and DICOM pixel PHI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# image-redaction

Use this sub-skill when the task is about Presidio Image Redactor package workflows: OCR text detection in images, redacting image pixels, returning or validating bounding boxes, choosing the OCR engine, or handling DICOM burnt-in text redaction.

## Use when

- You need `ImageRedactorEngine.redact()` or `redact_and_return_bbox()` on a PIL image, image-like object, NumPy array, or image file path accepted by the image preprocessor.
- You need `ImageAnalyzerEngine.analyze()` to run OCR, feed extracted text through Presidio Analyzer, and map analyzer spans back to image bounding boxes.
- You need `ImagePiiVerifyEngine.verify()` for an annotated verification image showing OCR/PII boxes.
- You need `DicomImageRedactorEngine` for DICOM pixel redaction from a loaded `pydicom` instance, one file, or a directory tree.
- You need `DicomImagePiiVerifyEngine` to create DICOM verification overlays or compute precision/recall against ground-truth bounding boxes.
- You need to choose or troubleshoot `TesseractOCR` versus optional `DocumentIntelligenceOCR`.
- You need `ImageRecognizerResult`, bbox coordinate semantics, color/fill choices, `ocr_kwargs`, or analyzer kwargs passed through image workflows.

## Route elsewhere

- Text analyzer tuning, recognizer design, entity/language lists, score thresholds, context, allow lists, NLP engine configuration, or missing spaCy model diagnosis beyond the image pass-through: `../analyze-text/SKILL.md`.
- Text anonymization operators or deanonymization: `../anonymize-text/SKILL.md`.
- HTTP service startup, Docker/container guidance, or REST endpoint use: `../../references/service-and-rest-api.md`.
- DICOM metadata de-identification: outside this sub-skill. This sub-skill only covers pixel redaction; metadata PHI must be scrubbed by a DICOM metadata de-identification workflow after pixel redaction.

## Read first

- `references/api-reference.md` for constructors, methods, return values, bbox shape, fill values, and kwarg routing.
- `references/ocr-and-dicom-workflows.md` for standard image, custom analyzer, Azure Document Intelligence, DICOM file/directory, and verification recipes.
- `references/troubleshooting.md` for missing Tesseract, empty OCR, analyzer/model failures, Azure credentials, pydicom/GDCM, and bbox/fill surprises.
- `scripts/image_ocr_smoke.py` for a no-source-path smoke check that imports the package, checks Tesseract, creates an in-memory image, and verifies at least one redaction bbox.

## Operating checklist

1. Confirm prerequisites: `presidio-image-redactor` is importable; Tesseract is on `PATH` for the default `TesseractOCR`; the default analyzer path has `en_core_web_lg` unless you inject a custom analyzer that does not need it.
2. Decide OCR backend:
   - Use `TesseractOCR` by default for local image and DICOM workflows.
   - Use `DocumentIntelligenceOCR` only when Azure Document Intelligence credentials and one-page document constraints are acceptable.
3. Decide analyzer behavior:
   - Pass image workflow kwargs such as `language`, `entities`, `score_threshold`, `allow_list`, `allow_list_match`, and `context` through to the underlying `AnalyzerEngine.analyze()`.
   - Route recognizer/NLP design details to `../analyze-text/SKILL.md`.
4. For standard images, choose `ImageRedactorEngine.redact()` when only the image is needed; choose `redact_and_return_bbox()` when you need `ImageRecognizerResult` objects for validation or downstream review.
5. For DICOM, choose `redact_and_return_bbox()` for loaded instances and `redact_from_file()`/`redact_from_directory()` for filesystem workflows. Use `save_bboxes=True` when you need sidecar bbox JSON.
6. Treat `use_metadata=True` as a pixel-detection aid only: it uses DICOM metadata terms to find matching burnt-in pixel text, but it does not remove or alter metadata PHI.
7. When a run returns no boxes, debug in this order: Tesseract availability, raw OCR words, image resolution/contrast/orientation, `ocr_threshold`, analyzer kwargs/entities/language/model, then bbox mapping.

## Fast facts

- Standard-image `fill` is an integer grayscale value or an RGB tuple, for example `1`, `255`, or `(255, 0, 0)`.
- DICOM `fill` is `"contrast"`/`"invert"`/`"inverted"`/`"inverse"` for a contrasting mask, or `"background"`/`"bg"` for a background-like mask.
- `ocr_kwargs` is forwarded to the OCR backend after image code strips `ocr_threshold`; `ocr_threshold` accepts values from `-1` through `100`.
- Analyzer kwargs are passed through to Presidio Analyzer; keep complex analyzer construction in `../analyze-text/SKILL.md` and inject the resulting `AnalyzerEngine` into `ImageAnalyzerEngine`.
- `ImageRecognizerResult` has text span fields plus pixel fields: `entity_type`, `start`, `end`, `score`, `left`, `top`, `width`, `height`.
- Multi-word or overlapping analyzer results can produce multiple boxes for one entity; overlapping image boxes can represent different entity labels for the same OCR word.
- DICOM file/directory helpers duplicate inputs into the requested output directory before editing; loaded-instance methods return a copied in-memory dataset.
