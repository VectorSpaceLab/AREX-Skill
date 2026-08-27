# Vector Reference

## Core Feast Vector Objects

Use a vector field when a `FeatureView` should support similarity search. Live API facts show this constructor shape:

```python
Field(
    name="embedding",
    dtype=Array(Float32),
    vector_index=True,
    vector_length=384,
    vector_search_metric="COSINE",
)
```

Important metadata:

- `vector_index=True` marks the field as the indexed vector column.
- `vector_length` should equal the embedding model output dimension. Feast examples use `384` for `all-MiniLM-L6-v2`; custom OpenAI-style embeddings may need `1536` or another explicit dimension.
- `vector_search_metric` is store-specific but Feast examples use `"COSINE"` and `"L2"`; some configs use lowercase `similarity: cosine`.
- A `FeatureView` should not define more than one vector-indexed field; Feast validates vector fields during feature view construction.
- Keep text/context fields in the same view when using `retrieve_online_documents_v2(...)` so RAG prompts can include more than raw vectors.

Minimal vector feature view:

```python
from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource, ValueType
from feast.types import Array, Float32, String

passage = Entity(name="passage_id", join_keys=["passage_id"], value_type=ValueType.STRING)
source = FileSource(name="passage_source", path="data/passages.parquet", timestamp_field="event_timestamp")

wiki_passages = FeatureView(
    name="wiki_passages",
    entities=[passage],
    ttl=timedelta(days=1),
    schema=[
        Field(name="passage_text", dtype=String),
        Field(
            name="embedding",
            dtype=Array(Float32),
            vector_index=True,
            vector_length=384,
            vector_search_metric="COSINE",
        ),
    ],
    online=True,
    source=source,
)
```

For non-vector entities, sources, TTLs, and transformations, route to `../../feature-definitions/SKILL.md`.

## Online Store Selection

Feast vector support is alpha/experimental. Prefer `retrieve_online_documents_v2(...)` when the store supports it because it retrieves vector search results and ordinary features together.

| Store | Use when | Config hints | Notes |
|---|---|---|---|
| Milvus | Primary RAG/vector DB path | `type: milvus`, `vector_enabled: true`, `embedding_dim`, `index_type`, `metric_type`, optional `host`, `port`, credentials | Supports `retrieve_online_documents_v2`; local Milvus Lite-style path is useful for demos, remote host/port for services. |
| SQLite vector mode | Local development/tests | `type: sqlite`, `vector_enabled: true` where available | Limited access; evidence says Python 3.10 and sqlite loadable extension constraints may apply. |
| Postgres/pgvector | SQL deployment with pgvector extension | `type: postgres` or pgvector repo config, `vector_enabled: true` | Supports vector retrieval; ensure pgvector is installed and enabled. |
| Elasticsearch | Search infrastructure already available | `vector_enabled: true`, store-specific host/index settings | Supports vector indexing/retrieval and v2 methods in current source. |
| Qdrant | Dedicated vector service | `type: qdrant`, service URL/API key as needed, `vector_enabled` inherited | Good for service-backed vector search; verify service credentials. |
| MongoDB Atlas vector search | MongoDB/Atlas deployment | `vector_enabled: true`, optional vector index wait timeout/poll interval | Source validates vector field length and waits for Atlas vector indexes. |
| Faiss | In-process similarity experiments | fully qualified class path `feast.infra.online_stores.faiss_online_store.FaissOnlineStore`, `dimension`, `index_path`, `index_type`, `nlist` | Config exists, but alpha matrix marks Faiss retrieval/indexing support incomplete; use with caution. |

Milvus local-style example:

```yaml
project: rag
provider: local
registry: data/registry.db
offline_store:
  type: file
online_store:
  type: milvus
  path: data/online_store.db
  vector_enabled: true
  embedding_dim: 384
  index_type: FLAT
  metric_type: COSINE
entity_key_serialization_version: 3
auth:
  type: no_auth
```

Remote Milvus example:

```yaml
online_store:
  type: milvus
  host: milvus.example.internal
  port: 19530
  username: ${MILVUS_USERNAME}
  password: ${MILVUS_PASSWORD}
  vector_enabled: true
  embedding_dim: 384
  index_type: FLAT
  metric_type: COSINE
```

Faiss example:

```yaml
online_store:
  type: feast.infra.online_stores.faiss_online_store.FaissOnlineStore
  dimension: 384
  index_path: data/faiss_index
  index_type: IVFFlat
  nlist: 100
```

## Retrieval APIs

Use `FeatureStore(repo_path=...)` for SDK access. Live API facts verify the constructor is:

```python
FeatureStore(repo_path: str | None = None, config=None, fs_yaml_file=None)
```

Preferred v2 vector retrieval:

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
context_df = store.retrieve_online_documents_v2(
    features=[
        "wiki_passages:embedding",
        "wiki_passages:passage_text",
    ],
    query=query_embedding,          # list[float]
    top_k=3,
    distance_metric="COSINE",
).to_df()
```

Hybrid/text-capable stores may also accept query text:

```python
context_df = store.retrieve_online_documents_v2(
    features=["wiki_passages:embedding", "wiki_passages:passage_text"],
    query=query_embedding,
    query_string="largest city in New York",
    top_k=5,
    distance_metric="COSINE",
).to_df()
```

Legacy retrieval is still present but documented for future deprecation:

```python
response = store.retrieve_online_documents(
    features=["wiki_passages:embedding", "wiki_passages:passage_text"],
    query=query_embedding,
    top_k=5,
    distance_metric="COSINE",
)
```

## Apply And Write Sequence

Typical local sequence:

```bash
feast apply
```

```python
import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
df = pd.DataFrame(
    {
        "passage_id": ["doc1_0"],
        "passage_text": ["New York City is the most populous city in New York."],
        "embedding": [[0.0] * 384],
        "event_timestamp": [pd.Timestamp.utcnow()],
    }
)
store.write_to_online_store(feature_view_name="wiki_passages", df=df)
```

Then retrieve:

```python
store.retrieve_online_documents_v2(
    features=["wiki_passages:embedding", "wiki_passages:passage_text"],
    query=[0.0] * 384,
    top_k=1,
    distance_metric="COSINE",
).to_df()
```

## Validation Checklist

- `feature_store.yaml` has `online_store.vector_enabled: true` for vector-capable stores that require it.
- The vector field has `vector_index=True` and a positive `vector_length`.
- `embedding_dim` or store-specific dimension config matches the field `vector_length` and query vector length.
- The retrieval `features` list includes the vector field and user-facing context fields.
- The feature view has `online=True` if it must be written/retrieved from the online store.
- The query embedding is a flat list of floats, not a nested batch, tensor, or NumPy array unless converted first.
- Service-backed stores have reachable hosts, ports, credentials, and any required indexes/extensions.
