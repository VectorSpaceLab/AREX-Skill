# Parsing and data formats

## Inputs this sub-skill accepts

Langroid document flows can start from:

- a local file path
- a folder path
- a URL
- raw bytes
- a `FileAttachment` for direct model input

For retrieval, use paths/URLs/bytes that will be parsed into `Document` objects.
For direct multimodal prompting, use `FileAttachment`.

## Parser dispatch

`DocumentParser.create(source, config, doc_type=None)` chooses a parser by document type and parser config.

| Input type | Typical route |
| --- | --- |
| PDF | `PdfParsingConfig.library` selects the PDF parser |
| DOCX | `DocxParsingConfig.library` selects the DOCX parser |
| DOC | `unstructured` path |
| XLS / XLSX / PPTX | `markitdown`-backed parser |
| text | plain text path and normal chunking |
| URL | `URLLoader` or `extract_content_from_path(...)` |

`extract_content_from_path(...)` and `DocChatAgent.ingest_doc_paths(...)` both accept lists, single values, and bytes.

## PDF parsers

The default PDF parser is `pypdfium2` because it is permissively licensed and ships in core dependencies.
Other choices trade convenience, structure, OCR, and dependency weight.

| Library | Best for | Notes |
| --- | --- | --- |
| `pypdfium2` | Fast default text extraction | Good first choice |
| `pymupdf4llm` | Markdown-friendly layout preservation | Richer output, more optional deps |
| `fitz` | Direct PyMuPDF text extraction | Useful when you want a simpler parse path |
| `docling` | Layout-aware PDF conversion | Heavier dependency stack |
| `pypdf` | Basic PDF text extraction | Simple and explicit |
| `unstructured` | Broad document support | Flexible but extra-heavy |
| `pdf2image` | Image-based PDFs | Usually paired with OCR |
| `llm-pdf-parser` | Multimodal PDF-to-Markdown | Uses an LLM and is slower by design |
| `marker` | Layout-heavy markdown conversion | Powerful but version-sensitive |

### PDF-specific config

```python
from langroid.parsing.parser import ParsingConfig, PdfParsingConfig

cfg = ParsingConfig(
    pdf=PdfParsingConfig(library="pypdfium2"),
    n_neighbor_ids=2,
)
```

## DOCX / DOC / office parsers

| Format | Config | Notes |
| --- | --- | --- |
| DOCX | `DocxParsingConfig(library="unstructured")` | Flexible default |
| DOCX | `DocxParsingConfig(library="python-docx")` | Lightweight text path |
| DOCX | `DocxParsingConfig(library="markitdown-docx")` | Markdown-friendly office parsing |
| DOC | `DocParsingConfig(library="unstructured")` | Legacy Word documents |
| XLS / XLSX | `MarkitdownXLSParsingConfig()` | Spreadsheet-to-markdown path |
| PPTX | `MarkitdownPPTXParsingConfig()` | Slide-to-markdown path |

## Chunking

`ParsingConfig` controls how documents are split before embedding.

| Field | Purpose |
| --- | --- |
| `splitter` | `MARKDOWN`, `TOKENS`, `PARA_SENTENCE`, or `SIMPLE` |
| `chunk_size` | Target chunk length |
| `chunk_size_variation` | Allowed size wiggle room |
| `overlap` | Token overlap between chunks |
| `max_chunks` | Hard cap on total chunks |
| `min_chunk_chars` | Minimum useful chunk length |
| `discard_chunk_chars` | Drop tiny fragments |
| `n_neighbor_ids` | Stored neighbor window size for retrieval context |
| `n_similar_docs` | Deprecated compatibility path |
| `chunk_by_page` | Page-aware split toggle |

### Splitter guidance

- `MARKDOWN`: best for markdown-like structure and heading-aware chunks
- `TOKENS`: balanced token chunks
- `PARA_SENTENCE`: paragraph/sentence-aware split
- `SIMPLE`: fast separator-based split

## URL loading and crawling

`URLLoader` selects a crawler from its config.
The default is `TrafilaturaConfig`.

| Crawler | Strengths | Notes |
| --- | --- | --- |
| `TrafilaturaConfig` | Default web text extraction | No API key required |
| `ExaCrawlerConfig` | API-backed web extraction | Requires `EXA_API_KEY` |
| `FirecrawlConfig` | Scrape or crawl mode | Requires `FIRECRAWL_API_KEY` |
| `Crawl4aiConfig` | Browser-style crawling | Supports simple and deep crawl |

Document URLs are sent through the document parser path.
Plain web pages are scraped as web pages.

## FileAttachment summary

`FileAttachment` is for direct model payloads, not retrieval ingestion.

- `from_path(...)`
- `from_bytes(...)`
- `from_io(...)`
- `from_text(...)`
- `to_dict(model)`

It chooses `file` or `image_url` payloads depending on the content type and model family.

## Practical parsing choices

- Use `pypdfium2` first unless you need stronger layout recovery.
- Use `markitdown` for office docs when markdown output matters.
- Use `URLLoader` for page crawling; use `ingest_doc_paths(...)` for mixed local inputs.
- Use `FileAttachment` only when you need direct multimodal file understanding.
