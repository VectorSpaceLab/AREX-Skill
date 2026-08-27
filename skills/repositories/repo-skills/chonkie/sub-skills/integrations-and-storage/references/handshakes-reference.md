# Handshakes reference

Chonkie handshakes are storage adapters for writing `Chunk` objects into vector
or datastore backends. They are useful after chunking/refining, but most of them
can create collections/indexes and mutate services during construction or
`write(...)`. Treat this reference as an API and safety checklist before any
live run.

For chunk creation and `Document.chunks`, see `../chunking-and-types/`. For
`Pipeline.store_in(...)` ordering and parameter splitting, see
`../pipelines-and-processing/`. For embedding model selection, dimensions, and
provider/model-download risk, see `../embeddings-and-generative/`. For CLI
`--handshaker` flags, see `../interfaces-and-deployment/`.

## Common contract

| API | Contract |
| --- | --- |
| `BaseHandshake.write(chunks)` | Implemented by each concrete handshake. Accepts a single `Chunk` or a list/sequence of chunks and writes to the backend. |
| `BaseHandshake.awrite(chunks, **kwargs)` | Async wrapper that delegates `write` in a worker thread. |
| `handshake(chunks)` | Calls `write(chunks)` and returns the write result. Invalid input raises `TypeError`. |
| `search(...)` | Implemented by concrete vector handshakes. Most accept `query`, `embedding`, and `limit`; `PgvectorHandshake.search` requires a text `query` and adds optional filters/return flags. |
| Metadata merge | Chonkie storage fields such as `text`, `start_index`, `end_index`, and `token_count` override same-named keys in `chunk.metadata`. Chroma and Pinecone coerce non-primitive metadata values to JSON strings and drop `None`. |
| IDs | Many handshakes use deterministic UUID5 strings based on the collection/index/table/namespace name, chunk list position, and chunk text. Changing random names changes IDs and idempotence behavior. |

The default embedding model for handshakes is usually
`"minishlab/potion-retrieval-32M"`. A string model is resolved through
Chonkie's embedding registry and may need optional packages, local cache, or a
model download. For no-network tests, pass a small `BaseEmbeddings` subclass or
mock that returns fixed vectors with a stable `dimension`.

## Alias, extra, constructor, and safety table

Install only the extra needed for the selected backend; avoid `all` for a small
inspection or production environment.

| Alias | Class | Extra / client import | Main constructor arguments | Default behavior and safety notes |
| --- | --- | --- | --- | --- |
| `chroma` | `ChromaHandshake` | `chonkie[chroma]`; `chromadb` | `client=None`, `collection_name="random"`, `embedding_model=...`, `path=None` | With no `client` and no `path`, uses an in-process Chroma client. With `path`, uses a persistent local client. Creates/gets a collection and upserts documents. Good first local vector test when dependencies are installed; use a temporary path for persistence checks. |
| `qdrant` | `QdrantHandshake` | `chonkie[qdrant]`; `qdrant_client` | `client=None`, `collection_name="random"`, `embedding_model=...`, `url=None`, `path=None`, `api_key=None`, `**kwargs` | With no `client`, `url`, or `path`, uses an in-memory Qdrant client. With `path`, uses local persistence. With `url`/`api_key`, targets a service. Creates collection with cosine vectors sized from the embedding model. |
| `lancedb` | `LanceDBHandshake` | `chonkie[lancedb]`; `lancedb` | `connection=None`, `uri="memory://"`, `table_name="random"`, `embedding_model=...`, `**kwargs` | Defaults to an in-memory LanceDB connection and creates a table schema. Uses merge-insert upsert by `id`. Good for local mock/in-memory examples. |
| `milvus` | `MilvusHandshake` | `chonkie[milvus]`; `pymilvus` | `client=None`, `uri=""`, `collection_name="random"`, `embedding_model=...`, `host="localhost"`, `port="19530"`, `user=""`, `api_key=""`, `alias="default"`, `**kwargs` | Constructor connects through Milvus client/ORM, may create a collection, creates a default HNSW index, and loads the collection. This is a live-service path; do not use defaults unless a writable Milvus service is intentionally running. |
| `mongodb` | `MongoDBHandshake` | `chonkie[mongodb]`; `pymongo` | `client=None`, `uri=None`, `username=None`, `password=None`, `hostname=None`, `port=None`, `db_name="random"`, `collection_name="random"`, `embedding_model=...`, `**kwargs` | With no client/URI/hostname, constructs `mongodb://localhost:27017`. `write` uses `insert_many`; repeated deterministic `_id` values can fail with duplicate key errors. Search loads documents and computes cosine similarity client-side. Use a provided mock/client unless live writes are approved. |
| `pgvector` | `PgvectorHandshake` | `chonkie[pgvector]`; `vecs` | `client=None`, `host="localhost"`, `port=5432`, `database="postgres"`, `user="postgres"`, `password="postgres"`, `connection_string=None`, `collection_name="chonkie_chunks"`, `embedding_model=...`, `vector_dimensions=None` | Uses `vecs.create_client(...)` unless a client is supplied, then `get_or_create_collection`. Defaults are a real local PostgreSQL target with default credentials; avoid unless explicitly approved. Supports `create_index`, `delete_collection`, and `get_collection_info`. |
| `pinecone` | `PineconeHandshake` | `chonkie[pinecone]`; `pinecone` | `client=None`, `api_key=None`, `index_name="random"`, `spec=None`, `embedding_model=...`, `**kwargs` | Requires a supplied client or `api_key`/`PINECONE_API_KEY`. Defaults to a serverless spec when creating a missing index. Remote billing and mutation risk: prefer a mocked Pinecone client/index for tests. |
| `turbopuffer` | `TurbopufferHandshake` | `chonkie[tpuf]` or `turbopuffer`; `turbopuffer` | `namespace=None`, `namespace_name="random"`, `embedding_model=...`, `api_key=None`, `region="gcp-us-central1"` | Requires `api_key` or `TURBOPUFFER_API_KEY` and creates a Turbopuffer client before using a namespace. It lists namespaces and may create/use a remote namespace. Use only with explicit live approval or a fully mocked module/namespace. |
| `weaviate` | `WeaviateHandshake` | `chonkie[weaviate]`; `weaviate` | `client=None`, `collection_name="random"`, `embedding_model=...`, `url=None`, `api_key=None`, `auth_config=None`, `batch_size=100`, `batch_dynamic=True`, `batch_timeout_retries=3`, `additional_headers=None`, `http_secure=False`, `grpc_host=None`, `grpc_port=50051`, `grpc_secure=False` | With no client, defaults to `http://localhost:8080`, tries cloud/custom connection helpers, and creates a collection if missing. Supports `close`, `delete_collection`, and `get_collection_info`. Use an existing mocked/client object for no-service tests. |
| `elastic` | `ElasticHandshake` | `chonkie[elastic]`; `elasticsearch` | `client=None`, `index_name="random"`, `embedding_model=...`, `hosts=None`, `cloud_id=None`, `api_key=None`, `**kwargs` | With no client/hosts/cloud settings, targets `http://localhost:9200`. Creates a dense-vector mapping if the index is missing and writes through the bulk API. Treat defaults as live-service mutation. |

## Random names and repeatability

`collection_name`, `table_name`, `index_name`, `namespace_name`, and `db_name`
accept `"random"` in many handshakes. Random names are Chonkie-themed
three-part lowercase names such as `happy-chomping-hippo`; Milvus and Weaviate
use underscores where required by backend naming rules.

Use random names for disposable in-memory or test stores. For reproducible
experiments, explicit names are safer because:

- deterministic IDs include the target name;
- random targets are hard to rediscover later;
- rerunning with a different random name creates an independent target;
- some stores upsert by deterministic ID while others append/insert.

## Write and search behavior by backend

| Backend | Write behavior | Search notes |
| --- | --- | --- |
| Chroma | `collection.upsert(ids=..., documents=..., metadatas=...)`. | `search(query=... | embedding=..., limit=...)`; returns `id`, `score`, `text`, plus metadata. Converts distance to a similarity-like score depending on collection metric. |
| Qdrant | Builds `PointStruct` records and `upsert(..., wait=True)`. | `query_points` with payload included; result dictionaries include `id`, `score`, and payload fields. |
| LanceDB | Creates rows with JSON-serialized `chunk_metadata`; uses merge-insert upsert by `id`. | Uses cosine metric; returns `id`, `score`, `text`, indexes, token count, and parsed metadata when possible. |
| Milvus | Inserts columnar data and flushes; primary key is auto-generated. | Uses HNSW/L2 search; returns hit ID, distance as `score`, stored fields, and parsed metadata when possible. Rewrites may append duplicates. |
| MongoDB | Inserts documents with deterministic `_id`; metadata is merged into the document. | Performs client-side cosine similarity over all documents containing embeddings; not an indexed vector search implementation. |
| Pgvector | Upserts `(id, vector, metadata)` records through `vecs`. | `search(query, limit=..., filters=..., include_metadata=True, include_value=True)` returns ID plus similarity/metadata depending flags. |
| Pinecone | Upserts vector tuples `(id, embedding, metadata)`. | `search(query=... | embedding=..., limit=...)`; if both query and embedding are supplied, query embedding wins. Requires list-of-floats vectors. |
| Turbopuffer | Writes columnar `upsert_columns` with cosine distance. | Query returns rows with `score = 1 - distance`, text/index fields, token count, and parsed metadata. |
| Weaviate | Batch-adds objects with deterministic UUIDs and explicit vectors; tolerates some batch errors but raises if errors exceed threshold. | `near_vector` query; returns UUID, similarity-like score, properties, and parsed metadata. Call `close()` for owned clients when done. |
| Elasticsearch | Bulk indexes documents under deterministic `_id`. | KNN dense-vector search; returns `_score`, `_id`, and source fields except the embedding. |

## Safe no-live-write patterns

### Dependency and class probe first

```bash
python scripts/handshake_dependency_probe.py
python scripts/handshake_dependency_probe.py --json
```

The probe imports Chonkie handshake/porter classes and checks optional client
package importability. It does not instantiate datastore clients, open sockets,
create collections, or write chunks.

### Fixed tiny embedding for local or mocked tests

Use a tiny `BaseEmbeddings` implementation to avoid model downloads and make
vector dimensions deterministic:

```python
import numpy as np
from chonkie.embeddings import BaseEmbeddings

class TinyEmbeddings(BaseEmbeddings):
    @property
    def dimension(self) -> int:
        return 4

    def embed(self, text: str) -> np.ndarray:
        seed = (sum(ord(ch) for ch in text) % 10) / 10.0
        return np.array([seed, 0.1, 0.2, 0.3], dtype=np.float32)

    def get_tokenizer(self):
        return None
```

Pass `embedding_model=TinyEmbeddings()` to handshakes that accept
`BaseEmbeddings`. Turbopuffer currently resolves `embedding_model` through
Chonkie's automatic embedding selector, so prefer a mocked Turbopuffer namespace
and registry patch for no-network tests.

### Prefer in-memory/local backends for smoke tests

When dependency packages are already present and the user wants a bounded smoke
without external services:

```python
from chonkie import TokenChunker
from chonkie.handshakes import QdrantHandshake

chunks = TokenChunker(chunk_size=32).chunk("small local text only")
store = QdrantHandshake(collection_name="chonkie_tmp_smoke", embedding_model=TinyEmbeddings())
store.write(chunks)
print(store.search(query="local", limit=1))
```

This example uses Qdrant's in-memory default. Equivalent low-risk choices are
Chroma with an in-process client and LanceDB with `uri="memory://"`. Still ask
before writing if the user's environment or target path is not disposable.

### Mocked client handoff examples

- Pinecone: pass a fake `client` whose `has_index`, `create_index`, and `Index`
  methods return a mock index with `upsert` and `query`.
- Elasticsearch: pass a fake `client` whose `indices.exists`, `indices.create`,
  and `search` methods are controlled; monkeypatch the bulk helper in tests.
- MongoDB: pass or patch a fake `MongoClient`/collection so `insert_many` and
  `find` are local mocks.
- Weaviate: pass a fake `client` with `collections.exists/get/create/delete` and
  a collection mock whose `batch.fixed_size(...)` is a context manager.
- Pgvector: pass a fake `vecs.Client` with `get_or_create_collection`; make the
  collection expose `upsert`, `query`, `create_index`, `name`, and `dimension`.
- Milvus and Turbopuffer constructors touch global/service client APIs; use
  dedicated monkeypatching or wrapper tests instead of default constructors.

## Pipeline storage integration

Use `Pipeline.store_in(alias, **kwargs)` for handshakes. Pipeline execution
orders write steps after fetch/process/chunk/refine, extracts chunks from the
current `Document` or document list, calls `component.write(chunks, **call_kwargs)`,
and returns that write result.

```python
from chonkie import Pipeline

result = (
    Pipeline()
    .chunk_with("recursive", chunk_size=128)
    .store_in("qdrant", collection_name="scratch", embedding_model=TinyEmbeddings())
    .run(texts="store this after chunking")
)
```

Pipeline validates keyword arguments against the handshake constructor and
`write(...)` signature. Unknown parameter names raise a clear `ValueError`; for
example use `collection_name` for Qdrant/Chroma, `table_name` for LanceDB,
`index_name` for Pinecone/Elastic, and `namespace_name` for Turbopuffer.
