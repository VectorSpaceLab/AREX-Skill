---
name: search-retrieval
description: "Use and troubleshoot Khoj semantic search, query filters,
  embeddings, reranking, and SearchResponse interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Khoj Search Retrieval

Use this sub-skill when working on Khoj semantic search, `/api/search`, query filters, retrieval ranking, or search-result interpretation.

## Route Map

- Use `references/search-api.md` for `/api/search` parameters, `SearchType` values, result collation, dedupe, reranking, and `SearchResponse` fields.
- Use `references/query-filters.md` for date, file, and word filter syntax; examples; defiltering; and edge cases.
- Use `references/embeddings-and-ranking.md` for embedding models, cross-encoder reranking, `max_distance`, defaults, and performance tradeoffs.
- Use `references/troubleshooting.md` for no results, excessive results, bad filters, stale indexes, model/backend failures, user/agent isolation, and reranker failures.
- Use `scripts/inspect_query_filters.py` to safely inspect filter terms and defiltered query text without starting the Khoj server.

## Boundaries

- This sub-skill covers semantic search, `/api/search`, filters, embeddings, reranking, and `SearchResponse` interpretation.
- Route content ingestion, sync, update/index rebuild implementation, and file parsing to `content-indexing`.
- Route chat, `/notes`, conversation context construction, and agent response behavior to `chat-agents`.
- Route server startup, auth, deployment, Docker, and API infrastructure setup to `deployment-api`.
- Route maintainer test selection, development setup, and release scripts to `development`.

## Evidence Basis

This guidance is distilled from Khoj source and tests for search routing, text retrieval, filters, embeddings, API response models, and documented search/filter/performance behavior. It is self-contained for future coding agents and does not require reading original repo docs or tests at runtime.
