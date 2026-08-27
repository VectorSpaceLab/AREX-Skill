# Reranking Workflows

## No-Download Smoke Check

From this sub-skill directory, run the bundled smoke script when you need to prove BEIR reranking mechanics without model downloads:

```bash
python scripts/rerank_smoke.py
```

The script uses a fake pair scorer, confirms that only the requested `top_k` candidates are scored, and asserts that reranker scores replace retrieval scores.

## Cross-Encoder Over Existing Results

Use this when retrieval is already complete and `results` follows BEIR's `dict[query_id][doc_id] = score` format.

```python
from beir.reranking import Rerank
from beir.reranking.models import CrossEncoder
from beir.retrieval.evaluation import EvaluateRetrieval

cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
reranker = Rerank(cross_encoder, batch_size=128)
rerank_results = reranker.rerank(corpus, queries, results, top_k=100)
ndcg, _map, recall, precision = EvaluateRetrieval.evaluate(qrels, rerank_results, [1, 3, 5, 10, 100])
```

Operational notes:

- Retrieval scores only decide the candidate slice; the final scores are model scores.
- `Rerank` returns only reranked candidates, so keep the original `results` separately when you need a fallback or comparison.
- Cross-encoder checkpoints can download on first use; prepare cache/network/GPU expectations before long jobs.

## MonoT5 Over BM25 Candidates

Use MonoT5 when you need sequence-to-sequence relevance scoring. It shares the same `Rerank` wrapper but has heavier runtime requirements.

```python
from beir.reranking import Rerank
from beir.reranking.models import MonoT5

mono_t5 = MonoT5(
    "castorini/monot5-base-msmarco",
    token_false="▁false",
    token_true="▁true",
)
rerank_results = Rerank(mono_t5, batch_size=32).rerank(corpus, queries, results, top_k=100)
```

Prefer smaller `batch_size` values for large T5 checkpoints or CPU-only runs. If true/false token ids are wrong or missing, MonoT5 scoring can fail before returning scores.

## BM25 + Reranker Recipe

1. Load `corpus`, `queries`, and `qrels` with the data-loading sub-skill.
2. Retrieve candidates with the retrieval-evaluation sub-skill, commonly BM25 top 100.
3. Instantiate a cross-encoder or MonoT5 reranker.
4. Call `Rerank.rerank(corpus, queries, results, top_k=100)`.
5. Evaluate `qrels` against the reranked result dictionary.
6. Compare retrieval metrics before and after reranking at the same k values.

Keep BM25 service setup, Elasticsearch host/index choices, and indexing behavior in retrieval-evaluation. This sub-skill starts after candidate retrieval exists.

## Dense or SBERT Candidate Rescoring

For bi-encoder/SBERT rescoring, BEIR examples use `EvaluateRetrieval.rerank(corpus, queries, results, top_k=...)` with a dense retriever model rather than `beir.reranking.Rerank`. Use retrieval-evaluation for the dense rerank API and return here only if adapting that dense model behind a `predict(sentence_pairs, batch_size)` protocol.

## Custom Pair-Scoring Model

Use a custom scorer when you already have a local model, API client, or rule-based scorer.

```python
class MyPairScorer:
    def predict(self, sentence_pairs, batch_size=32):
        scores = []
        for query, document in sentence_pairs:
            scores.append(score_pair(query, document))
        return scores

rerank_results = Rerank(MyPairScorer(), batch_size=16).rerank(corpus, queries, results, top_k=20)
```

Checklist for custom models:

- Return one numeric score per sentence pair in the same order.
- Avoid returning nested lists unless each item can be converted by `float(...)`.
- Raise clear errors for API/network failures rather than silently returning partial scores.
- Keep model batching independent of BEIR query grouping; BEIR passes one flat list of pairs.

## Top-K Interpretation

For each query:

- If candidate count is greater than `top_k`, BEIR sorts by original retrieval score descending, slices to `top_k`, and reranks only that slice.
- If candidate count is less than or equal to `top_k`, BEIR iterates the result dictionary as-is.
- Documents outside the reranked slice do not appear in `rerank_results`.

When a user wants "rerank top 2 from a larger run", tell them the final per-query result dictionary will contain at most two docs, even if the original retrieval dictionary had many more.

## Comparing Before and After

A compact comparison pattern:

```python
k_values = [1, 3, 5, 10, 100]
before = EvaluateRetrieval.evaluate(qrels, results, k_values)
after = EvaluateRetrieval.evaluate(qrels, rerank_results, k_values)
```

Interpret deltas only at depths supported by the reranked candidate count. If reranking top 10, changes at `@100` reflect candidate truncation as much as reranker quality.
