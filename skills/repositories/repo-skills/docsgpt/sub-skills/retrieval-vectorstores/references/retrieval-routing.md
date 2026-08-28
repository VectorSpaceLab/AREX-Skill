# Retrieval Routing

## Per-source request resolution

Each source has query-time retrieval config. When `PER_SOURCE_RETRIEVAL_ENABLED=false`, dispatch collapses to classic behavior.

A stored source `retrieval.chunks` value outranks a request top-k for that source. Request-level `chunks=0` still means skip retrieval for a turn. Keep this distinction when comparing API requests with observed context.

## Retriever choices

### Classic

Vector similarity retrieval. Query rephrasing may make an LLM side call before search. Use it as the portable baseline across stores.

### Hybrid

Fuses vector and keyword results with reciprocal-rank-style behavior. Keyword search is implemented only for pgvector at this snapshot. On other stores the keyword side contributes nothing and behavior effectively becomes vector-only.

Use hybrid when exact product codes, names, identifiers or phrases matter, but prove both vector and keyword candidates in diagnostics.

### GraphRAG

Routes to graph retrieval for a GraphRAG source; see the focused reference. Missing graph data falls back to classic retrieval.

## Exposure

- `prefetch`: retrieve before generation and inject context into the prompt; predictable for focused Q&A.
- `agentic_tool`: expose source search as a tool; model may search repeatedly, refine, or skip retrieval. Wiki sources default toward this browse-as-you-go model.

Agent type and exposure interact. Classic agents are naturally prefetch-oriented; agentic/research flows can exploit search tools.

## Threshold and pre-screen

`score_threshold` is meaningful for pgvector and MongoDB Atlas. FAISS, Qdrant, Milvus and hybrid paths may ignore it; inspect API warnings rather than assuming enforcement.

Pre-screening adds an LLM map/reduce relevance filter:

1. fetch `candidate_k` base candidates;
2. screen batches of `batch_size`;
3. retain up to `max_keep`;
4. pass final top-k to the answer.

Constraints: values 1–500, `max_keep <= candidate_k`, and `candidate_k >= chunks`. Cost and latency increase with candidates/batches. Start with pre-screen off, establish baseline recall, then add it for noisy corpora.

## Evaluation pattern

Use a small question set containing:

- semantic paraphrase;
- exact identifier/keyword;
- irrelevant query;
- multi-source conflict;
- multi-hop relationship if testing GraphRAG.

Measure retrieval before generation: expected chunk present, rank, citation/source id, latency and extra LLM calls. Then assess answer quality separately.
