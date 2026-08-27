# Storage backend troubleshooting

Use this guide after confirming the issue is in storage selection, storage persistence, graph service setup, or vector adapter behavior. If the graph is empty because the LLM produced no entities/relations, route to provider and customization troubleshooting after the storage checks below.

## HNSWVectorStorage

### `ModuleNotFoundError` or hnswlib build failures

Symptoms:

- Importing storage classes fails with a missing `hnswlib` module.
- `pip install hnswlib` fails because a compiler or wheel is unavailable.

Recovery:

1. If HNSW is optional for the user, switch back to `NanoVectorDBStorage` and keep the same `working_dir` only if vector artifacts are compatible; otherwise use a fresh working directory.
2. If HNSW is required, install a Python version and platform with an available `hnswlib` wheel or provide the compiler/build toolchain required by hnswlib.
3. Re-run a storage smoke after install. The storage package imports HNSW in its storage namespace, so a missing hnswlib can break broader storage imports.

### `ValueError: Cannot insert ... Current: ..., Max: ...`

Cause: the number of existing HNSW elements plus new data exceeds `max_elements`.

Recovery:

```python
GraphRAG(
    vector_db_storage_cls=HNSWVectorStorage,
    vector_db_storage_cls_kwargs={"max_elements": 2_000_000},
    embedding_func=your_embedding_func,
)
```

Set `max_elements` above the expected total vectors before indexing. If old HNSW artifacts were created with incompatible capacity or dimension, back them up and use a fresh working directory or remove only the affected vector artifacts after confirming the user wants a rebuild.

### `top_k` is larger than `ef_search`

`HNSWVectorStorage.query()` caps `top_k` to the current element count. If `top_k > ef_search`, it raises the hnswlib search parameter to `top_k` for that query and logs a warning.

Recovery:

- For frequent large `top_k`, set `vector_db_storage_cls_kwargs={"ef_search": desired_top_k_or_higher}`.
- Higher `ef_search` can improve recall but costs search time.

## Vector dimension mismatch

Symptoms:

- HNSW/NanoVectorDB load or query failures after changing embedding models.
- Unexpected results after reusing a `working_dir` with a different embedding function.
- Shape errors because the embedding function returns a vector length different from `embedding_func.embedding_dim`.

Recovery:

1. Confirm the embedding function returns a NumPy array shaped `(len(texts), embedding_func.embedding_dim)`.
2. Do not reuse persisted vector artifacts across embedding dimensions. Use a fresh `working_dir`, or back up and delete the affected vector files before re-indexing.
3. For HNSW, rebuild `<namespace>_hnsw.index` and `<namespace>_hnsw_metadata.pkl` when dimension changes.
4. For NanoVectorDB, rebuild `vdb_<namespace>.json` when dimension changes.
5. For FAISS/Milvus/Qdrant adapters, recreate the collection/index with the new dimension.

## Neo4jStorage

### Missing `addon_params`

Symptom:

```text
ValueError: Missing neo4j_url or neo4j_auth in addon_params
```

Recovery:

```python
import os
from nano_graphrag._storage import Neo4jStorage

neo4j_config = {
    "neo4j_url": os.environ.get("NEO4J_URL", "neo4j://localhost:7687"),
    "neo4j_auth": (
        os.environ.get("NEO4J_USER", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "neo4j"),
    ),
}

rag = GraphRAG(
    graph_storage_cls=Neo4jStorage,
    addon_params=neo4j_config,
    embedding_func=your_embedding_func,
)
```

Both keys must be inside `addon_params`; setting only environment variables is not enough unless the caller maps them into this dict.

### Connectivity/authentication succeeds but Leiden clustering fails

Neo4j graph storage uses GDS procedures for Leiden clustering. Basic upserts can work while clustering fails if GDS is absent or blocked.

Checklist:

1. Neo4j server is 5.x.
2. Neo4j Graph Data Science plugin is installed and compatible with the server.
3. The configured user can run `gds.graph.project`, `gds.leiden.write`, and `gds.graph.drop`.
4. The graph has nodes and `RELATED` relationships with `weight` properties before clustering.
5. The service URI matches the deployment; both `neo4j://...` and `bolt://...` are driver URI styles, but the deployment must accept the chosen one.

### Neo4j data appears mixed across runs

`Neo4jStorage` builds a label from the working directory and namespace. Reusing the same `working_dir` targets the same namespaced label. Use a different working directory or explicitly clean the target graph only after user approval.

## NetworkXStorage and empty graph clustering

Symptoms:

- Global queries return the fail response because no community schema exists.
- `community_schema()` returns `{}`.
- Leiden or largest-connected-component code fails on an empty graph.
- Logs indicate no new entities were found.

Storage checks:

1. Confirm the GraphML file exists after insertion: `graph_chunk_entity_relation.graphml` for the default graph namespace.
2. Confirm the graph has nodes and edges before clustering.
3. If nodes exist but no `clusters` attribute exists, clustering did not run or failed.
4. If no nodes/edges exist, the root cause is usually entity extraction/provider output, prompt formatting, chunking, or input content rather than NetworkX persistence.

Routing:

- Storage-only fix: rebuild from a fresh `working_dir` if the GraphML file is corrupted or incompatible.
- Provider/customization fix: troubleshoot LLM output format, context size, entity extraction prompts, and malformed JSON when extraction produced zero entities/relations.

## Optional FAISS/Milvus/Qdrant adapters

### Import or service errors

These are optional patterns, not required default dependencies.

- FAISS requires the correct `faiss`/`faiss-cpu` package for the platform.
- Milvus Lite or Milvus requires `pymilvus`; full Milvus may require an external service while Milvus Lite stores a local DB file.
- Qdrant requires `qdrant-client`; local file mode and remote service mode have different persistence and locking behavior.

If optional dependencies are unavailable, keep `NanoVectorDBStorage` or `HNSWVectorStorage` until the user explicitly asks to install/configure the optional backend.

### Adapter returns wrong ids or metadata

Symptoms:

- Local mode finds vector hits but then graph node lookup fails.
- Naive mode vector hits cannot retrieve text chunks.
- Results are ranked but missing `entity_name` or `id`.

Recovery:

- Entity vector queries must return the original `entity_name` preserved from `meta_fields={"entity_name"}`.
- Chunk vector queries must return the original chunk `id`.
- Preserve all requested `meta_fields` in the backend payload/sidecar metadata.
- If the backend uses integer or UUID internal ids, keep a sidecar or payload mapping back to the original source id.

### Distance/score direction is inconsistent

Built-in NanoVectorDB returns `distance`; HNSW returns `distance` and `similarity`. Qdrant-like backends often return higher-is-better `score`; FAISS inner product can also be higher-is-better.

Recovery:

1. Keep query results sorted best-first before returning them.
2. Include a clear diagnostic field (`distance`, `similarity`, or `score`) and document whether higher or lower is better.
3. If converting similarity to distance, use a consistent conversion such as `distance = 1 - similarity` for cosine-like normalized vectors.
4. Remember that GraphRAG's local and naive paths mainly consume the result order plus `entity_name`/`id`; diagnostic score fields still matter for debugging and future adapters.

## GraphML visualization helper

- If `networkx.read_graphml` fails, confirm the file is valid GraphML and not a Neo4j export in another format.
- If the helper refuses to write output, the target file already exists; choose a new output path or pass `--overwrite` intentionally.
- If HTML preview is hard to interpret on a large graph, export JSON and inspect/filter it with a dedicated graph tool.
