# Data Processing Reference

This reference covers Nexent document parsing, file splitting, conversion, image extraction, and background process/forward flows. It is distilled so future agents do not need to reopen source docs for normal tasks.

## Core SDK Surface

`DataProcessCore` is the main SDK entry point.

| API | Contract | Notes |
| --- | --- | --- |
| `DataProcessCore()` | Builds processors for `Unstructured`, `OpenPyxl`, `UniversalImageExtractor`, and `FileSplitter`. | Importing this stack may require optional data-process dependencies. |
| `file_process(file_data, filename, chunking_strategy="basic", processor=None, **params)` | Returns `(chunks, images_info)`. `file_data` bytes and `filename` are required. | Valid strategies: `basic`, `by_title`, `none`. Explicit `processor` must be `Unstructured`, `OpenPyxl`, or `UniversalImageExtractor`. |
| `file_split(file_data, filename, splitter=None, **params)` | Returns `List[BytesIO]` parts. | Uses `FileSplitter`; failures fall back to the original bytes instead of raising. |
| `get_supported_file_types()` | Returns Excel and generic extension lists. | Generic support depends on the unstructured processor. |
| `validate_file_type(filename)` / `get_processor_info(filename)` | Fast validation and processor classification. | Useful before starting background tasks. |

### Processor Selection

- `.xlsx` and `.xls` use the OpenPyXL processor for table-aware Excel extraction.
- Other supported documents use the unstructured processor: `.txt`, `.pdf`, `.docx`, `.doc`, `.html`, `.htm`, `.md`, `.rtf`, `.odt`, `.pptx`, `.ppt`, `.epub`, `.json`, `.xml`, and `.csv`.
- If `model_type="multi_embedding"` and the file is PDF/Office/Excel/PowerPoint, the image extractor also runs. Text-only embedding skips image-metadata chunks during vectorization.
- `processor` overrides text processor selection, but image extraction may still run when `model_type="multi_embedding"` and the extension qualifies.

### Chunk Output Shape

Text chunks use dictionaries with these common fields:

| Field | Meaning |
| --- | --- |
| `content` | Extracted text or table representation. |
| `filename` | Original filename used for format detection/display. |
| `metadata.chunk_index` | Per-file chunk order when chunked. |
| `metadata.element_type` | Unstructured element class when available. |
| `metadata.page_number` / `metadata.coordinates` | PDF/document location metadata when supplied by the parser. |
| `language` | First detected language when parser metadata provides it. |

Excel chunks convert rows to markdown tables. Single-column sheets are emitted as line-based content with a sheet marker; multi-column sheets use the detected title row and merged-cell expansion.

## Chunking and Splitting

Chunking controls text partitioning after parsing; splitting controls pre-processing of large source bytes.

| Mechanism | Values / formats | Behavior |
| --- | --- | --- |
| `chunking_strategy` | `basic`, `by_title`, `none` | Passed to unstructured; `none` returns one document from all elements. |
| `FileSplitter` supported extensions | `.csv`, `.epub`, `.xlsx`, `.xls`, `.json`, `.md`, `.pdf`, `.txt`, `.xml`, `.doc`, `.docx` | Unsupported extensions return the original bytes unchanged from `DataProcessCore.file_split`. |
| `max_size` | Bytes, default about 5 MB when not supplied. | Size-based splitting for supported formats. |
| `target_parts` | Positive integer. | Overrides size target by estimating per-part size; PDF has a direct page-balanced path. |
| Word splitting | `.doc`/`.docx` convert to PDF through LibreOffice, then split PDF pages. | If conversion produces no real split, original Word bytes are retained. |

PowerPoint files are parsed by the unstructured processor but are not pre-split by `DataProcessCore.file_split`; diagnose large `.pptx` failures as conversion/parser/resource problems rather than expecting native splitter behavior.

## Backend Data-Process Flow

The backend exposes process endpoints under `/tasks` and routes most file-ingestion work through a background process-to-forward chain.

| Route / operation | Purpose | Downstream owner |
| --- | --- | --- |
| `POST /tasks` | Enqueue one process → forward chain for a source. | Celery/Ray data-process tasks, then vector indexing. |
| `POST /tasks/batch` | Enqueue one chain per uploaded file. | `DataProcessService.create_batch_tasks_impl`. |
| `POST /tasks/process` | Synchronous extraction for immediate text. | High-priority processing queue with timeout. |
| `POST /tasks/process_text_file` | Upload bytes and process directly through `DataProcessCore`. | No vector forwarding. |
| `GET /tasks` / `GET /tasks/indices/{index_name}` / `GET /tasks/{task_id}/details` | Inspect task status and errors. | Redis/Celery task metadata. |
| `POST /tasks/convert_state` | Convert Celery process/forward states to UI states. | Pure state-mapping logic. |
| `POST /tasks/convert_to_pdf` | Convert Office object in storage to PDF using the data-process service. | LibreOffice, storage download/upload, validation. |
| `POST /tasks/filter_important_image` | Filter image relevance using CLIP when enabled, with size-only fallback. | Optional CLIP model cache/provider. |

### Process → Forward Stages

1. File-management code uploads source bytes to storage or accepts local/sync input.
2. It triggers the data-process service with `source`, `source_type`, `chunking_strategy`, `index_name`, `original_filename`, `embedding_model_id`, `tenant_id`, and telemetry context.
3. The process task fetches source bytes, optionally splits large supported files, runs `DataProcessCore.file_process`, formats chunks, and may store aggregated chunks in Redis under task-scoped keys.
4. The forward task reads chunks from the payload or Redis, sends them to vector indexing, and records progress/error metadata.
5. Knowledge-file status combines process and forward task states with Redis progress.

Custom state mapping:

| Process state | Forward state | Custom state |
| --- | --- | --- |
| failure | any | `PROCESS_FAILED` |
| success | failure | `FORWARD_FAILED` |
| success | success | `COMPLETED` |
| success | pending | `WAIT_FOR_FORWARDING` |
| success | started | `FORWARDING` |
| pending | unset | `WAIT_FOR_PROCESSING` |
| started | unset | `PROCESSING` |

## Optional Dependencies and Models

The selected minimum verification is CPU-only, but data processing has optional runtime dependencies:

- `unstructured` and format extras for PDF, DOCX, PPTX, XLSX, CSV, and Markdown parsing.
- `openpyxl`/`xlrd` for Excel handling.
- `pypdf`, `ijson`, `ebooklib`, and markdown splitters for file splitting.
- `python-pptx` for direct PPTX image extraction.
- LibreOffice (`soffice`) for Office-to-PDF conversion and Word splitting.
- Table-transformer and unstructured model-cache parameters for high-resolution PDF image extraction.
- CLIP model files for image importance scoring when image filtering is enabled; otherwise Nexent falls back to size-only image acceptance.

## Safe Test Strategy

- For parser logic, use in-memory byte fixtures and mocked processors to avoid LibreOffice/model-cache requirements.
- For splitting, unit-test supported extensions with tiny byte streams and mock LibreOffice conversion for Office files.
- For background processing, test task-state mapping and service calls with mocked Celery/Redis/Ray objects; do not require live workers.
- For upload size issues, check both product documentation and active backend/frontend limits. The documented user-facing upload limit can differ from backend constants, so verify the active request path before changing limits.
