# Storage Reference

LightRAG composes four storage categories. Each category is selected independently by class name, and `LightRAG.__post_init__` validates that the selected class is compatible with its category before constructing storages.

## Four Categories

| Category | Constructor argument | API/server env var | Purpose |
| --- | --- | --- | --- |
| KV storage | `kv_storage` | `LIGHTRAG_KV_STORAGE` | LLM cache, full documents, text chunks, full entity/relation metadata, chunk tracking KV stores. |
| Vector storage | `vector_storage` | `LIGHTRAG_VECTOR_STORAGE` | Entity, relationship, and chunk embeddings used by vector and graph-assisted retrieval. |
| Graph storage | `graph_storage` | `LIGHTRAG_GRAPH_STORAGE` | Entity/relation graph used by local, global, hybrid, and mix retrieval. |
| Doc-status storage | `doc_status_storage` | `LIGHTRAG_DOC_STATUS_STORAGE` | Ingestion state, processing status, pagination, track IDs, file path lookup, and pipeline recovery state. |

Default constructor selections are:

```python
LightRAG(
    kv_storage="JsonKVStorage",
    vector_storage="NanoVectorDBStorage",
    graph_storage="NetworkXStorage",
    doc_status_storage="JsonDocStatusStorage",
)
```

For service-style configuration, the API/server layer reads `LIGHTRAG_KV_STORAGE`, `LIGHTRAG_VECTOR_STORAGE`, `LIGHTRAG_GRAPH_STORAGE`, and `LIGHTRAG_DOC_STATUS_STORAGE`. Operational tools such as the vector rebuild tool use the same storage-selection env vars for the categories they need.

## Exact Registry Names

### KV Storage

| Class name | Backend | Typical use | Required env vars in registry |
| --- | --- | --- | --- |
| `JsonKVStorage` | Local JSON files | Development, single-node prototypes, simple local deployments. | None |
| `RedisKVStorage` | Redis | Shared cache/doc KV for service deployments. | `REDIS_URI` |
| `PGKVStorage` | PostgreSQL | Consolidated SQL-backed KV. | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE` |
| `MongoKVStorage` | MongoDB | Mongo-backed KV alongside Mongo graph/vector/doc status. | `MONGO_URI`, `MONGO_DATABASE` |
| `OpenSearchKVStorage` | OpenSearch | OpenSearch-backed KV with the OpenSearch family. | `OPENSEARCH_HOSTS` |

### Vector Storage

| Class name | Backend | Typical use | Required env vars in registry |
| --- | --- | --- | --- |
| `NanoVectorDBStorage` | Local NanoVectorDB JSON files | Default local vector backend. | None |
| `FaissVectorDBStorage` | Local Faiss index | Local/offline vector search with Faiss dependency. | None |
| `MilvusVectorDBStorage` | Milvus | Dedicated vector service and configurable Milvus indexes. | `MILVUS_URI`, `MILVUS_DB_NAME` |
| `PGVectorStorage` | PostgreSQL + vector extension | SQL-backed vector storage, commonly paired with PG graph/KV/doc status. | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE` |
| `QdrantVectorDBStorage` | Qdrant | Qdrant vector service with workspace payload isolation. | `QDRANT_URL` |
| `MongoVectorDBStorage` | MongoDB vector search | Mongo-backed vector storage. | `MONGO_URI`, `MONGO_DATABASE` |
| `OpenSearchVectorDBStorage` | OpenSearch k-NN | OpenSearch vector search. | `OPENSEARCH_HOSTS` |

`ChromaVectorDBStorage` is present in the module mapping but is not listed as a compatible `VECTOR_STORAGE` implementation in the registry. Do not select it unless the installed package version explicitly changes the compatibility registry.

### Graph Storage

| Class name | Backend | Typical use | Required env vars in registry |
| --- | --- | --- | --- |
| `NetworkXStorage` | Local GraphML via NetworkX | Default local graph backend. | None |
| `Neo4JStorage` | Neo4j | Dedicated graph database. | `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` |
| `PGGraphStorage` | PostgreSQL/AGE-style graph support | PostgreSQL-backed graph data. | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE` |
| `MongoGraphStorage` | MongoDB | Mongo-backed graph storage. | `MONGO_URI`, `MONGO_DATABASE` |
| `MemgraphStorage` | Memgraph | Dedicated graph service compatible with Memgraph. | `MEMGRAPH_URI` |
| `OpenSearchGraphStorage` | OpenSearch graph indices | OpenSearch-backed graph traversal/search. | `OPENSEARCH_HOSTS` |

`AGEStorage` is present in the module mapping and env requirement table but is not listed as a compatible graph implementation in the registry. Prefer `PGGraphStorage` unless the installed registry explicitly allows `AGEStorage` for `GRAPH_STORAGE`.

### Doc-Status Storage

| Class name | Backend | Typical use | Required env vars in registry |
| --- | --- | --- | --- |
| `JsonDocStatusStorage` | Local JSON files | Default local ingestion status. | None |
| `RedisDocStatusStorage` | Redis | Service deployment with Redis status tracking. | `REDIS_URI` |
| `PGDocStatusStorage` | PostgreSQL | SQL-backed status, pagination, and recovery. | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE` |
| `MongoDocStatusStorage` | MongoDB | Mongo-backed status tracking. | `MONGO_URI`, `MONGO_DATABASE` |
| `OpenSearchDocStatusStorage` | OpenSearch | OpenSearch-backed status tracking and pagination. | `OPENSEARCH_HOSTS` |

## Backend Families and Optional Services

| Family | Classes | Python dependency source | External service |
| --- | --- | --- | --- |
| Local default | `JsonKVStorage`, `NanoVectorDBStorage`, `NetworkXStorage`, `JsonDocStatusStorage` | Base package dependencies include `nano-vectordb` and `networkx`. | None |
| Local Faiss vector | `FaissVectorDBStorage` | `offline-storage` extra includes `faiss-cpu`. | None |
| Redis | `RedisKVStorage`, `RedisDocStatusStorage` | `offline-storage` extra includes `redis`. | Redis reachable at `REDIS_URI`. |
| PostgreSQL | `PGKVStorage`, `PGVectorStorage`, `PGGraphStorage`, `PGDocStatusStorage` | `offline-storage` extra includes `asyncpg` and `pgvector`. | PostgreSQL reachable with `POSTGRES_*` settings; vector storage requires compatible vector extension/index support. |
| MongoDB | `MongoKVStorage`, `MongoVectorDBStorage`, `MongoGraphStorage`, `MongoDocStatusStorage` | `offline-storage` extra includes `pymongo`. | MongoDB reachable at `MONGO_URI` with `MONGO_DATABASE`. |
| Neo4j | `Neo4JStorage` | `offline-storage` extra includes `neo4j`. | Neo4j reachable with URI, username, password. |
| Memgraph | `MemgraphStorage` | Uses Memgraph client requirements from storage implementation. | Memgraph reachable at `MEMGRAPH_URI`. |
| Milvus | `MilvusVectorDBStorage` | `offline-storage` extra includes `pymilvus`. | Milvus reachable at `MILVUS_URI`; database name from `MILVUS_DB_NAME`. |
| Qdrant | `QdrantVectorDBStorage` | `offline-storage` extra includes `qdrant-client`. | Qdrant reachable at `QDRANT_URL`; `QDRANT_API_KEY` is optional when service permits unauthenticated access. |
| OpenSearch | `OpenSearchKVStorage`, `OpenSearchVectorDBStorage`, `OpenSearchGraphStorage`, `OpenSearchDocStatusStorage` | `offline-storage` extra includes `opensearch-py`. | OpenSearch reachable at `OPENSEARCH_HOSTS`; k-NN support is needed for vector search. |

Optional storage implementations may attempt dynamic installation through package helpers if dependencies are missing. In locked-down or offline environments, preinstall `lightrag-hku[offline-storage]` or `lightrag-hku[offline]` instead of relying on runtime installation.

## Constructor Selection Patterns

### All-Local Prototype

```python
rag = LightRAG(
    working_dir="./rag_storage",
    embedding_func=embedding_func,
    llm_model_func=llm_model_func,
)
await rag.initialize_storages()
```

### All-PostgreSQL Storage

```python
rag = LightRAG(
    working_dir="./rag_storage",
    workspace="project_a",
    embedding_func=embedding_func,
    llm_model_func=llm_model_func,
    kv_storage="PGKVStorage",
    vector_storage="PGVectorStorage",
    graph_storage="PGGraphStorage",
    doc_status_storage="PGDocStatusStorage",
)
await rag.initialize_storages()
```

### Mixed Storage

```python
rag = LightRAG(
    working_dir="./rag_storage",
    workspace="project_a",
    embedding_func=embedding_func,
    llm_model_func=llm_model_func,
    kv_storage="PGKVStorage",
    vector_storage="QdrantVectorDBStorage",
    graph_storage="PGGraphStorage",
    doc_status_storage="PGDocStatusStorage",
)
await rag.initialize_storages()
```

Mixed storage is valid when each selected service is configured, but operational tasks become multi-service: backups, clears, rebuilds, and migrations must cover every selected backend used by the workspace.

## Vector Storage Keyword Arguments

Every vector backend expects `cosine_better_than_threshold` to be present in `vector_db_storage_cls_kwargs`. The `LightRAG` constructor injects it from the top-level `cosine_better_than_threshold` value, so normal users can set either the top-level threshold or override through the dict.

```python
rag = LightRAG(
    working_dir="./rag_storage",
    embedding_func=embedding_func,
    vector_storage="MilvusVectorDBStorage",
    cosine_better_than_threshold=0.2,
    vector_db_storage_cls_kwargs={
        "index_type": "HNSW",
        "metric_type": "COSINE",
    },
)
```

Milvus additionally accepts index parameters through `vector_db_storage_cls_kwargs`. Supported Milvus keys include:

- `index_type`: `AUTOINDEX`, `HNSW`, `HNSW_SQ`, `IVF_FLAT`, `IVF_SQ8`, `IVF_PQ`, `DISKANN`, `SCANN`, and related supported index variants from the installed package.
- `metric_type`: `COSINE`, `L2`, or `IP`.
- HNSW keys: `hnsw_m`, `hnsw_ef_construction`, `hnsw_ef`.
- HNSW_SQ keys: `sq_type`, `sq_refine`, `sq_refine_type`, `sq_refine_k`.
- IVF keys: `ivf_nlist`, `ivf_nprobe`.

Milvus kwargs take priority over Milvus environment variables; environment variables take priority over implementation defaults. Non-Milvus keys are ignored by the Milvus index config bridge except for the common vector threshold.

## Selection Heuristics

- Choose the local defaults for single-process experiments, quick tests, or no external services.
- Choose PostgreSQL classes when the deployment already standardizes on PostgreSQL and wants one service for KV, vector, graph, and doc-status data.
- Choose Qdrant or Milvus when vector search scale/ops is the deciding factor, and pair with suitable KV, graph, and doc-status stores.
- Choose MongoDB or OpenSearch families only when the corresponding service is already operational and the team accepts backend-specific indexing/query behavior.
- Keep all four categories on the same backend family when operational simplicity matters more than specialized performance.
- Use explicit `workspace` values for multi-tenant or repeated test runs; do not depend on default/empty workspace behavior for shared services.
