# OCR and Parser Backends

## DeepDoc Vision Stack

DeepDoc uses vision models to recover text, layout, and tables from PDFs and images:

| Component | Responsibility | Typical failure surface |
| --- | --- | --- |
| OCR | Detect and recognize text regions from rendered pages/images | Missing model files, ONNX/runtime issues, no text from scanned pages, language mismatch. |
| Layout recognizer | Labels regions such as text, title, figure, table, caption, header, footer, reference, and equation | Headers/footers not removed, tables/figures mislabeled, layout recognizer backend mismatch. |
| Table structure recognizer | Reconstructs table rows/columns/spans and table HTML/text | Rotated tables, merged cells, sparse OCR, cropped tables, model/runtime availability. |
| Figure/image enrichment | Optionally describes image/table sections with an image-to-text model | Missing VLM provider, slow media enrichment, undesired table/image-to-text flattening. |

The native PDF parser emits both semantic content and layout geometry. Preserve both when modifying OCR or layout behavior; downstream chunk preview and citation behavior depends on positions and `doc_type_kwd`.

## Layout Labels

DeepDoc layout recognition uses these common labels:

- `text`
- `title`
- `figure`
- `figure caption`
- `table`
- `table caption`
- `header`
- `footer`
- `reference`
- `equation`

Flow-level PDF normalization converts these into a smaller downstream contract. `table` maps to table chunks; `figure` maps to image chunks; text/title/equation-like content normally maps to text unless a parser explicitly carries an image and flattening is disabled.

## Environment and Runtime Controls

| Setting | Applies to | Effect |
| --- | --- | --- |
| `LAYOUT_RECOGNIZER_TYPE` | DeepDoc PDF layout | Selects `onnx` or `ascend`; unsupported values should raise a clear error. |
| `TABLE_AUTO_ROTATE` | DeepDoc PDF table TSR | Enables/disables table auto-rotation. Default behavior is enabled. |
| `OCR_INTRA_OP_NUM_THREADS` / `OCR_INTER_OP_NUM_THREADS` | OCR ONNX runtime | Controls OCR thread counts. |
| `OCR_GPU_MEM_LIMIT_MB` | OCR runtime | Limits GPU memory where applicable. |
| `OCR_ARENA_EXTEND_STRATEGY` / `OCR_GPUMEM_ARENA_SHRINKAGE` | OCR runtime | Tunes ONNX arena behavior. |
| `HF_ENDPOINT` | Model downloads | Can point model downloads at a mirror when native model fetches are slow/unavailable. |

Do not hard-code local model paths in runtime docs or parser logic. Use project-relative model lookup or configured provider/service settings.

## PDF Parser Backend Matrix

| Backend | Local or remote | Configuration source | Strengths | Cautions |
| --- | --- | --- | --- | --- |
| DeepDoc | Local parser/model stack | DeepDoc defaults and environment | Default OCR + layout + TSR; good for scanned/layout-heavy PDFs; preserves geometry. | Heavy optional dependencies/models; can be slow; garbled source text may require OCR path. |
| Plain text | Local text extraction | `parse_method: plain_text` | Fast for selectable-text PDFs. | Skips OCR/layout/TSR; wrong choice for scanned pages or image-only PDFs. |
| MinerU | RAGFlow remote client to MinerU API/provider | Model provider or `MINERU_*` env auto-provisioning | Strong structured PDF conversion; content-list output supports text/table/image/equation/list blocks. | Requires reachable MinerU API; backend/method/language confusion is common. |
| Docling | Local package or external Docling Serve | `DOCLING_SERVER_URL` or local `docling` package | Useful document conversion/chunking backend with table/picture handling. | Remote endpoint contract varies by version; local package is optional. |
| OpenDataLoader | Remote service | `OPENDATALOADER_APISERVER`, optional API key/timeouts | Deterministic service-backed structured JSON + Markdown fallback. | Requires service health; RAGFlow still renders page images locally for crop positions. |
| PaddleOCR | Remote async job API/provider | Model provider or `PADDLEOCR_*` env | PaddleOCR-VL/PP-OCR/PP-Structure algorithms and image parsing. | Needs access token; async submit/poll/fetch; result is JSONL and may omit layout for OCR-only models. |
| Tencent Cloud ADP | Remote Tencent Cloud API | `tcadp_config` service config and parser config options | Cloud document parser for PDF/spreadsheet/slides. | Requires credentials; downloads result ZIP; table/image options are provider-specific. |
| VLM image parser | Provider model | Tenant image-to-text/default model config | Useful when pages should be described as images. | Not the same as OCR/layout; may lose fine-grained bboxes and tables. |

## MinerU Details

MinerU parser options include:

- Backend: `pipeline`, `vlm-http-client`, `vlm-transformers`, `vlm-vllm-engine`, `vlm-mlx-engine`, `vlm-vllm-async-engine`, `vlm-lmdeploy-engine`.
- Parse method: `auto`, `txt`, `ocr`.
- Language: RAGFlow language names are mapped to MinerU language codes such as `en`, `ch`, `latin`, `korean`, `japan`, and others.
- Feature flags: formula extraction and table extraction can be toggled.
- Output cleanup: temporary output may be deleted unless configured otherwise.

Use `mineru_parse_method: ocr` when a PDF is image-based and `auto` fails to extract useful text. Use `vlm-http-client` only when the downstream VLM server URL is configured and reachable.

MinerU block handling:

| MinerU block type | Transfer behavior |
| --- | --- |
| `text` | Text section. |
| `table` | Table body/caption/footnote text; HTML-like table bodies are sanitized unless table mode is enabled. |
| `image` | Caption/footnote plus optional VLM description. |
| `equation` | Equation text. |
| `code` | Code body plus caption. |
| `list` | Joined list items. |
| `header`, `footer`, `page_number`, `discarded` | Skipped. |

## Docling Details

Docling can run locally if the package is importable, or remotely when a server URL is configured. Remote parsing attempts chunking/conversion endpoints and ingests returned Markdown/text/document structures. For remote mode, validate:

1. Server URL has no trailing path confusion.
2. `/openapi.json`, `/docs`, or conversion endpoints are reachable.
3. Request timeout is long enough for the PDF size.
4. Response shape contains document entries, Markdown, text, or chunk fields.
5. Tables and pictures preserve bbox-derived crops where possible.

## OpenDataLoader Details

OpenDataLoader requires a service URL and optionally an API key. The parser sends PDFs to `/file_parse`, retries failures, and prefers `json_doc` over `md_text` fallback. Structured elements are classified into text, table, image, or equation; page bboxes are converted from PDF coordinate space to image-space position tags.

Useful configuration variables:

- `OPENDATALOADER_APISERVER`
- `OPENDATALOADER_API_KEY`
- `OPENDATALOADER_TIMEOUT`

Do not require a Java runtime on the RAGFlow host if the OpenDataLoader service container owns conversion.

## PaddleOCR Details

PaddleOCR parser submits an async job, polls until completion, fetches JSONL result data, then transfers layout/OCR blocks into sections.

Supported algorithm names include:

- `PaddleOCR-VL`
- `PaddleOCR-VL-1.6`
- `PaddleOCR-VL-1.5`
- `PP-OCRv5`
- `PP-OCRv6`
- `PP-StructureV3`

Important configuration fields:

| Field | Meaning |
| --- | --- |
| `base_url` | PaddleOCR API base URL; can come from `PADDLEOCR_BASE_URL`. |
| `access_token` | Bearer token; can come from `PADDLEOCR_ACCESS_TOKEN`. |
| `algorithm` | Model/API algorithm name. |
| `request_timeout` | End-to-end submit/poll/fetch timeout. |
| `prettify_markdown` | Clean Markdown output. |
| `show_formula_number` | Include formula numbering. |
| `visualize` | Request visual output when supported. |
| `algorithm_config` | Algorithm-specific options such as layout detection, OCR for image blocks, merge layout blocks, title releveling, markdown ignored labels, or VLM args. |

For OCR-only results, layout blocks may be absent and the parser falls back to recognized text boxes.

## Tencent Cloud ADP Details

TCADP uses configured Tencent Cloud credentials and options such as:

- `table_result_type`
- `markdown_image_response_type`
- file type, start page, end page
- retry count

The parser sends Base64 file content, receives a downloadable result URL, extracts safe JSON/Markdown files from a ZIP, and converts content to sections/tables. Ensure ZIP handling rejects symlinks, absolute paths, and traversal entries when modifying this backend.

## Choosing a Backend

| User report | Likely choice | Validation path |
| --- | --- | --- |
| Selectable text PDF parses slowly | `plain_text` | Confirm text is extractable and no scanned pages/tables/figures need OCR. |
| Scanned PDF has empty chunks | DeepDoc, MinerU OCR, PaddleOCR, or Docling/OpenDataLoader if configured | Verify OCR-capable backend, provider reachability, language, page image rendering, and parser output before indexing. |
| Complex tables lose structure | DeepDoc with TSR, PaddleOCR/Docling/OpenDataLoader, or spreadsheet HTML for XLSX | Check table labels, HTML output, crop positions, `flatten_media_to_text`, and chunk table handling. |
| Garbled CJK PDF text | OCR-capable backend instead of plain text | Check PDF garbled detection and backend OCR language. |
| Need deterministic service parser | OpenDataLoader or Docling Serve | Confirm service health and response transfer tests. |
| Need provider-managed OCR | MinerU, PaddleOCR, or TCADP | Confirm credentials/provider model/environment and avoid local install assumptions. |

## Safe Debugging Pattern

1. Run `scripts/parse_smoke.py --extension <ext> --config <json>` to validate extension family, output format, backend name, and optional import availability without parsing a document.
2. If a backend is remote, run only explicit health checks requested by the user or existing tests that mock the service.
3. If changing PDF metadata, test conversion from position tags to normalized PDF positions.
4. If changing table/image handling, verify `doc_type_kwd`, crop availability, and image/table text enrichment.
5. If parser output reaches zero chunks after parsing succeeds, switch to the dataset ingestion/retrieval sub-skill and inspect chunk building/indexing.
