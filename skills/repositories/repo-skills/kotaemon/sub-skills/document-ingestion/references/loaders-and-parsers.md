# Loaders, Parsers, and Splitters

Kotaemon ingestion uses reader classes that return lists of `kotaemon.base.Document` objects. Most readers expose `load_data(...)` and `run(...)`; `BaseReader` subclasses can also be called as components in pipelines. Many structure-aware readers are optional integrations, so choose based on input type, table/figure requirements, and installed dependencies.

## Reader Families

| Need | Reader | Typical input | Key output behavior | Main dependency or service |
| --- | --- | --- | --- | --- |
| Generic LlamaIndex file reader | `AutoReader("PDFReader")` or other LlamaIndex reader name | PDF or LlamaIndex-supported files | Converts LlamaIndex documents into Kotaemon `Document` objects | `llama_index` reader package |
| Directory ingestion | `DirectoryReader` | Folder or file list | Wraps LlamaIndex `SimpleDirectoryReader`; supports `exclude`, `recursive`, `required_exts`, `file_metadata`, and `file_extractor` | `llama_index` |
| Plain text | `TxtReader` | `.txt`, UTF-8 text | One document with caller-provided `extra_info` metadata | none beyond core |
| HTML | `HtmlReader` | `.html` | Converts HTML to text with optional page-break splitting; adds `page_label` | `html2text` |
| MHTML | `MhtmlReader` | `.mhtml` | Extracts HTML part with BeautifulSoup; metadata can include `source` and `title` | `beautifulsoup4`, `lxml` |
| DOCX with tables | `DocxReader` | `.docx` | Paragraphs become text document(s); tables become CSV-like documents with `type: table` and `table_origin` | `python-docx`, `pandas` |
| Excel workbook | `ExcelReader` | `.xlsx` | One document per sheet; metadata includes `page_label` and `sheet_name` | `pandas`, spreadsheet engine |
| Flattened Excel | `PandasExcelReader` | `.xlsx` | One flattened text document across selected sheets | `pandas`, spreadsheet engine |
| Web URL text | `WebReader` | URL string | Fetches Markdown-like text through Jina Reader endpoint | network, optional `JINA_API_KEY` |
| Unstructured local/API parser | `UnstructuredReader` | text, DOCX, PPTX, image, email, HTML, PDF, and more | Either one joined document or per-element documents with unstructured metadata | `unstructured`; optional API |
| PDF page thumbnails | `PDFThumbnailReader` | `.pdf` | Adds page-thumbnail documents with `type: thumbnail`, `image_origin`, and `page_label` | `PyMuPDF`, `Pillow` |
| Local Docling parser | `DoclingReader` | PDF and other Docling-supported formats | Text by page plus table/image documents; optional VLM captions | `docling`; optional VLM endpoint |
| PaddleOCR structure parser | `PPStructureV3Reader` | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif` | Text, table, image, formula-aware documents via `PaddleOCRResult` | `paddleocr[doc-parser]`, PaddlePaddle |
| PaddleOCR-VL parser | `PaddleOCRVLReader` | `.pdf`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.tif`, `.webp` | VLM layout parser for text, tables, figures, formulas, charts, seals | `paddleocr[doc-parser]`, PaddlePaddle |
| FullOCR service reader | `OCRReader` | PDF | Calls OCR endpoint, merges PDF text with table OCR, emits table/text docs | FullOCR endpoint, `unstructured` PDF stack |
| Image OCR service reader | `ImageReader` | images/PDF pages | Calls OCR endpoint and returns CSV-like content documents | FullOCR endpoint |
| Mathpix PDF parser | `MathpixPDFReader` | PDF | Uses Mathpix API or supplied `response_content`; parses Markdown tables into table docs | Mathpix credentials/API |
| Azure Document Intelligence | `AzureAIDocumentIntelligenceLoader` | PDF, images, TIFF, DOCX, XLSX, PPTX, HTML | Text plus optional table/image docs; can cache markdown output | Azure endpoint and credential |
| Adobe PDF Services | `AdobeReader` | PDF | Text, table, and figure documents from Adobe structured data | Adobe service credentials, optional VLM endpoint |

## Choosing a Loader

- Prefer the simplest local reader that preserves the facts needed for indexing. For clean text, HTML, DOCX, and XLSX, the format-specific readers are easier to debug than broad OCR/service parsers.
- Use a table-aware reader when downstream QA needs faithful cell structure. Good table documents have `metadata.type == "table"` and `metadata.table_origin` containing the original table representation.
- Use `DoclingReader` for local structure-aware parsing when `docling` is installed and table/figure extraction matters. If no VLM endpoint is configured, figure caption generation is skipped but text/tables still parse.
- Use PaddleOCR readers when scanned, skewed, multilingual, formula-heavy, or layout-complex documents need OCR. `PaddleOCRVLReader` supports more image suffixes; both readers reject unsupported suffixes with `ValueError`.
- Use `MathpixPDFReader`, `AzureAIDocumentIntelligenceLoader`, `AdobeReader`, `WebReader`, and OCR endpoint readers only when credentials/network/service requirements are acceptable.
- Use `UnstructuredReader(split_documents=True)` when element-level metadata is useful. With `split_documents=False`, it joins extracted elements into one document.
- Use `DirectoryReader(file_extractor={...})` to override extension handling for mixed corpora, for example routing `.pdf` to a table-aware reader while leaving `.txt` to a simple reader.

## Common Calls

```python
from kotaemon.loaders import DocxReader, ExcelReader, DoclingReader

text_docs = DocxReader().load_data("handbook.docx", extra_info={"source": "handbook.docx"})
sheets = ExcelReader().load_data("metrics.xlsx", sheet_name=None, extra_info={"source": "metrics.xlsx"})
structured = DoclingReader().load_data("report.pdf", extra_info={"source": "report.pdf"})
```

```python
from kotaemon.loaders import DirectoryReader, TxtReader, DoclingReader

reader = DirectoryReader(
    input_dir="corpus",
    recursive=True,
    required_exts=[".txt", ".pdf"],
    file_extractor={".txt": TxtReader(), ".pdf": DoclingReader()},
    file_metadata=lambda path: {"source": path},
)
documents = reader.load_data()
```

## Splitting and Extraction

- `TokenSplitter(chunk_size=1024, chunk_overlap=20, separator=" ")` wraps LlamaIndex `TokenTextSplitter`. It returns Kotaemon `Document` chunks and preserves LlamaIndex relationships such as source, previous, and next.
- `SentenceWindowSplitter(window_size=3, window_metadata_key="window", original_text_metadata_key="original_text")` wraps LlamaIndex `SentenceWindowNodeParser` and stores surrounding sentence context in metadata.
- `TitleExtractor(llm=None, nodes=5)` and `SummaryExtractor(llm=None, summaries=["self"])` wrap LlamaIndex extractors. They require an appropriate LLM if generation is needed.
- Split after parsing, not before. Table/image-aware parsers often attach metadata that can be lost or diluted if raw text is chunked first.
- Tune `chunk_size` by retrieval behavior: too large reduces precision and citation clarity; too small fragments tables, headings, and page context. Keep overlap large enough to preserve cross-boundary references without duplicating whole pages.

## Optional Dependency Notes

- Core imports may work while full loader dependencies are absent. Treat `ImportError` from a reader as a configuration signal, not proof that Kotaemon itself is broken.
- `DocxReader`, `HtmlReader`, `MhtmlReader`, `ExcelReader`, and `UnstructuredReader` import optional packages lazily.
- `PaddleOCRVLReader` and `PPStructureV3Reader` lazily create model pipelines; the first real parse may download/load models and require hardware-compatible PaddlePaddle wheels.
- `OCRReader` accepts `response_content` for fixture/testing paths, avoiding a live OCR endpoint.
- `MathpixPDFReader` accepts `response_content` for fixture/testing paths, avoiding a Mathpix API call.
