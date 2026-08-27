# Parser Reference

## Architecture Seams

RAGFlow has two parser layers:

- `deepdoc.parser`: format-specific parser classes and optional PDF backend adapters.
- Flow parser component: extension dispatch, `parser_config` normalization, output-format selection, PDF metadata normalization, and optional vision enrichment for media sections.

DeepDoc parsers are reusable parsing primitives. The flow parser component is the ingestion-pipeline wrapper that reads the source blob, selects a branch by file suffix, calls the parser, and writes outputs such as `json`, `markdown`, `text`, or `html` for downstream chunk/index stages.

## Extension Routing Matrix

| File family | Extensions | Default parser | Main outputs | Notes |
| --- | --- | --- | --- | --- |
| PDF | `pdf` | `RAGFlowPdfParser` through PDF branch | `json` or `markdown` | Supports DeepDoc, plain text, MinerU, Docling, OpenDataLoader, Tencent Cloud ADP, PaddleOCR, or configured VLM parser. |
| Spreadsheet | `xls`, `xlsx`, `csv` | `RAGFlowExcelParser` | `html`, `json`, or `markdown` | HTML output preserves complex tables; JSON output converts rows to key/value-style text. |
| DOC | `doc` | Tika-backed text extraction | `json` or `markdown` | Requires Tika availability; unsupported when Tika import/content fails. |
| DOCX | `docx` | DOCX parser wrapper | `json` or `markdown` | Extracts text, images, table HTML, heading outlines, optional TOC/header/footer removal. |
| Markdown | `md`, `markdown`, `mdx` | Markdown parser wrapper | `json` or `text` | Can separate tables and preserve code fences/tables during delimiter splitting. |
| Text/code | `txt`, `py`, `js`, `java`, `c`, `cpp`, `h`, `php`, `go`, `ts`, `sh`, `cs`, `kt`, `sql` | `RAGFlowTxtParser` | `json` or `text` | Uses token chunk size and delimiter splitting. |
| HTML | `htm`, `html` | `RAGFlowHtmlParser` | `json` or `text` | Removes scripts/styles/comments, chunks block text, appends table HTML. |
| Slides | `ppt`, `pptx` | `RAGFlowPptParser` | `json` | DeepDoc parses PPTX text; TCADP can handle PPT/PPTX if configured. |
| Image | `jpg`, `jpeg`, `png`, `gif` | DeepDoc OCR | `json` | OCR path returns image doc type; non-OCR VLM image parser can be configured. |
| EPUB | `epub` | `RAGFlowEpubParser` | `json` or `text` | Produces text sections. |
| Email/audio/video | `eml`, `msg`, audio/video suffixes | Specialized flow branches | `json` or `text` | These are parsed in the flow component rather than DeepDoc core classes. |

If a suffix does not match any configured family, parsing should fail with a clear unsupported-extension error.

## Parser Classes and Contracts

| Class or wrapper | Responsibility | Key contract |
| --- | --- | --- |
| `RAGFlowPdfParser` | DeepDoc PDF OCR, layout recognition, table structure recognition, text/table/figure extraction | Produces bbox-like items with text, layout, page/coordinate fields, images for tables/figures, and outlines. |
| `PlainParser` | Plain text extraction from PDFs | Produces text lines and skips OCR/layout/TSR. |
| `VisionParser` | Treats PDF pages as images and asks an image-to-text model | Produces text with PDF position tags from page-level image handling. |
| `MinerUParser` | Remote MinerU API client and content-list transfer | Converts MinerU blocks into text/table/image/equation/list sections with optional position tags. |
| `DoclingParser` | Local Docling or external Docling Serve parsing | Converts Docling text/formula/table/picture items into sections/tables with position tags where available. |
| `OpenDataLoaderParser` | Remote OpenDataLoader service client | Converts structured JSON or Markdown fallback into sections and table/image tuples. |
| `PaddleOCRParser` | Remote PaddleOCR async job API client | Converts layout/OCR JSONL results into sections with position tags; can parse images too. |
| `TCADPParser` | Tencent Cloud ADP document parser client | Downloads/extracts parsing result zip and converts JSON/Markdown outputs to sections/tables. |
| `RAGFlowDocxParser` and app wrapper | DOCX text, image, table, heading/outlines | JSON emits text/image/table sections; Markdown emits document markdown. |
| `RAGFlowExcelParser` | XLS/XLSX/CSV workbook loading and table conversion | `html()`, `markdown()`, and row-to-text `__call__()` variants. |
| `RAGFlowMarkdownParser` | Markdown tables and block extraction | Separates Markdown/HTML tables; protects fenced code and tables from delimiter splitting. |
| `MarkdownElementExtractor` | Markdown section splitter | Preserves code fences, Markdown tables, HTML tables, list blocks, blockquotes, and lone header merge behavior. |
| `RAGFlowHtmlParser` | HTML text/table extraction | Removes scripts/styles/comments, chunks block text, appends table HTML. |
| `RAGFlowTxtParser` | Plain text/code splitting | Splits by token budget and escaped/custom delimiters. |
| `RAGFlowPptParser` | Presentation text extraction | Extracts text from slide shapes. |
| `RAGFlowJsonParser` | JSON/JSONL splitting | Splits nested JSON while preserving structure where possible. |
| `RAGFlowEpubParser` | EPUB extraction | Emits text sections. |

## PDF Backend Selection

PDF parsing is selected through the PDF setup `parse_method` value:

| `parse_method` | Behavior | Use when |
| --- | --- | --- |
| `deepdoc` | Native OCR, layout recognition, table structure recognition, table auto-rotation, bbox normalization | Default for layout-heavy PDFs, scanned pages, tables, and figures. |
| `plain_text` | Extract only text lines, no OCR/layout/TSR | PDFs are guaranteed to contain selectable text and speed matters. |
| `mineru` or model ending `@MinerU` | Calls a configured MinerU provider/model and converts content-list output | Need MinerU's PDF-to-structured-output behavior. |
| `docling` | Calls local Docling or external Docling Serve | Need Docling conversion/chunking behavior or server-backed parsing. |
| `opendataloader` | Calls OpenDataLoader service and ingests JSON or Markdown fallback | Need deterministic local-first structured PDF parsing from the service. |
| `tcadp parser` | Calls Tencent Cloud ADP document parsing | Need TCADP cloud parser for PDF/spreadsheet/slides. |
| `paddleocr` or model ending `@PaddleOCR` | Calls configured PaddleOCR provider/model | Need PaddleOCR-VL or PP-OCR/PP-Structure backend behavior. |
| Other configured model id | Uses image-to-text/VLM parser | Need page-image description rather than DeepDoc OCR/layout. |

Backend names are case-normalized in several paths, but preserve public spelling in UI/API config where existing code expects it.

## Output Shapes

### PDF JSON Items

PDF parser branches normalize to bbox-like dictionaries before output:

```json
{
  "text": "extracted text",
  "layout_type": "text",
  "doc_type_kwd": "text",
  "_pdf_positions": [[1, 10.0, 200.0, 20.0, 40.0]]
}
```

Common `layout_type` values include `text`, `title`, `table`, `figure`, `equation`, and backend-specific labels. The flow wrapper maps `layout_type` into `doc_type_kwd`:

- `table` becomes `table` unless `flatten_media_to_text` is true.
- `figure` or image-bearing unlabeled blocks become `image` unless flattened.
- Everything else defaults to `text`.

Position tags use the parser-owned format `@@page	left	right	top	bottom##`. They are converted into normalized one-indexed PDF positions before downstream chunk metadata is finalized.

### Markdown and Text Outputs

Markdown output concatenates parser sections and converts titles to headings. PDF figure blocks become embedded image markdown only when an image is present. Text output is usually newline-joined plain sections.

### Table and Image Outputs

Table outputs may appear as HTML strings, text converted from cells, or table/image tuples with optional crops. Keep table/image distinction stable because downstream chunk builders and previews use `doc_type_kwd`, image IDs, and position metadata.

## Important Parser Config Keys

Parser config is extensible, but these keys directly affect parsing behavior:

| Key | Applies to | Meaning |
| --- | --- | --- |
| `parse_method` | Flow PDF/spreadsheet/slides setup | Backend selector such as `deepdoc`, `plain_text`, `mineru`, `docling`, `opendataloader`, `tcadp parser`, or `paddleocr`. |
| `output_format` | Most flow parser families | Must match allowed formats for that family, such as PDF `json`/`markdown`, spreadsheet `html`/`json`/`markdown`, Markdown `text`/`json`. |
| `lang` | PDF/image/OCR backends | Language hint; also maps to MinerU OCR language codes. |
| `flatten_media_to_text` | PDF/DOCX/Markdown/spreadsheet JSON paths | Forces table/image media sections to be treated as text. |
| `remove_toc` | PDF/DOCX/HTML/Markdown setup | Removes table-of-contents-like content using outlines or heuristics. |
| `remove_header_footer` | PDF/DOCX/HTML setup | Removes header/footer items by layout label or document header/footer text. |
| `enable_multi_column` | PDF DeepDoc branch | Reorders text boxes for multi-column PDFs using rendered page geometry. |
| `chunk_token_num` | TXT/HTML/Markdown-related splitting | Token budget for section splitting. |
| `delimiter` | TXT/Markdown splitting | Custom delimiter string; Markdown protects code fences and tables before splitting. |
| `html4excel` | Dataset/chunking configuration | General chunking flag that makes complex spreadsheet tables use HTML representation. Cross-check ingestion code when this is involved. |
| `table_result_type` | TCADP | Tencent Cloud ADP table result behavior. |
| `markdown_image_response_type` | TCADP | Tencent Cloud ADP image-in-markdown response behavior. |
| `mineru_lang` | MinerU | Language override before mapping to MinerU codes. |
| `mineru_parse_method` | MinerU | MinerU method, commonly `auto`, `txt`, or `ocr`. |
| `mineru_formula_enable` | MinerU | Enables formula extraction. |
| `mineru_table_enable` | MinerU | Enables table extraction; also affects table sanitization behavior. |
| `mineru_llm_name` | Flow PDF branch | Explicit MinerU provider model name when not encoded in parse method. |
| `opendataloader_llm_name` | Flow PDF branch | Explicit OpenDataLoader provider model name. |
| `paddleocr_llm_name` | Flow PDF branch | Explicit PaddleOCR provider model name. |
| `vlm` | PDF/DOCX/Markdown/media paths | Optional image-to-text model config for enriching image/table sections. |

Public dataset/document `parser_config` may use keys such as `layout_recognize`, `html4excel`, and chunk settings before the ingestion layer converts them into parser setup. If a parser_config bug crosses into task execution, use the dataset ingestion/retrieval sub-skill to verify config merge/default behavior.

## Format-Specific Notes

### PDF

DeepDoc PDF parsing initializes OCR, layout recognizer, table structure recognizer, and a text-concat XGBoost model. It detects garbled extracted PDF text using CID placeholder patterns, private-use/replacement/control characters, and subset-font heuristics. Table auto-rotation evaluates 0, 90, 180, and 270 degrees with OCR confidence and is enabled by default unless disabled via config/environment.

For PDF changes, verify:

1. Backend selection and provider/model resolution.
2. Outlines and TOC removal behavior.
3. `layout_type` normalization and `doc_type_kwd` mapping.
4. Position tag conversion to `_pdf_positions`, `position_int`, `page_num_int`, and `top_int` downstream.
5. Cropping behavior for table/image/text previews.

### DOCX and DOC

DOCX parsing preserves paragraphs, page-break tracking, tables, images, and heading outlines. Flow-level JSON output emits text sections plus table HTML sections; Markdown output goes through `to_markdown` in the app wrapper. Header/footer removal compares normalized text from DOCX section headers/footers. Legacy `.doc` uses Tika and should degrade clearly if Tika is unavailable or returns empty content.

### Spreadsheets

Spreadsheet parsing tries workbook loading with OpenPyXL, falls back through Pandas, and treats non-Excel bytes as CSV. Default row text combines headers and cell values. HTML output emits `<table><caption>sheet</caption>...` chunks and is the safer path for complex spreadsheets, merged cells, many columns, or multiple tables per sheet. The UI/docs `Excel to HTML` behavior corresponds to `html4excel` in ingestion config, while the flow parser's spreadsheet output uses `output_format: html`.

### Markdown

Markdown parsing separates Markdown tables, borderless pipe tables, and HTML tables. Delimiter splitting protects fenced code blocks, Markdown tables, and HTML tables; lone heading lines may be merged into the following prose chunk. When changing delimiter/table handling, include tests for backtick and tilde fences, nested fences, pipe tables, HTML tables, and headings adjacent to body text.

### HTML

HTML parsing removes `style`, `script`, inline style attributes, and comments. It chunks block text by token budget and appends table HTML. Header/footer removal happens in the flow wrapper by deleting `header`, `footer`, `role=banner`, and `role=contentinfo` elements.

### JSON and TXT

JSON parsing detects JSONL by sampling valid JSON lines and splits nested JSON into size-bounded chunks. TXT/code parsing decodes bytes, interprets delimiter escape sequences, and chunks by token budget.

## Parser Test Map

Useful native candidates:

- Markdown delimiter and table behavior: custom delimiters, code fences, nested fences, Markdown tables, HTML tables, and header merge cases.
- Excel parser: workbook/CSV loading, HTML chunk row splitting, empty/header-only chunk regressions.
- EPUB parser: text extraction and section output.
- MinerU parser: content-list fixture transfer, HTML sanitization, image/table/equation/list types, position tags.
- OpenDataLoader parser: multipart request setup, JSON response transfer, Markdown fallback, retry and error behavior.
- Docling parser: remote server payloads and fallback endpoints.
- PDF garbled detection: CID placeholders, Unicode private-use/replacement characters, subset-font CJK corruption heuristics.
- DOCX question/heading level and table column-role tests where parser output interacts with chunking.

## Change Checklist

1. Add or adjust parser class behavior with optional dependency guards.
2. Update flow parser setup defaults, allowed output formats, and backend selection if the new behavior is user-selectable.
3. Preserve output shape and metadata fields consumed by chunking/indexing.
4. Add parser-specific unit tests before broad ingestion tests.
5. Run the offline smoke helper to verify extension routing/config spelling/import availability.
6. Cross-check dataset ingestion/retrieval behavior if parser output shape, `parser_config`, or chunk method behavior changed.
