---
name: document-parsing-and-conversion
description: "Routes PaddleOCR users to structured document parsing,
  PaddleOCR-VL, and Office conversion workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Document Parsing and Conversion

Use this route when the task is about turning a page, PDF, scan, or office document into structured Markdown, JSON, or other document-centric outputs. This is the sub-skill for full pipelines, not single-model OCR predictors.

## Handle these tasks here

- `PPStructureV3` and `PaddleOCRVL` document parsing.
- `DocPreprocessor`, `DocUnderstanding`, `PPChatOCRv4Doc`, `PPDocTranslation`, `FormulaRecognitionPipeline`, `SealRecognition`, and `TableRecognitionPipelineV2`.
- Office document conversion through `doc2md_convert`, `doc2md_supported_formats`, and the `paddleocr doc2md` CLI.
- Document-level outputs such as Markdown, JSON, page restructuring, resource saving, and layout-aware formatting.

## Route away from here

- Plain OCR, text detection, recognition, orientation, and unwarping belong in `local-ocr-pipelines`.
- Hosted API, MCP, and LangChain integration belong in `cloud-api-and-integrations`.
- Training, export, deployment, and TIPC evidence belong in `training-export-and-deployment`.

## Read these references

- [`references/document-parsing-workflows.md`](references/document-parsing-workflows.md) for PP-StructureV3, PaddleOCR-VL, and the document understanding family.
- [`references/doc2md-reference.md`](references/doc2md-reference.md) for Office document conversion, supported formats, and output behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md) for doc-parser, VLM, and doc2md failures.

## Use the bundled scripts

- [`scripts/run_document_parser.py`](scripts/run_document_parser.py) wraps the public structured-document pipelines.
- [`scripts/convert_office_doc_to_markdown.py`](scripts/convert_office_doc_to_markdown.py) wraps the public doc2md converter.

## What future agents should know

- `PPStructureV3` is the classic layout-aware pipeline that combines layout detection, OCR, table recognition, seal recognition, formula recognition, and chart parsing.
- `PaddleOCRVL` is the VLM-oriented document parser. Use the full pipeline, not only the underlying VLM component, when you need the highest-fidelity structured parsing workflow.
- `PPChatOCRv4Doc` and `PPDocTranslation` are document workflows with additional vector, chat, translation, and reformatting helpers.
- `doc2md_convert()` returns a conversion result with Markdown plus optional extracted images for office documents.
- The document parsing family has more optional extras than the base package. Read the installation reference before selecting a backend or an extra.

## Common triggers

- "Convert this PDF to Markdown"
- "Extract the tables and formulas from this document"
- "Should I use PP-StructureV3 or PaddleOCR-VL?"
- "How do I convert DOCX/XLSX/PPTX to Markdown?"
- "Why is the document parser using the wrong pipeline version?"
