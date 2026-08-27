---
name: document-parsing
description: "Modify and debug RAGFlow DeepDoc document parsers, PDF OCR/layout
  backends, parser_config parsing options, and parser-specific tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Document Parsing

Use this sub-skill when changing or debugging RAGFlow's document parsing layer: DeepDoc parsers, PDF OCR/layout/table recognition, parser backend selection, file-extension routing, parser output metadata, or parser-specific tests.

## Start Here

1. Identify the file family and parser backend before editing:
   - PDF: DeepDoc, plain text, MinerU, Docling, OpenDataLoader, Tencent Cloud ADP, PaddleOCR, or a configured VLM parser.
   - Office/text formats: DOC/DOCX, spreadsheets, slides, HTML, Markdown, JSON, TXT/code, EPUB, images, email, audio, and video.
2. Check the relevant reference:
   - `references/parser-reference.md` for parser classes, extension routing, output shapes, parser_config keys, and tests.
   - `references/ocr-backends.md` for DeepDoc OCR/layout/TSR and optional PDF parser providers.
   - `references/troubleshooting.md` for missing imports, backend configuration, garbled PDFs, empty scanned PDFs, Excel tables, and metadata problems.
3. For safe offline validation, run the bundled helper before parsing real files:
   - `python scripts/parse_smoke.py --extension pdf --config parser_config.json`
   - `python scripts/parse_smoke.py --extension xlsx --config '{"spreadsheet":{"output_format":"html"}}'`

## Scope Boundaries

- Include `deepdoc.parser` classes, `deepdoc.vision` OCR/layout/table recognition, parser wrappers, PDF backend options, `parser_config` keys that affect parsing, and parser-specific tests.
- Exclude dataset task orchestration, indexing, embedding, retrieval ranking, RAPTOR, and GraphRAG; use the dataset ingestion/retrieval sub-skill for those flows.
- Exclude public REST/SDK client recipes; use the SDK/HTTP integration sub-skill for API callers.
- Exclude deployment startup and service composition; use deployment/configuration guidance for Redis, MySQL, MinIO, Elasticsearch/Infinity, and parser provider services.

## High-Value Checks

- Preserve parser output contracts: PDF JSON items carry `text`, `layout_type`, `doc_type_kwd`, and position metadata where available; table/image chunks must not silently become plain text unless `flatten_media_to_text` is intended.
- Keep file extension routing aligned with parser defaults and `allowed_output_format`; unknown extensions should fail clearly.
- Treat optional parsers as optional: guard imports/configuration and prefer actionable errors over import-time crashes.
- Validate parser_config spelling and backend-specific key names before assuming a parser bug.
- When parser changes affect chunk shape, cross-check the dataset ingestion/retrieval sub-skill because downstream chunk builders consume parser output.

## Native Verification Candidates

Prefer focused parser tests for Markdown delimiter/table protection, Excel/EPUB parsing, MinerU content-list transfer, OpenDataLoader service response transfer, Docling remote payloads, PDF garbled detection, DOCX heading/question levels, and table chunk column roles.

## Difficult Usability Cases

- Diagnose a scanned PDF producing empty chunks by selecting an OCR-capable backend, validating OCR/provider configuration, confirming page images/layout boxes, and checking downstream chunk visibility.
- Add support for a new structured PDF output block while preserving `layout_type`, text/table/image distinction, bounding-box position tags, crop/preview behavior, and downstream metadata fields.
