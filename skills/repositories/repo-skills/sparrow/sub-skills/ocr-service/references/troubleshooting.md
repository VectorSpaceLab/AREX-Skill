# OCR Service Troubleshooting

Use this guide to distinguish request-shape errors, URL/content-type failures, PDF conversion issues, PaddleOCR runtime costs, bbox response surprises, table fallback, and debug side effects.

## Quick triage

1. Confirm the service is reachable: `GET /` should return `{"message": "Sparrow OCR API"}`.
2. Confirm the routed API surface: open `/api/v1/sparrow-ocr/docs` or fetch `/api/v1/sparrow-ocr/openapi.json`.
3. Check optional features without model execution: `GET /api/v1/sparrow-ocr/features`.
4. Reproduce response post-processing without PaddleOCR: run `python scripts/ocr_response_smoke.py --dump-json` from this sub-skill directory.
5. Only then run `/api/v1/sparrow-ocr/inference`, because the first inference can initialize PaddleOCR and download model assets.

## Upload: HTTP 400 invalid file type

Typical response detail:

```text
Invalid file type. Only JPG/PNG images and PDF are allowed.
```

Likely causes:

- The uploaded multipart field is not named `file`.
- The client did not send one of the accepted upload content types: `image/jpeg`, `image/jpg`, `image/png`, or `application/pdf`.
- The browser or HTTP client sent `application/octet-stream` for an upload. Uploads do not accept octet-stream, even though the URL branch accepts octet-stream as PDF bytes.
- The file is a TIFF, GIF, WEBP, HEIC, text file, HTML page, or a PDF with the wrong multipart content type.

Fixes:

- In Python Requests, set the filename and MIME type explicitly:

  ```python
  files = {"file": ("document.pdf", open("document.pdf", "rb"), "application/pdf")}
  data = {"include_bbox": "true"}
  response = requests.post(f"{base_url}/api/v1/sparrow-ocr/inference", files=files, data=data)
  ```

- Convert unsupported images to PNG/JPEG before upload.
- For PDFs, prefer `application/pdf`; do not rely on automatic MIME guessing.

## URL: fetch error or content-type failure

URL failures are wrapped as HTTP 400 with detail beginning like:

```text
Failed to process URL: ...
```

The wrapped error can represent several different problems:

- DNS, TLS, redirect, timeout, 403, 404, or other network/fetch failures.
- The remote server returns HTML or another unsupported content type.
- The remote server returns `application/octet-stream` for an image; the service treats octet-stream as PDF and PDF conversion may fail.
- The URL points to a web page that displays the document rather than a direct image/PDF byte stream.
- A content-type rejection inside the URL branch is also wrapped as a URL-processing failure, so it may appear as `Failed to process URL: 400: Invalid file type...` rather than the direct upload error text.

Fixes:

- Use a direct downloadable URL and confirm headers with `curl -I "$URL"`.
- If the server mislabels image bytes as octet-stream, download the file yourself and upload it with an explicit image MIME type.
- If the URL requires cookies, signed headers, or authentication, fetch outside the OCR service and upload the bytes.
- Keep the URL branch for public direct image/PDF resources.

## PDF first-page behavior and missing poppler

Current PDF behavior is first-page only:

- PDF bytes are converted at 300 DPI.
- Only `pages[0]` is passed to OCR.
- The response does not include page numbers.

If the task needs every page, split or render pages before calling OCR, then call `/inference` once per page or once per rendered image.

PDF conversion depends on poppler tools used by `pdf2image`. Common failures include messages about missing `pdfinfo`, missing `pdftoppm`, inability to get page count, or PDF conversion timeouts. Install poppler for the service host and ensure the poppler executables are on the service process `PATH`.

## PaddleOCR model and dependency downloads

The `/inference` path lazily creates a cached PaddleOCR model instance. First use can be slow or fail due to:

- Downloading PP-OCRv5 mobile detection/recognition assets.
- Network restrictions or model cache permissions.
- Incompatible `paddleocr`/`paddlepaddle` wheels for the Python version, OS, CPU/GPU runtime, or available instruction set.
- Large transitive dependency installs. The distilled OCR dependency set includes `pdf2image==1.17.0`, `torch==2.8.0`, `opencv-python==4.11.0.86`, `torchvision`, `torchaudio`, `datasets==4.2.0`, `paddleocr==3.2.0`, `paddlepaddle==3.2.0`, `pillow==11.3.0`, `python-multipart`, `fastapi==0.119.0`, `uvicorn[standard]`, and `rich`.

Diagnostic approach:

- Use `/features` or `/docs` to test the server without loading OCR weights.
- Use `scripts/ocr_response_smoke.py` to validate response parsing without PaddleOCR.
- Treat a failure that happens only on the first `/inference` call as likely model initialization, dependency, download, or cache related.
- Do not claim OCR accuracy or model execution was verified if only the smoke script passed.

## `include_bbox` shape surprises

When `include_bbox=true`, bbox output is not the older prose-doc list shape. Current post-processing emits:

```json
{
  "text": "Total: $42.50",
  "bbox": {
    "x1": 120,
    "y1": 260,
    "x2": 300,
    "y2": 292,
    "width": 180,
    "height": 32
  },
  "confidence": 0.977
}
```

Important details:

- `text_regions` is omitted entirely when `include_bbox=false`.
- Low-confidence text with score `<= 0.3` is filtered out.
- Empty or whitespace-only recognized text is filtered out.
- `avg_confidence` averages all recognition scores, including filtered entries.
- There is no page field in `text_regions`; endpoint output is a list of OCR result dictionaries.
- Bbox coordinates are cast to integers and `width`/`height` are computed as `x2 - x1` and `y2 - y1`.

Use the bundled smoke script to verify consumer code against this shape without loading OCR weights.

## Experimental table enhancement fallback

At service startup, optional table-processing helpers are imported if available. If import fails:

- Startup logs warn that experimental features are unavailable.
- `GET /api/v1/sparrow-ocr/features` reports `experimental_features_available: false` and an empty `features` object.
- `enhance_tables=true` on `/inference` logs a warning, disables table enhancement, and continues OCR instead of failing the request.
- The response metadata should show `experimental_features_used: false`.

If the experimental helpers are available but feature lookup fails, `/features` can include an `error` field while still returning HTTP 200.

Do not promise table grid output solely because `enhance_tables=true` is accepted. Validate the live response before writing downstream consumers that require table images or table metadata.

## Debug output side effects

When `debug=true`, OCR result objects attempt to save visualization images to an `output` directory relative to the service process. Current response post-processing does not guarantee a returned `debug_path`.

Operational implications:

- Debug files can accumulate and consume disk space.
- File creation can fail if the service user cannot write to the working directory.
- Concurrent requests may share the same output directory.
- Keep `debug=false` in production unless visual inspection is needed.

## No-input response is not an error

Calling `/api/v1/sparrow-ocr/inference` without `file` and without `image_url` returns HTTP 200 with an informational payload and feature availability. If an integration expected a 4xx for no input, handle this branch explicitly.

## When to route elsewhere

- If the task is to extract structured JSON from OCR text, document images, or VLM backends, use [document-extraction](../../document-extraction/SKILL.md).
- If the task is to call the Sparrow LLM API, instruction endpoint, or CLI, use [api-engine-and-cli](../../api-engine-and-cli/SKILL.md).
