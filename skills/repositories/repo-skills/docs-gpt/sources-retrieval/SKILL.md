---
name: sources-retrieval
description: "Use for DocsGPT source upload and ingestion, chunking, retrieval,
  search, vector stores, wiki sources, re-ingest, and GraphRAG."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sources and retrieval skill

Use this subskill for upload, ingestion, chunking, retrieval, re-ingest, search, vector-store, wiki-source, or GraphRAG work.

## Primary surfaces

- Source upload and management: `/api/sources`, `/api/sources/paginated`, `/api/sources/reingest`, `/api/delete_old`, `/api/manage_sync`, `/api/sync_source`, `/api/directory_structure`.
- Source config: `/api/sources/<source_id>/config`.
- Wiki sources: `/api/sources/<source_id>/wiki/...`.
- GraphRAG: `/api/sources/<source_id>/graphrag/enable`, `/api/sources/<source_id>/graph`, `/api/sources/<source_id>/graph/node/<node_id>`.
- Chunks/search: `/api/get_chunks`, `/api/add_chunk`, `/api/delete_chunk`, `/api/update_chunk`, plus the fast `/api/search` answer route.

## Core concepts

- **Chunking** is bake-time. Changing chunking settings requires re-ingest for existing content.
- **Retrieval** is live. Changing retriever/top-k/exposure/prescreen settings affects the next query.
- Per-source retrieval config can override request-level `chunks`.
- `classic`, `hybrid`, and `graphrag` are the key retriever modes.
- `agentic_tool` exposure makes a source available as a search tool rather than prefetching chunks.

## Special cases

- **Wiki sources** use the agentic exposure path and have dedicated page/convert endpoints.
- **GraphRAG** is pgvector-only and requires `GRAPHRAG_ENABLED=true`.
- **Remote sources** and connectors can enqueue ingest jobs; check Celery and the task-status endpoint.
- **Per-source configuration** supports chunking strategy, retriever, exposure, chunk count, score threshold, rephrase, and prescreen options.

## Source flow checklist

1. Confirm the ingestion path the user wants: local upload, remote URL, wiki source, or connector/sync.
2. Determine whether a full re-ingest is needed or only a retrieval config change.
3. Check the current vector store and whether GraphRAG or hybrid search is actually supported by that store.
4. For source failures, inspect parser errors, Celery queue state, and document-size limits before changing retrieval logic.

## Useful source files

- `application/api/user/sources/routes.py`
- `application/api/user/sources/upload.py`
- `application/api/user/sources/chunks.py`
- `application/parser/document_reader.py`
- `application/core/settings.py`
- `application/vectorstore/`
- `application/retriever/`
- `application/graphrag/`

## Safe checks

```bash
python skills/disco/docs-gpt/scripts/inspect_api_routes.py --repo . --contains /api/sources
python -m pytest tests/parser/test_document_reader.py tests/retriever/* tests/graphrag/*
```

If you need a deployment-level reminder, read:

- `docs/content/Sources/Per-source-configuration.mdx`
- `docs/content/Sources/GraphRAG.mdx`
- `docs/content/Sources/Wiki-sources.mdx`
- `docs/content/Guides/How-to-train-on-other-documentation.mdx`
