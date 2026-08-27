---
name: conversion
description: "Use Docling's Python conversion API for local paths, URLs,
  streams, and in-memory Markdown/HTML/DocLang strings, including safe smoke
  conversions and failure handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Conversion

Use this sub-skill when a task needs Python API conversion into a `DoclingDocument` with `DocumentConverter`, `convert`, `convert_all`, `convert_string`, or `DocumentStream`.

Route elsewhere when the task is mainly about:
- CLI commands, supported format tables, or shell recipes: `cli-and-formats`.
- Export formats, Markdown/JSON/HTML serialization strategy, or chunking: `document-outputs`.
- OCR, table structure, PDF model options, accelerator settings, or artifacts paths: `pipeline-configuration`.
- VLM, ASR, remote model services, or advanced backends: `advanced-pipelines`.
- Structured data extraction with `DocumentExtractor`: `extraction`.

## Fast Path

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")  # local path or URL
markdown = result.document.export_to_markdown()
```

For string content, do not pass the raw string to `convert`; use `convert_string` with a supported `InputFormat`:

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

converter = DocumentConverter(allowed_formats=[InputFormat.MD])
result = converter.convert_string("# Title\n\nBody", format=InputFormat.MD, name="note.md")
```

## References

- `references/api-reference.md` for constructor signatures, source types, limits, headers, batch conversion, and status handling.
- `references/workflows.md` for copy-ready local path, URL, stream, string, batch, and smoke-test recipes.
- `references/troubleshooting.md` for optional dependency, model download, wrong format option, headers, file limit, invalid path, and `raises_on_error` failures.
- `scripts/convert_fixture.py` for a safe installed-package helper that converts a caller-supplied path or string to Markdown or JSON.

## Safety Defaults

- Prefer `allowed_formats=[...]` for smoke tests and user-controlled uploads so accidental format detection cannot trigger heavier pipelines.
- Use `max_num_pages`, `max_file_size`, and `page_range` for PDFs or untrusted documents.
- Use `raises_on_error=False` when collecting partial batch results; inspect `result.status` and `result.errors` before exporting.
- Expect first PDF/image conversions to download model artifacts unless the environment has prefetched models.
