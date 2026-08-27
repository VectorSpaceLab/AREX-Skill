---
name: storage-backends
description: "Choose, configure, validate, and troubleshoot nano-graphrag
  storage backends for KV data, vector indexes, graph persistence, Neo4j, and
  safe GraphML visualization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Storage Backends

Use this sub-skill when a user needs to choose a nano-graphrag storage class, configure `GraphRAG` storage arguments, validate local storage persistence, adapt a third-party vector database, set up Neo4j graph storage, or inspect a GraphML knowledge graph.

Do not use this sub-skill for provider-specific LLM or embedding implementation details; storage docs only state the vector `embedding_func` contract and should hand off actual provider code to the sibling [provider-and-model-integrations](../provider-and-model-integrations/SKILL.md) skill. Do not use it for the high-level insert/query workflow; route that to the sibling [core-graphrag-workflows](../core-graphrag-workflows/SKILL.md) skill.

## Runtime references and scripts

- Read [references/storage-backends.md](references/storage-backends.md) when choosing among `JsonKVStorage`, `NanoVectorDBStorage`, `HNSWVectorStorage`, `NetworkXStorage`, `Neo4jStorage`, or when implementing a FAISS/Milvus/Qdrant-style vector adapter.
- Read [references/graphml-visualization.md](references/graphml-visualization.md) when the user has a GraphML file and wants JSON export or an optional local browser preview.
- Read [references/troubleshooting.md](references/troubleshooting.md) when storage initialization, persistence, HNSW capacity/search, Neo4j/GDS, empty graph clustering, or vector adapter behavior fails.
- Run [scripts/storage_smoke.py](scripts/storage_smoke.py) to instantiate NetworkX plus local vector storage with a fake embedding function and no provider API calls.
- Run [scripts/visualize_graphml.py](scripts/visualize_graphml.py) to convert a user-provided GraphML file to node-link JSON and, only if requested, generate/serve a local HTML preview.

## Fast routing

- Default local file-backed setup: keep `JsonKVStorage`, `NanoVectorDBStorage`, and `NetworkXStorage`; use a fresh `working_dir` for an independent index.
- Larger/faster local vector search: set `vector_db_storage_cls=HNSWVectorStorage` and tune `vector_db_storage_cls_kwargs` before inserting data.
- External graph service: set `graph_storage_cls=Neo4jStorage` and provide `addon_params={"neo4j_url": ..., "neo4j_auth": (...)}` after confirming Neo4j 5.x plus the GDS plugin are running.
- Third-party vector database: subclass `BaseVectorStorage`, preserve `upsert`, `query`, and `index_done_callback`, return ranked results containing source ids plus any required metadata.
- If a storage symptom is caused by LLM/entity extraction producing no graph, route to the sibling [customization-and-troubleshooting](../customization-and-troubleshooting/SKILL.md) skill after confirming the graph backend itself is healthy.
