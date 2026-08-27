---
name: document-core
description: "Open, inspect, authenticate, convert, save, and safely manage
  PyMuPDF documents and shared geometry primitives."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Document Core

Use this sub-skill for the core PyMuPDF document lifecycle: open or create a document, inspect page/metadata/outline basics, authenticate protected PDFs, convert supported non-PDF inputs to PDF, choose a safe save mode, or reason about shared geometry primitives.

## Read or run

- [references/api-reference.md](references/api-reference.md) covers verified signatures and core objects.
- [references/workflows.md](references/workflows.md) covers open/save/convert/authenticate patterns.
- [references/troubleshooting.md](references/troubleshooting.md) covers open, password, save, format, corruption, and object-lifetime failures.
- Run [scripts/document_roundtrip_smoke.py](scripts/document_roundtrip_smoke.py) to create, serialize, reopen, and verify a tiny PDF.

## Boundaries

Route text/OCR/tables/RAG to [../text-tables-and-rag/SKILL.md](../text-tables-and-rag/SKILL.md), rendering/images to [../rendering-images-and-graphics/SKILL.md](../rendering-images-and-graphics/SKILL.md), PDF editing/forms/redaction to [../pdf-editing-annotations-forms/SKILL.md](../pdf-editing-annotations-forms/SKILL.md), and CLI/build/test concerns to [../cli-and-maintenance/SKILL.md](../cli-and-maintenance/SKILL.md).

## Default checklist

Use `import pymupdf`; open local paths with `pymupdf.open(path)`, memory with `pymupdf.open(stream=data, filetype="pdf")`, and text-like inputs with an explicit `filetype`. Authenticate when `doc.needs_pass` is true. Prefer full save to a new path unless intentional incremental update is supported. Reacquire pages and child objects after page-tree changes or document close/reopen.

