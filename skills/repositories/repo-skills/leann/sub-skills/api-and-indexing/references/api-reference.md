# Python API reference

This reference describes the LEANN 0.3.8 Python surface verified from the
installed package and implementation. Import public lifecycle types with:

```python
from leann import LeannBuilder, LeannSearcher
from leann.api import SearchResult
```

## `LeannBuilder`

```python
LeannBuilder(
    backend_name: str,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    dimensions: int | None = None,
    embedding_mode: str = "sentence-transformers",
    embedding_options: dict[str, Any] | None = None,
    prebuild_bm25: bool = False,
    bm25_backend: str = "fts5",
    passage_id_scheme: str = "sequential",
    **backend_kwargs,
)
```

| Parameter | Meaning and verified behavior |
| --- | --- |
| `backend_name` | Required registered backend, normally `"hnsw"`, `"ivf"`, or `"diskann"` when that package is installed. |
| `embedding_model` | Model identifier persisted in metadata and reused for query/recompute embedding. |
| `dimensions` | Expected vector width. Ordinary builds infer it by embedding `"dummy"` when omitted; precomputed-array builds infer it from `embeddings.shape[1]`. |
| `embedding_mode` | Provider mode persisted in metadata. Provider details belong to the embeddings sub-skill. |
| `embedding_options` | Provider options persisted when nonempty. |
| `prebuild_bm25` | Signature default is `False`. In 0.3.8, the default `bm25_backend="fts5"` nevertheless makes ordinary `build_index` prebuild FTS5; array/pickle build methods do not call the BM25 builder. |
| `bm25_backend` | Only `"fts5"` is active. Any other value emits a warning and is replaced by `"fts5"`. |
| `passage_id_scheme` | `"sequential"` or `"content-hash"`. An explicit metadata `id` overrides either scheme. |
| `backend_kwargs` | Forwarded to the selected backend. Do not copy tuning values between backends without consulting [backends and storage](../../backends-and-storage/SKILL.md). |

Normalized OpenAI, Voyage, and Cohere embedding names are detected. If no
`distance_metric` backend argument is set, detection sets it to `"cosine"` and
warns; a conflicting explicit metric also warns.

### Passage methods

```python
builder.add_text(text: str, metadata: dict[str, Any] | None = None)
builder.build_index(index_path: str)
builder.build_index_from_arrays(index_path: str, ids: list, embeddings: numpy.ndarray)
builder.build_index_from_embeddings(index_path: str, embeddings_file: str)
builder.update_index(index_path: str, remove_passage_ids: list[str] | None = None) -> None
```

`add_text` buffers a record shaped as:

```python
{"id": passage_id, "text": text, "metadata": metadata}
```

ID behavior:

- `metadata["id"]` wins when truthy.
- `sequential` generates `str(len(builder.chunks))`.
- `content-hash` generates the first 16 hexadecimal characters of the SHA-256
  hash of the text.
- IDs should be unique strings. A duplicate can overwrite the passage offset
  map entry while leaving multiple backend vectors or JSONL rows.

`build_index` requires at least one buffered chunk, removes blank/non-string
text before embedding, and fails if none remains. It computes embeddings using
the configured provider and writes the complete artifact family.

`build_index_from_arrays` expects shape `(N, D)` and `len(ids) == N`. It sets or
checks `dimensions`. If no chunks were added, it creates `"Document <id>"`
placeholders with `{"id": str(id), "from_embeddings": True}` metadata. If
chunks exist, their count must equal `N`.

A critical alignment invariant is not enforced by the method: backend labels
come from `str(ids[i])`, while passage JSONL IDs come from the corresponding
buffered chunk. Ensure both are identical. A safe custom-ID pattern is:

```python
ids = ["alpha", "beta"]
for passage_id, text in zip(ids, texts, strict=True):
    builder.add_text(text, {"id": passage_id})
builder.build_index_from_arrays(base_path, ids, embeddings)
```

Use contiguous `numpy.float32` arrays even though the high-level method does
not normalize every input dtype itself.

`build_index_from_embeddings` unpickles a trusted local file containing exactly
`(ids, embeddings)`, requires `embeddings` to be a NumPy array, then delegates
to `build_index_from_arrays`. Never unpickle an untrusted file.

`update_index` computes embeddings internally; there is no precomputed-vector
update argument in this method. Backend-specific update semantics are in
[indexing and search workflows](indexing-and-search-workflows.md).

## `LeannSearcher`

```python
LeannSearcher(
    index_path: str,
    enable_warmup: bool = True,
    recompute_embeddings: bool = True,
    use_daemon: bool = True,
    daemon_ttl_seconds: int = 900,
    **backend_kwargs,
)
```

Relative `index_path` values are resolved to absolute paths. Construction reads
`<index_path>.meta.json`, resolves passage artifacts relative to that metadata
file, creates the stored backend searcher, and optionally warms the query
embedding path. Use `enable_warmup=False` for an offline BM25-only check.

`recompute_embeddings` is the searcher-wide setting. `use_daemon` and
`daemon_ttl_seconds` control embedding-server reuse. Explicit backend kwargs
override same-named stored backend kwargs.

### `search`

```python
searcher.search(
    query: str,
    top_k: int = 5,
    complexity: int = 64,
    beam_width: int = 1,
    prune_ratio: float = 0.0,
    recompute_embeddings: bool | None = None,
    pruning_strategy: Literal["global", "local", "proportional"] = "global",
    expected_zmq_port: int = 5557,
    metadata_filters: dict[str, dict[str, str | int | float | bool | list]] | None = None,
    batch_size: int = 0,
    use_grep: bool = False,
    vector_weight: float = 1.0,
    provider_options: dict[str, Any] | None = None,
    **kwargs,
) -> list[SearchResult]
```

| Control | Verified behavior |
| --- | --- |
| `top_k` | Result target. Vector/BM25 paths cap it to passage count; grep returns before this cap. Post-filtering can return fewer. |
| `complexity` | Backend candidate/search complexity; higher generally trades latency for recall. |
| `beam_width` | Backend parallel search paths or I/O requests. |
| `prune_ratio` | Approximate-distance pruning ratio forwarded to the backend. |
| `recompute_embeddings` | Deprecated per-call override; prefer the constructor. |
| `pruning_strategy` | `global`, `local`, or `proportional`, forwarded to the backend. |
| `expected_zmq_port` | Requested embedding-server port when effective recomputation is enabled; the manager may assign another port. |
| `metadata_filters` | Applied to enriched results after retrieval and fusion. Ignored by the early-return grep path. |
| `batch_size` | Forwarded only for HNSW. |
| `use_grep` | Bypasses vector embedding, BM25, fusion, metadata filtering, and query logging. |
| `vector_weight` | `1.0` vector, `0.0` BM25, strictly between them linear fusion. Use only `[0, 1]`; 0.3.8 does not reject out-of-range values. |
| `provider_options` | Only per-call `prompt_template` affects query text. Stored embedding options remain the provider configuration. |
| `kwargs` | Forwarded as backend/server search options. The deprecated `gemma=` alias sets `vector_weight` with a warning. |

When effective recomputation is true, LEANN ensures the embedding server is
running, computes the query embedding, and forwards its port. When false, it
computes the query directly unless the request is pure BM25 or grep.

### Result and cleanup

```python
@dataclass
class SearchResult:
    id: str
    score: float
    text: str
    metadata: dict[str, Any]
```

Scores are backend- or retrieval-path-specific; compare rank within one query,
not raw scores across vector, BM25, and hybrid modes. The hybrid implementation
sorts larger fused scores first.

Use either cleanup form:

```python
with LeannSearcher(base_path) as searcher:
    results = searcher.search("query")

searcher = LeannSearcher(base_path)
try:
    results = searcher.search("query")
finally:
    searcher.cleanup()
```

`cleanup()` stops the owned embedding-server manager and calls the backend
`close()` method when present. It is important on platforms where native
indexes keep file or memory-map handles open.

## Artifact naming

For a base path such as `indexes/demo.leann`, common siblings are:

| Artifact | Purpose |
| --- | --- |
| `demo.leann.meta.json` | Backend, dimensions, embedding configuration, passage sources, and storage flags. |
| `demo.leann.passages.jsonl` | One UTF-8 JSON object per passage. |
| `demo.leann.passages.idx` | Pickled passage-ID-to-byte-offset map. |
| `demo.ids.txt` | Backend label order when emitted by the builder. |
| `demo.index` | Common primary backend index name; a backend can add other files. |
| `demo.leann.bm25.sqlite` | FTS5 BM25 database when prebuilt or created on demand. |

The `.leann` suffix is conventional, not a required file extension. Always
pass the same base path used for the build. Move or publish the complete
artifact directory, not selected files. Passage source names in metadata are
relative and are resolved first against the metadata directory.
