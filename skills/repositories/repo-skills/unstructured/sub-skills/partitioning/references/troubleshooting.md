# Partitioning Troubleshooting

## First Checks

Run doctor before changing code:

```bash
python -m unstructured.cli doctor
python -m unstructured.cli doctor --for pdf
python -m unstructured.cli doctor --file docs/report.pdf
```

Use the bundled wrapper when you also want JSON output or a small partition preview:

```bash
python scripts/partition_diagnostics.py --for pdf --json
python scripts/partition_diagnostics.py --partition docs/report.pdf --strategy fast --limit 3
```

## Exactly-One Input Errors

Most partitioners require exactly one source argument. Common valid patterns:

- `partition(filename="report.pdf")`
- `partition(file=binary_file, metadata_filename="report.pdf")`
- `partition(url="https://example.com/report.pdf", request_timeout=30)`
- `partition_text(text="...")`
- `partition_html(text="...")`

Do not pass both `filename` and `file`, or both `text` and `filename`, unless the specific partitioner documents that combination.

## Unsupported or Misdetected Formats

Symptoms: unknown file type, unsupported format, JSON rejected, or the wrong partitioner is selected.

Actions:

- Pass `content_type` when MIME type is trustworthy.
- Pass `metadata_filename` for file-like objects so extension detection has a logical filename.
- Install/fix `libmagic` if doctor warns that MIME detection is degraded.
- For JSON, ensure the input is an unstructured element JSON array; for NDJSON, ensure each record is newline-delimited JSON.
- For source-code-like files, expect plain text classification.

## Missing Python Extras

Symptoms: `ModuleNotFoundError`, doctor reports missing modules, or partitioner imports fail.

Install only the needed extra:

```bash
pip install "unstructured[pdf]"
pip install "unstructured[docx]"
pip install "unstructured[xlsx]"
pip install "unstructured[md]"
pip install "unstructured[audio]"
```

Prefer targeted extras over `all-docs` for constrained environments. Use `all-docs` only when the user explicitly wants broad local format support and accepts the dependency footprint.

## Missing System Tools

- `libmagic`: affects MIME detection; extension fallback may still work but is less robust.
- `pandoc`: needed by pypandoc-backed RST/RTF/ODT/Org/EPUB flows when no bundled binary is available.
- `soffice`: required for legacy `.doc` and `.ppt` conversion through LibreOffice.
- `tesseract`: required for OCR paths in scanned PDF/image workflows.
- `poppler` or image/PDF conversion tools: commonly required by the PDF/image stack.
- `ffmpeg`: required for Whisper/audio decoding.

If a tool cannot be installed, switch strategy or route to an approved API workflow when the user permits network processing.

## PDF/Image Strategy Confusion

- `fast` is PDF-only and requires extractable embedded text.
- `ocr_only` requires OCR dependencies; it produces OCR text without layout segmentation.
- `hi_res` requires layout inference dependencies; use it for table structure, image blocks, coordinates, forms, and layout-aware extraction.
- `auto` can fall back and warn based on dependency availability and text extractability.
- Image inputs default to `hi_res` under `auto`; `fast` is invalid for images.

For table HTML in PDFs/images, use `hi_res` and enable table inference. In `partition_pdf`, use `infer_table_structure=True`; in `partition()`, control `skip_infer_table_types`.

## Deprecated Options

- Prefer `languages` over `ocr_languages`.
- Prefer `hi_res_model_name` over `model_name`.
- Prefer `skip_infer_table_types` over `pdf_infer_table_structure`.
- `extract_images_in_pdf` is marked for deprecation; prefer `extract_image_block_types` with `extract_image_block_output_dir` or `extract_image_block_to_payload`.

## Language and OCR Issues

- Use Tesseract language codes or codes that unstructured can map, such as `languages=["eng", "spa"]`.
- Install the corresponding Tesseract language packs on the system.
- Do not use `ocr_languages="auto"`; use `languages=["auto"]` for language detection where supported.
- Set `detect_language_per_element=True` only when per-element metadata is required because it can add overhead.

## URL and Network Problems

- Always set `request_timeout` for URL partitioning.
- Pass `headers` only with `url`; they are ignored for local files.
- Use `ssl_verify=False` only for explicitly approved debugging against known internal endpoints.
- If the URL returns HTML, prefer `partition_html(url=...)`; otherwise use `partition(url=..., content_type=...)` if MIME detection needs help.

## API Workflow Failures

API partitioning requires credentials, endpoint selection, network connectivity, and payload-size planning. Failures often come from missing API keys, wrong endpoint, strategy not supported by the service, large PDFs, or invalid JSON responses. Keep retries idempotent and avoid logging secrets. For large PDFs, split outside this skill, preserve `starting_page_number`, and combine JSON arrays in order.

## Table Inspection Problems

If `scripts/inspect_tables.py` finds no tables:

- Confirm elements contain `type == "Table"`.
- Confirm each table has `metadata.text_as_html`; plain table text alone is not enough.
- Re-run partitioning with table structure enabled and `strategy="hi_res"` for PDF/image cases.
- For CSV/XLSX, verify the partitioner actually emits table HTML for the chosen input and options.

## Performance and Timeouts

- Start with `strategy="fast"` for digital PDFs unless layout/table/OCR features are required.
- Avoid `detect_language_per_element` on large corpora unless needed.
- Avoid `all-docs` installation in small environments.
- For long PDFs, process page splits and preserve `starting_page_number`.
- For remote URLs or APIs, set explicit timeouts and retry budgets.