# Sparrow OCR API Reference

This reference describes the runtime OCR service surface and the response post-processing contract. It is written so a later agent can operate the service without reading the original repository.

## Service surface

The OCR service is a FastAPI application with these stable paths:

| Path | Method | Purpose |
| --- | --- | --- |
| `/` | `GET` | Root health-style message: `{"message": "Sparrow OCR API"}`. |
| `/api/v1/sparrow-ocr/docs` | `GET` | Swagger UI for the OCR API. |
| `/api/v1/sparrow-ocr/openapi.json` | `GET` | OpenAPI schema. |
| `/api/v1/sparrow-ocr/inference` | `POST` | Run OCR on an uploaded file or a remote URL. |
| `/api/v1/sparrow-ocr/features` | `GET` | Report whether experimental table-processing features are importable. |

The service enables permissive CORS. The command-line server accepts an explicit `--port`; code default and documentation examples may differ, so always use the port from the running deployment.

## `POST /api/v1/sparrow-ocr/inference`

Submit form data to the router prefix `/api/v1/sparrow-ocr`.

| Field | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `file` | multipart upload | No, unless `image_url` is absent | none | Accepted upload content types are `image/jpeg`, `image/jpg`, `image/png`, and `application/pdf`. |
| `image_url` | form string | No, unless `file` is absent | none | The service fetches the URL with a browser-like `User-Agent`. Accepted URL response content types are `image/jpeg`, `image/jpg`, `image/png`, `application/pdf`, and `application/octet-stream`. `application/octet-stream` is treated as PDF bytes. |
| `include_bbox` | form boolean | No | `false` | Adds per-text-region bbox dictionaries to the post-processed response. |
| `enhance_tables` | form boolean | No | `false` | Experimental. If the experimental import is unavailable, the service logs a warning and continues without table enhancement. |
| `debug` | form boolean | No | `false` | Saves OCR visualization images to an `output` directory relative to the service process when OCR result objects support that operation. |

Input precedence and no-input behavior:

- If `file` is supplied, the upload branch is used and `image_url` is ignored.
- If only `image_url` is supplied, the URL branch is used.
- If neither input is supplied, the endpoint returns HTTP 200 with an informational payload and experimental feature availability instead of running OCR.

### Upload request examples

```bash
curl -X POST "$BASE_URL/api/v1/sparrow-ocr/inference" \
  -F "file=@document.pdf;type=application/pdf" \
  -F "include_bbox=true" \
  -F "debug=false"
```

```python
import requests

with open("receipt.png", "rb") as f:
    response = requests.post(
        f"{base_url}/api/v1/sparrow-ocr/inference",
        files={"file": ("receipt.png", f, "image/png")},
        data={"include_bbox": "true", "debug": "false"},
        timeout=120,
    )
response.raise_for_status()
ocr_pages = response.json()
```

### URL request examples

```bash
curl -X POST "$BASE_URL/api/v1/sparrow-ocr/inference" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "image_url=https://example.invalid/document.png" \
  -d "include_bbox=true" \
  -d "debug=false"
```

```python
response = requests.post(
    f"{base_url}/api/v1/sparrow-ocr/inference",
    data={
        "image_url": "https://example.invalid/document.pdf",
        "include_bbox": "false",
        "enhance_tables": "false",
    },
    timeout=120,
)
```

## Content-type and PDF handling

Uploads and URLs are handled differently:

- Uploads accept only image JPEG/JPG/PNG and `application/pdf`.
- URL fetches also accept `application/octet-stream`, but that content is passed to PDF conversion. If the remote server labels an image as octet-stream, conversion can fail.
- PDFs are converted at 300 DPI and only the first page is processed (`pages[0]`). Multi-page extraction must be orchestrated outside this endpoint by splitting or converting pages before calling OCR.
- Image inputs are opened with Pillow. PDF inputs require the `pdf2image` stack and system poppler tools available to the service process.

## OCR processing pipeline

For successful input, the service:

1. Opens the uploaded or fetched image, or converts the first PDF page to a PIL image.
2. Lazily initializes one cached PaddleOCR instance with PP-OCRv5 mobile detection and recognition model names.
3. Writes the PIL image to a temporary PNG or JPEG file. PNG is used only for `image/png`; all other accepted content types are written as JPEG for OCR.
4. Calls `ocr.predict(temp_path)`.
5. For each PaddleOCR result object, reads its `.json` payload and runs `extract_text_from_json` post-processing.
6. Adds `processing_info` to the first response item, including elapsed seconds, whether experimental features were used, and the worker process id.
7. Removes the temporary image file.

## Actual response shape

The source post-processor returns a list of page/result dictionaries. Do not assume a top-level `text`, `pages`, or `status` field when integrating with the current service implementation.

Without `include_bbox`:

```json
[
  {
    "extracted_text": "Invoice Number: 12345 Date: 2024-01-15",
    "text_count": 2,
    "avg_confidence": 0.94,
    "processing_info": {
      "processing_time_seconds": 2.31,
      "experimental_features_used": false,
      "worker_pid": 12345
    }
  }
]
```

With `include_bbox=true`:

```json
[
  {
    "extracted_text": "Invoice Number: 12345 Date: 2024-01-15",
    "text_count": 2,
    "avg_confidence": 0.94,
    "text_regions": [
      {
        "text": "Invoice Number: 12345",
        "bbox": {
          "x1": 100,
          "y1": 50,
          "x2": 300,
          "y2": 80,
          "width": 200,
          "height": 30
        },
        "confidence": 0.95
      }
    ],
    "processing_info": {
      "processing_time_seconds": 2.31,
      "experimental_features_used": false,
      "worker_pid": 12345
    }
  }
]
```

### `extract_text_from_json` contract

The post-processor expects a Paddle-style dictionary with OCR data under `result_json["res"]`:

```json
{
  "res": {
    "rec_texts": ["Invoice Number: 12345", "Date: 2024-01-15"],
    "rec_scores": [0.95, 0.92],
    "rec_boxes": [[100, 50, 300, 80], [100, 90, 250, 120]]
  }
}
```

Rules applied by the post-processor:

- Text entries are stripped and joined with spaces into `extracted_text`.
- Empty text and confidence scores `<= 0.3` are filtered out of `extracted_text` and `text_regions`.
- `text_count` counts only kept text entries.
- `avg_confidence` is the average of all `rec_scores`, rounded to two decimals, not only the kept scores.
- When `include_bbox=false`, `text_regions` is omitted.
- When `include_bbox=true`, each kept box with at least four coordinates becomes a bbox dictionary with integer `x1`, `y1`, `x2`, `y2`, `width`, and `height` fields. The current shape is a dictionary, not a four-number list, and it has no page number.
- Confidence in each text region is rounded to three decimals.

Use `scripts/ocr_response_smoke.py` to validate this contract without importing PaddleOCR.

## `GET /api/v1/sparrow-ocr/features`

This endpoint does not require an OCR model call. It reports whether optional experimental table-processing helpers were importable at service startup:

```json
{
  "experimental_features_available": false,
  "features": {}
}
```

If the experimental package is present but feature lookup fails, the endpoint still returns HTTP 200 and may include an `error` field.

## Table enhancement behavior

`enhance_tables=true` is accepted by the inference form. If experimental features are missing, the service disables the flag and continues OCR. If experimental features are present, the current response metadata can indicate that experimental features were requested and available, but callers should not rely on table grid data unless the live OpenAPI schema and response payload demonstrate it.

For downstream structured extraction from OCR text or document images, route to [document-extraction](../../document-extraction/SKILL.md). For calling the Sparrow LLM inference API directly, route to [api-engine-and-cli](../../api-engine-and-cli/SKILL.md).
