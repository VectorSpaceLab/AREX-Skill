# Official PaddleOCR API

This reference covers the hosted PaddleOCR Python client, the `paddleocr api` CLI, and the public request/response objects behind them.

## Client classes

- `PaddleOCRClient`: synchronous client that submits a job, polls for completion, and returns parsed results.
- `AsyncPaddleOCRClient`: async variant for `asyncio` workflows and concurrent polling/submission.

Both clients require token-based auth. The token may come from a constructor argument or from `PADDLEOCR_ACCESS_TOKEN`.

## Supported model families

The public `Model` enum includes:

- `PP-OCRv5`
- `PP-OCRv5-latin`
- `PP-OCRv6`
- `PP-StructureV3`
- `PaddleOCR-VL`
- `PaddleOCR-VL-1.5`
- `PaddleOCR-VL-1.6`

The API validates that OCR requests use OCR models and document-parsing requests use document-parsing models.

## Option dataclasses

- `OCROptions`
- `PPStructureV3Options`
- `PaddleOCRVLOptions`

These objects convert to the service payload using the public `to_payload()` method. Invalid combinations or out-of-range values raise `InvalidRequestError` before a request is sent.

Important validation examples:

- `top_p` must be in `(0, 1]`
- `temperature` must be non-negative
- `repetition_penalty` must be positive
- `min_pixels` and `max_pixels` must be positive, with `min_pixels <= max_pixels`

## Core client methods

### OCR

- `ocr(...)`
- `submit_ocr(...)`
- `wait_ocr_result(...)`

### Document parsing

- `parse_document(...)`
- `submit_document_parsing(...)`
- `wait_document_parsing_result(...)`

### Status and resource helpers

- `get_status(job_id)`
- `get_batch_status(batch_id)`
- `save_resource(resource_url, destination, ...)`
- `save_ocr_result_resources(result, destination, ...)`
- `save_document_parsing_result_resources(result, destination, ...)`

## CLI surface

The `paddleocr api` CLI exposes:

- `--model_type {ocr, doc_parsing}`
- `--model`
- `--file_url` / `--file_path`
- `--base_url`
- `--token`
- `--client_platform`
- `--output`
- `--request_timeout`
- `--poll_timeout`
- `--save_resources`
- `--overwrite_resources`
- `--page_ranges`
- `--batch_id`
- document-preprocessing and layout toggles such as `--use_doc_orientation_classify`, `--use_doc_unwarping`, `--use_layout_detection`, `--use_chart_recognition`, `--use_seal_recognition`, `--use_table_recognition`, and `--use_formula_recognition`

## Response shape

The client parses API responses into dedicated result objects. Important fields include:

- OCR: job id, page list, OCR text/boxes, and raw response data
- Document parsing: job id, page list, Markdown text, image/resource mappings, exports, and raw page data

## Error hierarchy

Treat these as distinct troubleshooting cases:

- `PaddleOCRAPIError`
- `AuthError`
- `InvalidRequestError`
- `APIError`
- `RateLimitError`
- `ServiceUnavailableError`
- `JobFailedError`
- `RequestTimeoutError`
- `PollTimeoutError`
- `ResponseFormatError`
- `ResultParseError`
- `NetworkError`

## Safe usage notes

- Use fake clients or local unit tests to validate request shape before sending a real request.
- Keep OCR and document-parsing payloads separate; model and option validation happens before the network call.
- The `client_platform` header is available for integrations that need to identify their runtime.
