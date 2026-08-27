# Pipeline workflows

Chonkie `Pipeline` is a fluent document-processing builder. It accepts local text or file paths, converts input into `Document` objects, runs one or more chunkers, applies optional refineries, and optionally exports or writes the final chunks.

## Mental model: CHOMP order

Pipeline steps may be added in any order, but execution is normalized to CHOMP:

```text
fetch -> vision -> process -> chunk -> refine -> export -> write
```

Step ordering details:

- `fetch` runs before processing unless `run(texts=...)` is supplied; direct text input skips any fetcher step.
- `vision` is for file-path OCR/extraction before a chef. Only the last vision step is kept during ordering.
- `process` converts paths or text into `Document` objects. Exactly one user-added chef is allowed. If no chef is added, Pipeline automatically inserts the default `text` chef.
- `chunk` is required. Multiple chunk steps are allowed and run in the order they were added within the chunk phase.
- `refine` is optional. Multiple refinery steps are allowed and run in the order they were added within the refine phase.
- `export` and `write` are optional. Export preserves the document/list return value; write returns the handshake's result.

`Pipeline.describe()` and `repr(pipeline)` show the CHOMP-normalized order, not necessarily the order in which methods were called.

## Fluent API surface

| Method | Component aliases in this sub-skill | Main arguments | Result in pipeline |
| --- | --- | --- | --- |
| `fetch_from(source_type, **kwargs)` | `"file"` | `path=...` for one file, or `dir=...`, `ext=[...]` for a directory | `Path` or `list[Path]` |
| `process_with(chef_type, **kwargs)` | `"text"`, `"markdown"`, `"table"`, `"liteparse"`, `"mistral"` | Chef constructor/call arguments | `Document` or `list[Document]` |
| `chunk_with(chunker_type, **kwargs)` | Common deterministic choices: `"recursive"`, `"token"`, `"sentence"`; table/code details route to `../chunking-and-types/` | Chunker constructor/call arguments such as `tokenizer`, `chunk_size`, `min_characters_per_chunk` | `Document` with `.chunks` |
| `refine_with(refinery_type, **kwargs)` | `"overlap"`, `"embeddings"` | Refinery constructor/call arguments | `Document` with refined `.chunks` |
| `export_with(porter_type, **kwargs)` | `"json"`, `"datasets"` | Porter arguments such as `file=...`, `lines=False`, `save_to_disk=...` | Original `Document`/`list[Document]` is returned after export |
| `store_in(handshake_type, **kwargs)` | Vector/datastore handshakes | Service, collection, credentials, embedding model arguments | Handshake `write()` result; route live storage design to `../integrations-and-storage/` |

Pipeline splits keyword arguments into component constructor arguments and call-time arguments by inspecting signatures. Unknown names fail with a clear parameter error. Prefer exact public parameter names.

## Required validation rules

A pipeline fails before or during execution when any of these rules are violated:

1. At least one step must be present.
2. A chunker is required: use `chunk_with(...)`.
3. Input is required: either add `fetch_from(...)` or pass `texts=...` to `run()`/`arun()`.
4. Only one user-added chef is allowed: do not chain `process_with("text").process_with("markdown")`.
5. Component aliases must be registered and unambiguous.
6. Component parameters must be accepted by the component constructor or the relevant step method.

`run(texts=[])` returns an empty list instead of failing.

## Return shapes

| Input form | Typical construction | Return from `run()` |
| --- | --- | --- |
| One text string | `Pipeline().chunk_with("recursive").run(texts="...")` | One `Document` |
| List of text strings | `Pipeline().chunk_with("recursive").run(texts=["a", "b"])` | `list[Document]` |
| One fetched file | `Pipeline().fetch_from("file", path="doc.txt").chunk_with("recursive").run()` | One `Document` |
| Directory fetch | `Pipeline().fetch_from("file", dir="docs", ext=[".txt", ".md"]).chunk_with("recursive").run()` | `list[Document]` |
| Empty list input | `Pipeline().chunk_with("recursive").run(texts=[])` | Empty list |
| Pipeline export | `...export_with("json", file="chunks.jsonl").run(...)` | Original `Document` or `list[Document]`; the export file is a side effect |
| Pipeline write | `...store_in("chroma", ...).run(...)` | The handshake `write()` result, not the original document |

## Deterministic local text ingestion

Use direct `texts=...` input for generated or already-loaded strings. The fetcher is optional, and the default `text` chef is inserted if no chef is specified.

```python
from chonkie import Pipeline

text = "Intro paragraph.\n\nSecond paragraph with more detail."

doc = (
    Pipeline()
    .chunk_with("recursive", tokenizer="word", chunk_size=128, min_characters_per_chunk=1)
    .run(texts=text)
)

assert doc.content == text
assert doc.chunks
```

When exact pre-processing matters, specify the chef explicitly:

```python
doc = (
    Pipeline()
    .process_with("text")
    .chunk_with("recursive", tokenizer="word", chunk_size=128, min_characters_per_chunk=1)
    .run(texts=text)
)
```

## Single file ingestion

```python
from chonkie import Pipeline

# Default TextChef is inserted because no process_with() call is present.
doc = (
    Pipeline()
    .fetch_from("file", path="notes.txt")
    .chunk_with("recursive", tokenizer="word", chunk_size=256, min_characters_per_chunk=1)
    .run()
)

assert doc.metadata.get("filename") == "notes.txt"
assert doc.chunks
```

For file-backed processing, fetched values are `Path` objects. A chef receives paths via `process(path)`, so file metadata such as `metadata["filename"]` is set by local chefs that support it.

## Directory ingestion

```python
docs = (
    Pipeline()
    .fetch_from("file", dir="documents", ext=[".txt", ".md"])
    .process_with("text")
    .chunk_with("recursive", tokenizer="word", chunk_size=256, min_characters_per_chunk=1)
    .run()
)

assert isinstance(docs, list)
for doc in docs:
    assert doc.metadata.get("filename")
    assert doc.chunks
```

Always pass `ext=[...]` for directory mode unless the directory is known to contain only text-like files. Without a filter, `FileFetcher` recursively returns every regular file under the directory tree.

## Markdown-aware ingestion

Use `process_with("markdown")` when you need markdown tables, fenced code blocks, images, and remaining prose identified before chunking.

```python
from chonkie import Pipeline, MarkdownDocument

markdown = """# Report

A short paragraph.

| Metric | Value |
| --- | --- |
| Accuracy | 0.95 |

```python
print("hello")
```
"""

doc = (
    Pipeline()
    .process_with("markdown")
    .chunk_with("recursive", tokenizer="word", chunk_size=128, min_characters_per_chunk=1)
    .run(texts=markdown)
)

assert isinstance(doc, MarkdownDocument)
assert doc.tables
assert doc.code
assert doc.chunks
```

For modality-specific table/code chunkers after markdown parsing, route raw chunker details to `../chunking-and-types/`.

## Add overlap refinement

`OverlapRefinery` is deterministic and local. It can add context from neighboring chunks without embeddings or network calls.

```python
doc = (
    Pipeline()
    .process_with("text")
    .chunk_with("recursive", tokenizer="word", chunk_size=80, min_characters_per_chunk=1)
    .refine_with(
        "overlap",
        tokenizer="word",
        context_size=12,
        mode="token",
        method="suffix",
        merge=False,
        inplace=False,
    )
    .run(texts="Long text. " * 200)
)

if len(doc.chunks) > 1:
    assert hasattr(doc.chunks[0], "context")
```

Choose overlap methods by retrieval intent:

- `method="suffix"`: add context from the next chunk to each chunk except the last.
- `method="prefix"`: add context from the previous chunk to each chunk except the first.
- `method="justified"`: add both neighboring contexts for middle chunks.
- `merge=True`: context is concatenated into `chunk.text` and token counts increase.
- `merge=False`: context is stored separately in `chunk.context` while text and indexes stay easier to reason about.
- `inplace=False`: original chunks are copied before refinement.

## Add embeddings as a refinement step

The registered pipeline alias is `"embeddings"`:

```python
doc = (
    Pipeline()
    .chunk_with("recursive", tokenizer="word", chunk_size=512)
    .refine_with("embeddings", embedding_model=my_base_embeddings_instance)
    .run(texts="Text to embed")
)
```

Embedding refineries call the embedding model on every chunk and set `chunk.embedding`. String model names can trigger optional dependency resolution or model/provider access. For provider keys, model downloads, semantic chunking, or local embedding cache decisions, route to `../embeddings-and-generative/` before running.

## JSON export from a pipeline

`export_with("json", ...)` flattens all chunks from the returned document(s), writes them, and then returns the original document(s) for chaining/inspection.

```python
doc = (
    Pipeline()
    .chunk_with("recursive", tokenizer="word", chunk_size=128, min_characters_per_chunk=1)
    .export_with("json", file="chunks.jsonl")
    .run(texts="Export me. " * 50)
)

assert doc.chunks
```

Use `export_with("json", lines=False, file="chunks.json")` to write a JSON array instead of JSONL. For direct porter usage outside a pipeline, instantiate `JSONPorter(lines=True|False)` and call `export(chunks, file=...)`.

## Dataset export/porting pattern

`DatasetsPorter` converts chunks into a Hugging Face `Dataset` and can save it to disk. In direct use, `export()` returns the `Dataset`. In pipeline use, `export_with("datasets", ...)` still returns the original document(s) after performing the export side effect.

```python
from chonkie import DatasetsPorter

# Direct porter pattern; requires the datasets dependency.
dataset = DatasetsPorter().export(doc.chunks, save_to_disk=False)
```

Use JSON when the environment may not have the `datasets` package or when a simple portable artifact is enough.

## Config and recipe construction

`Pipeline.from_config(...)` accepts either a list or a JSON file path. Steps can be tuples or dictionaries.

```python
from chonkie import Pipeline

pipeline = Pipeline.from_config([
    ("process", "text"),
    ("chunk", "recursive", {"tokenizer": "word", "chunk_size": 256}),
    ("refine", "overlap", {"tokenizer": "word", "context_size": 20}),
])

doc = pipeline.run(texts="Configured pipeline text. " * 20)
```

`Pipeline.to_config(path=None)` exports the currently added steps using component aliases.

`Pipeline.from_recipe(name, path=None)` loads a recipe. Supplying a local `path` is the safe offline pattern. Loading by name without a local path may require hub/network access.

## Async execution

Use `await pipeline.arun(texts=...)` when integrating with async applications. It mirrors `run()` behavior and uses async component methods where available.

```python
async def build_docs(texts):
    pipe = Pipeline().chunk_with("recursive", tokenizer="word", chunk_size=256)
    return await pipe.arun(texts=texts)
```

Do not use async execution to hide model-download, credential, or external-service dependencies; plan those dependencies explicitly first.
