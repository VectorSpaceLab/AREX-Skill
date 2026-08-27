# API reference for parsing and chunking

This reference lists the parser APIs and signatures verified from installed
package facts and local source evidence. Signature details are for PaperQA
2026.8.12-era packages; run `../scripts/inspect_parsers.py` in the active
environment before relying on optional readers.

## Core reader functions

### `paperqa.readers.read_doc`

```python
async def read_doc(
    path: str | os.PathLike,
    doc: Doc,
    parsed_text_only: bool = False,
    include_metadata: bool = False,
    chunk_chars: int = 5000,
    overlap: int = 250,
    multimodal_enricher: Callable[[ParsedText], Awaitable[str]] | None = None,
    parse_pdf: PDFParserFn | None = None,
    **parser_kwargs,
) -> list[Text] | ParsedText | tuple[list[Text], ParsedMetadata]
```

Use it when you want PaperQA's suffix dispatch plus chunking:

- `parsed_text_only=True` returns `ParsedText` before chunking.
- `include_metadata=True` with chunking returns `(list[Text], ParsedMetadata)` and
  stores `ChunkMetadata` on `metadata.chunk_metadata`.
- PDFs require `parse_pdf`; direct `read_doc("x.pdf", ...)` without it raises a
  `ValueError`. `Docs.aadd` usually supplies `settings.parsing.parse_pdf` for you.
- `parser_kwargs` are forwarded to `parse_text`, `parse_image`, `parse_office_doc`,
  or the selected PDF parser. Unknown kwargs are ignored by many parser functions.

Safe parse-only PDF example:

```python
from paperqa.types import Doc
from paperqa.readers import read_doc
from paperqa_pypdf import parse_pdf_to_pages

parsed = await read_doc(
    "paper.pdf",
    Doc(docname="paper", citation="Local PDF", dockey="paper"),
    parsed_text_only=True,
    parse_pdf=parse_pdf_to_pages,
    page_range=(1, 3),
    parse_media=False,
)
```

Safe chunking example with metadata:

```python
texts, metadata = await read_doc(
    "notes.txt",
    Doc(docname="notes", citation="Local notes", dockey="notes"),
    include_metadata=True,
    chunk_chars=1000,
    overlap=100,
)
```

### `paperqa.readers.parse_text`

```python
def parse_text(
    path: str | os.PathLike,
    html: bool = False,
    split_lines: bool = False,
    page_size_limit: int | None = None,
    **_,
) -> ParsedText
```

- Reads text with default encoding, then retries as UTF-8 with invalid bytes
  ignored on `UnicodeDecodeError`.
- `html=True` converts HTML to Markdown-like text via `html2text` and records the
  parser library in metadata.
- `split_lines=True` returns a list of lines for code-style chunking. HTML cannot
  be combined with split-line parsing.
- `page_size_limit` is relevant to split-line pages and rejects pages that appear
  too large.

### `paperqa.readers.parse_image`

```python
async def parse_image(
    path: str | os.PathLike,
    validator: Callable[[bytes], Awaitable] | None = None,
    **_,
) -> ParsedText
```

- Reads `.png`, `.jpg`, or `.jpeg` bytes into a single `ParsedMedia` object.
- Returns no text: page content is `{"1": ("", [media])}`.
- A validator can check image bytes; failures become `ImpossibleParsingError`.

### `paperqa.readers.parse_office_doc`

```python
def parse_office_doc(path: str | os.PathLike, **kwargs) -> ParsedText
```

- Parses `.docx`, `.xlsx`, and `.pptx` via `unstructured.partition.auto.partition`.
- Extracts element text, image bytes, and table HTML when available.
- Requires `paper-qa[office]`; otherwise raises an ImportError instructing that
  install selector.
- Forwards kwargs to `unstructured.partition.auto.partition`.

### Chunking helpers

```python
def chunk_text(parsed_text: ParsedText, doc: Doc, chunk_chars: int, overlap: int,
               use_tiktoken: bool = True) -> list[Text]
def chunk_pdf(parsed_text: ParsedText, doc: Doc, chunk_chars: int,
              overlap: int) -> list[Text]
def chunk_code_text(parsed_text: ParsedText, doc: Doc, chunk_chars: int,
                    overlap: int) -> list[Text]
def resolve_page_range(page_range: int | tuple[int, int] | None,
                       page_count: int) -> range
```

- `resolve_page_range` accepts one-indexed `page_range`; `1` means the first page,
  `(1, 2)` means pages 1 and 2, and an end beyond page count truncates.
- `chunk_text` requires string content and raises `ImpossibleParsingError` on
  empty text.
- `chunk_pdf` requires dict page content and raises `ImpossibleParsingError` on an
  empty page dict. It uses page names rather than tokenized chunk numbers.
- `chunk_code_text` handles string or list content from generic suffixes.

## Settings integration

### `ParsingSettings`

Important fields:

```python
ParsingSettings(
    page_size_limit=1_280_000,
    reader_config={"chunk_chars": 5000, "overlap": 250},
    multimodal=MultimodalOptions.ON_WITH_ENRICHMENT,
    parse_pdf=<default parser>,
    configure_pdf_parser=<default configurator>,
    disable_doc_valid_check=False,
    defer_embedding=False,
    enrichment_page_radius=1,
)
```

Default PDF parser resolution tries PyMuPDF first, then pypdf. The parser field
also accepts an import string such as `"paperqa_docling.parse_pdf_to_pages"`; it
is validated by locating the callable and checking it against PaperQA's
`PDFParserFn` protocol.

`Docs.aadd` uses settings approximately like this:

- Peeks at PDF text with `page_range=(1, 3)` and `parse_media=False` when needed
  for citation/details checks.
- Computes `parse_media, enrich_media = settings.parsing.should_parse_and_enrich_media`.
- Calls `read_doc(..., page_size_limit=settings.parsing.page_size_limit,
  parse_pdf=settings.parsing.parse_pdf, include_metadata=True,
  **multimodal_kwargs, **settings.parsing.reader_config)`.

To pass reader kwargs through `Docs.aadd`:

```python
from paperqa import Settings
from paperqa.settings import MultimodalOptions
from paperqa_pypdf import parse_pdf_to_pages

settings = Settings(
    parsing={
        "parse_pdf": parse_pdf_to_pages,
        "multimodal": MultimodalOptions.ON_WITHOUT_ENRICHMENT,
        "reader_config": {
            "chunk_chars": 3000,
            "overlap": 100,
            "page_range": (1, 5),
            "parse_media": True,
            "full_page": False,
            "dpi": 144,
        },
    }
)
```

Avoid passing `parse_media` in `reader_config` when using `Docs.aadd` unless you
intentionally want to override the multimodal-derived value; duplicate keyword
values can conflict if supplied both ways in custom wrappers.

## PDF parser signatures

### `paperqa_pypdf.parse_pdf_to_pages`

```python
def parse_pdf_to_pages(
    path: str | os.PathLike,
    page_size_limit: int | None = None,
    page_range: int | tuple[int, int] | None = None,
    parse_media: bool = True,
    full_page: bool = False,
    image_cluster_tolerance: float = 50,
    image_cluster_padding: float = 10,
    dpi: float | None = None,
    **_: Any,
) -> ParsedText
```

Behavior:

- Text uses `pypdf.PdfReader` and cleans invalid Unicode.
- `parse_media=False` returns per-page strings with no media.
- With `parse_media=True` and `full_page=True`, uses `pypdfium2` to render one
  page screenshot per page; Pillow must be present for `to_pil().save(...)`.
- With `parse_media=True`, `full_page=False`, and `pdfplumber` installed, clusters
  nearby images and extracts tables; otherwise it falls back to individual page
  images from pypdf.
- Metadata names include `pdf|page_range=...|multimodal|dpi=...|mode=...` when
  media are parsed.

### `paperqa_pymupdf.parse_pdf_to_pages`

```python
def parse_pdf_to_pages(
    path: str | os.PathLike,
    page_size_limit: int | None = None,
    page_range: int | tuple[int, int] | None = None,
    use_block_parsing: bool = False,
    parse_media: bool = True,
    full_page: bool = False,
    image_cluster_tolerance: float | tuple[float, float] = 25,
    dpi: float | None = None,
    num_workers: int = min(os.cpu_count() or 1, 4),
    **_,
) -> ParsedText
```

Behavior:

- Text can use block parsing (`page.get_text("blocks", sort=False)`) or sorted text.
- Individual media uses `page.cluster_drawings(...)` for drawings and
  `page.find_tables()` for tables. Table Markdown is cleaned for invalid Unicode.
- `full_page=True` with media uses multiprocessing to render page screenshots.
- Exports `setup_pymupdf_python_logging()`, and PaperQA's default configurator
  calls it when PyMuPDF is installed.

### `paperqa_docling.parse_pdf_to_pages`

```python
def parse_pdf_to_pages(
    path: str | os.PathLike,
    page_size_limit: int | None = None,
    page_range: int | tuple[int, int] | None = None,
    parse_media: bool = True,
    pipeline_cls: type = StandardPdfPipeline,
    dpi: int | None = None,
    custom_pipeline_options: Mapping[str, Any] | None = None,
    backend: type[AbstractDocumentBackend] = DoclingParseDocumentBackend,
    **_,
) -> ParsedText
```

Behavior:

- Builds a Docling `DocumentConverter` for PDF input.
- When media parsing is on, generates picture and table images and uses
  `images_scale = 1.0` or `dpi / 72`.
- Supports custom pipeline options such as `document_timeout`.
- Raises `ImpossibleParsingError` on Docling `ConversionError` or non-success
  conversion status.

### `paperqa_nemotron.parse_pdf_to_pages`

```python
async def parse_pdf_to_pages(
    path: str | os.PathLike,
    page_size_limit: int | None = None,
    page_range: int | tuple[int, int] | None = None,
    parse_media: bool = True,
    full_page: bool = False,
    dpi: int | None = 300,
    api_params: Mapping[str, Any] | None = None,
    concurrency: int | asyncio.Semaphore | None = 128,
    border: int | tuple[int, int] = 60,
    failover_parser: str | PDFParserFn | None = None,
    num_workers: int = min(os.cpu_count() or 1, 4),
    **kwargs: Any,
) -> ParsedText
```

Behavior:

- Renders pages with `pypdfium2`, pads pages when bbox extraction is needed, and
  calls Nemotron through NVIDIA API or SageMaker depending on `api_params`.
- Default hosted path needs `NVIDIA_API_KEY`. `api_params={"model_name":
  "sagemaker/nvidia/nemotron-parse"}` uses SageMaker and requires the
  `sagemaker` extra plus AWS endpoint access.
- `concurrency` limits page processing; use a lower value for large PDFs or memory
  limits.
- `failover_parser` can be a callable or import string. It is used for selected
  length, bbox, and timeout failures and receives relevant parser kwargs.
- Metadata records both `pypdfium2` and the model name.

## Return object notes

- `ParsedText.content` is either a string, list of lines, or a page dictionary.
- `ParsedMetadata` includes parser library names, PaperQA version, total parsed
  text length, media count, parser-summary name, and optionally chunk metadata.
- `ParsedMedia` must have exactly one of `data` or `url`. `to_image_url()` returns
  provider-ready `data:` URLs for in-memory images, using suffix info to choose
  image MIME type when present.
- Media IDs/hashes derive from media data/text/info and can deduplicate repeated
  logos/equations/tables across pages.

## No-network parse/chunk smoke

Use the bundled smoke script to validate core text parsing in the current
environment:

```bash
python sub-skills/docs-and-parsing/scripts/parse_text_smoke.py --markdown
```

It creates or reads a tiny local text/Markdown file, calls `parse_text`, chunks
with `chunk_text`, and prints JSON without invoking embeddings, LLMs, metadata
clients, PDFs, or Office dependencies.
