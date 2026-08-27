# Document and Metadata Formats

Kotaemon ingestion records are `kotaemon.base.Document` objects. The class extends LlamaIndex `Document` and accepts either `Document(content=...)` or `Document(text=...)`; when `content` is provided, text is derived with `str(content)`. Loader outputs should be treated as document-like records with text/content plus metadata.

## Minimal Document Shape

A serialized or synthetic document-like record should have one of these text fields:

- `text`: preferred plain text field for LlamaIndex-compatible records.
- `content`: Kotaemon raw content; may be any JSON value, but indexing text should be non-empty after string conversion.
- `page_content`: accepted by some external tools; convert it to `text` or `content` before using Kotaemon APIs when practical.

Metadata should be a JSON object. Use stable, portable values: strings, numbers, booleans, nulls, lists, and nested objects. Avoid storing local absolute paths in public fixtures or reusable skill examples.

## Metadata Keys Seen in Kotaemon Ingestion

| Key | Typical value | Produced by | How to use |
| --- | --- | --- | --- |
| `source` | Original source id, file name, URL, or upload id | Caller `extra_info`, Mathpix text docs, MHTML | Stable provenance for filtering and citations. Prefer portable identifiers over machine-local paths. |
| `type` | `table`, `text`, `image`, `thumbnail` | Table/OCR/image/thumbnail readers | Route table/image handling and validate `table_origin` or `image_origin`. Text docs may omit this key. |
| `table_origin` | Markdown, HTML, CSV, or extracted table text | DOCX, OCR, Mathpix, Azure DI, Adobe, Docling, PaddleOCR | Preserve original table structure for LLM prompts or visualization. Required for high-quality table docs. |
| `page_label` | 1-based page/sheet label, usually int or string | PDF/OCR/HTML/DOCX/Excel/thumbnail readers | Use in citations and debug reports. Some LlamaIndex PDF readers may provide strings. |
| `page_number` | Numeric page number | Mathpix table docs | Secondary page provenance; keep consistent with `page_label`. |
| `file_name` | Basename such as `report.pdf` | Unstructured, Docling, Adobe, PaddleOCR | Human-readable provenance. |
| `file_path` | Parser-side path string or `Path` object before serialization | Unstructured, Docling, Adobe, PaddleOCR | Useful during live ingestion, but avoid publishing absolute paths in reusable fixtures. |
| `sheet_name` | Excel worksheet name | `ExcelReader` | Use with `page_label` for spreadsheet citations. |
| `title` | MHTML document title | `MhtmlReader` | Useful for web archive provenance. |
| `image_origin` | Base64 data URL or image payload | Docling, Azure DI, Adobe, PaddleOCR, thumbnail reader | Optional image/figure provenance; can be large. |
| `window`, `original_text` | Sentence-window context | `SentenceWindowSplitter` | Helps retrieval surface neighboring context. |

## Table Records

A table document should look like this when serialized:

```json
{
  "text": "| Region | Revenue |\n| --- | --- |\n| APAC | 42 |",
  "metadata": {
    "source": "quarterly-report.pdf",
    "type": "table",
    "table_origin": "| Region | Revenue |\n| --- | --- |\n| APAC | 42 |",
    "page_label": 7
  }
}
```

Checks to make before indexing:

- `text` or `content` is non-empty.
- `metadata.type` is `table` when `table_origin` is present.
- `metadata.table_origin` is non-empty and resembles the original table, not just a short summary.
- `metadata.page_label` is present when the source is paginated.
- Any extra source identifiers supplied through `extra_info` survived parser output.

## Text Records

Text documents commonly omit `type`; if present, use `type: text`. For plain text, HTML, MHTML, DOCX paragraph text, Excel sheet text, and Unstructured joined output, expected metadata may be as small as `{ "source": "..." }` plus page/sheet labels when available.

```json
{
  "text": "Refund requests must be submitted within 30 days.",
  "metadata": {
    "source": "policy.md",
    "page_label": 1,
    "type": "text"
  }
}
```

## Image and Thumbnail Records

Image-like documents normally use `type: image` or `type: thumbnail` and may include `image_origin`. Their `text` should contain a caption or placeholder that is meaningful to retrieval. If a parser can extract the figure but no VLM endpoint is configured, expect empty or extractive-only captions.

## Splitter Output

Splitter output is still a list of `Document` objects, but LlamaIndex relationship fields may be added. Tests verify that `TokenSplitter(chunk_size=30, chunk_overlap=10)` produces chunks whose relationships point back to the source document and neighboring chunks. Preserve metadata through splitting so retrieval can cite the original source/page/table.

## Validator Contract

The bundled validator accepts either:

- a JSON array of document-like objects, or
- a single JSON object representing one document-like object.

It reports errors for missing text/content, non-object metadata, malformed important keys, and table/image consistency problems. It reports warnings for likely provenance gaps such as table records without `page_label` or path-like `source` values.
