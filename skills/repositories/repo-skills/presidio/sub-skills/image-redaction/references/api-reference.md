# Image redactor API reference

This reference covers the package API verified for Presidio Image Redactor. Import from the package root when possible:

```python
from presidio_image_redactor import (
    DocumentIntelligenceOCR,
    DicomImagePiiVerifyEngine,
    DicomImageRedactorEngine,
    ImageAnalyzerEngine,
    ImagePiiVerifyEngine,
    ImageRedactorEngine,
    TesseractOCR,
)
from presidio_image_redactor.entities import ImageRecognizerResult
```

## Standard image API

| Class or object | Purpose | Key surface |
| --- | --- | --- |
| `ImageAnalyzerEngine` | Runs OCR, analyzes extracted text with Presidio Analyzer, and maps analyzer spans to image bboxes. | `ImageAnalyzerEngine(analyzer_engine=None, ocr=None, image_preprocessor=None)`; `analyze(image, ocr_kwargs=None, **text_analyzer_kwargs) -> list[ImageRecognizerResult]` |
| `ImageRedactorEngine` | Redacts image pixels over detected PII boxes. | `ImageRedactorEngine(image_analyzer_engine=None)`; `redact(image, fill=(0, 0, 0), ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> PIL.Image.Image`; `redact_and_return_bbox(...) -> tuple[PIL.Image.Image, list[ImageRecognizerResult]]` |
| `ImagePiiVerifyEngine` | Draws verification overlays for OCR text and detected PII boxes. | `verify(image, is_greyscale=False, display_image=True, show_text_annotation=True, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> PIL.Image.Image or None` |
| `ImageRecognizerResult` | Analyzer result plus pixel bbox. | Constructor fields: `entity_type`, `start`, `end`, `score`, `left`, `top`, `width`, `height` |

Important behavior:

- `ImageAnalyzerEngine` defaults to `AnalyzerEngine()` and `TesseractOCR()` when not supplied.
- If `language` is not passed in image analyzer kwargs, the image analyzer uses English (`"en"`).
- `ImageRedactorEngine.redact()` and `redact_and_return_bbox()` duplicate the image before drawing; they do not mutate the original PIL image object in-place.
- `ad_hoc_recognizers` must be `None` or a non-empty list of `presidio_analyzer.PatternRecognizer` objects. Passing an empty list or non-recognizer item raises `TypeError`.
- `redact_and_return_bbox()` returns `ImageRecognizerResult` objects, not dictionaries. Use `bbox.left`, `bbox.top`, `bbox.width`, `bbox.height`, or `bbox.to_dict()`/`str(bbox)` for inspection.

### Standard image fill values

`fill` is passed to `PIL.ImageDraw.Draw(...).rectangle(..., fill=fill)` for every detected bbox.

- Grayscale images: pass an integer, for example `1`, `128`, or `255`.
- RGB images: pass a tuple, for example `(0, 0, 0)` or `(255, 0, 0)`.
- If the image mode and fill value do not match, PIL may coerce the value or raise. Prefer matching fill to image mode.

## DICOM API

| Class or object | Purpose | Key surface |
| --- | --- | --- |
| `DicomImageRedactorEngine` | Redacts burnt-in pixel text in DICOM images. | `redact_and_return_bbox(image, fill="contrast", padding_width=25, crop_ratio=0.75, use_metadata=True, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> tuple[pydicom.dataset.FileDataset, list[dict]]`; `redact(image, fill="contrast", padding_width=25, crop_ratio=0.75, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> FileDataset`; `redact_from_file(input_dicom_path, output_dir, padding_width=25, crop_ratio=0.75, fill="contrast", use_metadata=True, save_bboxes=False, verbose=True, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> None`; `redact_from_directory(input_dicom_path, output_dir, padding_width=25, crop_ratio=0.75, fill="contrast", use_metadata=True, save_bboxes=False, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> None` |
| `DicomImagePiiVerifyEngine` | Creates DICOM verification overlays and evaluates detected PHI boxes against ground truth. | `DicomImagePiiVerifyEngine(ocr_engine=None, image_analyzer_engine=None)`; `verify_dicom_instance(instance, padding_width=25, display_image=True, show_text_annotation=True, use_metadata=True, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> tuple[image-or-None, list, list]`; `eval_dicom_instance(instance, ground_truth, padding_width=25, tolerance=50, display_image=False, use_metadata=True, ocr_kwargs=None, ad_hoc_recognizers=None, **text_analyzer_kwargs) -> tuple[image-or-None, dict]` |

Important behavior:

- DICOM methods require a `pydicom.dataset.FileDataset` or `pydicom.dataset.Dataset` with accessible `PixelData`.
- Loaded-instance redaction methods return a copied dataset with altered `PixelData`; they do not scrub metadata fields.
- `redact_from_file()` and `redact_from_directory()` copy the source file(s) into the output directory, then edit the copies. They can write `.json` bbox sidecars with `save_bboxes=True`.
- `redact()` forwards unknown keyword arguments into `redact_and_return_bbox()` and then the analyzer. To control `use_metadata` explicitly on an in-memory DICOM instance, prefer `redact_and_return_bbox(..., use_metadata=...)`; `redact(..., use_metadata=True)` also works in the verified package because the keyword is forwarded.
- `use_metadata=True` builds an ad-hoc deny-list recognizer from DICOM text metadata, name fields, patient-related fields, and generic sex markers (`M`, `F`, `X`, `U`, with bracketed forms). It helps detect matching burnt-in pixel text; it does not alter metadata values.

### DICOM fill and geometry values

- `fill="contrast"`, `"invert"`, `"inverted"`, or `"inverse"`: draw a contrasting mask relative to the image background.
- `fill="background"` or `"bg"`: draw a background-like mask.
- Other DICOM fill strings raise `ValueError("fill must be 'contrast' or 'background'")`.
- `padding_width` must be positive and below `100`. Padding is added before OCR so edge text can be recognized; returned bbox coordinates have padding removed.
- `crop_ratio` must be greater than `0` and less than `1`; it controls how much of the image corners are used to estimate the background pixel value.
- For grayscale DICOM images, the engine rescales pixel arrays to 0-255 for OCR and uses DICOM pixel values for final masking. RGB DICOM support exists, but some grayscale-only helper paths raise when asked to compute most-common pixel value on RGB pixel arrays.

## OCR engines

| OCR engine | Purpose | Key surface |
| --- | --- | --- |
| `TesseractOCR` | Default local OCR backend. | `perform_ocr(image, **kwargs) -> dict` delegates to `pytesseract.image_to_data(..., output_type=pytesseract.Output.DICT, **kwargs)` |
| `DocumentIntelligenceOCR` | Optional Azure Document Intelligence OCR backend. | `DocumentIntelligenceOCR(endpoint=None, key=None, model_id="prebuilt-document", credential=None)`; `perform_ocr(image, **kwargs) -> dict` |

Expected OCR dictionary shape:

```python
{
    "left": [123, 345],
    "top": [0, 15],
    "width": [100, 75],
    "height": [25, 30],
    "conf": ["95", "87"],
    "text": ["JOHN", "DOE"],
}
```

Tesseract notes:

- The `tesseract` executable must be installed separately and discoverable by `pytesseract`.
- Tesseract kwargs such as `lang`, `config`, and other `pytesseract.image_to_data()` parameters belong in `ocr_kwargs`.
- Language data files must be installed at the Tesseract level before `ocr_kwargs={"lang": "..."}` can work.

Document Intelligence notes:

- Supported model ids: `prebuilt-document`, `prebuilt-read`, `prebuilt-layout`, `prebuilt-contract`, `prebuilt-healthInsuranceCard.us`, `prebuilt-invoice`, `prebuilt-receipt`, `prebuilt-idDocument`, `prebuilt-businessCard`.
- The constructor accepts either `key` or `credential`, not both.
- If `endpoint` and `key` are omitted, the engine checks `DOCUMENT_INTELLIGENCE_ENDPOINT` and `DOCUMENT_INTELLIGENCE_KEY`.
- `credential` can be an Azure SDK credential object; endpoint is still required.
- `perform_ocr()` supports exactly one returned page. Zero pages or multiple pages raise `ValueError`.
- The Azure OCR adapter converts word polygons to `left`, `top`, `width`, and `height` boxes by taking the polygon min/max coordinates.

## Analyzer kwargs in image workflows

Image methods forward `**text_analyzer_kwargs` to `AnalyzerEngine.analyze()` after OCR text reconstruction.

Common kwargs:

- `language="en"` or another language configured on the injected analyzer.
- `entities=["PERSON", "PHONE_NUMBER"]` to limit entity types.
- `score_threshold=0.4` or another threshold.
- `allow_list=["word", "phrase"]` and `allow_list_match="exact"` or `"regex"`.
- `context=["patient", "phone"]`.
- `return_decision_process=True` if the analyzer engine supports and you need explanations.

For custom recognizers, either pass `ad_hoc_recognizers=[PatternRecognizer(...)]` to image redactor/analyzer methods, or build a custom `AnalyzerEngine` and inject it into `ImageAnalyzerEngine(analyzer_engine=...)`. Use `../analyze-text/SKILL.md` for recognizer registry, NLP engine, model, supported entity, and language details.

## `ocr_kwargs` and confidence filtering

`ImageAnalyzerEngine` parses `ocr_kwargs` into two parts:

- `ocr_threshold`: consumed by image analyzer code and used to filter OCR words by confidence.
- all other keys: passed through to `ocr.perform_ocr()`.

`ocr_threshold` must be between `-1` and `100`. Values outside that range raise `ValueError`. If the threshold is high, valid words can disappear before text analysis and bbox mapping.

Example:

```python
redacted, bboxes = ImageRedactorEngine().redact_and_return_bbox(
    image,
    fill=(0, 0, 0),
    ocr_kwargs={"ocr_threshold": 50, "config": "--psm 6"},
    entities=["PERSON", "PHONE_NUMBER"],
    score_threshold=0.4,
)
```

## Bounding-box mapping semantics

Image bbox mapping is word-based:

1. OCR returns words plus pixel boxes.
2. The OCR text is reconstructed by joining words with spaces.
3. Presidio Analyzer detects text spans in the reconstructed string.
4. `ImageAnalyzerEngine.map_analyzer_results_to_bounding_boxes()` maps analyzer span overlap back to OCR word boxes.

Practical consequences:

- A single multi-word entity can return multiple `ImageRecognizerResult` rows.
- One OCR word can be reported more than once if multiple analyzer entity types overlap the same span.
- `allow_list` prevents allowed OCR words from being converted into redaction boxes.
- Empty OCR results, empty analyzer results, or mismatched OCR dictionary keys lead to empty boxes or a `KeyError`.
- DICOM bboxes returned by `redact_and_return_bbox()` are dictionaries rather than `ImageRecognizerResult` objects after padding removal.

## Verification helpers

- `ImagePiiVerifyEngine.verify()` returns an annotated image when `display_image=True`; returns `None` when `display_image=False`.
- `DicomImagePiiVerifyEngine.verify_dicom_instance()` returns `(verification_image_or_none, ocr_bboxes, analyzer_bboxes)`.
- `DicomImagePiiVerifyEngine.eval_dicom_instance()` returns `(verification_image_or_none, eval_results)` where `eval_results` contains `all_positives`, `ground_truth`, `precision`, and `recall`.
- `DicomImagePiiVerifyEngine` removes duplicate detected entities by keeping the highest-scoring box within the pixel tolerance used by its helper.
