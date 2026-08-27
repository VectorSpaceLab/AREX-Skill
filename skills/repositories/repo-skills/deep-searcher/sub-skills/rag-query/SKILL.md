---
name: rag-query
description: "Use and troubleshoot DeepSearcher query, retrieve, and RAG agent workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepSearcher RAG Query

Use this sub-skill when a task is about asking questions over already-loaded DeepSearcher data, retrieving references, choosing or instantiating RAG agents, tuning iteration/token tradeoffs, or diagnosing query-time failures.

Do not use this sub-skill for ingestion, provider configuration, CLI/service operation, or benchmark evaluation. Route those to the sibling sub-skills listed below.

## Start Here

1. Confirm that an environment has DeepSearcher installed and that provider/vector DB setup and data loading were already handled.
2. Pick the API surface:
   - Global convenience API: `deepsearcher.online_query.query`, `retrieve`, `naive_retrieve`, or `naive_rag_query`.
   - Manual agents: `DeepSearch`, `ChainOfRAG`, `NaiveRAG`, or `RAGRouter` when you already have `llm`, `embedding_model`, and `vector_db` objects.
3. Choose the lowest-cost agent that can answer the request:
   - `NaiveRAG` for cheap direct retrieval plus one summarization call.
   - `DeepSearch` for broad reports or surveys where sub-query expansion and reflection are useful.
   - `ChainOfRAG` for factual or multi-hop questions where intermediate answers and support-doc filtering matter.
   - `RAGRouter` when you want an LLM to select among multiple RAG agents from descriptions.
4. Inspect returned references before trusting an answer. Query APIs return `RetrievalResult` objects whose `text`, `reference`, `metadata`, and `score` fields explain what was used.

## Reference Map

- [API reference](references/api-reference.md): signatures, return shapes, constructors, `RetrievalResult`, and router APIs.
- [Workflows](references/workflows.md): query/retrieve patterns, agent selection, token controls, and no-result handling.
- [Agent behavior](references/agent-behavior.md): DeepSearch, ChainOfRAG, NaiveRAG, RAGRouter, CollectionRouter, and `wider_text` behavior.
- [Troubleshooting](references/troubleshooting.md): parse failures, no results, collection routing, wrapper caveats, token issues, notebook async issues, and relevant compatibility warnings.
- [Mock smoke helper](scripts/mock_rag_smoke.py): no-network return-shape smoke checks for `NaiveRAG` and `DeepSearch` using mock LLM, embedding, and vector DB objects.

## Safe Smoke Check

Run the bundled helper only in an environment with DeepSearcher installed. It uses in-memory mocks, performs no network calls, and does not require credentials:

```bash
python scripts/mock_rag_smoke.py --agent naive --format json
python scripts/mock_rag_smoke.py --agent deep-search --max-iter 1
```

## Route Elsewhere

- Data loading, chunking, file/web sources, and collection creation: use `data-ingestion`.
- Provider credentials, model classes, embedding dimensions, and vector DB connection setup: use `provider-configuration`.
- Console script behavior, CLI help, service deployment, and API server usage: use `cli-and-service`.
- Benchmark metrics, recall/error/token plots, and evaluation scripts: use `evaluation`.
