# Conversion Troubleshooting

## Import or Optional Dependency Failures

Symptoms:

- Import errors while constructing a converter or loading a format backend.
- Runtime failures for audio, PDF/image model features, VLM, MLX, or API-backed backends.

Actions:

- Confirm the environment uses Python 3.10 or newer and has Docling installed.
- For basic Markdown/HTML conversion, restrict `allowed_formats` to avoid initializing heavier formats accidentally.
- For audio conversion, install ASR extras and ensure `ffmpeg` is available.
- For VLM, GPU, MLX, remote API, or advanced backend setup, route to `advanced-pipelines`.
- For PDF OCR/table/model option setup, route to `pipeline-configuration`.

## First Conversion Downloads Models

Docling may download model artifacts on first use for PDF/image and advanced pipelines. This is expected for online environments but can fail offline.

Actions:

- Use Markdown or HTML smoke tests when validating the conversion API itself.
- Prefetch models with public Docling tooling before offline PDF/image conversion.
- Configure artifacts paths through pipeline options or environment variables; route detailed setup to `pipeline-configuration`.

## Unsupported `convert_string` Format

Symptom:

```text
ValueError: format ... is not supported in `convert_string`
```

Cause:

`convert_string` supports only Markdown, HTML, and DocLang XML.

Fix:

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.MD])
result = converter.convert_string("# Title", format=InputFormat.MD, name="note.md")
```

For PDF, DOCX, PPTX, images, audio, CSV, XLSX, EPUB, email, LaTeX, or XML variants other than DocLang string content, provide a local path, URL, or `DocumentStream` with bytes and an extension-bearing `name`.

## No Recognizable Format

Symptoms:

- `ConversionError` says no recognizable format or format not in allowed formats.
- `convert_all` yields no result when errors are not raised.

Actions:

- Check that the file path exists and has a supported extension.
- For streams, provide a `DocumentStream(name="file.md", stream=...)` with the correct extension.
- Ensure `allowed_formats` includes the intended `InputFormat`.
- If input is a raw Markdown/HTML string, use `convert_string` rather than `convert`.

## Wrong `format_options` Keys or Classes

Symptoms:

- Validation errors when constructing `DocumentConverter`.
- A format fails because an option object does not match the input format.

Actions:

- Use `InputFormat` enum keys, not strings, in `format_options`.
- Pair each key with the matching format option class, such as `PdfFormatOption` for `InputFormat.PDF` or `HTMLFormatOption` for `InputFormat.HTML`.
- Keep conversion-only code simple; route detailed pipeline customization to `pipeline-configuration`.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption

converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF],
    format_options={InputFormat.PDF: PdfFormatOption()},
)
```

## URL Headers Do Not Work

Symptoms:

- HTTP 401, 403, or content negotiation failures.
- A URL succeeds in a browser but fails in code.

Actions:

- Pass headers to `convert` or `convert_all` for URL fetching.
- Use exact header strings required by the server, such as authorization or user-agent headers.
- Do not use `headers` to configure Docling remote service clients; remote services have separate service URL/API key and opt-in settings.

```python
result = converter.convert(
    "https://example.com/private/report.pdf",
    headers={"Authorization": "Bearer <token>", "User-Agent": "docling-client"},
)
```

## Limits Reject the Document

Symptoms:

- Conversion fails or skips because the document is too large or has too many pages.
- Only part of a PDF is needed but the full source is expensive.

Actions:

- Increase `max_file_size` only when the caller trusts the source and resources allow it.
- Increase `max_num_pages` only when full-document processing is intended.
- Use `page_range=(start, end)` for bounded PDF conversion.

```python
result = converter.convert(
    "manual.pdf",
    max_num_pages=20,
    max_file_size=25 * 1024 * 1024,
    page_range=(1, 20),
)
```

## Conversion Raises Instead of Returning Errors

Symptom:

- `ConversionError` stops a batch at the first failure.

Fix:

Use `raises_on_error=False` for best-effort processing and inspect each `ConversionResult`.

```python
for result in converter.convert_all(paths, raises_on_error=False):
    if result.errors:
        print([error.error_message for error in result.errors])
```

Only export from `result.document` after checking that the status is `SUCCESS` or `PARTIAL_SUCCESS`.

## Remote Services Are Blocked

Symptom:

- An error indicates remote operations are not allowed.

Cause:

Docling requires explicit opt-in before a pipeline sends user data to remote services.

Actions:

- Do not work around this in conversion code.
- Route the setup to `advanced-pipelines` or `pipeline-configuration` and configure the relevant pipeline options with explicit remote-service enablement.

## Invalid Paths or Unsafe HTML Resources

Symptoms:

- File not found errors.
- HTML conversion cannot resolve relative resources.
- Remote or absolute resources are rejected by safety checks.

Actions:

- Resolve caller-supplied paths before conversion when appropriate.
- For HTML strings, provide a meaningful `name` with `.html`; for HTML files, prefer file paths so relative resources can be resolved safely.
- Keep remote fetching explicit and avoid hidden network access in smoke tests.
