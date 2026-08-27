# Integrations and storage troubleshooting

Use this guide when Chonkie exports or handshakes fail. Start with the safest
question: is the user asking for an offline export, a local temporary vector
smoke, or an approved live datastore write?

## Quick triage

1. **Offline export requested?** Use `JSONPorter` first, or `DatasetsPorter` if
   the caller specifically needs Hugging Face Datasets.
2. **Dependency uncertainty?** Run `python scripts/handshake_dependency_probe.py`
   before constructing optional handshakes.
3. **Chunks missing?** Load `../chunking-and-types/` and
   `../pipelines-and-processing/` to create or flatten chunks.
4. **Embedding errors?** Load `../embeddings-and-generative/`; handshakes need a
   model whose vector dimension is stable and compatible with the target store.
5. **CLI confusion?** Load `../interfaces-and-deployment/`; the chunk CLI has
   `--handshaker`, while the pipeline CLI also has `--handshaker-params`.
6. **Live write risk?** Stop and ask for explicit service, collection/index
   name, credentials policy, and write approval.

## Import and optional-extra failures

| Symptom | Likely cause | Safe fix |
| --- | --- | --- |
| `ImportError: ChromaDB is not installed` | `chromadb` missing | Install only `chonkie[chroma]` when Chroma is selected. |
| `ImportError: Qdrant is not installed` | `qdrant-client` missing | Install `chonkie[qdrant]`. |
| `ImportError: LanceDB is not installed` | `lancedb` missing | Install `chonkie[lancedb]`. |
| `ImportError: Milvus is not installed` | `pymilvus` missing | Install `chonkie[milvus]`; still requires a service for real writes. |
| `ImportError: pymongo is not installed` | `pymongo` missing | Install `chonkie[mongodb]`; use a mock/local service only with approval. |
| `ImportError: vecs is not installed` | `vecs` missing | Install `chonkie[pgvector]`; then provide a PostgreSQL/pgvector target or mock. |
| `ImportError: Pinecone is not installed` | `pinecone` missing | Install `chonkie[pinecone]`; use a mocked client unless remote writes are approved. |
| `ImportError: Turbopuffer is not available` | `turbopuffer` missing | Install `chonkie[tpuf]` or `turbopuffer`; requires API key for live use. |
| `ImportError: Weaviate not available` | `weaviate-client` missing | Install `chonkie[weaviate]`; provide a client or approved endpoint for real writes. |
| `ImportError: Elasticsearch is not installed` | `elasticsearch` missing | Install `chonkie[elastic]`; avoid default localhost writes without approval. |
| `The 'datasets' library is not installed` | Hugging Face Datasets missing | Install `chonkie[datasets]` or `datasets`. |

The aggregate extra for datastore support is `chonkie[handshakes]`, but a
single-backend extra is better for small environments.

## Constructor succeeds but writes should still be blocked

Some constructors create clients, collections, indexes, or schemas before
`write(...)` is called. Do not call these constructors for live services unless
the target is approved.

| Backend | Risky default |
| --- | --- |
| Milvus | Attempts local/URI service connections, creates collection schema/index, and loads collection. |
| MongoDB | Defaults to `mongodb://localhost:27017` when no client/URI/hostname is supplied. |
| Pgvector | Builds a default PostgreSQL connection string from host/user/password/database. |
| Pinecone | Creates a Pinecone client from `api_key` or `PINECONE_API_KEY`; may create an index. |
| Turbopuffer | Requires key, creates a client, lists namespaces, and may use/create a namespace. |
| Weaviate | Defaults to localhost URL, tries connection helpers, and may create a collection. |
| Elasticsearch | Defaults to `http://localhost:9200` and may create an index mapping. |

Lower-risk constructors for explicit local smoke tests are Chroma in-process,
Qdrant `:memory:`, and LanceDB `memory://`, but they still write to an in-memory
or local store. Use them only when a disposable target is acceptable.

## Credential and service safety

- Never paste API keys into code examples or logs.
- Prefer approved environment variables or secret manager retrieval in the
  caller's environment.
- Use explicit target names, not production defaults.
- Confirm whether collection/index creation is allowed.
- Confirm whether existing records may be upserted, overwritten, or duplicated.
- For managed services, mention possible cost and data retention before the run.
- For local services, confirm the service belongs to the user and is disposable
  or has a backup.

Credential names accepted by Chonkie constructors include `PINECONE_API_KEY` and
`TURBOPUFFER_API_KEY` through environment fallback. Other services can receive
credentials through constructor arguments such as `api_key`, `connection_string`,
`uri`, `username`, `password`, `cloud_id`, or `auth_config`.

## Embedding and vector dimension issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Model download/network error | String `embedding_model` triggered automatic model resolution | Use a cached model, choose an installed embedding provider, or pass a tiny `BaseEmbeddings` mock for tests. |
| `ValueError: ... BaseEmbeddings instance` | Constructor received an unsupported object | Pass a model string Chonkie can resolve or a proper `BaseEmbeddings` subclass. |
| Dimension mismatch at store creation/query | Existing collection/index dimension differs from embedding model | Use the original embedding model, create a new target, or specify `vector_dimensions` for Pgvector when appropriate. |
| Pinecone/Weaviate rejects vector shape | Embedding is not a flat list of floats/ints | Convert NumPy vectors with `.tolist()` or fix custom embedding return values. |
| Turbopuffer ignores custom `BaseEmbeddings` instance | Its constructor resolves `embedding_model` through automatic embeddings | Mock the embedding registry/service for tests or use a supported model string with approved dependencies. |

For repeatable tests, use a fixed tiny embedding implementation. For production,
keep the embedding model constant across indexing and querying.

## Metadata and serialization quirks

- `JSONPorter` writes `chunk.to_dict()` exactly, preserving Unicode.
- `DatasetsPorter` builds rows from `chunk.to_dict()` and can include fields
  such as `id`, `context`, `embedding`, and `metadata`.
- Chroma and Pinecone accept only primitive metadata values, so non-primitives
  are JSON-encoded strings and `None` is skipped.
- LanceDB, Milvus, Turbopuffer, and Weaviate store `chunk.metadata` as a JSON
  string field named like `chunk_metadata` and parse it back when possible.
- Qdrant, Pgvector, MongoDB, and Elasticsearch merge metadata into payload or
  source dictionaries; store-specific restrictions may still apply.
- Chonkie storage fields override same-named user metadata keys.

If metadata roundtrip fidelity matters, validate one representative chunk before
batching many records.

## Duplicate, overwrite, and idempotence issues

| Backend | Repeat write behavior to consider |
| --- | --- |
| Chroma, Qdrant, Pinecone, LanceDB, Pgvector | Generally upsert by deterministic ID, so same target/name/index/text-position can update existing records. |
| Elasticsearch | Bulk indexing with deterministic `_id` can overwrite/update documents for the same ID. |
| Weaviate | Uses deterministic UUIDs in batch writes; behavior depends on Weaviate client's insert semantics and batch errors. |
| MongoDB | Uses `insert_many` with deterministic `_id`; repeated writes can raise duplicate key errors. |
| Milvus | Uses auto primary keys and insert/flush; repeated writes can append duplicates. |
| Turbopuffer | Writes upsert columns keyed by deterministic IDs. |

For reproducible experiments, keep a stable target name and input order. For
append-only or audit workflows, prefer JSONL snapshots and include run metadata
outside the Chonkie chunk fields.

## JSONPorter problems

| Symptom | Fix |
| --- | --- |
| `FileNotFoundError` | Create the parent directory before export. |
| JSON array written to `chunks.jsonl` | Pass `file="chunks.json"` when using `JSONPorter(lines=False)`. |
| Need one object per line | Use `JSONPorter(lines=True)`; validate each line with `json.loads`. |
| Empty output file | Check whether the chunk list is empty; JSONL for empty chunks is an empty file by design. |
| Unexpected escaped Unicode | Chonkie writes UTF-8 with `ensure_ascii=False`; if escapes appear, a downstream tool likely rewrote the file. |

## DatasetsPorter problems

| Symptom | Fix |
| --- | --- |
| Import error for `datasets` | Install `chonkie[datasets]` or `datasets`. |
| Need in-memory dataset return | Call `DatasetsPorter().export(chunks, save_to_disk=False)` directly. Pipeline export returns the `Document`/documents, not the `Dataset`. |
| Save directory unexpected | Pass an explicit `path`; default is `"chunks"`. |
| Save options ignored | Pass Datasets `save_to_disk` kwargs such as `num_shards` or `num_proc` to `export(...)`. |
| Schema surprises | Inspect `dataset.column_names`; rows are produced from `chunk.to_dict()`. |

## Pipeline parameter mistakes

Chonkie's pipeline splits `export_with(...)` and `store_in(...)` kwargs between
constructor parameters and call parameters. Unknown names raise a `ValueError`
that lists valid constructor and method parameters.

Common corrections:

- JSON export uses `file=...`, not `output_path=...`.
- JSON format mode uses `lines=False`.
- Datasets export uses `save_to_disk=True/False` and `path=...`.
- Chroma/Qdrant use `collection_name`; LanceDB uses `table_name`; Pinecone and
  Elasticsearch use `index_name`; Turbopuffer uses `namespace_name`; MongoDB uses
  both `db_name` and `collection_name`.
- `Pipeline.store_in(...)` returns the handshake write result. If you need the
  documents after a storage attempt, keep them from an earlier `run(...)` or use
  `export_with(...)` for file export.

## CLI handshaker pitfalls

- `chonkie chunk ... --handshaker ALIAS` instantiates the selected handshaker
  with default constructor arguments; that is unsafe for live-service aliases
  and offers no per-handshake parameter flag in the chunk command.
- `chonkie pipeline ... --handshaker ALIAS --handshaker-params key=value ...`
  can pass constructor/write kwargs and is safer only if explicit target values
  are supplied.
- Unknown aliases print an available list and exit with an error.
- A storage failure prints `Error storing chunks: ...` or a pipeline failure that
  names the failed step.

When the user asks for CLI storage, route to `../interfaces-and-deployment/` for
full CLI syntax, then apply this sub-skill's backend-specific safety gates.

## Mocked alternatives for verification

Use mocks when a live service is not approved:

- dependency probe only: confirms optional packages/classes without constructors;
- fixed tiny embeddings: avoids model downloads and dimension instability;
- fake client/index/collection objects: exercise constructor branches and
  `write/search` formatting without sockets;
- in-memory Chroma/Qdrant/LanceDB: acceptable only when optional packages are
  installed and the user agrees to a local disposable write;
- JSONPorter golden files: good synthetic verification for chunk flattening and
  metadata serialization across workflows.
