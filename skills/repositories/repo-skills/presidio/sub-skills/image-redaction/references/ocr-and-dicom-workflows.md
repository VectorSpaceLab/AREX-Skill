# OCR and DICOM workflows

Use these recipes as self-contained patterns for Presidio image redaction. They assume the installed package is available in the current Python environment and do not depend on a source checkout.

## Prerequisite checklist

- Python package: `presidio-image-redactor`.
- Local OCR default: Tesseract OCR executable installed and available to `pytesseract`.
- Analyzer default model: the default `AnalyzerEngine()` path expects the documented English spaCy model. If a no-download or custom-only workflow is needed, inject a custom analyzer with `NoOpNlpEngine` and explicit recognizers.
- DICOM: `pydicom` and `python-gdcm` are part of the image-redactor dependency surface; compressed pixel data may require GDCM support at runtime.
- Optional Azure OCR: Azure Document Intelligence endpoint plus API key or Azure SDK credential.

## Standard image redaction

Use this for PNG, JPEG, TIFF, or other image types that Pillow can open.

```python
from pathlib import Path

from PIL import Image
from presidio_image_redactor import ImageRedactorEngine

image = Image.open("input.png")
engine = ImageRedactorEngine()

redacted = engine.redact(
    image=image,
    fill=(0, 0, 0),
    entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"],
    score_threshold=0.4,
)
redacted.save("redacted.png")
```

Use `redact_and_return_bbox()` when you need evidence about what was redacted:

```python
redacted, bboxes = engine.redact_and_return_bbox(
    image,
    fill=(255, 0, 0),
    ocr_kwargs={"ocr_threshold": 50, "config": "--psm 6"},
    language="en",
    entities=["PERSON", "EMAIL_ADDRESS"],
)

for bbox in bboxes:
    print(bbox.entity_type, bbox.score, bbox.left, bbox.top, bbox.width, bbox.height)
```

Decision points:

- Prefer `redact()` for production output when bboxes are not needed.
- Prefer `redact_and_return_bbox()` for validation, test assertions, QA review, or downstream annotation.
- Choose a fill matching the image mode: integer for grayscale, RGB tuple for color.
- Use `ocr_kwargs` for OCR settings and analyzer kwargs for entity/language/filter settings.

## Inspect raw OCR before analysis

When a redaction run returns no boxes, isolate OCR first:

```python
from PIL import Image
from presidio_image_redactor import TesseractOCR

image = Image.open("input.png")
ocr = TesseractOCR()
raw = ocr.perform_ocr(image, config="--psm 6")
words = [word for word in raw.get("text", []) if word and not word.isspace()]
print(words)
```

If `words` is empty, analyzer kwargs will not help; adjust image quality, orientation, language data, or OCR settings first. If OCR words are present but no image boxes are returned, debug entity names, language/model support, score threshold, allow list, and custom recognizers.

## No-download custom analyzer path

Use this when you only need deterministic pattern or deny-list detection and do not want to depend on the default spaCy model. Route complex recognizer design to `../analyze-text/SKILL.md`.

```python
from PIL import Image
from presidio_analyzer import AnalyzerEngine, PatternRecognizer
from presidio_analyzer.nlp_engine import NoOpNlpEngine
from presidio_analyzer.recognizer_registry import RecognizerRegistry
from presidio_image_redactor import ImageAnalyzerEngine, ImageRedactorEngine

recognizer = PatternRecognizer(
    supported_entity="PERSON",
    deny_list=["JOHN", "SMITH", "JOHN SMITH"],
    supported_language="en",
)
registry = RecognizerRegistry(recognizers=[recognizer], supported_languages=["en"])
nlp_engine = NoOpNlpEngine(models=[{"lang_code": "en", "model_name": "no_op"}])
analyzer = AnalyzerEngine(
    registry=registry,
    nlp_engine=nlp_engine,
    supported_languages=["en"],
)

image_analyzer = ImageAnalyzerEngine(analyzer_engine=analyzer)
redactor = ImageRedactorEngine(image_analyzer_engine=image_analyzer)

image = Image.open("input.png")
redacted, bboxes = redactor.redact_and_return_bbox(
    image,
    entities=["PERSON"],
    score_threshold=0.0,
)
```

Limits of this path:

- `NoOpNlpEngine` provides no token, lemma, or context artifacts. It is good for regex and deny-list recognizers, not for recognizers requiring NLP features.
- If OCR changes casing or splits words, include expected variants in the deny list or use regex patterns.

## Verification overlay for standard images

Use `ImagePiiVerifyEngine` to create a review image with detected PII highlighted:

```python
from PIL import Image
from presidio_image_redactor import ImagePiiVerifyEngine

image = Image.open("input.png")
verify_image = ImagePiiVerifyEngine().verify(
    image,
    is_greyscale=False,
    display_image=True,
    show_text_annotation=True,
    entities=["PERSON", "PHONE_NUMBER"],
)
if verify_image is not None:
    verify_image.save("verification.png")
```

The verification overlay is for review and diagnostics; use the redactor engine for actual redacted output.

## Optional Azure Document Intelligence OCR

Use `DocumentIntelligenceOCR` when local Tesseract quality is not acceptable and Azure Document Intelligence is approved for the data.

```python
from azure.identity import DefaultAzureCredential
from presidio_image_redactor import (
    DocumentIntelligenceOCR,
    ImageAnalyzerEngine,
    ImageRedactorEngine,
)

ocr = DocumentIntelligenceOCR(
    endpoint="https://example.cognitiveservices.azure.com/",
    credential=DefaultAzureCredential(),
    model_id="prebuilt-document",
)
image_analyzer = ImageAnalyzerEngine(ocr=ocr)
redactor = ImageRedactorEngine(image_analyzer_engine=image_analyzer)
redacted, bboxes = redactor.redact_and_return_bbox("input.png")
```

Alternative key-based setup:

```python
ocr = DocumentIntelligenceOCR(endpoint="https://example.cognitiveservices.azure.com/", key="...")
```

Or set environment variables before constructing the OCR object:

```sh
export DOCUMENT_INTELLIGENCE_ENDPOINT="https://example.cognitiveservices.azure.com/"
export DOCUMENT_INTELLIGENCE_KEY="..."
```

Operational constraints:

- Do not pass both `key` and `credential`.
- Use one of the supported model ids listed in `api-reference.md`.
- The adapter expects the service result to contain exactly one page.
- Treat Azure OCR as an external-cloud workflow with credential, network, privacy, and billing implications.

## DICOM pixel redaction from a loaded instance

Use this for burnt-in text visible in the pixel array.

```python
import pydicom
from presidio_image_redactor import DicomImageRedactorEngine

instance = pydicom.dcmread("input.dcm")
engine = DicomImageRedactorEngine()

redacted_instance, bboxes = engine.redact_and_return_bbox(
    image=instance,
    fill="contrast",
    padding_width=25,
    crop_ratio=0.75,
    use_metadata=True,
    ocr_kwargs={"ocr_threshold": 50},
)
redacted_instance.save_as("redacted.dcm")
print(bboxes)
```

Decision points:

- `use_metadata=True` augments pixel detection with metadata-derived terms, such as patient/name fields and generic sex markers. It does not scrub metadata.
- Run pixel redaction before a separate metadata-scrubbing/de-identification workflow so metadata terms can still help find matching burnt-in text.
- Use `fill="contrast"` for visually obvious masks and `fill="background"` when you want the mask to blend with the background.
- Keep `padding_width` positive and below `100`; reduce it only when padding creates coordinate review issues.
- Keep `crop_ratio` in `(0, 1)`; default `0.75` samples image corners for background estimation.

## DICOM file and directory workflows

For a single file:

```python
from presidio_image_redactor import DicomImageRedactorEngine

engine = DicomImageRedactorEngine()
engine.redact_from_file(
    input_dicom_path="input.dcm",
    output_dir="output",
    fill="contrast",
    padding_width=25,
    crop_ratio=0.75,
    use_metadata=True,
    save_bboxes=True,
    ocr_kwargs={"ocr_threshold": 50},
)
```

For a directory tree containing `.dcm` or `.dicom` files:

```python
engine.redact_from_directory(
    input_dicom_path="dicom-input-dir",
    output_dir="dicom-output-dir",
    fill="background",
    save_bboxes=True,
)
```

Operational notes:

- The file/directory helpers copy inputs under `output_dir` before processing, then edit the copies.
- If `save_bboxes=True`, sidecar JSON files use the redacted DICOM file name with a `.json` suffix.
- Input path validation is strict: a file workflow rejects directories, a directory workflow rejects files, and `output_dir` must not be an existing file.
- Directory traversal covers `.dcm`, `.DCM`, `.dicom`, and `.DICOM` suffixes.

## DICOM verification and evaluation

Create a verification image and inspect OCR/analyzer boxes:

```python
import pydicom
from presidio_image_redactor import DicomImagePiiVerifyEngine

instance = pydicom.dcmread("input.dcm")
engine = DicomImagePiiVerifyEngine()
verification_image, ocr_bboxes, analyzer_bboxes = engine.verify_dicom_instance(
    instance,
    padding_width=25,
    display_image=True,
    show_text_annotation=True,
    use_metadata=True,
)

if verification_image is not None:
    verification_image.save("dicom-verification.png")
print("OCR boxes:", ocr_bboxes)
print("Detected PHI boxes:", analyzer_bboxes)
```

Evaluate against hand-labeled ground truth:

```python
ground_truth = [
    {"label": "JOHN", "left": 25, "top": 25, "width": 120, "height": 35},
]
_, eval_results = engine.eval_dicom_instance(
    instance,
    ground_truth=ground_truth,
    tolerance=50,
    use_metadata=True,
)
print(eval_results["precision"], eval_results["recall"])
```

Ground-truth labels are lists of dictionaries with `label`, `left`, `top`, `width`, and `height`. When creating labels from a verification image, account for the padding used during OCR.

## Bounding-box review rules

- `left`/`top` are the pixel coordinate of the upper-left corner.
- `width`/`height` are dimensions in pixels.
- Standard image bboxes are `ImageRecognizerResult` objects; DICOM post-padding bboxes are dictionaries.
- One text entity may map to multiple boxes when OCR splits it into words.
- An OCR word can be represented by more than one detected entity if analyzers overlap; verify whether the higher-scoring or more conservative interpretation should drive user-facing claims.
- Empty boxes mean either OCR produced no words, analyzer produced no matching entities, allowed words were filtered out, or OCR/analyzer text spans no longer align.

## Service endpoint boundary

This sub-skill covers Python package operation. For HTTP `POST /redact`, Docker containers, or long-running service endpoint choices, use `../../references/service-and-rest-api.md` instead of starting services from this sub-skill.
