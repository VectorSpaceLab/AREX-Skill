---
name: document-ingestion
description: "Ingest, parse, split, and validate documents for Kotaemon indexing workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Document Ingestion

Use this sub-skill when a task involves turning files, URLs, scanned documents, tables, or pre-parsed records into Kotaemon `Document` objects before indexing.

## Use This For

- Choosing a Kotaemon reader for PDF, table-heavy PDF, OCR, DOCX, HTML/MHTML, XLSX, TXT, directory, or web URL ingestion.
- Preserving or checking metadata such as `source`, `type`, `table_origin`, `page_label`, `file_name`, `file_path`, `sheet_name`, and `image_origin` before indexing.
- Configuring chunking with `TokenSplitter`, sentence-window splitting with `SentenceWindowSplitter`, or LlamaIndex extractors for titles/summaries.
- Diagnosing parser dependency, suffix, OCR/model, table extraction, or chunk-size problems.
- Validating small synthetic document-record fixtures with `scripts/validate_document_metadata.py` before handing them to an index.

## Route Elsewhere

- Use `../rag-core/SKILL.md` for vector indexes, retrieval pipelines, reranking, QA, citations, `RetrievedDocument`, and final answer composition.
- Use `../app-deployment/SKILL.md` for app login, UI upload flows, Gradio settings screens, Docker/local launch, and PDF.js setup.
- Use `../model-providers/SKILL.md` for LLM, embedding, VLM endpoint, API-key, Ollama, Azure OpenAI, or GraphRAG provider setup.

## Fast Path

1. Identify input shape: local file, directory, URL, OCR output, or already serialized `Document` records.
2. Pick a reader from `references/loaders-and-parsers.md`; prefer simple local readers first and structure-aware readers only when tables/images/layout matter.
3. Pass stable provenance through `extra_info`, commonly `source`, dataset id, tenant id, or upload id.
4. Inspect output metadata with `references/data-formats.md`; table documents should carry `type: table` and `table_origin` when a table-aware reader is used.
5. Split only after parsing: start with `TokenSplitter(chunk_size=1024, chunk_overlap=20)` and tune from observed chunk length and citation needs.
6. Validate fixture JSON before indexing:

```bash
python scripts/validate_document_metadata.py documents.json
```

## Reader Selection Heuristics

- Basic text PDF: `AutoReader("PDFReader")` or `PDFThumbnailReader` when page thumbnails are needed.
- Table-heavy PDF: `DoclingReader`, `PaddleOCRVLReader`, `PPStructureV3Reader`, `OCRReader`, `MathpixPDFReader`, `AzureAIDocumentIntelligenceLoader`, or `AdobeReader`, depending on installed dependencies and service credentials.
- Office/web formats: `DocxReader`, `ExcelReader`, `PandasExcelReader`, `HtmlReader`, `MhtmlReader`, `TxtReader`, `WebReader`, or `UnstructuredReader`.
- Mixed folders: `DirectoryReader` with `required_exts`, `exclude`, `recursive`, `file_metadata`, and optional per-extension `file_extractor` mappings.

## Difficult Cases

- Table-heavy PDF returns only plain text: compare the selected reader against `references/loaders-and-parsers.md`, confirm table-aware optional dependencies or credentials, then inspect metadata for `type: table` and `table_origin` using `references/data-formats.md`.
- Mixed pre-parsed records fail at indexing time: run `scripts/validate_document_metadata.py` on a tiny JSON fixture and fix missing `content`/`text`, non-object metadata, or inconsistent table metadata before routing to `../rag-core/SKILL.md`.

## References

- `references/loaders-and-parsers.md` - reader classes, parser dependencies, splitter/extractor choices, and selection matrix.
- `references/data-formats.md` - `Document` shape, metadata expectations, table/image records, and validation examples.
- `references/troubleshooting.md` - optional dependency failures, suffix errors, OCR/model/network issues, table parsing as plain text, and bad metadata.
