# Vector-indexing troubleshooting

## Import and optional dependency errors

DocArray lazily imports optional index backends. A missing backend import normally reports the missing library and the matching `docarray[...]` extra.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `HnswDocumentIndex` import names `hnswlib` | HNSWLib extra absent or wheel unavailable | Install `docarray[hnswlib]`; if compilation fails, use `InMemoryExactNNIndex` or a service backend. |
| Qdrant/Weaviate/Elastic/Redis/Milvus/Mongo/Epsilla import fails | Matching client extra absent | Install only the selected backend extra and rerun a tiny import check. |
| Import works but `index()` cannot connect | Service is not running, endpoint is wrong, or credentials/TLS are missing | Probe the service independently; verify host/port/API key and use a disposable index name. |
| Client import/version conflict | Backend client version does not match the repo's optional constraint | Inspect `pyproject.toml` and the backend's dependency variant; isolate conflicting v7/v8 clients. |

## Schema and dimensionality failures

- `A DocumentIndex must be typed with a Document type`: instantiate `InMemoryExactNNIndex[MyDoc]`, not the bare generic.
- A vector index cannot infer a dimension from an unparameterized predefined `embedding` field. Subclass the predefined doc with `NdArray[128]`, or use `Field(dim=128)` where the backend supports it.
- `search_field` validation errors mean the field is absent or not a supported tensor/vector field. Inspect the schema and pass the exact field name.
- Schema compatibility errors mean the index and input docs differ in field names/types. Use the same `BaseDoc` class, a compatible subclass, or convert the incoming data before indexing.
- A vector dimension is per document. For `NdArray[128]`, each document has shape `(128,)`; the batch axis belongs to `find_batched()`/`DocVec`, not the field annotation.

## InMemoryExactNNIndex behavior

- `text_search()` is not supported by the in-memory backend. Use `filter()` for structured predicates or select a backend that documents text search.
- `index(docs)` updates an existing document when its ID matches; it does not necessarily increase `num_docs()`.
- `index(docs=..., index_file_path=...)` is invalid. Choose a fresh in-memory index with docs or restore from one persisted file.
- A missing persistence file creates an empty index. Treat the warning as a missing data artifact, not a successful restore.
- `persist()` writes local state; ensure the destination directory is writable and use a unique path for concurrent experiments.

## Query builder and result failures

- A backend query builder can support a smaller operation set than the direct index. InMemory supports `find`, `find_batched`, and `filter`, but not text search.
- A score-tie edge case can produce `TypeError: '<' not supported between instances of ...` when the local implementation sorts equal-score `(score, document)` pairs. Reproduce with distinct scores or add a restrictive filter; report the case rather than treating it as a schema/import failure.
- Query-builder filter placement is backend-specific. Start with one operation, inspect the built query, then add pre/post filters incrementally.
- Do not pass an in-memory filter dictionary to Qdrant, Redis, Weaviate, Elasticsearch, or Milvus without translating it to that backend's documented query language.

## Nested subindex failures

- The nested field must be a typed `DocList[ChildDoc]` or compatible document-array field.
- The subindex name in `find_subindex(..., subindex="children")` must exactly match the schema field.
- Search the child vector field with the child field name, not a flattened root path.
- Deleting a root document also removes child subindex entries. Check parent IDs when diagnosing missing children.
- Optional or heterogeneous child collections should be resolved in the `document-modeling` route before indexing.

## Service and production boundaries

External backends were not verified in the minimum CPU environment. Before a production claim, verify:

1. package import and client version;
2. service health and network/TLS path;
3. schema/collection/index creation;
4. vector dimension and metric configuration;
5. tiny index/find/filter/delete round-trip;
6. persistence/restart behavior;
7. credentials and failure recovery.

If any of those need credentials, containers, or a vendor accelerator, preserve the unresolved backend block in the verification report instead of substituting the in-memory result.
