---
name: docs-and-parsing
description: "Use PaperQA parsing, chunking, document-format, PDF-reader, and
  multimodal media workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# docs-and-parsing

Use this sub-skill when the task is to parse local documents into PaperQA `Text`
chunks, select a PDF reader, diagnose parser dependency failures, or reason about
multimodal media extraction before retrieval/querying.

## Route here for

- `paperqa.readers.read_doc`, `parse_text`, `parse_image`, `parse_office_doc`,
  `chunk_text`, `chunk_pdf`, and code/Markdown line-based chunking.
- Local PDFs, `.txt`, Markdown/source/config files, `.html`, Office files,
  standalone images, and parser kwargs such as `page_range`, `page_size_limit`,
  `parse_media`, `full_page`, `dpi`, and `reader_config`.
- Choosing among `paper-qa-pypdf`, `paper-qa-pymupdf`, `paper-qa-docling`, and
  `paper-qa-nemotron`, including optional extras and service requirements.
- Understanding media parsing versus media enrichment cost and retrieval effects.

## Route elsewhere

- RAG querying, `Docs.aquery`, `ask`, `agent_query`, answer/evidence objects, and
  callbacks: use `../agentic-rag/`.
- CLI index scanning, manifest columns, file filters, full-text index reuse, and
  `pqa` commands: use `../cli-and-indexing/`.
- LLM/provider selection, enrichment model credentials, named settings, prompts,
  embeddings, or vector stores: use `../settings-and-configuration/`.

## Operating entry points

1. Start with [references/parsers-and-formats.md](references/parsers-and-formats.md)
   to choose the file-format path and PDF reader.
2. Use [references/api-reference.md](references/api-reference.md) for verified
   signatures, return shapes, parser kwargs, and safe parse/chunk recipes.
3. Use [references/troubleshooting.md](references/troubleshooting.md) when imports,
   corrupt files, media parsing, reader services, or enrichment fail.
4. Run [scripts/inspect_parsers.py](scripts/inspect_parsers.py) to inventory parser
   availability without requiring optional packages.
5. Run [scripts/parse_text_smoke.py](scripts/parse_text_smoke.py) for a no-network
   text/Markdown parse-and-chunk smoke before attempting PDFs or Office files.

## Minimal safe pattern

For a local text or Markdown file, parse and chunk without LLMs or embeddings:

```python
from paperqa.readers import parse_text, chunk_text
from paperqa.types import Doc

parsed = parse_text("notes.md")
texts = chunk_text(
    parsed,
    Doc(docname="notes", citation="Local notes", dockey="notes"),
    chunk_chars=1000,
    overlap=100,
)
```

For PDFs, construct `Settings(parsing={...})` or pass `parse_pdf=` directly to
`read_doc`; do not assume every optional reader or media backend is installed.
