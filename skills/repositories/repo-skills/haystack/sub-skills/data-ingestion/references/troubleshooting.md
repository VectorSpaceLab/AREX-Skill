# Data Ingestion Troubleshooting

Use this page when ingestion code imports successfully but conversion, preprocessing, routing, or validation behaves unexpectedly.

## Install and Import Issues

Symptoms:
- `ModuleNotFoundError: No module named 'haystack'`
- Imports from old package names fail.
- Code imports a converter from an internal module path that changed.

Fixes:
- Install the distribution package `haystack-ai` in the target environment.
- Use public imports when possible: `from haystack import Document, Pipeline`; `from haystack.dataclasses import ByteStream, ChatMessage, FileContent, ImageContent`; `from haystack.components.converters import TextFileToDocument`.
- Keep Python at `>=3.10`.
- If working inside the Haystack repository, use the repository’s Hatch commands for tests and scripts. Do not assume direct `python` or `pip` commands in repo automation.

## Optional Dependency Failures

Symptoms:
- A converter raises an import error with instructions such as installing `pypdf`, `markdown-it-py`, `mdit_plain`, `python-docx`, parsing libraries, OCR clients, or HTTP/2 extras.
- `MultiFileConverter` works for text files but fails or skips PDF, DOCX, PPTX, XLSX, HTML, or image inputs.

Fixes:
- Choose the converter whose optional dependencies are available, for example `PyPDFToDocument` versus `PDFMinerToDocument` for PDFs.
- Catch optional dependency failures around format-specific branches and route the source to an unsupported/needs-install path instead of losing it silently.
- For Markdown, `MarkdownToDocument` checks for `markdown-it-py` and `mdit_plain`; if unavailable, use `TextFileToDocument` as a lower-fidelity fallback.
- For PDF/image OCR, document the backend requirement clearly and avoid pretending scanned documents are extractable with a text-only converter.

## Credential and Backend Issues

Symptoms:
- OCR or cloud document conversion fails with authentication, endpoint, quota, or region errors.
- URL fetching fails behind proxies, blocks, redirects, or TLS restrictions.

Fixes:
- Separate local deterministic converters from external OCR/cloud converters.
- Pass credentials through normal runtime configuration or environment variables for the application, not through generated skill text or metadata examples.
- For `LinkContentFetcher`, set `raise_on_failure=False` for batch fetches where partial success is acceptable, and set bounded `retry_attempts` and `timeout`.
- For HTTP/2, install the required `httpx[http2]` support or let the fetcher fall back to HTTP/1.1.

## API Misuse

Symptoms and fixes:
- `Document(content=...)` rejects non-string content: convert bytes, JSON, tables, or images with a converter first, or store binary data in `blob=ByteStream(...)`.
- `DocumentSplitter` raises `ValueError` for `content is None`: route binary/empty documents to OCR, captioning, or a non-text branch before splitting.
- `DocumentSplitter` raises for invalid split configuration: keep `split_length > 0`, `split_overlap >= 0`, and `split_overlap < split_length`; provide `splitting_function` when `split_by="function"`.
- `DocumentCleaner` raises `TypeError`: pass `list[Document]`, not a single `Document` or a list of dictionaries.
- `FileTypeRouter` raises `ValueError` for an empty MIME list or invalid regex: provide at least one exact MIME or valid regex pattern.
- `DocumentTypeRouter` raises because both metadata fields are missing: set `mime_type_meta_field`, `file_path_meta_field`, or both.
- `MetadataRouter` raises invalid filter syntax: every rule must include an `operator`; compound rules use `operator` plus `conditions`.
- `FileContent` raises invalid base64: use `FileContent.from_file_path()` or provide a valid base64 string and MIME type.

## Data and Configuration Problems

Symptoms:
- Converted documents have missing or surprising metadata.
- Files are routed to `unclassified`.
- PDF conversion returns empty content.
- Metadata filters do not match expected documents.

Fixes:
- Pass `meta` as one dictionary for all sources or a list with exactly the same length as `sources`.
- For `ByteStream` sources, set `mime_type` explicitly or use `guess_mime_type=True` when reading from a path.
- Preserve source traceability with `file_path`, `source`, `url`, `mime_type`, `language`, and stable external IDs.
- Remember that many converters store only the basename of `file_path` unless `store_full_path=True`.
- Inspect `unclassified`, `failed`, and `unmatched` outputs; do not index only the happy path without accounting for them.
- Empty PDF text can mean the file is scanned or image-only; route to OCR/image extraction rather than splitting empty documents.
- Metadata filter fields should usually be prefixed with `meta.`, for example `meta.language`.

## Workflow-Specific Issues

Mixed file ingestion:
- Use `FileTypeRouter` or `MultiFileConverter` before format-specific processing.
- Validate counts per format, `unclassified`, and `failed` before merging documents.
- Keep optional PDF/DOCX dependencies isolated so text/Markdown ingestion can still succeed.

Metadata preservation:
- After conversion, assert important keys remain in `doc.meta`.
- After splitting, assert `source_id` is present and points to the original document ID.
- Avoid overwriting source-level metadata accidentally with a batch-level `meta` dictionary that uses the same keys.

Cache/fetch checks:
- Do not assume network access in tests.
- Use deterministic inline `ByteStream` inputs for smoke checks.
- For live fetches, record skipped, failed, and successfully fetched URLs distinctly.

Pipeline wiring:
- Component output names matter: connect `converter.documents` to `cleaner.documents`, then `cleaner.documents` to `splitter.documents`.
- `Pipeline.run()` input dictionaries are keyed by component name, such as `{"converter": {"sources": [...]}}`.
- If a component is a SuperComponent such as `DocumentPreprocessor` or `MultiFileConverter`, prefer its public `run()` method unless custom wiring is needed.

## Quick Debug Checklist

1. Print `type(item)` for a representative input and output at each step.
2. Assert output keys: `documents`, `streams`, MIME-type keys, `unclassified`, `failed`, or `unmatched`.
3. Assert counts before and after conversion, cleaning, splitting, and routing.
4. Inspect `doc.meta` after every stage that should preserve source information.
5. Reduce to `TextFileToDocument` plus `DocumentSplitter` before debugging optional converter backends.
6. Run `../scripts/ingestion_smoke_check.py` from this sub-skill to verify baseline public APIs.
