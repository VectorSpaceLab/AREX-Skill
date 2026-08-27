# OCR Guide

This guide covers the OCR wrappers and saved-response parsing helpers.

## Main APIs

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `TesseractAgent(languages='eng', **kwargs)` | Tesseract OCR wrapper | Uses `pytesseract`; live OCR also needs the `tesseract` binary |
| `TesseractAgent.with_tesseract_executable(path, **kwargs)` | Set a custom binary path | Updates `pytesseract.pytesseract.tesseract_cmd` |
| `TesseractFeatureType` | Aggregation levels for Tesseract responses | `PAGE`, `BLOCK`, `PARA`, `LINE`, `WORD` |
| `GCVAgent(languages=None, ocr_image_decode_type='.png')` | Google Cloud Vision OCR wrapper | Requires `google-cloud-vision==1` and credentials for live OCR |
| `GCVAgent.with_credential(path, **kwargs)` | Set the credentials file path | Sets `GOOGLE_APPLICATION_CREDENTIALS` before construction |
| `GCVFeatureType` | Aggregation levels for GCV responses | `PAGE`, `BLOCK`, `PARA`, `WORD`, `SYMBOL` |

## What the agents return

### Tesseract

- `detect(image)` returns text by default.
- `return_response=True` returns the raw `text` string plus dataframe output.
- `agg_output_level=` returns a layout aggregated at the requested level.
- `load_response()` and `save_response()` work with pickled response data.

### Google Cloud Vision

- `detect(image)` returns the full text or a parsed layout depending on flags.
- `return_response=True` returns the raw API response object.
- `return_only_text=True` returns the text content only.
- `gather_text_annotations()` parses the loose `text_annotations` list.
- `gather_full_text_annotation()` parses hierarchical text at the requested
  aggregation level.
- `load_response()` and `save_response()` work with JSON response files.

## Aggregation levels

| Backend | Levels |
| --- | --- |
| Tesseract | `PAGE`, `BLOCK`, `PARA`, `LINE`, `WORD` |
| GCV | `PAGE`, `BLOCK`, `PARA`, `WORD`, `SYMBOL` |

Tesseract uses `group_levels` on the enum to decide how to aggregate rows from
its dataframe. GCV uses `child_level` to walk the hierarchical response tree.

## Typical workflows

### 1) Parse a saved OCR response

1. Load a saved response file.
2. Convert it into a `Layout` at the desired aggregation level.
3. Filter or regroup the resulting blocks with `layout-objects`.
4. Render the result with `visualization`.

### 2) Run live OCR

1. Choose Tesseract or GCV.
2. Make sure the Python package, the binary or credential, and the language
   hints are available.
3. Call `detect()` on an image array or image path.
4. Use `return_response=True` only when you need the raw engine output.

### 3) Build table parsing on top of OCR

1. Convert OCR output into a `Layout`.
2. Split the text into columns or rows with `Interval` and `filter_by()`.
3. Use `group_textblocks_based_on_category()` or custom distance logic for row
   grouping.
4. Export the structured result to a dataframe.

## Troubleshooting

- `ImportError` when constructing an agent: the required backend package is not
  installed.
- `ModuleNotFoundError: pkg_resources` when using GCV: install a setuptools
  build that still exposes `pkg_resources`.
- `TesseractAgent.detect()` returns empty or poor text: confirm the host binary
  and language pack are installed.
- `GCVAgent.with_credential()` warns about missing credentials: set the
  credential file path and `GOOGLE_APPLICATION_CREDENTIALS`.
- `agg_output_level` must be one of the enum values, not a plain string.
- Live OCR outputs can differ by engine version; saved responses are better for
  deterministic tests.

## Read next

- `../layout-objects/references/guide.md` for grouping and layout filtering
- `../visualization/references/guide.md` for rendering OCR regions
- `../../../references/troubleshooting.md` for backend, credential, and binary issues
