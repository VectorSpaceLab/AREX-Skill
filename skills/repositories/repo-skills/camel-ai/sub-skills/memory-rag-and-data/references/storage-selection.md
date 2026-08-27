# Storage Selection

Choose storage by retrieval semantics, persistence needs, deployment constraints, and optional dependencies. Always begin from the data contract: key-value records, vector records, blobs, or graph triplets.

## Decision Matrix

| Need | Prefer | Why | Watch For |
| --- | --- | --- | --- |
| Fast unit tests, no persistence | `InMemoryKeyValueStorage`, Qdrant without `path`, Chroma `ephemeral`, FAISS without `storage_path` | No service setup and low cleanup cost | Data disappears at process exit |
| Local persistent chat history | `JsonStorage(path)` | Human-readable and easy to inspect | Not for concurrent writers or large datasets |
| Local persistent vector RAG | Qdrant `path=...`, Chroma `client_type='persistent'`, FAISS `storage_path=...` | Works without a remote service | Dimension/collection migrations and local file cleanup |
| Production vector search | Qdrant remote, Milvus, PgVector, Weaviate, TiDB, OceanBase, Surreal, Chroma HTTP/cloud | Scales beyond local process | Credentials, network, index config, operational ownership |
| Exact keyword search | `BM25Retriever` | Deterministic, transparent, no embedding credentials | Lower semantic recall |
| Mixed semantic + exact search | `HybridRetriever` | Combines vector and BM25 with reciprocal rank fusion | Requires both ingestion paths and deduping |
| File/blob persistence | S3, Azure Blob, Google Cloud object storage | Store documents or artifacts, not vector search | IAM, bucket/container lifecycle, upload/download semantics |
| Structured relationships | `Neo4jGraph`, `NebulaGraph` | Triplets/schema/query for graph reasoning | Graph service auth, schema refresh, Cypher/nGQL correctness |
| Remote cache/session state | `RedisStorage` | Fast shared key-value storage | Redis URL, event loop handling, TTL/expiry |

## Vector Storage Invariants

- `vector_dim` must equal `embedding.get_output_dim()` for every record and query.
- Collection names should encode embedding family/version or dimension when persistent: `support_docs_text3small_1536`.
- Existing persistent/remote collections should be treated as immutable with respect to dimension. Re-embed into a new collection when changing embeddings or dimensions.
- Validate `storage.status().vector_count` after ingestion and after cleanup when the backend supports it.
- Store enough payload metadata to debug retrieval: source ID, chunk number, loader name, content hash or version, and human-readable text.
- Avoid storing secrets in vector payloads; payloads can be returned to the agent and logs.

## Backend Notes

### Qdrant

`QdrantStorage(vector_dim, collection_name=None, url_and_api_key=None, path=None, distance=VectorDistance.COSINE, delete_collection_on_del=False, **kwargs)` supports three modes:

- No `path` and no `url_and_api_key`: in-memory local client for tests.
- `path='...'`: local persistent directory.
- `url_and_api_key=(url, api_key)`: remote service.

Qdrant checks existing collection dimensions and raises when they differ from `vector_dim`. Use this as an early migration signal.

### Chroma

`ChromaStorage` supports `client_type='ephemeral'`, `'persistent'`, `'http'`, or `'cloud'`. Use `ephemeral` in tests, `persistent` for local development, and `http`/`cloud` only when service configuration is explicit. Cloud/HTTP may need headers, tenant, database, API key, SSL, host, and port settings.

### FAISS

`FaissStorage(vector_dim, index_type='Flat', storage_path=None, distance=...)` is local and fast. Use `Flat` for correctness-first tests. IVF/HNSW/PQ settings trade accuracy, memory, and speed and may require training or more careful setup. FAISS only stores vectors natively, so CAMEL maintains ID and payload mappings alongside the index.

### Milvus, TiDB, PgVector, Weaviate, Surreal, OceanBase

Use these for production or integration tests that already own the service. They need optional packages, connection strings, and cleanup plans. Keep connection values outside skill content and code examples; use environment variables or application config in real projects.

### Key-Value Storage

- `InMemoryKeyValueStorage`: best for tests and transient agent memory.
- `JsonStorage(path)`: best for small local persistent memory; inspectable but not robust for high-concurrency writes.
- `RedisStorage(sid, url, loop=None, **kwargs)`: shared state with optional expiry; validate the Redis connection and event-loop lifecycle.
- `Mem0Storage`: hosted memory; treat API keys and user IDs as sensitive.

### Object Storage

Object storages hold file artifacts, datasets, or blobs. They do not provide semantic retrieval by themselves. Pair them with loaders and a vector store when building RAG over stored objects.

### Graph Storage

`Neo4jGraph` and `NebulaGraph` model relationship data as triplets. Use them when the query is naturally graph-shaped or when agents need schema-aware relationship traversal. Always call `refresh_schema()` after schema changes and validate auth/space/database selection before adding triplets.

## Optional Extras And Python Constraints

CAMEL exposes optional groups relevant to this sub-skill:

- `camel-ai[rag]`: vector stores, retrievers, rerankers, unstructured parsing, graph DB clients, Chroma, and related RAG dependencies.
- `camel-ai[storage]`: storage backends such as Qdrant, Milvus, FAISS, Neo4j, Nebula, Redis, S3/cloud clients, and related packages.
- `camel-ai[document_tools]`: file/document parsing and conversion helpers such as PyMuPDF, docx2txt, unstructured, MarkItDown, and OCR/document packages.

Python caveats from repository metadata:

- CAMEL supports Python `>=3.10,<3.15`.
- `unstructured==0.16.20` and `pyobvector` are constrained to Python `<3.13` in relevant extras.
- `markitdown` is included under `document_tools` for Python `>=3.13`.
- If using Python 3.13+, prefer MarkItDown/BaseIO-compatible paths or verify loader availability with the inspection script before using `UnstructuredIO` or OceanBase-dependent flows.

## Persistence And Cleanup Checklist

- For tests, prefer in-memory or temporary directories; clear/delete collections after assertions.
- For local persistent paths, keep storage directories outside package source and add them to project `.gitignore` if needed.
- For remote stores, create per-test collection names and delete them explicitly; avoid `delete_collection_on_del=True` as the only cleanup mechanism in long-running services.
- For JSON chat memory, use deterministic file names per agent/test and remove files after tests.
- For graph/object stores, separate read-only integration probes from destructive add/delete tests.

## Dimension Migration Playbook

1. Detect old collection `vector_dim` with `storage.status()` or backend metadata.
2. Compare with `embedding.get_output_dim()`.
3. If different, create a new collection/table/index; do not add mixed-dimension vectors.
4. Re-run loaders/chunkers to recover the text and metadata source of truth.
5. Re-embed all chunks with the new embedding and write them to the new collection.
6. Switch queries only after `vector_count` and sample retrieval checks pass.
