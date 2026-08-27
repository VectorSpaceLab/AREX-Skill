# Data formats and local loaders

Use this reference for the source-to-`Document` half of a DB-GPT RAG pipeline.
The loader classes live in the `dbgpt_ext.rag.knowledge` package and return
`dbgpt.core.Document` objects with `content` and `metadata`.

## Factory dispatch

```python
from dbgpt.rag.knowledge.base import KnowledgeType
from dbgpt_ext.rag.knowledge import KnowledgeFactory

knowledge = KnowledgeFactory.create(
    datasource="notes.md",
    knowledge_type=KnowledgeType.DOCUMENT,
    metadata={"dataset": "demo"},
)
# or:
knowledge = KnowledgeFactory.from_file_path("notes.md")
text_knowledge = KnowledgeFactory.from_text(
    "small deterministic fixture", metadata={"dataset": "demo"}
)
```

`KnowledgeFactory.create` accepts `datasource`, `knowledge_type`, and optional
metadata. `DOCUMENT` dispatches by the final extension; `TEXT` creates a
`StringKnowledge`; `URL` creates a `URLKnowledge` and can perform network I/O
when loaded. Unsupported extensions raise an error rather than being guessed.
Use a concrete loader when a format-specific option matters.

The factory recognizes these document implementations in 0.8.1:

| Format | Class | Local behavior and metadata |
|---|---|---|
| `.csv` | `CSVKnowledge` | One `Document` per row; `source` and zero-based `row` metadata. Optional `source_column` sets the source value. `encoding` defaults to UTF-8. |
| `.md` | `MarkdownKnowledge` | One document containing the file; `source` and basename-like `title` metadata. UTF-8 by default and `errors="ignore"` for direct file loading. |
| `.txt` | `TXTKnowledge` | Reads bytes and uses `chardet` to detect encoding; falls back to UTF-8 when detection has no encoding. `source` metadata is retained. |
| `.pdf` | `PDFKnowledge` | Parser-dependent page/text extraction; output carries page/title/type/source metadata. Requires the PDF parser stack and should be tested with a tiny valid PDF. |
| `.docx` | `DocxKnowledge` | Reads paragraph text from a local Word document and joins paragraphs with newlines. Requires `python-docx`. |
| `.xlsx` | `ExcelKnowledge` | Reads every non-empty sheet, detects a header row, handles merged cells, emits one document per non-empty data row, and adds `sheet_name`, row, `data_type="excel"`, source, and column metadata. Requires `openpyxl`, pandas, and the package's Excel dependencies. |
| `.html` | `HTMLKnowledge` | HTML parser-backed local document loading; parser extras may be optional. |
| `.doc` / `.pptx` | corresponding document classes | Optional parser support; treat import/fixture availability as a gate. |
| datasource | `DatasourceKnowledge` | Builds database summary documents from a `BaseConnector`; this is schema RAG, not a file parser. |

The exact extension must match the factory's `DocumentType` values (`pdf`,
`csv`, `md`, `pptx`, `docx`, `txt`, `html`, `datasource`, `xlsx`, `doc`). A
`.markdown` suffix is not the same as `.md` for factory dispatch; normalize or
select `MarkdownKnowledge` explicitly if needed.

## File safety and encodings

1. Resolve a user-provided path as a file under an approved working directory;
   do not recursively ingest an unspecified home directory.
2. Check `is_file()`, size, and read permission before constructing a loader.
   A zero-byte file is valid filesystem input but not useful RAG input: warn and
   skip it unless the caller explicitly wants an empty-document diagnostic.
3. For CSV, choose `encoding` deliberately. UTF-8 is the default; if decoding
   fails, retry only with an encoding identified by the caller or a bounded
   detection step. Do not silently reinterpret a credential/export file.
4. For TXT, the implementation detects encoding from bytes. Record the detected
   encoding in a validation report if reproducibility matters; detection can be
   uncertain for short or mixed-byte files.
5. Markdown direct loading ignores undecodable bytes. Preserve the original file
   as the source of truth and report that replacement/ignored-byte behavior may
   lose content. Use an explicit encoding and a preflight decode for strict
   ingestion.
6. CSV rows with `None` keys/values omit those cells. If `source_column` is set
   but absent, loading raises `ValueError`; fix the column name rather than
   treating the entire row as source content.
7. Excel sheets with no usable columns, no data rows, or only blank values are
   skipped. Numeric-only sheets fall back to numeric column names; this is a
   warning-worthy fallback, not a header guarantee.
8. PDF, DOCX, and XLSX are binary formats. A file extension is not proof of a
   valid file. Catch parser exceptions and report the file as invalid; do not
   pass raw binary bytes to a text splitter.

## Documents and metadata

A `Document` should have non-empty string content before chunking. Keep metadata
small and serializable. Recommended fields are:

```python
{
    "source": "approved-relative-name.md",
    "format": "md",
    "dataset": "fixture",
    "page": 1,          # when the parser provides it
    "row": 0,           # CSV or spreadsheet row
    "sheet_name": "Sheet1",
}
```

Do not put passwords, full private filesystem paths, or raw connection URLs in
metadata. For repeated indexing, supply a stable document identity in metadata
or use the caller's file/document id so duplicate detection is possible.

## Chunk strategies by format

`Knowledge.default_chunk_strategy()` is format-specific:

- Markdown defaults to `CHUNK_BY_MARKDOWN_HEADER`, preserving heading metadata
  and using recursive splitting for oversized heading sections.
- CSV and TXT default to `CHUNK_BY_SIZE`; they also support
  `CHUNK_BY_SEPARATOR`.
- DOCX supports size, paragraph, and separator strategies.
- Excel and row-oriented data support size and separator strategies; Excel rows
  are treated as table-like chunks and preserve row metadata.
- PDF and datasource knowledge support strategies appropriate to their page or
  schema representation; inspect the concrete class before overriding.

An explicit `ChunkParameters(chunk_strategy="Automatic", ...)` asks the
knowledge object to use its default. An invalid strategy raises a descriptive
`ValueError`; do not fall back to an unrelated splitter.

## Invalid and duplicate inputs

For a batch:

- classify each file as `accepted`, `skipped-empty`, `skipped-unsupported`, or
  `skipped-invalid`;
- include a short reason and deterministic relative identifier;
- continue only when the caller allows partial ingestion;
- fail the run if every file is skipped or if strict mode is requested.

Duplicate files can produce duplicate chunks. Before persistence, compare a
stable source/document id and content hash within the current batch. Decide
whether duplicates mean `skip`, `replace`, or `allow`; do not assume that a
vector store's upsert is equivalent to knowledge-space duplicate policy. Live
knowledge-space duplicate/upload behavior belongs to the API/client route.
