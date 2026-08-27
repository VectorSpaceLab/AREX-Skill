# Partitioning API Reference

## Installed Package Facts

- Distribution version observed during private inspection: `unstructured==0.23.1`.
- Import checks passed for `unstructured`, CLI/doctor modules, auto/text/html partitioners, elements, chunking, cleaners, staging, metrics, table metrics, and embeddings interfaces.
- CLI checks passed for `python -m unstructured.cli` and `python -m unstructured.cli doctor`.
- A direct tiny `partition_text` smoke timed out during private inspection; do not claim a partition runtime smoke passed solely from that check.

## Auto Partitioner

```python
from unstructured.partition.auto import partition

elements = partition(
    filename=None,
    *,
    file=None,
    encoding=None,
    content_type=None,
    url=None,
    headers={},
    ssl_verify=True,
    request_timeout=None,
    strategy="auto",
    skip_infer_table_types=["pdf", "jpg", "png", "heic"],
    ocr_languages=None,
    languages=None,
    detect_language_per_element=False,
    language_fallback=None,
    pdf_infer_table_structure=False,
    extract_images_in_pdf=False,
    extract_image_block_types=None,
    extract_image_block_output_dir=None,
    extract_image_block_to_payload=False,
    data_source_metadata=None,
    metadata_filename=None,
    hi_res_model_name=None,
    model_name=None,
    starting_page_number=1,
    **kwargs,
)
```

Rules and caveats:

- `partition()` enforces exactly one of `filename`, `file`, or `url`.
- File type detection uses strong binary checks, caller `content_type`, libmagic or fallback MIME guesses, then extension mapping.
- If `file` is provided, pass `metadata_filename` when the file object lacks a useful `.name` or when extension/MIME metadata matters.
- `headers` are ignored without `url`; `request_timeout=None` can block indefinitely.
- JSON and NDJSON are special: JSON must look like an array of objects; NDJSON must be newline-delimited JSON records.

## Document-Specific APIs

| Input family | Function | Module | Key options | Main extras/tools |
| --- | --- | --- | --- | --- |
| Plain text | `partition_text` | `unstructured.partition.text` | `filename`, `file`, `text`, `encoding`, `paragraph_grouper`, `detection_origin` | base install |
| HTML | `partition_html` | `unstructured.partition.html` | `filename`, `file`, `text`, `url`, `skip_headers_and_footers`, `html_parser_version`, `image_alt_mode`, request options | base install |
| PDF | `partition_pdf` | `unstructured.partition.pdf` | `strategy`, `infer_table_structure`, `languages`, `detect_language_per_element`, `hi_res_model_name`, image block options, forms, password, pdfminer margins | `unstructured[pdf]`, poppler/Tesseract for OCR paths |
| Images | `partition_image` | `unstructured.partition.image` | `strategy`, `languages`, image block/table options | `unstructured[image]`, Tesseract/poppler-style image stack |
| DOCX/DOC | `partition_docx`, `partition_doc` | `unstructured.partition.docx`, `unstructured.partition.doc` | strategy/layout knobs for DOCX; DOC converts through LibreOffice | `unstructured[docx]`, `soffice` for legacy DOC |
| PPTX/PPT | `partition_pptx`, `partition_ppt` | `unstructured.partition.pptx`, `unstructured.partition.ppt` | `strategy`, include speaker notes where supported | `unstructured[pptx]`, `soffice` for legacy PPT |
| XLSX/CSV/TSV | `partition_xlsx`, `partition_csv`, `partition_tsv` | matching modules | sheet/table handling, encoding/delimiters as supported | `unstructured[xlsx]`, `unstructured[csv]` |
| Email | `partition_email`, `partition_msg` | `unstructured.partition.email`, `unstructured.partition.msg` | content-source, attachment recursion/options, metadata | base for EML, `python-oxmsg` for MSG in base deps |
| Markdown/RST/Org/RTF/ODT/EPUB | `partition_md`, `partition_rst`, `partition_org`, `partition_rtf`, `partition_odt`, `partition_epub` | matching modules | conversion and language options | `markdown` or `pypandoc`; pandoc executable may be required |
| XML | `partition_xml` | `unstructured.partition.xml` | XML parsing plus language metadata options | base install |
| JSON/NDJSON | `partition_json`, `partition_ndjson` | matching modules | unstructured element JSON records | base install |
| Audio | `partition_audio` | `unstructured.partition.audio` | transcription strategy and audio segment behavior | `unstructured[audio]`, `ffmpeg` |

Many partitioners are decorated with `add_chunking_strategy`, so `chunking_strategy="basic"` or `"by_title"` may work directly. Prefer routing chunking design to the `chunking` sub-skill when the task is about chunk boundaries rather than initial partitioning.

## Text and HTML Signatures

```python
from unstructured.partition.text import partition_text
partition_text(filename=None, *, file=None, encoding=None, text=None, paragraph_grouper=None, detection_origin="text", **kwargs)
```

```python
from unstructured.partition.html import partition_html
partition_html(
    filename=None,
    *,
    file=None,
    text=None,
    encoding=None,
    url=None,
    headers={},
    ssl_verify=True,
    skip_headers_and_footers=False,
    detection_origin=None,
    html_parser_version="v1",
    image_alt_mode="to_text",
    extract_image_block_to_payload=False,
    extract_image_block_types=None,
    languages=None,
    detect_language_per_element=False,
    language_fallback=None,
    **kwargs,
)
```

## PDF Signature Highlights

```python
from unstructured.partition.pdf import partition_pdf
partition_pdf(
    filename=None,
    file=None,
    include_page_breaks=False,
    strategy="auto",
    infer_table_structure=False,
    languages=None,
    detect_language_per_element=False,
    hi_res_model_name=None,
    extract_image_block_types=None,
    extract_image_block_output_dir=None,
    extract_image_block_to_payload=False,
    starting_page_number=1,
    extract_forms=False,
    form_extraction_skip_tables=True,
    password=None,
    pdfminer_word_margin=0.185,
    **kwargs,
)
```

Use `infer_table_structure=True` only with `strategy="hi_res"`. In `partition()`, the equivalent modern control is `skip_infer_table_types`: pass an empty list to request table inference for all supported types, or omit `pdf`/image types from the skip list only where needed.

## Strategy Selection

Valid PDF/image strategies are `"auto"`, `"fast"`, `"ocr_only"`, and `"hi_res"`.

- `fast`: PDF text extraction with pdfminer-style processing; not valid for images.
- `ocr_only`: OCR text extraction without layout segmentation.
- `hi_res`: layout model path; needed for table structure, image blocks, layout coordinates, and forms.
- `auto`: delegates to unstructured fallback logic.

Fallback behavior from `unstructured.partition.strategies`:

- Image `auto` becomes `hi_res`.
- PDF `auto` becomes `hi_res` when table or image extraction is requested.
- PDF `auto` becomes `fast` when text is extractable and no hi-res-only feature is requested.
- PDF `auto` becomes `ocr_only` when text is not extractable.
- Missing `unstructured_inference` can force `hi_res` to fall back to `ocr_only` or `fast`.
- Missing `unstructured_pytesseract` can force `ocr_only` to fall back to `fast` for extractable PDFs or `hi_res` otherwise.

## Extras and System Tools

From `pyproject.toml`, use targeted extras instead of installing `all-docs` by default:

- `unstructured[csv]`: CSV/TSV via pandas.
- `unstructured[docx]`: DOCX via `python-docx`; `unstructured[doc]` includes DOCX but legacy DOC also needs `soffice`.
- `unstructured[pptx]`: PPTX via `python-pptx`; legacy PPT needs `soffice`.
- `unstructured[xlsx]`: Excel via pandas/openpyxl/xlrd/msoffcrypto/networkx.
- `unstructured[image]` and `unstructured[pdf]`: image/PDF OCR and layout stack.
- `unstructured[md]`: Markdown support.
- `unstructured[epub]`, `unstructured[odt]`, `unstructured[org]`, `unstructured[rtf]`, `unstructured[rst]`: pandoc-backed formats.
- `unstructured[audio]`: Whisper-based audio partitioning; also requires `ffmpeg`.

System tools commonly involved:

- `libmagic`: improves MIME detection; doctor warns if the Python `magic` module or backing library is not usable.
- `pandoc`: needed by pypandoc-backed formats when a bundled binary is unavailable.
- `soffice`: LibreOffice CLI needed for legacy `.doc` and `.ppt` conversion.
- `tesseract`: OCR runtime for scanned PDFs/images and OCR-only strategy.
- `ffmpeg`: audio decoding for Whisper.

## Doctor CLI

```bash
python -m unstructured.cli doctor
python -m unstructured.cli doctor --for pdf
python -m unstructured.cli doctor --file docs/report.pdf
unstructured doctor --for image
```

Return codes: `0` means ready for the requested diagnostic scope; `1` means missing capability; `2` means bad CLI usage or unknown file type specifier.

## API Partitioning Caveats

`unstructured.partition.api.partition_via_api()` and shell API workflows can submit files to a remote service and accept strategy-style parameters. They require an endpoint, credentials, network access, and retry/timeout decisions. Treat repository shell scripts such as API JSON export and parallel PDF processing as evidence for option names and operational patterns, not as local runtime dependencies for this skill.