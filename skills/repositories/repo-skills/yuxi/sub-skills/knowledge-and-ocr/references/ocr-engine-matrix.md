# OCR engine matrix

Yuxi has one business parsing facade, `parse_document`, and multiple OCR engines behind it. Prefer the facade because it resolves the system default engine, DB-backed option values, environment fallbacks, and engine-specific constructor kwargs before calling low-level parsers.

## Engine resolution model

1. If a parse request includes `ocr_engine`, that value is normalized and validated.
2. Otherwise, image/PDF parsing uses the system default OCR engine from `default_ocr_engine`.
3. Engine-specific endpoint/key values are read at runtime from DB config first, then the declared environment variable fallback.
4. The resolved kwargs are passed internally as `_ocr_processor_kwargs`; do not place endpoint URLs or credentials in file-level `processing_params` snapshots.
5. The legacy/nested `ocr_engine_config` field is stripped before parser invocation. Use current top-level parser params instead.
6. `disable` is special: it allows text extraction from PDFs through the PDF loader path, but image files reject `disable` because images need OCR to produce text.

Public configuration/inspection APIs:

```text
GET  /api/system/ocr/options
GET  /api/system/ocr/health
GET  /api/system/config
POST /api/system/config/update                 # includes default_ocr_engine
GET  /api/system/config/options                # engine-specific option forms
PUT  /api/system/config/options/{key}          # save one option value
```

Sensitive values are redacted on read. Do not echo secrets from request bodies, env, or DB while debugging.

## Supported engines

| Engine id | Display name | Output style | Supported extensions | Backend / config | Best use | Readiness and failure notes |
| --- | --- | --- | --- | --- | --- | --- |
| `rapid_ocr` | RapidOCR (ONNX) | Plain OCR text; PDF pages are rasterized and OCRed | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif` | Local CPU; no service endpoint. Uses PP-OCRv5 models lazily at first processing. | Default CPU-safe choice for simple image/PDF text extraction. | Health check returns healthy without loading OCR models. First parse may download/load models. Failures usually show model-load, unsupported file type, temp-file, image processing, or PDF processing errors. |
| `mineru_ocr` | MinerU OCR | Markdown from self-hosted MinerU `/file_parse`, with ZIP/image handling | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif` | Self-hosted service. DB option key `mineru_ocr_host_opts.server_url`; env fallback `MINERU_API_URI`; default local fallback is `http://localhost:30001`. Compose service normally exposes `mineru-api:30001` to backend containers. | High-quality complex PDF/layout/table/formula parsing when the MinerU service is running. | Health probes `/openapi.json` and expects `/file_parse`. GPU-backed service may be slow to build/start. Timeout uses `timeout_seconds` or `MINERU_TIMEOUT` (default long-running). Connection/timeout/response ZIP errors are service-required, not parser-registry bugs. |
| `mineru_official` | MinerU Official API | Markdown from MinerU cloud result; ZIP result preferred, Markdown fallback supported | `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.png`, `.jpg`, `.jpeg` | Cloud service. DB option key `mineru_official_api_opts.api_key`; env fallback `MINERU_API_KEY`. | Cloud parsing when local GPU MinerU is unavailable and data may be sent to MinerU. | Constructor requires an API key. Health check reports configured without creating a parsing task. Runtime failures include upload URL failure, file upload failure, task status errors, no result URL, download failure, parse failure, and timeout. |
| `pp_structure_v3_ocr` | PP-Structure-V3 | Markdown/text from PaddleX layout parsing result | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif` | Self-hosted PaddleX service. DB option key `pp_structure_v3_ocr_host_opts.server_url`; env fallback `PADDLEX_URI`; default local fallback `http://localhost:8080`. | Table/formula/layout-heavy PDFs/images when the PaddleX service and GPU are available. | Health probes `/health`; parsing posts to `/layout-parsing`. If health is not healthy, parsing fails before upload. Watch for API errors, service unavailable, timeout, and file type errors. |
| `deepseek_ocr` | DeepSeek OCR | Markdown-oriented OCR/understanding through DeepSeek-OCR model | `.pdf`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp` | Reuses enabled model provider `siliconflow-cn`; requires provider API key and Base URL. The parser fallback env name is `SILICONFLOW_API_KEY`, but application config resolves through the provider service. | Cloud OCR for image/document understanding when SiliconFlow/DeepSeek-OCR is approved. | Requires external model credentials and network. Health checks model endpoint. Failures include missing provider credential, HTTP status errors, processing failure, max token issues, and timeout. |
| `paddleocr_vl_1_6` | PaddleOCR-VL-1.6 | Layout Markdown; Markdown image URLs are re-uploaded/proxied through KB image storage | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif` | Baidu AI Studio cloud jobs API. Shared DB option key `paddleocr_api_opts` with `api_url` and `api_token`; env fallbacks `PADDLEOCR_API_URL` and `PADDLEOCR_API_TOKEN`; default API URL is the AI Studio jobs endpoint. | Cloud document layout parsing for PDFs/images when Markdown structure is needed. | Requires Access Token. Job API flow: submit job, poll status, download JSON result. Failures include missing token, submit failure, missing `jobId`, unknown/failed job state, missing `jsonUrl`, result download failure, empty result, and timeout. |
| `paddleocr_pp_ocrv6` | PP-OCRv6 | Plain OCR text lines | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif` | Same PaddleOCR API config as `paddleocr_vl_1_6`. | Cloud plain text OCR when layout Markdown is not needed. | Same job/token/timeout failure modes as PaddleOCR-VL. Output is joined recognized text lines, not full layout Markdown. |

## Common parser parameters

These params are safe to put in parse/index request `params` when the chosen engine supports them. Unknown or irrelevant params are generally ignored by engines unless the parser explicitly validates them.

| Engine | Parameters |
| --- | --- |
| `rapid_ocr` | `zoom_x`, `zoom_y` for PDF rasterization density. |
| `mineru_ocr` | `lang_list`, `backend`, `parse_method`, `formula_enable`, `table_enable`, `image_analysis`, `start_page_id`, `end_page_id`, `timeout_seconds`; an explicit `server_url` can override the configured endpoint for one call but should not be persisted with secrets. |
| `mineru_official` | `enable_formula`, `enable_table`, `language`, `is_ocr`, `page_ranges`, `max_wait_seconds`, `poll_interval_seconds`, `data_id`. |
| `pp_structure_v3_ocr` | `use_table_recognition`, `use_formula_recognition`, `use_seal_recognition`, `timeout_seconds`. |
| `deepseek_ocr` | `pdf_dpi`, `max_tokens`, `temperature`, `timeout_seconds`. |
| `paddleocr_vl_1_6` / `paddleocr_pp_ocrv6` | `poll_interval_seconds`, `max_wait_seconds`, and `optional_payload` for API payload overrides. |

For knowledge-base ingestion, `parse_document` also injects `image_bucket` and `image_prefix` so parser-produced images are stored under the KB image area and exposed through an authenticated image proxy.

## File and path rules

### Knowledge-base files

- Upload/import/fetch routes write source bytes to MinIO and pass MinIO URLs into document record creation.
- Parsed Markdown is stored in MinIO and referenced by `markdown_file`.
- Images extracted from Office/ZIP/OCR Markdown are uploaded into the KB image bucket and surfaced by an authenticated proxy path under `/api/knowledge/databases/{kb_id}/images/kb-images/...`.
- The image proxy rejects object paths that do not start with `kb-images/`, contain `..`, or contain backslashes.

### Agent sandbox OCR

`ocr_parse_file` is the agent-facing tool for sandbox files. It accepts only Yuxi virtual paths under user-data `workspace`, `uploads`, or `outputs`; it rejects paths outside the virtual prefix, missing files, and directories. Results are written to `outputs/ocr/` and returned as a parsed virtual path plus short preview.

Use it for:

- PDF/Office/image attachments that `read_file` cannot directly read.
- Long OCR results where the model should subsequently call `read_file` on the generated Markdown.

Do not use it to parse arbitrary host paths or source-checkout files. It is intentionally sandbox-scoped.

## `read_file` and OCR fallback behavior

- `read_file` supports UTF-8 text and image file types directly.
- `read_file` rejects PDF/Office files with guidance to use `ocr_parse_file` first.
- `read_file` rejects unsupported binary files with a text/image-only error.
- If image blocks returned by `read_file` reach a model that rejects image inputs, middleware can ask for `ocr_parse_file` on those same image paths and then continue from the OCR result.
- The multimodal fallback path is not proof that every OCR engine works; it only proves the agent can route from model image rejection to OCR parsing when the configured OCR engine and services are available.

## Native verification focus

`pytest backend/test/unit/knowledge/test_parser_facade.py` is the main CPU-safe proof for this matrix. It checks:

- Parser metadata comes from parser classes and engine IDs match `service_name`.
- Parser cache keys do not leak credentials.
- Targeted cache clearing works.
- MinerU endpoint normalization and MinerU Official health-check behavior.
- `parse_document` parses PDF with explicit `disable`, DOCX with fallback, CSV preserving numeric dtype, image with mocked OCR, and default OCR resolution from system config.
- Low-level PDF parsing rejects calls missing resolved `ocr_engine`.
- Image parsing ignores legacy `enable_ocr` and refuses `disable`.

Use the E2E OCR tests only after services are up and side effects are acceptable.
