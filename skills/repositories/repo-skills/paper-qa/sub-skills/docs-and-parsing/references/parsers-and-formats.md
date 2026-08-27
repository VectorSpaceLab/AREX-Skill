# Parsers and formats

This reference distills the PaperQA document-reading surfaces that turn local
files into `ParsedText` and then into `Text` chunks. It intentionally stops at
parsing and chunking; querying and model configuration belong to sibling
sub-skills.

## Supported suffixes and default dispatch

`read_doc(path, doc, ...)` dispatches by filename suffix:

| Input | Reader path | Parsed content shape | Chunking path |
| --- | --- | --- | --- |
| `.pdf` | `parse_pdf=` callable is required; `Settings().parsing.parse_pdf` resolves a default | `dict[str, str]` when text-only, or `dict[str, tuple[str, list[ParsedMedia]]]` when media are parsed | `chunk_pdf` with page-range chunk names |
| `.txt` | `parse_text(path)` | `str` | `chunk_text` using tiktoken by default |
| `.html` | `parse_text(path, html=True)` using `html2text` | Markdown-like `str` | `chunk_text` |
| `.png`, `.jpg`, `.jpeg` | `parse_image(path, validator=None)` | one pseudo-page containing empty text plus one `ParsedMedia` | `chunk_pdf` style, one media-bearing `Text` |
| `.docx`, `.xlsx`, `.pptx` | `parse_office_doc(path, **kwargs)` via `unstructured` | one pseudo-page containing text and extracted media | `chunk_pdf` |
| Other suffixes, including `.md`, source code, config files, marker files | `parse_text(path, split_lines=True)` | usually `list[str]`; binary-ish files may fall back to UTF-8 with ignored errors | `chunk_code_text` with line-number chunk names |

Operational implications:

- Markdown is treated as a generic non-`.txt` text file, so `read_doc` uses
  line-based parsing/chunking. If you need text-overlap chunking for Markdown,
  call `parse_text` + `chunk_text` directly or rename/use `.txt` semantics.
- Code and config examples in public docs list `.py`, `.ts`, `.yaml` as valid
  examples; any unrecognized suffix is read as text/code and chunked by lines.
- Office parsing requires the `office` extra and can forward `unstructured`
  partition kwargs via `reader_config`/`read_doc(**parser_kwargs)`.
- `read_doc` uses suffix strings; uppercase suffixes are not normalized by this
  dispatch. Prefer lower-case extensions or call the parser function directly.

## PDF parser resolution

PaperQA's `ParsingSettings.parse_pdf` default is resolved at settings
construction:

1. Try `paperqa_pymupdf.parse_pdf_to_pages` if importable.
2. Else try `paperqa_pypdf.parse_pdf_to_pages`.
3. Else raise an ImportError telling the user to install either `paper-qa[pypdf]`
   or `paper-qa[pymupdf]`.

The minimum verified environment for this skill included `paper-qa` and
`paper-qa-pypdf`; PyMuPDF, Docling, Nemotron, Office, and enhanced pypdf media
extras were optional and must be checked in the target environment.

To set a reader explicitly:

```python
from paperqa import Settings
from paperqa_pypdf import parse_pdf_to_pages

settings = Settings(parsing={"parse_pdf": parse_pdf_to_pages})
# or JSON/config form when the package is installed:
settings = Settings(parsing={"parse_pdf": "paperqa_pypdf.parse_pdf_to_pages"})
```

Parser choice participates in `Settings.get_index_name()` hashing together with
chunk size, overlap, `full_page`, and multimodal options. Changing readers or
media options can produce a different index name for otherwise identical paper
directories.

## Reader comparison

| Reader package | Install selector | License note | Sync/async | Strengths | Requirements and caveats |
| --- | --- | --- | --- | --- | --- |
| `paper-qa-pypdf` | `paper-qa[pypdf]` or `paper-qa-pypdf`; media extras `paper-qa-pypdf[media]`, enhanced `paper-qa-pypdf[enhanced]` | Apache-2.0 package | sync | Default lightweight fallback; text extraction; optional individual images, full-page screenshots, clustered figures/tables | Media rendering requires `pypdfium2`; image access/re-encoding requires Pillow/PyPDF image support; clustering/tables require `pdfplumber` via enhanced extra |
| `paper-qa-pymupdf` | `paper-qa[pymupdf]` or `paper-qa-pymupdf` | PyMuPDF-backed package is AGPLv3; review license obligations before embedding in proprietary deployments | sync | Often strong layout/order; block parsing option; drawing/table extraction; full-page screenshots; multiprocessing for full pages | Requires PyMuPDF. Some failures surface as PyMuPDF format/file errors. Default parser resolver prefers this reader if installed |
| `paper-qa-docling` | `paper-qa[docling]` or `paper-qa-docling` | Apache-2.0 package; Docling project requests citation consideration | sync | Model/layout-aware parsing; formulas, tables, pictures; configurable Docling pipeline/backend; DPI/image scaling | Heavy dependencies and slower startup. `custom_pipeline_options` can set timeouts; failed or partial conversions raise parsing errors |
| `paper-qa-nemotron` | `paper-qa[nemotron]` or `paper-qa-nemotron`; SageMaker extra `paper-qa-nemotron[sagemaker]` | Apache-2.0 package | async | VLM-backed reading-order Markdown and media boxes; fallback parser support; useful for complex scientific PDFs | Requires `NVIDIA_API_KEY` for hosted NVIDIA API unless using SageMaker config; SageMaker needs `aiobotocore`. Calls network/service, has rate/timeout/bbox failure modes, and can be expensive |

## Common parser kwargs

These kwargs can be placed in `Settings(parsing={"reader_config": {...}})` for
`Docs.aadd`, or passed directly to `read_doc`/parser functions when appropriate.

| Kwarg | Applies to | Meaning |
| --- | --- | --- |
| `chunk_chars` | `read_doc` / `reader_config` | Approximate target chunk size; default from `ParsingSettings.reader_config` is `5000` |
| `overlap` | `read_doc` / `reader_config` | Character overlap between chunks; default is `250` |
| `page_size_limit` | text line pages and PDF pages | Maximum characters allowed in one page/line-page; default settings value is `1_280_000`; catches corrupt or concatenated parses |
| `page_range` | PDF readers | One-indexed `int` or inclusive `(start, end)` tuple. Ranges beyond page count are truncated by `resolve_page_range` |
| `parse_media` | PDF readers; set by `ParsingSettings.multimodal` during `Docs.aadd` | Whether to extract images/tables/screenshots in addition to text |
| `full_page` | pypdf, PyMuPDF, Nemotron | If true with media parsing, store one screenshot per page instead of individual/clustered media |
| `dpi` | pypdf media/full-page, PyMuPDF, Docling, Nemotron | Image rendering resolution. Higher DPI can improve details but increases memory, payload size, and provider rejection risk |
| `reader_config` | `ParsingSettings` | Dict forwarded through `Docs.aadd` to `read_doc` and underlying parsers; also holds chunking args |
| `validator` | image parsing | Optional async callable receiving image bytes; failures become an image validation parsing error |

Reader-specific kwargs include:

- pypdf: `image_cluster_tolerance`, `image_cluster_padding` for pdfplumber-based
  figure/table clustering.
- PyMuPDF: `use_block_parsing`, `image_cluster_tolerance` (number or `(x, y)`),
  `num_workers` for parallel full-page screenshots.
- Docling: `pipeline_cls`, `custom_pipeline_options`, `backend`.
- Nemotron: `api_params`, `concurrency`, `border`, `failover_parser`,
  `num_workers`. `failover_parser` can be a callable or import string.

## Chunking behavior

- `chunk_text` expects `ParsedText.content` to be a string. It uses tiktoken
  `cl100k_base` by default to cut near token boundaries, then returns `Text`
  objects named `<docname> chunk N`.
- `chunk_pdf` expects page dictionary content. It concatenates page text until
  `chunk_chars`, creates names like `<docname> pages 1-3`, and attaches every
  `ParsedMedia` from covered pages. It tolerates missing blank page numbers.
- `chunk_code_text` handles string or list-of-lines content for unrecognized
  suffixes, produces line-range chunk names, and is appropriate for code/config.
- `chunk_chars=0` through `read_doc` disables chunk splitting and returns one
  reduced-content `Text` named after the `Doc`.
- Empty parsed content raises `ImpossibleParsingError` rather than silently
  producing a useless `Text`.

## Multimodal media and enrichment

PaperQA represents extracted images/tables/screenshots as `ParsedMedia` attached
to `Text` chunks. A media item can appear on more than one chunk when chunk
boundaries overlap pages, and identical logos/figures can appear across many
pages. Future media stores should treat media-to-chunk as many-to-many.

`ParsingSettings.multimodal` controls two related but distinct actions:

- `False` or `MultimodalOptions.OFF`: do not parse media.
- `True` or `ON_WITH_ENRICHMENT`: parse media and run the enrichment LLM at
  document-read time to add synthetic descriptions used for embeddings.
- `ON_WITHOUT_ENRICHMENT`: parse media but skip enrichment calls.

Important implications:

- Media enrichment is an LLM/provider operation, not a parser-only operation.
  It can fail because of provider credentials, image-size limits, model support,
  or bad images.
- Synthetic enrichment descriptions shift embeddings to make relevant images and
  tables retrievable, but they are kept separate from source text.
- Contextual summarization can pass both text and associated media to the summary
  LLM, while summaries remain text-only.
- If multimodal parsing is wanted but budget or credentials are constrained, use
  `MultimodalOptions.ON_WITHOUT_ENRICHMENT` and expect lower retrieval recall for
  figure-only evidence.

## Choosing a reader quickly

- Need a lightweight open default and mostly text: choose pypdf with
  `parse_media=False` or no enhanced extras.
- Need tables/figures without service calls: choose PyMuPDF or pypdf enhanced;
  check the PyMuPDF AGPL license before use.
- Need more layout/formula-aware extraction and can afford heavy dependencies:
  choose Docling.
- Need VLM parsing for complex pages and have NVIDIA/SageMaker service access:
  choose Nemotron, preferably with a failover parser.
- Need deterministic no-network smoke: use `parse_text`/`chunk_text` first, then
  inspect parser availability with `../scripts/inspect_parsers.py`.
