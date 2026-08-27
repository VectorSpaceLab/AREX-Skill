---
name: vector-search-and-retrieval
description: "Build and troubleshoot Superduper VectorIndex embedding retrieval
  workflows, local vector search behavior, and optional vector-search backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Vector Search and Retrieval

Use this sub-skill when a task involves Superduper `VectorIndex` construction, listener-generated embeddings, query-time embedding compatibility, `table.like(..., vector_index=..., n=...)` retrieval, local vector search behavior, or vector-search backend portability.

## Route Here For

- Building an embedding listener and wrapping it in a `VectorIndex`.
- Choosing or debugging `measure="cosine"`, `"dot"`, or `"l2"` retrieval.
- Using vector datatypes such as `vector[int:300]`, `vector[float:32]`, `Array`, or `Vector` in model/table schemas.
- Querying nearest neighbors with `table.like(query, vector_index="...", n=k).select().execute()`.
- Adding, deleting, copying, recovering, or inspecting local vector-search contents.
- Connecting an indexing listener to a separate compatible listener for a different query key.

## Route Elsewhere

- Generic Datalayer configuration, connection strings, artifact stores, and cluster setup belong in `datalayer-and-config`.
- Service-specific plugin installation, credentials, daemon startup, or cloud setup for Qdrant, ChromaDB, Lance, MongoDB Atlas, Snowflake, or other plugins belongs in `plugins-and-integrations`.

## Required Reading

1. For the end-to-end construction pattern and operational checklist, read [references/vector-index-workflow.md](references/vector-index-workflow.md).
2. For constructor signatures, datatype choices, measures, query semantics, and backend API details, read [references/vector-search-api.md](references/vector-search-api.md).
3. For failure diagnosis, read [references/troubleshooting.md](references/troubleshooting.md).
4. For a safe local smoke helper, use [scripts/superduper_vector_smoke.py](scripts/superduper_vector_smoke.py).

## Quick Operating Checklist

- Give the indexing `ObjectModel` a vector datatype with a concrete dimension before applying the `VectorIndex`.
- Make the indexing `Listener` read the source table/key that should be embedded and ensure its `select` is not `None` for indexing.
- Use a compatible listener only when query documents arrive under a different key than the indexed records.
- Apply the `VectorIndex` after the source data and listener inputs exist, or explicitly re-run/reinitialize vector-copy behavior after adding records.
- Expect result rows from `.like(...).select().execute()` to include a `score` field sorted descending by similarity.
- Treat optional vector databases as interchangeable only at the `VectorSearcher` contract level; their installation and service availability are plugin responsibilities.
