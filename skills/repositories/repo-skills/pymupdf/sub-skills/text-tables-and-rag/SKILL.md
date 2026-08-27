---
name: text-tables-and-rag
description: "Extract text, search, tables, OCR-aware textpages, and
  LLM/RAG-ready text outputs with PyMuPDF."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Text, Tables, and RAG

Use this sub-skill for text extraction, layout reconstruction, search locations, table detection/extraction, OCR boundaries, and Markdown/JSON/plain-text material for LLM and RAG pipelines.

## Read or run

- [references/text-extraction.md](references/text-extraction.md) covers `Page.get_text()` modes, clips, sorting, `TextPage`, words/blocks/dict/rawdict, and rotated text.
- [references/table-extraction.md](references/table-extraction.md) covers `Page.find_tables()`, `TableFinder`, `Table`, strategies, headers, Markdown, pandas, and lifetime rules.
- [references/rag-ocr.md](references/rag-ocr.md) covers PyMuPDF4LLM and Tesseract OCR as optional components.
- [references/troubleshooting.md](references/troubleshooting.md) covers empty/garbled text, table misses, and optional dependency failures.
- Run [scripts/extract_text_inspect.py](scripts/extract_text_inspect.py) and [scripts/table_detection_smoke.py](scripts/table_detection_smoke.py) for safe inspections.

## Boundaries

Opening/saving belongs to document-core; rendered images belong to rendering-images-and-graphics; annotation/redaction after search belongs to pdf-editing-annotations-forms; `python -m pymupdf gettext` belongs to cli-and-maintenance.

## Default decisions

Start with `page.get_text("text", sort=True)` or `words`; use `dict`/`rawdict` for spans/fonts/coordinates; use `search_for(..., quads=True)` for rotated text; use `find_tables()` and `Table.to_markdown()` for visible tables. Treat OCR and PyMuPDF4LLM as optional until verified.

