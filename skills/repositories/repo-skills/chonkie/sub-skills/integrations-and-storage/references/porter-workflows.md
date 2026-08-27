# Porter workflows

Porters export Chonkie chunks for offline storage or dataset handoff. They are
not query engines. Use them when the user wants files, artifacts, or a Hugging
Face `Dataset` rather than a vector database.

For chunk creation and data types, see `../chunking-and-types/`. For pipeline
composition and CHOMP execution order, see `../pipelines-and-processing/`. For
CLI output/deployment surfaces, see `../interfaces-and-deployment/`.

## Porter API summary

| Class | Install surface | Constructor | Main call | Return value | Notes |
| --- | --- | --- | --- | --- | --- |
| `JSONPorter` | Base Chonkie package | `JSONPorter(lines=True)` | `export(chunks, file="chunks.jsonl")`; `porter(chunks, file=...)`; `aexport(...)` | `None` | `lines=True` writes JSONL; `lines=False` writes one JSON array with 4-space indentation. Uses UTF-8 and `ensure_ascii=False`. |
| `DatasetsPorter` | `chonkie[datasets]` or compatible `datasets` package | `DatasetsPorter()` | `export(chunks, save_to_disk=True, path="chunks", **save_kwargs)`; `porter(...)`; `aexport(...)` | `datasets.Dataset` | Builds `Dataset.from_list([chunk.to_dict() ...])`. When `save_to_disk=True`, forwards extra kwargs to `Dataset.save_to_disk`. |

`BasePorter` defines the shared `export`, `aexport`, and `__call__` contract.
Inputs are lists of `Chunk` objects. If you have a `Document` or a list of
`Document` objects, flatten `doc.chunks` first or use `Pipeline.export_with(...)`.

## JSONPorter workflows

### JSONL for streaming or append-friendly downstream tools

```python
from pathlib import Path
from chonkie import TokenChunker
from chonkie.porters import JSONPorter

Path("artifacts").mkdir(exist_ok=True)
chunks = TokenChunker(chunk_size=64).chunk("Unicode text: café 世界 🌍")
JSONPorter(lines=True).export(chunks, file="artifacts/chunks.jsonl")
```

Properties:

- one JSON object per line;
- each object is `chunk.to_dict()`;
- non-ASCII text is written as original UTF-8 characters, not `\uXXXX` escapes;
- an empty chunk list creates an empty file;
- parent directories are not created automatically, so create them first.

### Pretty JSON array for review or interchange

```python
from chonkie.porters import JSONPorter

porter = JSONPorter(lines=False)
porter.export(chunks, file="artifacts/chunks.json")
```

Important quirk: the default `file` value is always `"chunks.jsonl"`, even when
`lines=False`. Pass a `.json` filename explicitly when writing JSON arrays.

### Async JSON export

```python
await JSONPorter(lines=True).aexport(chunks, file="chunks.jsonl")
```

`aexport` delegates synchronous file writing to a worker thread; it is useful in
async orchestration but does not make the file format itself streaming-async.

## DatasetsPorter workflows

### Return an in-memory Dataset without saving

```python
from chonkie.porters import DatasetsPorter

porter = DatasetsPorter()
dataset = porter.export(chunks, save_to_disk=False)
print(dataset.column_names)
```

Typical columns reflect `Chunk.to_dict()` output, including fields such as
`id`, `text`, `start_index`, `end_index`, `token_count`, `context`, `embedding`,
and `metadata` when present in the chunk representation.

### Save to disk for later `Dataset.load_from_disk(...)`

```python
from datasets import Dataset
from chonkie.porters import DatasetsPorter

out_dir = "artifacts/chonkie_dataset"
dataset = DatasetsPorter().export(
    chunks,
    save_to_disk=True,
    path=out_dir,
    num_shards=1,
)
reloaded = Dataset.load_from_disk(out_dir)
assert len(reloaded) == len(dataset)
```

`save_to_disk` kwargs such as `num_shards` and `num_proc` are forwarded to the
underlying Hugging Face Datasets method. Avoid writing into a non-empty important
directory unless the user approves overwriting or updating that dataset.

### Missing dependency behavior

Constructing `DatasetsPorter()` checks for the `datasets` library. If it is not
available, install the selected optional dependency, for example:

```bash
python -m pip install 'chonkie[datasets]'
```

The no-network dependency probe in `scripts/handshake_dependency_probe.py` also
reports `datasets` availability.

## Pipeline export patterns

`Pipeline.export_with(porter_type, **kwargs)` registers a porter step. During
`run(...)`, Chonkie orders export after fetch/process/chunk/refine, extracts all
chunks from the current `Document` or document list, calls `export(chunks,
**call_kwargs)`, and returns the original document output for continued use.

### Export direct text to JSONL

```python
from chonkie import Pipeline

result_doc = (
    Pipeline()
    .chunk_with("recursive", chunk_size=128)
    .export_with("json", lines=True, file="artifacts/chunks.jsonl")
    .run(texts="Text to chunk and export")
)
print(len(result_doc.chunks))
```

`lines` is a `JSONPorter` constructor argument; `file` is an `export(...)`
argument. Chonkie's pipeline splits these parameters automatically.

### Export direct text to a Dataset directory

```python
from chonkie import Pipeline

result_doc = (
    Pipeline()
    .chunk_with("recursive", chunk_size=128)
    .export_with("datasets", save_to_disk=True, path="artifacts/chunks_ds")
    .run(texts="Text to chunk and turn into a Hugging Face Dataset")
)
```

Use `save_to_disk=False` when the caller wants the returned `Document` and does
not need a persisted dataset. If the caller needs the in-memory `Dataset` object
itself, call `DatasetsPorter.export(...)` directly because pipeline export
returns the document(s), not the porter return value.

## Manual flattening from documents

```python
from chonkie import Pipeline
from chonkie.porters import JSONPorter

output = Pipeline().chunk_with("recursive", chunk_size=128).run(texts=["one", "two"])
docs = output if isinstance(output, list) else [output]
chunks = [chunk for doc in docs for chunk in doc.chunks]
JSONPorter(lines=True).export(chunks, file="chunks.jsonl")
```

Flatten manually when you need multiple exports from the same chunk set, custom
post-processing before export, or the `DatasetsPorter` return value.

## Choosing a porter vs a handshake

| User intent | Prefer | Why |
| --- | --- | --- |
| Save chunks for audit, snapshots, or deterministic tests | `JSONPorter` | No optional service or credentials; human-readable; easy diffing. |
| Feed chunks into Hugging Face dataset tooling | `DatasetsPorter` | Produces a `Dataset` and can save/load via Datasets APIs. |
| Search chunks by vector similarity in memory/local service | A safe handshake such as Qdrant/Chroma/LanceDB with temporary target | Adds embeddings and search behavior; still a mutation, so confirm target. |
| Write chunks to managed vector DB or production datastore | Concrete handshake only after explicit service/credential approval | Live writes can create indexes/collections and incur costs. |

## Output validation checklist

- Confirm the input is a list of `Chunk` objects or flatten `Document.chunks`.
- Create parent directories before file/dataset export.
- Use an explicit filename when `JSONPorter(lines=False)` should write a JSON
  array.
- For JSONL, validate by reading line-by-line with `json.loads`.
- For JSON arrays, validate with `json.load` and check list length.
- For datasets, check `len(dataset)` and required columns, and reload from disk
  when `save_to_disk=True`.
- Keep large or private chunk exports out of source-control unless the user
  explicitly wants them committed.
