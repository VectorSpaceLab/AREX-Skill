# Structured Document Parsing Workflows

This reference groups the end-to-end document workflows that build on layout analysis, OCR, and VLM-based document parsing.

## The main choices

| Workflow | Best for | Key entry point | Common output |
| --- | --- | --- | --- |
| `PPStructureV3` | Layout-aware parsing with OCR, tables, formulas, seals, and charts | `paddleocr pp_structurev3` / `PPStructureV3` | Structured page results, Markdown-like layout output, OCR/table/formula fields |
| `PaddleOCRVL` | VLM-oriented structured document parsing | `paddleocr doc_parser` / `PaddleOCRVL` | Markdown / JSON-like parsing output with optional page restructuring |
| `PPChatOCRv4Doc` | Chat-style document extraction with vector or MLLM helpers | `paddleocr pp_chatocrv4_doc` / `PPChatOCRv4Doc` | `visual_info`, layout parsing, vector/chat helpers |
| `PPDocTranslation` | Document translation with layout-aware parsing | `paddleocr pp_doctranslation` / `PPDocTranslation` | Translation-oriented layout parsing and Markdown or export output |
| `DocUnderstanding` | Query-driven document understanding | `DocUnderstanding` | A text answer for a document/query pair |
| `FormulaRecognitionPipeline` | Formula extraction as a document workflow | `FormulaRecognitionPipeline` | Formula result list |
| `SealRecognition` | Seal-aware document parsing | `SealRecognition` | Seal OCR and layout-aware seal outputs |
| `TableRecognitionPipelineV2` | Table extraction with OCR and HTML/table output | `TableRecognitionPipelineV2` | Table structure, HTML, and OCR-linked table results |

## PP-StructureV3

Use PP-StructureV3 when you want a classic layout-aware document pipeline. It combines:

- document preprocessing
- layout detection
- OCR
- table recognition
- seal recognition
- formula recognition
- chart parsing

Typical control flags:

- `use_doc_orientation_classify`
- `use_doc_unwarping`
- `use_textline_orientation`
- `use_table_recognition`
- `use_formula_recognition`
- `use_chart_recognition`
- `use_seal_recognition`
- layout thresholds and merge modes
- text detection / recognition thresholds

## PaddleOCR-VL

Use PaddleOCR-VL when you want the VLM-oriented parser. Important decisions:

- choose the pipeline version (`v1`, `v1.5`, or `v1.6`)
- choose the VLM backend if the installed environment supports a non-native inference path
- decide whether to enable layout detection, OCR for image blocks, or seal/chart recognition
- decide whether to restructure pages or merge tables after parsing

PaddleOCR-VL exposes helper methods such as:

- `concatenate_markdown_pages()`
- `restructure_pages()`

The full pipeline is what future agents should use when they want the document-level result. Do not confuse it with a standalone VLM component run in isolation.

## PP-ChatOCRv4Doc

Use this workflow when the user wants chat-style extraction from documents. It adds helpers for:

- `build_vector()`
- `chat()`
- `mllm_pred()`
- vector and visual-info save/load helpers

## PPDocTranslation

Use this workflow for translation-oriented document parsing. It adds helpers such as:

- `visual_predict()`
- `load_from_markdown()`
- `concatenate_markdown_pages()`

## Document-level outputs

Depending on the workflow, outputs may include:

- Markdown text
- structured page results
- table HTML
- formula result lists
- OCR text and polygons
- resource files and exported assets

Use the workflow-specific save helpers instead of rebuilding filenames by hand.
