# Conversion Workflows

These recipes use only public Docling Python APIs and work from an installed package.

## Minimal Local or URL Conversion

```python
from docling.document_converter import DocumentConverter

source = "document.pdf"  # local path, URL, or pathlib.Path
converter = DocumentConverter()
result = converter.convert(source)
markdown = result.document.export_to_markdown()
```

Use this for normal one-off conversion. If the source is untrusted or user-provided, add `allowed_formats`, page limits, and file-size limits.

## Restricted Markdown Smoke Test

Markdown conversion is a good low-cost smoke check because it avoids PDF model startup and can run in memory.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.MD])
result = converter.convert_string(
    "# Smoke Test\n\n- alpha\n- beta",
    format=InputFormat.MD,
    name="smoke.md",
)
assert "Smoke Test" in result.document.export_to_markdown()
```

## In-Memory HTML or Markdown

Use `convert_string` for text content that is already in memory.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.HTML])
result = converter.convert_string(
    "<html><body><h1>Title</h1><p>Body</p></body></html>",
    format=InputFormat.HTML,
    name="page.html",
)
```

Supported string formats are Markdown, HTML, and DocLang XML. For any other format, provide a path, URL, or `DocumentStream` with bytes and an extension-bearing name.

## Binary Stream Conversion

Use `DocumentStream` for uploaded files, bytes received from another service, or files already opened in memory.

```python
from io import BytesIO
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.document_converter import DocumentConverter

payload = b"# Streamed note\n\nConverted from memory."
source = DocumentStream(name="note.md", stream=BytesIO(payload))
converter = DocumentConverter(allowed_formats=[InputFormat.MD])
result = converter.convert(source)
```

Choose a `name` with the real extension. Without a recognizable extension or allowed format, conversion can fail because Docling cannot determine the backend.

## URL with Headers and Limits

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
result = converter.convert(
    "https://example.com/private/report.pdf",
    headers={"Authorization": "Bearer <token>"},
    max_num_pages=25,
    max_file_size=30 * 1024 * 1024,
    page_range=(1, 10),
)
```

Headers are for fetching the URL source. Remote services used inside pipelines still require explicit pipeline options such as `enable_remote_services=True`; route that setup to `advanced-pipelines` or `pipeline-configuration`.

## Batch Conversion with Error Collection

```python
from pathlib import Path
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter

sources = sorted(Path("uploads").glob("*.md"))
converter = DocumentConverter(allowed_formats=[InputFormat.MD])

converted = []
failed = []
for result in converter.convert_all(sources, raises_on_error=False):
    if result.status in {ConversionStatus.SUCCESS, ConversionStatus.PARTIAL_SUCCESS}:
        converted.append(result.document)
    else:
        failed.append(
            {
                "input": str(result.input.file),
                "errors": [error.error_message for error in result.errors],
            }
        )
```

Use `raises_on_error=False` when the caller wants a best-effort batch. Use `raises_on_error=True` when one bad document should stop the whole operation.

## Convert to JSON for Downstream Systems

Conversion and export are separate concerns. This recipe performs conversion, then uses a basic `DoclingDocument` export.

```python
import json
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.MD])
result = converter.convert_string("# Title\n\nText", format=InputFormat.MD, name="note.md")
payload = json.dumps(result.document.export_to_dict(), ensure_ascii=False)
```

For choosing between Markdown, JSON, YAML, HTML, text, DocTags, VTT, or DocLang output, route to `document-outputs`.

## Page and File Limit Pattern

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.PDF])
result = converter.convert(
    "large.pdf",
    max_num_pages=5,
    max_file_size=10 * 1024 * 1024,
    page_range=(1, 5),
)
```

`max_num_pages` rejects documents over the limit. `page_range` controls which pages are processed. `max_file_size` protects against oversized inputs.

## Bundled Helper Script

The bundled `scripts/convert_fixture.py` supports two safe modes:

```bash
python scripts/convert_fixture.py --input note.md --output-format markdown
python scripts/convert_fixture.py --string '# Title' --input-format md --output-format json
```

It is intended for smoke conversion of caller-supplied fixtures. It does not require a Docling source checkout.
