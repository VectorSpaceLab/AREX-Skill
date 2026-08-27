# Conversion API Reference

Docling's primary Python conversion entry point is `docling.document_converter.DocumentConverter`. It converts one or more sources into `ConversionResult` objects whose `document` attribute is a `DoclingDocument`.

## Imports

```python
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter
```

For basic conversion, these imports are enough. Format-specific option classes such as `PdfFormatOption`, `HTMLFormatOption`, and `MarkdownFormatOption` are accepted through `format_options`, but detailed OCR, table, backend, accelerator, and model configuration belongs in `pipeline-configuration` or `advanced-pipelines`.

## Constructor

```python
converter = DocumentConverter(
    allowed_formats=None,
    format_options=None,
)
```

- `allowed_formats`: optional list of `InputFormat` enum values. If omitted, all installed supported input formats are allowed.
- `format_options`: optional mapping from `InputFormat` to a matching format option object.
- Good safety pattern: restrict `allowed_formats` when the caller knows the expected type.

```python
converter = DocumentConverter(allowed_formats=[InputFormat.MD, InputFormat.HTML])
```

Supported `InputFormat` values in the installed package include `docx`, `pptx`, `html`, `image`, `pdf`, `asciidoc`, `md`, `csv`, `xlsx`, `xml_uspto`, `xml_jats`, `xml_xbrl`, `xml_doclang`, `mets_gbs`, `json_docling`, `audio`, `vtt`, `latex`, `email`, and `epub`.

## `convert`

```python
result = converter.convert(
    source,
    headers=None,
    raises_on_error=True,
    max_num_pages=sys.maxsize,
    max_file_size=sys.maxsize,
    page_range=(1, sys.maxsize),
)
```

Use `convert` for one local path, URL, or `DocumentStream`.

- `source`: `str`, `pathlib.Path`, or `DocumentStream`.
- `headers`: optional HTTP headers for URL inputs only, such as authorization or user-agent headers.
- `raises_on_error`: if `True`, failed conversion raises `ConversionError`; if `False`, errors are captured on `ConversionResult`.
- `max_num_pages`: maximum pages accepted for a document.
- `max_file_size`: maximum source size in bytes.
- `page_range`: inclusive page range tuple, typically useful for PDFs.

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert(Path("paper.pdf"), max_num_pages=10, page_range=(1, 3))
print(result.document.export_to_markdown())
```

## URL Conversion and Headers

```python
converter = DocumentConverter()
result = converter.convert(
    "https://example.com/report.pdf",
    headers={"Authorization": "Bearer <token>"},
    max_file_size=20 * 1024 * 1024,
)
```

Headers are passed while fetching URL sources. For remote conversion services or service-client settings, route to the remote/service guidance instead of using `DocumentConverter` headers as a substitute.

## `DocumentStream`

Use `DocumentStream` for binary streams or generated content where a filename extension should drive format detection.

```python
from io import BytesIO
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter

html = b"<html><body><h1>Hello</h1></body></html>"
source = DocumentStream(name="page.html", stream=BytesIO(html))
converter = DocumentConverter(allowed_formats=[InputFormat.HTML])
result = converter.convert(source)
```

The `name` should include the expected extension, such as `.pdf`, `.html`, or `.md`.

## `convert_string`

```python
result = converter.convert_string(content, format, name=None)
```

Use `convert_string` for raw string content. It supports only:

- `InputFormat.MD`
- `InputFormat.HTML`
- `InputFormat.XML_DOCLANG`

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.MD])
result = converter.convert_string(
    "# Release notes\n\n- Added conversion support.",
    format=InputFormat.MD,
    name="release-notes.md",
)
```

If a task tries `convert_string(..., format=InputFormat.PDF)` or another unsupported string format, advise using a file path, URL, `DocumentStream`, or one of the three supported string formats.

## `convert_all`

```python
for result in converter.convert_all(
    sources,
    headers=None,
    raises_on_error=True,
    max_num_pages=sys.maxsize,
    max_file_size=sys.maxsize,
    page_range=(1, sys.maxsize),
):
    ...
```

Use `convert_all` for batch conversion. It yields `ConversionResult` objects in iteration order.

```python
from pathlib import Path
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter

paths = sorted(Path("incoming").glob("*.md"))
converter = DocumentConverter(allowed_formats=[InputFormat.MD])

for result in converter.convert_all(paths, raises_on_error=False):
    if result.status in {ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS}:
        print(result.document.export_to_markdown()[:200])
    else:
        messages = [error.error_message for error in result.errors]
        print(f"failed: {result.input.file}: {'; '.join(messages)}")
```

## Result Handling

`ConversionResult` exposes status, input metadata, errors, and a converted `DoclingDocument` when conversion succeeds.

```python
from docling.datamodel.base_models import ConversionStatus

if result.status == ConversionStatus.SUCCESS:
    text = result.document.export_to_markdown()
elif result.status == ConversionStatus.PARTIAL_SUCCESS:
    text = result.document.export_to_markdown()
    # Preserve warnings/errors for user review.
else:
    messages = [error.error_message for error in result.errors]
    raise RuntimeError("; ".join(messages) or f"conversion status: {result.status}")
```

For export methods and output-format choices, route to `document-outputs`.
