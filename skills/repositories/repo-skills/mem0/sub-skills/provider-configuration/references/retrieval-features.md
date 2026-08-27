# Retrieval Features

Mem0 OSS retrieval combines semantic vector search with optional keyword and entity signals. Current OSS graph memory is built into the memory pipeline; it is not configured through an external graph store.

## Hybrid Retrieval Flow

The inspected Python and TypeScript OSS implementations use the same high-level retrieval sequence:

1. Validate search query, `top_k`/`topK`, `threshold`, and entity filters.
2. Lemmatize the query for BM25 when NLP support is available.
3. Extract query entities.
4. Embed the query and over-fetch semantic candidates from the vector store.
5. Ask the vector store for `keyword_search` results when supported.
6. Normalize BM25 scores and compute entity boosts.
7. Fuse semantic score, BM25 score, and entity boost into a single result `score`.
8. Optionally apply configured reranking when the caller asks for rerank.

BM25 and entity scores boost candidates; they do not expand recall beyond the semantic candidate pool. If vector semantic search misses a memory entirely, tune the embedder, filters, threshold, and `top_k` before assuming BM25 will rescue it.

## Scoring Details

`score_and_rank` / `scoreAndRank` gates candidates by semantic score first. Candidates below `threshold` are removed even if BM25 or entity matching would have boosted them.

The maximum combined score denominator adapts to active signals:

- Semantic only: `1.0`
- Semantic + BM25: `2.0`
- Semantic + entity boost: `1.5`
- Semantic + BM25 + entity boost: `2.5`

Entity boost weight is `0.5`. When `explain=True` in Python or `explain: true` in TypeScript, score details include semantic score, BM25 score, entity boost, raw score, max possible score, final score, and threshold.

## Built-in Graph Memory

Current OSS Mem0 removed external graph store configuration and replaced it with built-in entity linking:

- Remove stale `enable_graph` / `enableGraph` flags.
- Remove stale `graph_store` / `graphStore` blocks for Neo4j, Memgraph, Kuzu, Apache AGE, or Neptune.
- Entities are extracted on `add()` and stored in a parallel vector collection such as `{collection}_entities` or a separate file-backed entity store.
- At search time, entities extracted from the query are embedded and matched against the entity store. Linked memories receive an entity boost folded into the normal `score`.
- Search results do not expose the old external-graph `relations` payload; graph memory affects ranking.

Graph memory is automatic after new memories are added. Existing memories from older collections may not have entity links until re-added or migrated by an application-specific process.

## BM25 and Keyword Search

Vector stores can override `keyword_search`. If they do not, Mem0 warns or silently falls back to semantic-only/hybrid-without-BM25 behavior depending on SDK and store.

- Qdrant can use sparse vectors/BM25 and may need `fastembed` for keyword encoding.
- Elasticsearch, OpenSearch, pgvector, Qdrant, and other stores may have native keyword support depending on implementation.
- Missing NLP dependencies reduce lemmatization/entity quality but should not block semantic search.
- Keep text payloads and `text_lemmatized`/equivalent fields intact when writing custom vector stores; keyword search depends on indexed text.

## Reranking

Reranking is a second pass over already retrieved candidates. Configure a reranker provider, then explicitly request reranking on search when needed.

Good defaults:

- Start with vector/hybrid search working before adding a reranker.
- Use `top_k`/`topK` small enough to control hosted reranker cost and latency.
- Catch reranker failures and fall back to non-reranked results for latency-sensitive workflows.
- Prefer local `sentence_transformer` or `huggingface` rerankers when privacy requires on-device scoring; prefer hosted providers such as Cohere or Zero Entropy for quality when API calls are acceptable.

## Metadata and Entity Filters

Python OSS search requires `filters` to contain at least one of `user_id`, `agent_id`, or `run_id`. TypeScript OSS similarly requires scoped filters for search/getAll. Do not pass these as top-level search kwargs.

Supported enhanced metadata filters include equality, inequality, list membership, contains/icontains, wildcard `*`, and logical `AND`/`OR`/`NOT`. Complex logical filters are translated toward vector-store-compatible forms, but backend support varies. If results are too broad or too narrow, simplify filters to confirm the vector store's native behavior first.

## Temporal and Decay Boundaries

Current OSS Memory rejects or warns on platform-only temporal/decay features:

- Python `add(timestamp=...)` and `search(reference_date=...)` raise unsupported temporal feature errors.
- TypeScript `referenceDate` and `decay` paths produce explicit unsupported feature messages/notices.
- Temporal-looking metadata can trigger notices, but it does not enable platform temporal retrieval in OSS.

Route platform-specific temporal project settings and hosted-client behavior to `../sdk-memory/SKILL.md`.
