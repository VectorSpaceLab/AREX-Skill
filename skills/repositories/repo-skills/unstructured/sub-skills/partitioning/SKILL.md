---
name: partitioning
description: "Partition local files, file-like objects, URLs, text, HTML,
  PDF/image, Office, tabular, JSON/NDJSON, XML, RST/MD/EPUB, email, and audio
  inputs into unstructured Element objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Partitioning

Use this sub-skill when a task asks an agent to turn source documents into `unstructured.documents.elements.Element` objects or to diagnose why a document type cannot be partitioned. Route serialization/export of elements to `elements-and-metadata`, post-partition chunking to `chunking`, embeddings to `embeddings`, and extraction-quality scoring to `evaluation`.

## Start Here

- Prefer `unstructured.partition.auto.partition()` when the corpus has mixed file types or when MIME/extension detection is acceptable.
- Prefer document-specific `partition_*` APIs when a format has important knobs, such as PDF/image strategy, HTML parser options, email attachment handling, or spreadsheet/table behavior.
- Run `python -m unstructured.cli doctor` or `unstructured doctor` before debugging optional dependency failures; use `--for pdf`, `--for image`, `--for doc`, `--for audio`, or `--file PATH` for targeted checks.
- Use local partition APIs for offline processing. Treat API workflows as network/credential-dependent and do not assume they are available in a normal local agent session.

## Core Local API

```python
from unstructured.partition.auto import partition

elements = partition(filename="docs/report.pdf", strategy="auto")
```

`partition()` accepts exactly one of `filename`, `file`, or `url`. For file-like objects, open in binary mode and pass `metadata_filename` when extension-based detection or element metadata should reflect a logical name:

```python
with open("docs/report.pdf", "rb") as file:
    elements = partition(file=file, metadata_filename="report.pdf", strategy="fast")
```

Important options:

- `content_type`: overrides or supplements detection when the MIME type is known.
- `encoding`: resolves non-UTF text/HTML/JSON decoding issues.
- `headers`, `ssl_verify`, `request_timeout`: apply only when `url` is used; set a timeout explicitly for unreliable endpoints.
- `languages`: preferred language/OCR hint list, e.g. `languages=["eng", "spa"]` or ISO codes that can map to Tesseract codes.
- `detect_language_per_element`: stores language metadata per element instead of once per document.
- `skip_infer_table_types`: controls table structure inference by file type; default skips PDF and common image types.
- `starting_page_number`: shifts page metadata when partitioning a PDF section.

## Format Routes

- Text: `from unstructured.partition.text import partition_text`; accepts exactly one of `filename`, `file`, or `text`, plus `paragraph_grouper`.
- HTML: `from unstructured.partition.html import partition_html`; accepts `filename`, `file`, `text`, or `url`; useful knobs include `skip_headers_and_footers`, `html_parser_version`, `image_alt_mode`, and URL request options.
- PDF: `from unstructured.partition.pdf import partition_pdf`; choose `strategy`, table/image/form options, page numbering, password, and pdfminer margins.
- Image: `from unstructured.partition.image import partition_image`; use `strategy="hi_res"` or `"ocr_only"`; `"fast"` is invalid for images.
- Office: use `partition_docx`, `partition_doc`, `partition_pptx`, `partition_ppt`, `partition_xlsx`, and `partition_odt` for format-specific controls.
- Email: use `partition_email` for `.eml` and `partition_msg` for Outlook `.msg`; inspect attachment options before recursively partitioning attachments.
- Tabular: use `partition_csv`, `partition_tsv`, or `partition_xlsx`; table elements can contain `metadata.text_as_html` when table structure is inferred.
- Markup/books: use `partition_md`, `partition_rst`, `partition_org`, `partition_xml`, and `partition_epub` for explicit handling.
- JSON streams: `partition_json` expects an unstructured-style JSON array of element dictionaries; `partition_ndjson` handles newline-delimited element records.
- Audio: `partition_audio` transcribes audio to elements and requires the audio extra plus `ffmpeg`.

See `references/api-reference.md` for a compact API and dependency matrix.

## PDF/Image Strategy Rules

Use `strategy="fast"` for extractable PDF text when layout detection, OCR, image blocks, forms, or table HTML are not needed. Use `strategy="hi_res"` when table structure, coordinates, images, layout segmentation, or form extraction matters. Use `strategy="ocr_only"` for scanned PDFs/images when OCR text is enough and layout segmentation is unnecessary. Use `strategy="auto"` when the agent should let unstructured pick and fallback based on text extractability and installed dependencies.

`auto` chooses PDF `hi_res` if table/image extraction is requested, PDF `fast` when text is extractable, PDF `ocr_only` when text is not extractable, and image `hi_res` by default. If `unstructured_inference` or `unstructured_pytesseract` is missing, unstructured may warn and fall back between `hi_res`, `ocr_only`, and `fast`; if no viable path exists for a non-extractable PDF, it raises an error.

Prefer `languages` over deprecated `ocr_languages`. Prefer `hi_res_model_name` over deprecated `model_name`. Prefer `skip_infer_table_types` over deprecated `pdf_infer_table_structure`.

## Diagnostics Scripts

Bundled helpers live under this sub-skill's `scripts/` directory:

```bash
python scripts/partition_diagnostics.py --for pdf
python scripts/partition_diagnostics.py --file docs/report.pdf
python scripts/partition_diagnostics.py --partition docs/report.pdf --strategy fast --limit 5
python scripts/inspect_tables.py output/elements.json --out-dir tables --index
```

`partition_diagnostics.py` wraps the public doctor/capability APIs and can run a small local partition preview when the environment supports the target format. `inspect_tables.py` extracts `Table` element `metadata.text_as_html` values from exported JSON into standalone HTML files; it is a portable Python adaptation of the repository's user table-inspection shell script.

## Workflow Pointers

- For mixed corpora, inventory extensions first, install only required extras, run doctor for risky families, then partition with `partition()` and per-format overrides only where needed.
- For PDF table extraction, use `strategy="hi_res"` and set `skip_infer_table_types=[]` or call `partition_pdf(..., infer_table_structure=True)`; inspect table HTML with `scripts/inspect_tables.py` after serializing elements.
- For URL partitioning, always set `request_timeout`; for HTML pages prefer `partition_html(url=...)` if the URL is known to return HTML.
- For API partitioning, require an endpoint, credentials, and network access; do not embed credentials in scripts or skill content.

## Evidence

This sub-skill is grounded in the package metadata, public README guidance, partitioning modules, file type utilities, doctor/CLI diagnostics, partition behavior tests, example document fixtures, and user helper scripts distilled into this bundled guidance.
