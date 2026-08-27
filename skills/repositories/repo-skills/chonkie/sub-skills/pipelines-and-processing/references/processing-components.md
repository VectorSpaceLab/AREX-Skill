# Processing components

This reference summarizes the Chonkie components most often used inside local pipeline workflows. Component aliases are the strings passed to `fetch_from`, `process_with`, `refine_with`, and `export_with`.

## Component selection table

| Need | Use | Pipeline call | Notes |
| --- | --- | --- | --- |
| Read one local text file | `FileFetcher` + default/TextChef | `.fetch_from("file", path="doc.txt").chunk_with(...)` | Default `text` chef is inserted if no chef is specified. |
| Read a local directory | `FileFetcher` | `.fetch_from("file", dir="docs", ext=[".txt", ".md"])` | Recursive walk; pass `ext` to avoid binary/unwanted files. |
| Wrap raw strings as documents | `TextChef` | `.process_with("text").run(texts=...)` | Direct `texts` can omit this because default `TextChef` is inserted. |
| Preserve markdown modalities | `MarkdownChef` | `.process_with("markdown")` | Extracts tables, fenced code blocks, images, and remaining prose chunks. |
| Convert CSV/Excel or extract markdown/HTML tables | `TableChef` | `.process_with("table")` | File-backed CSV/Excel path requires pandas/table extras; direct text extracts tables from markdown-like content. |
| Parse PDFs/office/images locally | `LiteParse` | `.process_with("liteparse")` | Requires the `liteparse` optional dependency and local OCR/document parser support. |
| OCR PDFs/images through Mistral | `MistralOCR` | `.process_with("mistral")` | Requires `mistralai` dependency and a Mistral API key. |
| Add neighboring context | `OverlapRefinery` | `.refine_with("overlap", ...)` | Deterministic local refinery; safe default for RAG context. |
| Attach vectors to chunks | `EmbeddingsRefinery` | `.refine_with("embeddings", ...)` | String models may need optional packages, downloads, network, or provider credentials. |
| Export chunks to JSON/JSONL | `JSONPorter` | `.export_with("json", file="chunks.jsonl")` | Pipeline returns the original docs after writing. |
| Export chunks as Hugging Face Dataset | `DatasetsPorter` | `.export_with("datasets", save_to_disk=True, path="chunks")` | Requires `datasets`; direct use returns a `Dataset`. |

## FileFetcher

Alias: `"file"`

Constructor:

```python
FileFetcher()
```

Fetch method:

```python
fetch(path: str | os.PathLike | None = None,
      dir: str | os.PathLike | None = None,
      ext: list[str] | None = None) -> Path | list[Path]
```

Behavior:

- Provide exactly one of `path` or `dir`.
- `path` mode returns one `Path` and raises `FileNotFoundError` if it is not a file.
- `dir` mode recursively walks the directory without following symlink loops and returns all matching regular files.
- `ext` filters by exact extension strings such as `[".txt", ".md"]`; it only applies in directory mode.
- Directory order should not be used for semantic meaning; sort downstream if stable ordering matters.

Example:

```python
docs = (
    Pipeline()
    .fetch_from("file", dir="docs", ext=[".txt", ".md"])
    .process_with("text")
    .chunk_with("recursive", tokenizer="word", chunk_size=256)
    .run()
)
```

## TextChef

Alias: `"text"`

Constructor:

```python
TextChef()
```

Key methods:

```python
process(path: str | os.PathLike) -> Document
parse(text: str) -> Document
process_batch(paths: list[str | os.PathLike]) -> list[Document]
```

Behavior:

- `process(path)` reads UTF-8 text from a file and sets `doc.metadata["filename"]` to the basename.
- `parse(text)` wraps raw text in a `Document` and does not set `filename` metadata.
- In a pipeline, a fetched `Path` calls `process(path)`; a direct `texts="..."` string calls `parse(text)`.
- If no `process_with(...)` step is supplied, the pipeline inserts `TextChef` automatically.

## MarkdownChef

Alias: `"markdown"`

Constructor:

```python
MarkdownChef(tokenizer: TokenizerProtocol | str = "character")
```

Key methods:

```python
parse(text: str) -> MarkdownDocument
process(path: str | os.PathLike) -> MarkdownDocument
prepare_tables(markdown: str) -> list[MarkdownTable]
prepare_code(markdown: str) -> list[MarkdownCode]
extract_images(markdown: str) -> list[MarkdownImage]
```

Behavior:

- Parses markdown into `MarkdownDocument(content=..., tables=..., code=..., images=..., chunks=...)`.
- Fenced code blocks record language when present.
- Markdown pipe tables record `content`, `start_index`, and `end_index`.
- Images record alias/content/link and source indexes.
- Remaining non-table/code/image prose becomes initial `Chunk` objects.
- `process(path)` reads the file, parses it, and sets `metadata["filename"]`.

Example:

```python
md_doc = (
    Pipeline()
    .process_with("markdown", tokenizer="word")
    .chunk_with("recursive", tokenizer="word", chunk_size=256)
    .run(texts=markdown_text)
)

assert md_doc.tables or md_doc.code or md_doc.images or md_doc.chunks
```

## TableChef

Alias: `"table"`

Constructor:

```python
TableChef()
```

Key methods:

```python
process(path: str | os.PathLike) -> Document
parse(text: str) -> Document
extract_tables_from_markdown(markdown: str) -> list[MarkdownTable]
```

Behavior:

- For an existing `.csv` file, reads it with pandas and converts it to markdown table text.
- For an existing `.xls`/`.xlsx` file, reads all sheets and converts each to markdown table text.
- For non-file strings or direct `texts=...`, treats the string as markdown-like content and extracts markdown/HTML tables.
- Sets `metadata["filename"]` only when processing an actual file path.
- Requires the table/pandas dependency family for CSV/Excel conversion. If only markdown table extraction is needed, direct text parsing avoids spreadsheet reads.

Pitfall:

```python
# This parses the literal string "data.csv" as markdown text; it does not read the file.
Pipeline().process_with("table").chunk_with("recursive").run(texts="data.csv")

# Use file fetching so TableChef receives a Path and calls process(path).
Pipeline().fetch_from("file", path="data.csv").process_with("table").chunk_with("table").run()
```

Route `TableChunker` details to `../chunking-and-types/`.

## LiteParse

Alias: `"liteparse"`

Constructor:

```python
LiteParse(
    ocr_enabled: bool = True,
    ocr_server_url: str | None = None,
    ocr_language: str | None = None,
    tessdata_path: str | None = None,
    max_pages: int | None = None,
    target_pages: str | None = None,
    dpi: float | None = None,
    output_format: str | None = None,
    preserve_very_small_text: bool | None = None,
    password: str | None = None,
    quiet: bool | None = None,
    num_workers: int | None = None,
)
```

Supported file types include PDF, office formats such as DOC/DOCX/PPT/XLS/XLSX/CSV/TSV, and common image types such as PNG/JPG/TIFF/WEBP/SVG.

Behavior:

- `process(path)` validates file existence and supported suffix, then extracts text locally and returns a `Document` with `filename` metadata.
- `parse(text)` simply wraps the raw text in a `Document`; it does not OCR or parse a file from a string.
- Requires the `liteparse` package family. OCR may also require local OCR data or server configuration.

Use LiteParse when local document extraction is required and cloud OCR is not acceptable.

## MistralOCR

Alias: `"mistral"`

Constructor:

```python
MistralOCR(model: str = "mistral-ocr-latest", api_key: str | None = None)
```

Supported file types include PDF plus common image types such as PNG/JPG/JPEG/GIF/BMP/WEBP/TIFF.

Behavior:

- `process(path)` sends a data URI to the Mistral OCR API and returns a `MarkdownDocument` with page markdown joined by blank lines.
- `parse(text)` simply wraps raw text in a `Document`; it does not call OCR.
- Requires the `mistralai` dependency and either the `api_key` constructor argument or `MISTRAL_API_KEY` in the environment.
- Do not run this in a local smoke or offline workflow.

Use MistralOCR only after the user explicitly authorizes live OCR/API usage.

## OverlapRefinery

Alias: `"overlap"`

Constructor:

```python
OverlapRefinery(
    tokenizer: TokenizerProtocol | str = "character",
    context_size: int | float = 0.25,
    mode: "token" | "recursive" = "token",
    method: "suffix" | "prefix" | "justified" = "suffix",
    rules: RecursiveRules = RecursiveRules(),
    merge: bool = True,
    inplace: bool = True,
)
```

Behavior:

- Refines a list of chunks or a document's `.chunks` by adding neighboring context.
- `context_size` can be a positive integer token count or a float in `(0, 1]` interpreted relative to chunk token counts.
- `mode="token"` takes token windows; `mode="recursive"` uses recursive delimiter rules.
- `method="suffix"` adds context from the next chunk to earlier chunks.
- `method="prefix"` adds context from the previous chunk to later chunks.
- `method="justified"` adds both sides where available.
- `merge=True` concatenates context into `chunk.text`; `merge=False` keeps it in `chunk.context`.
- `inplace=False` copies chunks before mutation.
- Start/end indexes remain the original document positions even when context is merged into text.
- Chunks must be of one concrete chunk type for one refinement call.

Safe deterministic RAG default:

```python
.refine_with("overlap", tokenizer="word", context_size=50, mode="token", method="suffix", merge=False)
```

## EmbeddingsRefinery

Alias: `"embeddings"`

Constructor:

```python
EmbeddingsRefinery(
    embedding_model: str | BaseEmbeddings | AutoEmbeddings = "minishlab/potion-retrieval-32M",
    **kwargs,
)
```

Behavior:

- Calls `embed_batch([chunk.text for chunk in chunks])` and assigns each result to `chunk.embedding`.
- Passing an existing `BaseEmbeddings` instance is the safest deterministic/testable pattern.
- Passing a string model delegates to Chonkie's embedding resolution and may require optional packages, model downloads, provider credentials, or network access.
- The `dimension` property exposes the model's embedding dimension.

Route all provider/model selection, cache/download planning, and credential troubleshooting to `../embeddings-and-generative/` before running a live embedding step.

## JSONPorter

Alias: `"json"`

Constructor:

```python
JSONPorter(lines: bool = True)
```

Export method:

```python
export(chunks: list[Chunk], file: str | os.PathLike = "chunks.jsonl", **kwargs) -> None
```

Behavior:

- `lines=True` writes JSON Lines. Default filename is `chunks.jsonl`.
- `lines=False` writes a JSON array. Pass a suitable filename such as `chunks.json`.
- Uses each chunk's `to_dict()` representation and preserves non-ASCII text.
- Serializes fields such as `text`, `start_index`, `end_index`, `token_count`, `context`, `embedding`, and `metadata` when present.
- Pipeline export flattens chunks across all documents, writes the file, and returns the original document(s).

Example:

```python
Pipeline().chunk_with("recursive").export_with("json", file="chunks.jsonl").run(texts=text)
```

## DatasetsPorter

Alias: `"datasets"`

Constructor:

```python
DatasetsPorter()
```

Export method:

```python
export(
    chunks: list[Chunk],
    save_to_disk: bool = True,
    path: str | os.PathLike = "chunks",
    **kwargs,
) -> Dataset
```

Behavior:

- Requires the `datasets` package.
- Converts `[chunk.to_dict() for chunk in chunks]` into a Hugging Face `Dataset`.
- If `save_to_disk=True`, writes the dataset to `path` and forwards extra keyword arguments to `save_to_disk`.
- Direct use returns the `Dataset` object.
- Pipeline use performs the export side effect but returns the input `Document` or `list[Document]`.

Use `JSONPorter` as the default portable export when `datasets` is unavailable or not needed.

## Store/write boundary

`store_in(...)` is available on `Pipeline`, but live handshakes require datastore packages, services, credentials, and often embedding models. Keep vector DB planning and write/search behavior in `../integrations-and-storage/`; use this sub-skill only to place the write step correctly in the pipeline order.
