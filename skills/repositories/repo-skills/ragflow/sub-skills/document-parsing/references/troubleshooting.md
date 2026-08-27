# Troubleshooting Document Parsing

## Missing `beartype` or Core Imports

Symptoms:

- Importing the top-level package or parser wrapper fails before reaching the target parser.
- Errors mention `beartype`, optional document libraries, or import-time model/runtime dependencies.
- A source checkout cannot be installed in editable mode because package metadata and actual package roots disagree.

Checks:

1. Import the narrowest parser module possible instead of the entire application stack.
2. Run `python scripts/parse_smoke.py --extension pdf --check-imports` to see optional import availability without parsing files.
3. Confirm whether the error is a missing parser dependency, a broader application dependency, or package metadata/install layout issue.
4. For source-level inspection, avoid requiring full editable install when optional parser dependencies are unrelated to the change.

Fix patterns:

- Guard optional parser imports and raise actionable runtime errors when a user selects that backend.
- Do not import remote-provider parsers at app startup if they require credentials or heavyweight optional packages.
- Document missing dependency as parser-specific unless it affects all ingestion.
- Treat source install metadata mismatches as environment troubleshooting, not as parser behavior.

## Optional Document Libraries Missing

Symptoms:

- DOCX, spreadsheet, PPT, EPUB, JSON, Markdown, or HTML parser tests fail with missing packages.
- Errors mention packages such as document parsers, spreadsheet engines, Markdown renderer, BeautifulSoup, PDF tools, image libraries, or Tika.
- A parser works for one format but fails for another format in the same environment.

Checks:

1. Identify the exact file family and parser class.
2. Check whether the failure occurs on import, parser initialization, or actual parsing.
3. Validate extension routing and output format with `parse_smoke.py` before opening a real file.
4. For spreadsheet failures, distinguish XLSX/XLS/CSV handling and fallback engine behavior.
5. For legacy `.doc`, confirm Tika is installed and returns non-empty content.

Fix patterns:

- Add narrow dependency guards around the parser branch.
- Keep graceful fallback order intact, such as OpenPyXL to Pandas/calamine or Excel-to-CSV handling.
- Prefer format-specific tests with stubs/mocks over broad application startup when optional dependencies are missing.

## OCR Backend Not Installed or Model Unavailable

Symptoms:

- PDF/image parsing fails while initializing OCR, layout recognizer, table recognizer, ONNX runtime, XGBoost model, or image libraries.
- Logs mention model download failures, model file not found, unsupported layout recognizer type, or runtime provider errors.
- Scanned pages return empty text even though plain text PDFs work.

Checks:

1. Confirm the selected PDF backend is OCR-capable; `plain_text` intentionally skips OCR.
2. Check `LAYOUT_RECOGNIZER_TYPE`; only supported values should be used.
3. Confirm OCR/model assets are present or downloadable through the configured endpoint.
4. Check image rendering works for the PDF; OCR cannot run if pages cannot render.
5. For scanned images, test image OCR branch separately from PDF layout/table logic.

Fix patterns:

- Use DeepDoc, MinerU OCR, PaddleOCR, Docling, OpenDataLoader, or another configured OCR-capable backend for scanned PDFs.
- Surface missing model/runtime errors at parser selection time with backend-specific guidance.
- Do not silently fall back to plain text for scanned PDFs; it produces empty chunks and hides the cause.

## MinerU Mode Confusion

Symptoms:

- Error says MinerU model is not configured or `MINERU_APISERVER` is missing.
- `vlm-http-client` backend fails because no downstream server URL is configured.
- MinerU returns output, but text/table/image sections are missing or unexpectedly sanitized.
- Language or parse method appears ignored.

Checks:

1. Confirm RAGFlow is acting as a remote MinerU client, not running MinerU in-process.
2. Confirm the tenant/model provider exists or environment auto-provisioning variables are set.
3. Confirm `mineru_parse_method` is one of `auto`, `txt`, or `ocr`.
4. Confirm backend is one of the supported MinerU backend strings.
5. For `vlm-http-client`, confirm server URL is configured in addition to the MinerU API URL.
6. Inspect whether `mineru_table_enable` is changing HTML table sanitization behavior.

Fix patterns:

- Use `mineru_parse_method: ocr` for image-only PDFs when `auto` chooses text extraction poorly.
- Set a language that maps to MinerU's expected OCR language code.
- Preserve safe ZIP extraction and output file search behavior when changing MinerU output handling.
- Keep image/table/equation/list block transfers covered by fixture tests.

## Docling Local vs Remote Confusion

Symptoms:

- Error says `docling` is not importable despite expecting a server.
- Remote Docling server is reachable but conversion/chunking endpoint fails.
- Parser returns one giant Markdown section or no sections.

Checks:

1. Confirm whether `DOCLING_SERVER_URL` is set; remote mode should not require local `docling` import.
2. Probe server metadata/endpoints only when safe and requested; tests should mock remote requests.
3. Check remote response shape: document entries, chunks, Markdown, text, and results wrappers can vary.
4. Confirm parse method expected by downstream transfer: raw/manual/pipeline/paper tuple shapes differ.
5. Validate request timeout for large PDFs.

Fix patterns:

- Keep local package and remote-server paths separate.
- Prefer native Docling chunking endpoints when available, but keep conversion fallback.
- Convert remote Markdown/text fallback into sections even when structured document data is missing.

## PaddleOCR Configuration Confusion

Symptoms:

- Error says access token missing.
- Async job submit/poll/fetch fails or times out.
- Result JSONL cannot be parsed.
- OCR-only algorithm returns text but no layout blocks.

Checks:

1. Confirm access token and base URL are configured through provider/model or environment.
2. Confirm algorithm spelling matches a supported algorithm name.
3. Check request timeout covers submit, polling, and result fetch.
4. Inspect whether `algorithm_config` keys are supported and mapped to API field names.
5. For OCR-only fallback, verify recognized text boxes are converted into position tags.

Fix patterns:

- Raise clear errors for unsupported algorithm names and missing job IDs/result URLs.
- Keep fallback from `layoutParsingResults` to `ocrResults` for algorithms without layout output.
- Do not log or embed access tokens in runtime docs, errors, or test fixtures.

## OpenDataLoader Configuration Confusion

Symptoms:

- Error says `OPENDATALOADER_APISERVER` is not set.
- Health check fails or `/file_parse` retries all fail.
- Response has Markdown fallback but no structured JSON.
- Table/image positions are missing.

Checks:

1. Confirm service URL and optional API key are configured for the parser provider.
2. Confirm timeout is sufficient for the PDF size.
3. Verify `json_doc` transfer first; if absent, ensure `md_text` fallback produces sections.
4. Check page image rendering locally because crop/position conversion depends on local page images.
5. Validate bounding box coordinate conversion from PDF-space to image-space.

Fix patterns:

- Keep retry behavior bounded and error messages specific to service calls.
- Preserve Markdown fallback so service versions without structured JSON still produce text.
- Do not require Java on the RAGFlow host when the service container owns conversion.

## Tencent Cloud ADP Failures

Symptoms:

- Parser initialization fails with missing Tencent Cloud credentials.
- Cloud API returns no download URL or parsing result download fails.
- Extracted ZIP contains no useful JSON/Markdown result.
- Spreadsheet/slides parsing works locally but fails under TCADP mode.

Checks:

1. Confirm `tcadp_config` has secret id, secret key, region, and optional parser options.
2. Confirm file type sent to the provider matches PDF/XLSX/CSV/PPTX/PPT branch.
3. Check page start/end options.
4. Keep ZIP extraction safe: reject symlinks, absolute paths, traversal, and encrypted entries.
5. Confirm table and image response option values are passed as provider config.

Fix patterns:

- Fail fast when credentials are absent rather than creating partial parser state.
- Keep downloaded result handling isolated in temporary output and cleaned up when requested.
- Convert provider result types to stable section/table outputs before downstream chunking.

## PDF Garbled Text or Layout Problems

Symptoms:

- Extracted chunks contain `(cid:123)`, replacement characters, private-use glyphs, random punctuation, or unreadable CJK text.
- Chunks appear out of reading order for multi-column pages.
- Headers/footers or references dominate chunks.
- Tables/figures are mislabeled or missing captions.

Checks:

1. Confirm whether the PDF has selectable text or requires OCR.
2. Check garbled detection heuristics for CID placeholders, private-use/replacement/control characters, and subset-font CJK corruption.
3. Use OCR-capable parsing when source text extraction is corrupt.
4. For multi-column pages, check whether multi-column reordering is enabled and page images exist.
5. For header/footer removal, confirm layout labels and `remove_header_footer` behavior.
6. For TOC removal, inspect outlines and `remove_toc` behavior.

Fix patterns:

- Route garbled PDFs to DeepDoc OCR or a remote OCR backend instead of plain text.
- Preserve original bbox/position metadata when reordering text boxes.
- Keep header/footer removal conservative; over-removal can delete legitimate repeated content.

## Scanned PDF Produces Empty Chunks

Symptoms:

- Upload and parse complete, but no useful text appears.
- PDF preview exists but chunks are empty or only page remnants.
- Plain text parser returns nothing.

Checks:

1. Confirm `parse_method` is not `plain_text` for image-only PDFs.
2. Select an OCR-capable backend: DeepDoc, MinerU with OCR method, PaddleOCR, Docling/OpenDataLoader if configured, or a VLM parser for page descriptions.
3. Confirm language/provider settings match the document.
4. Check parser output before downstream ingestion: are sections/bboxes non-empty?
5. If parser output is non-empty but chunks are missing, switch to the dataset ingestion/retrieval sub-skill and inspect chunk building/indexing.

Fix patterns:

- Change parser backend/config rather than tuning retrieval thresholds.
- Add tests that assert parser output has text and layout metadata before indexing.
- Keep backend errors visible; an empty parser result should not masquerade as successful ingestion.

## Excel to HTML and Complex Tables

Symptoms:

- Spreadsheet chunks are garbled key/value lines.
- Merged cells, many columns, multiple tables, or complex sheets lose structure.
- Enabling PDF parser options does not affect spreadsheets.

Checks:

1. Confirm the file is a spreadsheet (`xls`, `xlsx`, or `csv`) and uses the spreadsheet branch.
2. Confirm `html4excel` or spreadsheet `output_format: html` is enabled for complex tables.
3. Inspect whether HTML output includes table captions and rows.
4. Confirm row chunking does not emit header-only chunks.
5. Confirm table chunks are preserved downstream rather than flattened unexpectedly.

Fix patterns:

- Use HTML output for complex spreadsheets.
- Keep CSV fallback separate from Excel workbook loading errors.
- Cross-check dataset ingestion/retrieval if `html4excel` is set in dataset config but flow parser setup still emits JSON.

## Table and Image Metadata Missing

Symptoms:

- Table/image chunks exist but previews/citations are missing.
- PDF chunks lack page numbers or coordinates.
- Cropping warnings mention out-of-range page indices or no page images.
- Image/table chunks become plain text unexpectedly.

Checks:

1. Confirm parser emitted position tags or bbox fields.
2. Confirm page images were rendered before crop calls.
3. Confirm position tags are one-indexed externally and normalized consistently.
4. Check `flatten_media_to_text`; it intentionally changes table/image doc type to text.
5. Confirm `layout_type` is normalized before assigning `doc_type_kwd`.
6. Check image storage conversion only after parser output has images.

Fix patterns:

- Preserve `@@page	left	right	top	bottom##` tags when transferring remote backend output.
- Keep `extract_positions`, crop, and PDF metadata normalization in sync.
- Do not drop image/table data when converting backend-specific tuples into shared bboxes.

## Parser Config Key Typos

Symptoms:

- Parser ignores a setting with no explicit error.
- Backend is not selected even though config appears to request it.
- Output format falls back to defaults.
- MinerU/PaddleOCR provider model name is not used.

Checks:

1. Run `python scripts/parse_smoke.py --extension pdf --config parser_config.json`.
2. Confirm setup family: PDF settings belong under `pdf` in flow parser config, spreadsheet settings under `spreadsheet`, and so on.
3. Check backend-specific spelling: `parse_method`, `mineru_parse_method`, `mineru_table_enable`, `paddleocr_llm_name`, `opendataloader_llm_name`, `table_result_type`, `markdown_image_response_type`.
4. Confirm public dataset config keys such as `layout_recognize` or `html4excel` have been converted by ingestion code before expecting flow parser behavior.
5. Confirm requested `output_format` is allowed for the file family.

Fix patterns:

- Normalize aliases at the service/ingestion boundary, not inside every parser class.
- Make unsupported output formats and backend names fail clearly.
- Add focused tests for config merge/defaults when typos could otherwise be silent.

## Adding a New Structured Output Type

Use this checklist when adding a new block such as chart, formula subtype, structured figure, or provider-specific semantic region:

1. Define how the parser backend labels the block and how it maps to `layout_type`.
2. Decide whether downstream `doc_type_kwd` should be `text`, `table`, or `image`.
3. Preserve text, bbox/position tags, optional image crop, captions, and provider metadata needed for citations.
4. Update PDF metadata normalization if the new block carries positions in a new shape.
5. Add parser-level tests for transfer logic before ingestion tests.
6. Cross-check dataset ingestion/retrieval for chunk insertion, image ID storage, and retrieval display.

## Safe Native Test Strategy

Start with parser-unit tests before running broad ingestion tests:

- Markdown parser: delimiters, code fences, tables, and header merge behavior.
- Excel parser: complex table HTML, CSV fallback, empty sheets, row limits.
- PDF parser: garbled detection and position normalization.
- MinerU/OpenDataLoader/Docling/PaddleOCR: mocked provider responses and fixture transfer.
- DOCX/table interaction: heading levels and table column-role tests when parser output feeds chunking.

Avoid tests that require live remote parser services unless the test is explicitly integration-scoped and credentials/service URLs are provided by the user.
