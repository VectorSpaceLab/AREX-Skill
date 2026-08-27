# Reranking API Reference

## Core Entry Point

`beir.reranking.Rerank(model, batch_size=128, **kwargs)` wraps any pair-scoring model that implements a compatible `predict` method.

```python
reranker = Rerank(model, batch_size=128)
rerank_results = reranker.rerank(corpus, queries, results, top_k=100)
```

`Rerank.rerank(corpus, queries, results, top_k)` expects:

| Argument | Shape | Notes |
| --- | --- | --- |
| `corpus` | `dict[doc_id, {"title": str, "text": str, ...}]` | `title` and `text` are concatenated as `(title + " " + text).strip()` for each rerank pair. Missing candidate doc ids raise `KeyError`. |
| `queries` | `dict[query_id, str]` | Each query id in `results` must be present. |
| `results` | `dict[query_id, dict[doc_id, score]]` | Retrieval scores are used only to choose the top candidates before reranking. |
| `top_k` | `int` | If a query has more than `top_k` candidates, BEIR sorts by retrieval score descending and reranks only that slice. If it has `top_k` or fewer, insertion order is used. |

The return value is `dict[query_id, dict[doc_id, rerank_score]]`. It preserves one outer entry for every query in `results`, but inner dictionaries contain only reranked candidates.

## Pair Construction

For every candidate chosen for reranking, BEIR appends:

```python
[queries[query_id], (corpus[doc_id].get("title", "") + " " + corpus[doc_id].get("text", "")).strip()]
```

The model never receives doc ids, original retrieval scores, qrels, or metadata beyond title/text. If the scoring model needs fields besides `title` and `text`, wrap or pre-format the corpus text before calling `Rerank`.

## Model Protocol

A custom reranking model can be any object with:

```python
def predict(sentence_pairs, batch_size=32, **kwargs) -> list[float]:
    ...
```

BEIR calls it as `model.predict(sentence_pairs, batch_size=self.batch_size)` and coerces every returned score with `float(score)`. The returned iterable must have exactly one score per input pair for reliable output. If it returns too few scores, trailing candidate ids disappear because BEIR zips pairs and scores. If it returns too many scores, extra scores are ignored.

## Built-in Wrapper Notes

### CrossEncoder

`beir.reranking.models.CrossEncoder(model_path, **kwargs)` wraps `sentence_transformers.cross_encoder.CrossEncoder` and forwards:

```python
predict(sentences, batch_size=32, show_progress_bar=True)
```

Use it for standard cross-encoder checkpoints such as `cross-encoder/ms-marco-MiniLM-L-6-v2`. Instantiation can download model weights and requires `sentence-transformers` dependencies.

### MonoT5

`beir.reranking.models.MonoT5(model_path, tokenizer=None, use_amp=True, token_false=None, token_true=None)` loads a seq2seq model and tokenizer through Hugging Face Transformers. Its `predict` groups pair inputs by query, tokenizes documents with a T5 prompt pattern, decodes one token, and returns log-probabilities for the true/relevant token.

Important MonoT5 details:

- Pass `token_false` and `token_true` for checkpoints whose true/false tokens are not inferable.
- It defaults to CUDA when available, otherwise CPU.
- Large MonoT5 checkpoints can be memory-heavy and slow for high `top_k`.

### SBERT-Style Reranking

The example called `evaluate_bm25_sbert_reranking.py` uses dense retrieval reranking through `EvaluateRetrieval.rerank`, not `beir.reranking.Rerank`. Route that workflow through retrieval evaluation when you want bi-encoder rescoring over candidates.

## Evaluation After Reranking

Use the normal evaluator on the returned reranked dictionary:

```python
from beir.retrieval.evaluation import EvaluateRetrieval

ndcg, _map, recall, precision = EvaluateRetrieval.evaluate(qrels, rerank_results, k_values)
```

Choose `k_values` that are no larger than the reranked candidate depth when possible. Evaluating `NDCG@100` after reranking only `top_k=10` measures a ten-document result list, not the original top 100.

## Provenance

This reference is based on BEIR 2.2.0 behavior observed in:

- `beir/reranking/rerank.py`
- `beir/reranking/models/cross_encoder.py`
- `beir/reranking/models/mono_t5.py`
- `examples/retrieval/evaluation/reranking/evaluate_bm25_ce_reranking.py`
- `examples/retrieval/evaluation/reranking/evaluate_bm25_monot5_reranking.py`
- `examples/retrieval/evaluation/reranking/evaluate_bm25_sbert_reranking.py`
- `examples/benchmarking/benchmark_bm25_ce_reranking.py`
