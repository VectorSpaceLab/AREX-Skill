---
name: retrieval-evaluation
description: "Run BEIR retrieval backends and metric evaluation for dense,
  sparse, lexical, API-backed, FAISS, and custom models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Retrieval Evaluation

Use this sub-skill when the task is to retrieve BEIR results, evaluate metrics, choose a first-stage backend, validate a custom retriever model, persist embeddings, or diagnose optional retrieval backends.

## Route

- Start with [references/workflows.md](references/workflows.md) for end-to-end exact dense, FAISS, sparse, BM25, API-backed, custom-model, metric, and export workflows.
- Use [references/api-reference.md](references/api-reference.md) for `EvaluateRetrieval`, backend classes, model protocols, metric names, and result/runfile APIs.
- Use [references/model-and-backend-guide.md](references/model-and-backend-guide.md) to choose exact vs FAISS vs sparse vs BM25/API backends and inspect optional dependency readiness.
- Use [references/troubleshooting.md](references/troubleshooting.md) for score-function errors, qrels/results mismatches, identical IDs, missing FAISS, Elasticsearch service failures, API credentials, embedding cache issues, and scale limits.

## Bundled Helpers

- Offline retrieval smoke test: `python scripts/retrieval_smoke.py`
- Save smoke-test runfile/results: `python scripts/retrieval_smoke.py --output-dir beir-retrieval-smoke-output`
- Optional backend inventory without service calls: `python scripts/inspect_optional_backends.py --json`

## Boundaries

- This sub-skill owns `EvaluateRetrieval`, dense exact search, dense FAISS search, sparse search, BM25/Elasticsearch lexical search, retrieval model wrappers, API-backed embedding wrappers, custom retrieval model protocols, metric evaluation, embedding persistence, and retrieval result export.
- Route dataset file schemas, `GenericDataLoader`, `HFDataLoader`, and BEIR JSONL/TSV validation to [../data-loading/SKILL.md](../data-loading/SKILL.md).
- Route second-stage reranking with cross-encoders, MonoT5, or reranker classes to [../reranking/SKILL.md](../reranking/SKILL.md).
- Route model training, query generation, passage expansion, and answer generation to their own sibling sub-skills when present.
