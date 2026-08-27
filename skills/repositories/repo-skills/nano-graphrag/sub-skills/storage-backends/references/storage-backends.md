# nano-graphrag storage backends

This reference is self-contained for choosing and adapting nano-graphrag storage classes. It covers storage constructor arguments, working-directory artifacts, HNSW and Neo4j configuration, and the minimum adapter contract for third-party vector databases.

## GraphRAG storage slots

`GraphRAG` exposes storage through dataclass parameters:

```python
GraphRAG(
    working_dir="./my_nano_graphrag_store",
    key_string_value_json_storage_cls=JsonKVStorage,
    vector_db_storage_cls=NanoVectorDBStorage,
    vector_db_storage_cls_kwargs={},
    graph_storage_cls=NetworkXStorage,
    addon_params={},
    enable_local=True,
    enable_naive_rag=False,
    enable_llm_cache=True,
    query_better_than_threshold=0.2,
    embedding_batch_num=32,
)
```

The default storage set is file-backed and requires no external storage service:

- KV documents/caches: `JsonKVStorage`.
- Entity/chunk vectors: `NanoVectorDBStorage`.
- Knowledge graph: `NetworkXStorage` persisted as GraphML.

Vector storage always needs an `embedding_func` object with `embedding_dim`, `max_token_size`, and async-call behavior. Keep actual provider/model implementation in the sibling [provider-and-model-integrations](../../provider-and-model-integrations/SKILL.md) sub-skill; this reference only describes how vector stores consume it.

## Working-directory artifacts

Paths below are relative to the user's `GraphRAG(working_dir=...)`.

| Runtime object | Namespace | Default class | Created when | Artifact(s) |
| --- | --- | --- | --- | --- |
| `full_docs` | `full_docs` | `JsonKVStorage` | Always | `kv_store_full_docs.json` |
| `text_chunks` | `text_chunks` | `JsonKVStorage` | Always | `kv_store_text_chunks.json` |
| `llm_response_cache` | `llm_response_cache` | `JsonKVStorage` | `enable_llm_cache=True` | `kv_store_llm_response_cache.json` |
| `community_reports` | `community_reports` | `JsonKVStorage` | Always | `kv_store_community_reports.json` |
| `chunk_entity_relation_graph` | `chunk_entity_relation` | `NetworkXStorage` | Always | `graph_chunk_entity_relation.graphml` |
| `entities_vdb` | `entities` | `NanoVectorDBStorage` | `enable_local=True` | `vdb_entities.json` |
| `chunks_vdb` | `chunks` | `NanoVectorDBStorage` | `enable_naive_rag=True` | `vdb_chunks.json` |
| `entities_vdb` with HNSW | `entities` | `HNSWVectorStorage` | `enable_local=True` and HNSW selected | `entities_hnsw.index`, `entities_hnsw_metadata.pkl` |
| `chunks_vdb` with HNSW | `chunks` | `HNSWVectorStorage` | `enable_naive_rag=True` and HNSW selected | `chunks_hnsw.index`, `chunks_hnsw_metadata.pkl` |
| Neo4j graph | `chunk_entity_relation` plus a working-dir-derived label prefix | `Neo4jStorage` | `graph_storage_cls=Neo4jStorage` | No local graph file; data is stored in Neo4j labels/relationships. |

`GraphRAG` creates `working_dir` by default. Set `always_create_working_dir=False` only when all selected storage components are external or otherwise handle their own directories.

## Built-in KV storage

### `JsonKVStorage(namespace: str, global_config: dict)`

- Uses `global_config["working_dir"]` and persists to `kv_store_<namespace>.json`.
- Loads existing JSON on construction.
- Implements async `all_keys`, `get_by_id`, `get_by_ids`, `filter_keys`, `upsert`, and `drop`.
- Writes the JSON file in `index_done_callback`; in-memory changes are not durable until the callback runs.

Use it unless the user needs a shared cache/document store. Any custom KV backend must preserve the same async method names and should treat `filter_keys(data)` as "return keys that are not already present."

## Built-in vector storage

### `NanoVectorDBStorage(namespace, global_config, embedding_func, meta_fields=set(), cosine_better_than_threshold=0.2)`

- Persists a `nano-vectordb` JSON file named `vdb_<namespace>.json`.
- Builds the vector dimension from `embedding_func.embedding_dim`.
- Batches embedding calls using `global_config["embedding_batch_num"]`.
- Uses `global_config.get("query_better_than_threshold", cosine_better_than_threshold)` as the query threshold.
- `upsert(data)` expects each value to contain a `content` field. It stores `__id__` plus fields listed in `meta_fields`.
- `query(query, top_k)` embeds the query and returns best-first dicts containing at least `id` and `distance`; metadata fields are preserved.
- `index_done_callback()` saves the vector DB JSON.

Use this default when the index is small/medium, file-backed persistence is acceptable, and optional HNSW/FAISS/Milvus/Qdrant complexity is unnecessary.

### `HNSWVectorStorage(namespace, global_config, embedding_func, meta_fields=set(), ef_construction=100, M=16, max_elements=1000000, ef_search=50, num_threads=-1)`

HNSW is a built-in alternative backed by `hnswlib` using cosine space.

Set it through `GraphRAG`:

```python
from nano_graphrag import GraphRAG
from nano_graphrag._storage import HNSWVectorStorage

rag = GraphRAG(
    working_dir="./my_nano_graphrag_store",
    vector_db_storage_cls=HNSWVectorStorage,
    vector_db_storage_cls_kwargs={
        "max_elements": 1_000_000,
        "ef_search": 200,
        "ef_construction": 100,
        "M": 50,
        "num_threads": -1,
    },
    embedding_func=your_embedding_func,
)
```

Verified parameters consumed from `vector_db_storage_cls_kwargs`:

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `max_elements` | HNSW index capacity. | Must exceed total vectors for the namespace. Increase before inserting, or create a fresh/compatible working directory if old artifacts conflict. |
| `ef_search` | Search-time candidate list size. | Higher can improve recall but costs latency. If `top_k > ef_search`, the storage raises `ef_search` to `top_k` for that query and logs a warning. |
| `ef_construction` | Build-time accuracy/speed tradeoff. | Higher can improve graph quality but costs build time. |
| `M` | HNSW connectivity parameter. | Higher can improve recall/memory tradeoff; example recipes use values such as `50` for larger indexes. |
| `num_threads` | hnswlib thread count. | `-1` delegates to hnswlib default. |

Runtime details:

- Persisted files are `<namespace>_hnsw.index` and `<namespace>_hnsw_metadata.pkl`.
- Existing files are loaded on construction with the configured `max_elements`.
- `upsert(data)` embeds each value's `content`, maps source ids to unsigned integer hnswlib ids, preserves `meta_fields`, and returns the integer ids.
- `query(query, top_k)` returns best-first dicts containing metadata plus `distance` and `similarity`; `top_k` is capped by the number of inserted elements.
- If a write would exceed `max_elements`, it raises `ValueError` with current/max counts.

## Built-in graph storage

### `NetworkXStorage(namespace: str, global_config: dict)`

- Uses an undirected `networkx.Graph` by default.
- Loads `graph_<namespace>.graphml` if it exists; otherwise starts an empty graph.
- Persists GraphML in `index_done_callback()`.
- Implements node/edge existence, get, degree, batch get/degree, upsert, clustering, `community_schema`, and optional `embed_nodes`.
- `clustering("leiden")` uses a stable largest connected component and `graspologic.partition.hierarchical_leiden` with `max_graph_cluster_size` and `graph_cluster_seed` from the global config.
- `community_schema()` reads each node's JSON `clusters` attribute and returns community records with `level`, `title`, `edges`, `nodes`, `chunk_ids`, `occurrence`, and `sub_communities`.
- `embed_nodes("node2vec")` is available through `graspologic.embed.node2vec_embed` and uses `node2vec_params`; it is not required for normal GraphRAG querying.

Use this for local/single-process file-backed graph persistence and GraphML visualization.

### `Neo4jStorage(namespace: str, global_config: dict)`

Neo4j is built in but service-backed. It requires configuration in `GraphRAG(addon_params=...)`:

```python
import os
from nano_graphrag import GraphRAG
from nano_graphrag._storage import Neo4jStorage

neo4j_config = {
    "neo4j_url": os.environ["NEO4J_URL"],
    "neo4j_auth": (os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
}

rag = GraphRAG(
    working_dir="./my_nano_graphrag_store",
    graph_storage_cls=Neo4jStorage,
    addon_params=neo4j_config,
    embedding_func=your_embedding_func,
)
```

Service prerequisites:

- Running Neo4j 5.x server.
- Neo4j Graph Data Science (GDS) plugin installed and allowed.
- A valid Neo4j driver URI; public examples use `neo4j://localhost:7687` while service tests may use `bolt://localhost:7687`.
- Credentials passed as `neo4j_auth=(user, password)`.

Runtime details:

- `__post_init__` reads `global_config["addon_params"]["neo4j_url"]` and `neo4j_auth`; missing either raises `ValueError("Missing neo4j_url or neo4j_auth in addon_params")`.
- The graph label is namespaced from the working directory plus the storage namespace so multiple stores do not share one label accidentally.
- `index_start_callback()` verifies authentication/connectivity and creates indexes on `id`, `entity_type`, `communityIds`, and `source_id`.
- Nodes are merged with the namespace label and an `entity_type` label; relationships are merged as `RELATED` and default missing `weight` to `0.0`.
- `clustering("leiden")` calls GDS `gds.graph.project`, `gds.leiden.write`, and `gds.graph.drop`; missing GDS or permissions will fail here even if basic node/edge operations work.
- `index_done_callback()` closes the async Neo4j driver.

Use Neo4j only when the user needs an external graph service and can operate the required service/plugins. It is optional and should not be part of a default no-service smoke test.

## Adapter contracts

All storage callbacks are async. If a method has no work, implement it as an async no-op.

### Base KV contract

A `BaseKVStorage` subclass must implement:

```python
async def all_keys(self) -> list[str]: ...
async def get_by_id(self, id: str): ...
async def get_by_ids(self, ids: list[str], fields: set[str] | None = None): ...
async def filter_keys(self, data: list[str]) -> set[str]: ...  # return missing keys
async def upsert(self, data: dict[str, dict]): ...
async def drop(self): ...
async def index_done_callback(self): ...  # flush/commit if needed
```

### Base vector contract

A `BaseVectorStorage` subclass must implement:

```python
async def upsert(self, data: dict[str, dict]): ...
async def query(self, query: str, top_k: int) -> list[dict]: ...
async def index_done_callback(self): ...  # save/flush if needed
```

Vector adapter requirements:

1. Accept `namespace`, `global_config`, `embedding_func`, and `meta_fields` through the dataclass constructor.
2. Build the underlying index dimension from `embedding_func.embedding_dim`.
3. In `upsert`, read each value's `content`, batch calls through `embedding_func`, and preserve fields in `meta_fields`.
4. In `query`, embed the query string, return results in best-first order, and include source identifiers:
   - Entity vector results must include `entity_name` because local GraphRAG uses it to fetch graph nodes.
   - Chunk vector results must include `id` because naive RAG uses it to fetch text chunks.
5. Include a diagnostic score field. Built-ins use `distance`; HNSW also includes `similarity`. A backend like Qdrant may naturally expose `score`, but the adapter must document/normalize whether higher or lower is better.
6. Persist or flush in `index_done_callback` if the backend needs an explicit commit.

Optional adapter patterns:

- FAISS: use an id-mapped index such as `IndexIDMap(IndexFlatIP)`, keep a sidecar metadata map from integer ids to source ids/meta, persist both index and metadata, and normalize embeddings if treating inner product as cosine similarity.
- Milvus/Milvus Lite: create a collection named by `namespace` with dimension `embedding_func.embedding_dim`, store source ids and `meta_fields` as payload, and set cosine search parameters explicitly.
- Qdrant: create a collection with vector size `embedding_func.embedding_dim` and cosine distance, store the original source id/meta in payload, and decide whether to return `score`, `distance`, or both.

### Base graph contract

A `BaseGraphStorage` subclass must implement node/edge CRUD, degree queries, batch methods, `clustering(algorithm)`, `community_schema()`, and optionally `embed_nodes(algorithm)`. Normal GraphRAG insertion expects:

- `upsert_node(node_id, node_data)` and `upsert_edge(source_node_id, target_node_id, edge_data)` to merge, not blindly duplicate.
- `node_data` to preserve `entity_type`, `description`, and `source_id`.
- `edge_data` to preserve `weight`, `description`, `source_id`, and optional `order`.
- `community_schema()` to return nonempty communities after successful clustering and report generation.

## Selection checklist

1. Need no external service and easiest persistence: keep defaults.
2. Need GraphML output or visual inspection: use `NetworkXStorage` and inspect `graph_chunk_entity_relation.graphml`.
3. Need higher recall/speed local vector search: use `HNSWVectorStorage`, pin embedding dimension, and set `max_elements` above expected total vectors.
4. Need a service-backed graph: use `Neo4jStorage` only after verifying Neo4j 5.x, GDS, URI, auth, and permissions.
5. Need FAISS/Milvus/Qdrant: implement the BaseVectorStorage contract first, then map backend-specific distance/score semantics.
6. Changing embedding dimensions or backend classes usually requires a fresh working directory or careful backup/removal of old vector artifacts.
