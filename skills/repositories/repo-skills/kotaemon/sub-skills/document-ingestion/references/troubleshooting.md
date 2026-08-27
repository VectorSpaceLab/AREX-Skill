# Document Ingestion Troubleshooting

Use this guide for parser, metadata, and splitting failures before handing records to indexing. For retrieval quality, reranking, citations, or QA failures after indexing, route to `../../rag-core/SKILL.md`.

## Optional Parser Dependency Missing

Symptoms:

- `ImportError: Please install docling`
- `ImportError: Please install paddleocr`
- `docx is not installed`
- `html2text is not installed`
- `beautifulsoup4 package not found`
- `install pandas ... to use this loader`
- Azure, Mathpix, Adobe, or OCR service credential/client errors

Actions:

1. Confirm the chosen reader is necessary; switch to a simpler local reader if tables/layout/OCR are not required.
2. Install only the dependency family for that reader, not every optional parser.
3. For service readers, confirm credentials, endpoints, and network policy before executing ingestion.
4. For tests or fixtures, prefer supported offline hooks such as `response_content` on `OCRReader` and `MathpixPDFReader`.

## Unsupported File Suffix

PaddleOCR readers intentionally reject unsupported suffixes. `PPStructureV3Reader` supports `.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff`, and `.tif`; `PaddleOCRVLReader` also supports `.bmp` and `.webp`. If a task uses another suffix:

- Convert the file to a supported format outside the ingestion call.
- Use `UnstructuredReader`, `AutoReader`, or a format-specific reader if the file is not image/PDF-like.
- In directory ingestion, set `required_exts` and `file_extractor` so unsupported files are skipped or routed correctly.

## PDF Tables Parse as Plain Text Only

Likely causes:

- The selected reader is a basic PDF text reader, not a table-aware parser.
- `UnstructuredReader(split_documents=False)` joined all elements into one text document.
- The table is scanned/image-only and needs OCR or a service parser.
- Optional table extraction dependency, model, or credential is missing.
- The parser extracted table content but metadata was overwritten by downstream code.

Actions:

1. Inspect document metadata: table docs should have `metadata.type == "table"` and non-empty `metadata.table_origin`.
2. Try `DoclingReader` for local structure-aware parsing if installed.
3. Try `PaddleOCRVLReader` or `PPStructureV3Reader` for scanned, image-heavy, or multilingual pages.
4. Try `OCRReader`, `MathpixPDFReader`, `AzureAIDocumentIntelligenceLoader`, or `AdobeReader` when service use is acceptable.
5. Validate a small sample with `scripts/validate_document_metadata.py` before indexing.

## OCR, Model, or Network Requirements

- `OCRReader` and `ImageReader` call a FullOCR-style endpoint. Configure `OCR_READER_ENDPOINT` or pass an endpoint explicitly; use fixture `response_content` for offline checks.
- `PaddleOCRVLReader` and `PPStructureV3Reader` create PaddleOCR pipelines lazily. First use can load models, require CPU/GPU-compatible PaddlePaddle wheels, and be slow.
- PaddleOCR CPU mode disables MKL-DNN in Kotaemon to avoid a known Paddle/PaddleX crash path; choose `device="cpu"` or `device="cpu:0"` for CPU-only hosts.
- `DoclingReader`, Azure DI, and Adobe figure captioning require a VLM endpoint for generated captions. Without one, text/tables may still parse while generated captions are absent.
- `WebReader`, Mathpix, Azure DI, and Adobe readers are network/service paths. Do not use them in offline or credential-free validation unless the task explicitly permits it.

## Bad Metadata Before Indexing

Symptoms:

- Table chunks cannot be distinguished from prose.
- Citations lack page or source labels.
- JSON fixtures fail serialization.
- Downstream filters do not match expected `source` or `type`.

Actions:

1. Ensure every record has non-empty `text`, `content`, or an equivalent text field.
2. Ensure `metadata` is an object, not a string/list/null.
3. For table docs, require `type: table` and `table_origin`.
4. Preserve `extra_info` through the reader call for stable provenance such as `source`, collection id, or upload id.
5. Avoid leaking machine-local absolute paths into reusable fixtures; prefer portable source ids.
6. Run the bundled validator on a small JSON fixture before indexing.

## Chunk Too Large or Too Small

- Too large: retrieval returns broad, low-precision chunks and citations point to whole pages or long tables.
- Too small: headings, table rows, and cross-sentence context are split apart; answers lose provenance.
- Start with `TokenSplitter(chunk_size=1024, chunk_overlap=20)` for general prose, then inspect retrieved chunks.
- Increase overlap or use `SentenceWindowSplitter` when answer context spans adjacent sentences.
- Avoid splitting table documents into pieces unless table length forces it; preserve `table_origin` on any derived chunks.

## MHTML, Cache, and Path Surprises

- `MhtmlReader` can write Markdown cache output when a cache directory is configured. Treat that as a parser-side artifact, not required runtime skill content.
- Several readers store `file_path` metadata using the live parse path. For generated examples and public fixtures, replace absolute paths with stable source ids or basenames.
- `PDFThumbnailReader`, image-aware readers, and captioning paths can create large base64 metadata fields. Keep only what downstream retrieval or UI actually needs.
