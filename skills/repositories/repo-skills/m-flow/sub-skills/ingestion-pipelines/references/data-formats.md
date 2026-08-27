# Data formats, loaders, and routing choices

This reference covers the data-shape and loader decisions owned by the `ingestion-pipelines` sub-skill.

## Public ingestion surfaces

Prefer these public APIs:

- `await m_flow.ingest(data, dataset_name=None, *, skip_memorize=False, **kwargs)` — one-step add then memorize.
- `await m_flow.add(data, dataset_name="main_dataset", preferred_loaders=None, incremental_loading=True, enable_cache=True, items_per_batch=20, created_at=None, ...)` — store raw data and extracted text in a dataset.
- `await m_flow.memorize(datasets=None, chunker=TextChunker, chunk_size=None, chunks_per_batch=None, run_in_background=False, incremental_loading=True, enable_cache=True, items_per_batch=20, conflict_mode="warn", **kwargs)` — turn stored data into memory nodes.

Use `ingest(skip_memorize=True)` only when the data should be staged but not queryable yet. The result status will be `MEMORIZE_SKIPPED`; follow with `memorize()` before search/query.

## Accepted input shapes

| Shape | Examples | Notes |
| --- | --- | --- |
| Plain text string | `"Agent memory note..."` | Stored as a text file, then parsed by `text_loader`. |
| Relative file path | `"docs/report.md"` | If the path exists under the current process working directory, it is treated as a local file. Otherwise it is plain text. |
| Local directory | `"docs/"` | Expanded by `resolve_data_directories(include_subdirectories=True)` into files before ingestion. |
| Absolute local path | `"/data/report.pdf"` | Allowed only when local-file access is enabled. The runtime setting is `MFLOW_ACCEPT_LOCAL_FILE_PATH` with default true. |
| `file://` URI | `"file:///data/report.pdf"` | Same local-file access rule as absolute paths. |
| `s3://` URI | `"s3://bucket/prefix/report.pdf"` | Directory expansion requires S3 credentials; individual files are downloaded to a temporary file before loader dispatch. |
| HTTP/HTTPS URL | `"https://example.org/article"` | Fetched through the web-scraper utility and stored as HTML before loader dispatch. For HTML extraction, prefer a registered HTML-capable loader. |
| Upload-like binary object | FastAPI `UploadFile` with `.file` and `.filename` | Public type hints include `BinaryIO`. Current ingestion code explicitly handles upload-like objects; if a bare binary stream is rejected, write it to a temporary file or wrap it with filename metadata. |
| List | `["notes", "docs/a.md", "https://example.org"]` | Each item is resolved and processed independently in the same dataset. Avoid mixing transcript and article content in one `memorize()` call if they need different `content_type` values. |

Optional integrations are recognized by type name when installed: LlamaIndex document objects and Docling `DoclingDocument` objects can be transformed into ingestible text.

## Loader registry

M-flow resolves every stored file through a loader registry. Use the exact `loader_name` values below in `preferred_loaders`.

| Loader name | Typical extensions / MIME | Dependency and behavior |
| --- | --- | --- |
| `text_loader` | `txt`, `md`, `json`, `xml`, `yaml`, `yml`, `log`; text-like MIME types | Core loader. Reads text with an `encoding` option, default `utf-8`. |
| `csv_loader` | `csv`, `text/csv` | Core loader. Formats each row as labeled key-value text. |
| `pypdf_loader` | `pdf`, `application/pdf` | Lightweight PDF extraction with `pypdf`. Option: `strict=False` by default. |
| `image_loader` | common image formats such as `png`, `jpg`, `gif`, `webp`, `tiff`, `bmp`, `heic`, `avif` | Core loader but requires a configured vision-capable LLM; converts the image to a textual description. |
| `audio_loader` | `mp3`, `m4a`, `ogg`, `flac`, `wav`, `aac`, etc. | Core loader but requires an LLM transcription backend; converts audio to text. |
| `unstructured_loader` | Office docs, spreadsheets, presentations, HTML/email/ePub | Optional; registered only when `unstructured` imports successfully. Options pass through to `unstructured.partition.auto.partition`, including `strategy`. |
| `advanced_pdf_loader` | `pdf` | Optional; registered when its dependencies import successfully. Layout-aware PDF extraction with table/image handling and fallback to `pypdf_loader`. Options include `strategy`. |
| `beautiful_soup_loader` | `html`, `htm` | Optional; registered when BeautifulSoup dependencies import successfully. Use `preferred_loaders` for this loader because it is not in the default priority list. Supports extraction-rule configs. |

Default fallback priority is:

1. `text_loader`
2. `pypdf_loader`
3. `image_loader`
4. `audio_loader`
5. `csv_loader`
6. `unstructured_loader`
7. `advanced_pdf_loader`

Because `pypdf_loader` comes before `advanced_pdf_loader`, explicitly prefer `advanced_pdf_loader` for layout-sensitive PDFs.

## `preferred_loaders` patterns

`add()` accepts `preferred_loaders` as a list of loader names or single-entry config dicts. It normalizes them into a mapping and tries the preferred names in order before the default priority.

```python
await m_flow.add(
    ["whitepaper.pdf", "spec.md"],
    dataset_name="product-docs",
    preferred_loaders=[
        {"advanced_pdf_loader": {"strategy": "hi_res"}},
        {"pypdf_loader": {"strict": False}},
        "text_loader",
    ],
)
```

```python
await m_flow.add(
    "https://example.org/article",
    dataset_name="web-articles",
    preferred_loaders=[
        {"beautiful_soup_loader": {"rules": {"main": {"selector": "main"}}}},
        "unstructured_loader",
    ],
)
```

If a preferred loader is not registered, the engine skips it and continues. Use the bundled inspector script to check actual runtime registration:

```bash
python sub-skills/ingestion-pipelines/scripts/pipeline_stage_inspector.py --json
```

## Content type and mixed inputs

`ContentType` has two public values:

- `ContentType.TEXT` / `"text"`: articles, reference docs, notes, code comments, reports.
- `ContentType.DIALOG` / `"dialog"`: chat logs, meetings, interviews, scripts, support transcripts.

Content routing operates with a single `content_type` per `memorize()` or `ingest()` call. For a batch containing both articles and transcripts, prefer either:

1. split into two dataset additions and two `memorize()` calls with different `content_type` values; or
2. use `ContentType.DIALOG` only for the transcript subset and `ContentType.TEXT` for the article subset.

When `content_type=ContentType.TEXT`, the sentence-level router can still auto-detect dialog if `MFLOW_AUTO_DETECT_DIALOG` is not disabled. Set `MFLOW_AUTO_DETECT_DIALOG=false` when code/config blocks or colon-heavy notes are being misdetected as speaker turns.

## Chunking choices

Default memorization uses `TextChunker`, which groups paragraph-like text up to `max_chunk_size`. If `chunk_size` is omitted, M-flow derives a max chunk token count from the LLM context window.

Use:

- smaller `chunk_size` for chat logs or highly mixed notes where fine routing matters;
- larger `chunk_size` for coherent articles where preserving context is more important;
- `chunks_per_batch` to control LLM stage batch size and token concurrency pressure;
- a custom `chunker` class only if it follows the base chunker constructor shape `(document, get_text, max_chunk_size)` and yields `ContentFragment` objects.
