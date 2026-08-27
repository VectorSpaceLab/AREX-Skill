# Partitioning Workflows

## Mixed Local Corpus

1. Inventory extensions and content families before installing extras.
2. Install only targeted extras needed by the corpus, such as `unstructured[pdf,docx,xlsx,md]` instead of `unstructured[all-docs]`.
3. Run capability checks for risky families:

   ```bash
   python -m unstructured.cli doctor --for pdf
   python -m unstructured.cli doctor --for doc
   python -m unstructured.cli doctor --for audio
   ```

4. Use `partition(filename=path, strategy="auto")` for most files.
5. Override per family only when needed: PDF/image strategy, HTML parser options, email attachments, table structure, language/OCR hints, password, or page offsets.
6. Hand off element serialization to `elements-and-metadata` and chunking decisions to `chunking`.

Minimal local loop:

```python
from pathlib import Path
from unstructured.partition.auto import partition

for path in Path("docs").glob("**/*"):
    if not path.is_file():
        continue
    try:
        elements = partition(filename=str(path), strategy="auto", request_timeout=30)
    except Exception as exc:
        print(f"{path}: {exc}")
        continue
    print(path, len(elements), sorted({type(element).__name__ for element in elements}))
```

## File-Like Objects

Use binary file objects for `partition()` and most binary document partitioners:

```python
from unstructured.partition.auto import partition

with open("docs/report.pdf", "rb") as file:
    elements = partition(file=file, metadata_filename="report.pdf", strategy="fast")
```

Use `metadata_filename` to preserve extension-based detection and metadata when the file-like object does not have a stable `.name`.

## Text and HTML Snippets

```python
from unstructured.partition.text import partition_text
from unstructured.partition.html import partition_html

text_elements = partition_text(text="Title\n\nA paragraph.")
html_elements = partition_html(text="<main><h1>Title</h1><p>A paragraph.</p></main>")
```

For URLs, prefer the specific HTML API when the endpoint returns HTML:

```python
elements = partition_html(url="https://example.com/page", request_timeout=30)
```

For arbitrary remote documents, use `partition(url=..., content_type=..., request_timeout=30)` and pass headers only when required.

## PDF Text-First Extraction

Use this when a PDF is digital text and the task values speed over layout semantics:

```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf("docs/report.pdf", strategy="fast")
```

Add `password="..."` for encrypted PDFs when the password is available. Use pdfminer margin options only after inspecting line/word grouping problems.

## PDF Tables, Images, Coordinates, and Forms

Use hi-res for table structure or layout-aware extraction:

```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf(
    "docs/report.pdf",
    strategy="hi_res",
    infer_table_structure=True,
    extract_image_block_types=["Image", "Table"],
    extract_image_block_to_payload=True,
)
```

When using `partition()`, request table inference by controlling skipped types:

```python
elements = partition(
    filename="docs/report.pdf",
    strategy="hi_res",
    skip_infer_table_types=[],
)
```

After serializing elements to JSON, inspect table HTML with:

```bash
python scripts/inspect_tables.py elements.json --out-dir table-html --index
```

## Scanned PDFs and Images

Use `ocr_only` when OCR text is enough:

```python
from unstructured.partition.pdf import partition_pdf

elements = partition_pdf("scanned.pdf", strategy="ocr_only", languages=["eng"])
```

Use `hi_res` when bounding boxes, table structure, image blocks, or layout segmentation are required. Use `languages` rather than deprecated `ocr_languages`; ensure matching Tesseract language packs are installed.

## Split or Parallel PDF Processing

For very large PDFs, the repository includes shell evidence for splitting PDFs and submitting chunks to an API. Treat that as an operational pattern requiring external tools and credentials, not as a bundled local workflow. If adapting it manually:

- Split pages with a local PDF tool outside this skill.
- Preserve `starting_page_number` for each split so element metadata has original page numbers.
- Merge serialized JSON arrays in page order.
- Record failed parts and make reruns idempotent.

## API-Based Partitioning

Use API partitioning only when the user has explicitly provided or approved network/service use. Required decisions:

- Endpoint and authentication mechanism.
- Strategy: `auto`, `fast`, `hi_res`, `ocr_only`, or service-specific options such as VLM strategy.
- Timeout, retry, and payload-size behavior.
- Whether images, coordinates, table HTML, or page splitting are required.

Never write credentials into generated scripts or examples. Use environment variables or the caller's secret manager.

## Minimal Extras Selection

Use this selection process for a mixed corpus without installing everything:

1. Map extensions to families: text/HTML/base, PDF/image, Office, spreadsheet, pandoc-backed markup/books, audio, email.
2. Check base support first; HTML, TXT, XML, JSON/NDJSON, EML, and MSG often need no extra beyond the base install in this repo version.
3. Add extras only for families present: `pdf`, `image`, `docx`, `pptx`, `xlsx`, `csv`, `md`, `audio`, or pandoc-backed extras.
4. Run `doctor --for` for each high-risk family.
5. If a system tool is missing, decide whether to install it, change formats, use `fast`, or route to an approved API service.

## Native Evidence Examples

Useful example-doc patterns in the repository include digital text files, UTF-encoded text, HTML variants, DOCX/PPTX/XLSX examples, PDF/image fixtures, email fixtures, JSON/NDJSON fixtures, and audio fixtures. Use them as reference evidence when designing tests, but do not make runtime skill content depend on source checkout paths.