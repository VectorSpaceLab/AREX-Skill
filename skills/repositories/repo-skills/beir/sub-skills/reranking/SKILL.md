---
name: reranking
description: "Rerank BEIR retrieval results with cross-encoder, MonoT5, SBERT,
  or custom pair-scoring models and re-evaluate top-k changes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BEIR Reranking

Use this sub-skill when you already have BEIR-style `corpus`, `queries`, and retrieval `results`, and need to rescore a candidate set with a pair-scoring model.

## Route Here

- Rerank top-k BM25, dense, sparse, or lexical retrieval candidates with `beir.reranking.Rerank`.
- Adapt a custom model that exposes `predict(sentence_pairs, batch_size=...)`.
- Diagnose candidate truncation, missing corpus documents, score-shape mismatches, or re-evaluation after reranking.

## Route Elsewhere

- Initial retrieval, BM25/Elasticsearch setup, dense retrieval, and `EvaluateRetrieval.rerank` routing belong to `retrieval-evaluation`.
- Dataset file layout, corpus/query/qrels loading, and schema repair belong to `data-loading`.
- Training rerankers or retrievers belongs to `training`.

## Start Points

- Read `references/api-reference.md` for `Rerank`, model protocol, pair construction, and result shape.
- Read `references/workflows.md` for BM25/dense + reranker recipes and evaluation handoff.
- Read `references/troubleshooting.md` for common reranking failures.
- Run `scripts/rerank_smoke.py` for a no-download deterministic check of top-k truncation and score replacement.

## Minimal Pattern

```python
from beir.reranking import Rerank
from beir.reranking.models import CrossEncoder
from beir.retrieval.evaluation import EvaluateRetrieval

reranker = Rerank(CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2"), batch_size=128)
rerank_results = reranker.rerank(corpus, queries, results, top_k=100)
ndcg, _map, recall, precision = EvaluateRetrieval.evaluate(qrels, rerank_results, k_values)
```

`rerank_results` contains only the candidates passed into reranking, scored by the reranker; it is not merged back with non-reranked retrieval hits.
