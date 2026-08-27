# Troubleshooting pipelines and processing

Use this when a Chonkie pipeline fails to construct, validate, run, refine, or export. Prefer deterministic local checks first: text input, `recursive` chunking, `overlap` refinement, and JSON export.

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Pipeline has no steps to execute` | `Pipeline()` was run without any fluent step | Add at least `chunk_with(...)`. |
| `Pipeline must include a chunker component` | No `chunk_with(...)` step | Add a deterministic chunker such as `.chunk_with("recursive", tokenizer="word", chunk_size=512)`. |
| `Pipeline must include a fetcher component ... or provide text input` | No fetcher and no `texts=` argument | Pass `run(texts=...)` or add `.fetch_from("file", path=...)`/`.fetch_from("file", dir=...)`. |
| `Multiple process steps found` | More than one chef was added | Choose one chef (`text`, `markdown`, `table`, `liteparse`, or `mistral`) and remove the others. |
| `Unknown component` or ambiguous alias | Bad alias or alias used in wrong component category | Use aliases exactly: `file`, `text`, `markdown`, `table`, `liteparse`, `mistral`, `overlap`, `embeddings`, `json`, `datasets`. |
| `Unknown parameters for ...` | A kwarg is accepted by neither the component constructor nor the step method | Check the component signature and rename/remove the parameter. |
| File not found | Bad `FileFetcher` path or directory | Confirm the path exists; in file mode use `path=...`, in directory mode use `dir=...`. |
| Directory returns too many files | Missing extension filter | Use `ext=[".txt", ".md"]` or another explicit suffix list. |
| Pipeline export wrote a file but returned docs | Expected pipeline behavior | `export_with(...)` is a side effect; inspect the returned `Document`/`list[Document]` and the output file separately. |
| Dataset export import error | `datasets` package absent | Install the datasets dependency or use JSON export. |
| Mistral OCR fails before processing | Missing API key or dependency | Provide `api_key`/`MISTRAL_API_KEY` and install provider dependency, or use local `liteparse`/text path instead. |
| Embedding refinement downloads or asks for credentials | String embedding model selected | Route model/provider planning to `../embeddings-and-generative/` or pass a prepared `BaseEmbeddings` instance. |

## Validation failures

### Empty pipeline

Bad:

```python
Pipeline().run(texts="hello")
```

Good:

```python
Pipeline().chunk_with("recursive", tokenizer="word", chunk_size=128).run(texts="hello")
```

### Missing chunker

Bad:

```python
Pipeline().process_with("text").run(texts="hello")
```

Good:

```python
(
    Pipeline()
    .process_with("text")
    .chunk_with("recursive", tokenizer="word", chunk_size=128)
    .run(texts="hello")
)
```

### Missing input

Bad:

```python
Pipeline().chunk_with("recursive").run()
```

Good direct text:

```python
Pipeline().chunk_with("recursive").run(texts="hello")
```

Good file input:

```python
Pipeline().fetch_from("file", path="doc.txt").chunk_with("recursive").run()
```

### Multiple chefs

Bad:

```python
(
    Pipeline()
    .process_with("text")
    .process_with("markdown")
    .chunk_with("recursive")
    .run(texts="# title")
)
```

Good:

```python
Pipeline().process_with("markdown").chunk_with("recursive").run(texts="# title")
```

Only one chef can define the document conversion step. If a workflow seems to need multiple chefs, split it into separate pipelines or pre-normalize the data outside Chonkie.

## Input and return-shape surprises

### Direct text skips fetching

If `run(texts=...)` is supplied, any fetch step is skipped. This can be useful for fallback tests, but it may also hide a bad path:

```python
# Succeeds because the nonexistent file is never fetched.
doc = (
    Pipeline()
    .fetch_from("file", path="missing.txt")
    .chunk_with("recursive")
    .run(texts="direct input")
)
```

Remove `texts=` when you want to verify file fetching.

### Single vs batch returns

- One text string or one file returns one `Document`.
- A list of text strings or a directory fetch returns `list[Document]`.
- `texts=[]` returns `[]`.

Normalize handling in user code:

```python
result = pipeline.run(texts=input_value)
docs = result if isinstance(result, list) else [result]
for doc in docs:
    for chunk in doc.chunks:
        ...
```

### Export does not change returned object

`export_with("json", file=...)` writes chunks and returns the original document(s):

```python
result = Pipeline().chunk_with("recursive").export_with("json", file="chunks.jsonl").run(texts=text)
assert result.chunks
```

If you need the exported data in memory, read the file or call a porter directly.

## File and chef mismatches

### `TableChef` with direct string input

Direct `texts="data.csv"` is parsed as the literal string `data.csv`; it does not read a CSV file.

Use:

```python
(
    Pipeline()
    .fetch_from("file", path="data.csv")
    .process_with("table")
    .chunk_with("table")
    .run()
)
```

Route `TableChunker` parameters and row-token behavior to `../chunking-and-types/`.

### `LiteParse` or `MistralOCR` with direct string input

For these chefs, `parse(text)` wraps the raw string as a `Document`. It does not parse or OCR a file named by that string. Use `fetch_from("file", path=...)` so the chef receives a `Path` and calls `process(path)`.

### Markdown metadata missing

`metadata["filename"]` is only set when a chef processes a file path. Direct `texts=...` parsing creates a document without source filename metadata. Add your own metadata after the run if needed.

## Parameter errors

Pipeline separates keyword arguments into constructor parameters and step-method parameters. Unknown kwargs fail. Common corrections:

| Wrong | Right |
| --- | --- |
| `.fetch_from("file", directory="docs")` | `.fetch_from("file", dir="docs")` |
| `.fetch_from("file", path="a.txt", dir="docs")` | Use exactly one of `path` or `dir`. |
| `.refine_with("overlap", merge_threshold=0.8)` | Use valid overlap args such as `context_size`, `mode`, `method`, `merge`, `inplace`. |
| `.refine_with("embedding", ...)` | Use `.refine_with("embeddings", ...)`. |
| `.export_with("json", output_path="chunks.jsonl")` | Use `.export_with("json", file="chunks.jsonl")`. |

If a parameter belongs to a chunker rather than a chef/refinery, put it on the `chunk_with(...)` step.

## Overlap refinery issues

### Invalid `context_size`

- Integer context sizes must be positive.
- Float context sizes must be in `(0, 1]`.

```python
.refine_with("overlap", tokenizer="word", context_size=20)    # fixed token count
.refine_with("overlap", tokenizer="word", context_size=0.25)  # relative to chunk size
```

### Unexpected text mutation

`merge=True` modifies `chunk.text` by adding context. Use `merge=False` to keep original text and store context separately:

```python
.refine_with("overlap", tokenizer="word", context_size=20, merge=False)
```

Use `inplace=False` when you need to preserve the original chunk objects.

### Mixed chunk types

One overlap call expects all chunks to be the same concrete chunk type. If a document has mixed chunk types after multiple modality chunkers, refine homogeneous groups separately or avoid an overlap refinery at that stage.

## Optional dependency and credential gates

### JSON vs Datasets export

Use JSON/JSONL for the broadest local compatibility:

```python
.export_with("json", file="chunks.jsonl")
```

Use datasets only when the `datasets` package is installed and a Hugging Face `Dataset` is actually needed:

```python
.export_with("datasets", save_to_disk=True, path="chunks_dataset")
```

### LiteParse

LiteParse requires its optional parser dependency. OCR may additionally require local OCR data or a configured OCR server. If unavailable, switch to text/markdown/table chefs for local smoke workflows.

### Mistral OCR

Mistral OCR requires a provider dependency and Mistral API key. Do not use it in offline tests. Confirm supported suffixes before running: PDF and common image types.

### EmbeddingsRefinery

`refine_with("embeddings", embedding_model="...")` can require optional packages, model downloads, or credentials. Before using a string model in production, route to `../embeddings-and-generative/` to choose provider/local-model strategy, cache location, fallbacks, and credential handling.

### Store/write handshakes

`store_in(...)` may create or mutate an external datastore. Before writing, route to `../integrations-and-storage/` to verify package extras, service endpoint, collection/index choice, embedding requirements, and safety constraints.

## Config/recipe failures

`Pipeline.from_config(...)` accepts tuples `(type, component)` or `(type, component, kwargs)` and dicts with `type` plus `component` keys.

Common mistakes:

- Tuple length other than 2 or 3.
- Dict missing `component`.
- Step type not in `fetch`, `vision`, `process`, `chunk`, `refine`, `export`, `write`.
- Passing kwargs with names not accepted by the selected component.

`Pipeline.from_recipe(name)` without a local recipe path can require network access. Use a local recipe file when operating offline or in a reproducible environment.

## Safe smoke command

From any environment where Chonkie is installed:

```bash
python skills/disco/chonkie/sub-skills/pipelines-and-processing/scripts/pipeline_smoke.py
```

Expected behavior:

- Creates temporary text and markdown fixtures.
- Runs direct-text, single-file, directory, markdown, overlap, and JSON export pipelines.
- Asserts return shapes and output file existence.
- Makes no network calls, model downloads, provider API calls, datastore writes, or persistent changes unless `--keep-temp` is requested.
