# Reranking Troubleshooting

## Empty Candidate Sets

Symptom: `rerank_results[query_id]` is empty or evaluation metrics drop unexpectedly.

Cause: `results[query_id]` is empty before reranking. `Rerank` does not retrieve replacement documents.

Fix:

- Route upstream retrieval issues to retrieval-evaluation.
- Confirm `results` uses `dict[query_id][doc_id] = score` and includes candidates for every query you evaluate.
- Evaluate only queries that have retrieved candidates when debugging retrieval failures.

## Missing Corpus Document IDs

Symptom: `KeyError: '<doc_id>'` while calling `Rerank.rerank`.

Cause: A candidate doc id in `results` is not present in `corpus`. BEIR looks up `corpus[doc_id]` before calling the model.

Fix:

```python
missing = {
    doc_id
    for query_results in results.values()
    for doc_id in query_results
    if doc_id not in corpus
}
if missing:
    raise KeyError(f"results contain doc ids missing from corpus: {sorted(missing)[:10]}")
```

If missing ids come from a mismatched dataset, route dataset loading and id normalization to data-loading.

## Query IDs Missing From Queries

Symptom: `KeyError` for a query id when building sentence pairs.

Cause: `results` contains query ids not present in `queries`.

Fix: Validate query ids before reranking and make sure retrieval was run for the same loaded split.

## Predict Output Count Mismatch

Symptom: Fewer docs than expected in reranked output, silently missing candidates, or scores assigned only to early candidates.

Cause: `Rerank` uses `zip(pair_ids, rerank_scores)`. Too few scores drop trailing candidates; too many scores are ignored.

Fix: Wrap custom models with a guard:

```python
scores = model.predict(sentence_pairs, batch_size=batch_size)
if len(scores) != len(sentence_pairs):
    raise ValueError(f"predict returned {len(scores)} scores for {len(sentence_pairs)} pairs")
```

For built-in wrappers, mismatches are usually caused by a model/tokenizer failure; inspect the original exception and reduce batch size.

## Predict Output Type Mismatch

Symptom: `TypeError` or `ValueError` from `float(score)`.

Cause: The model returns non-scalar values, strings that are not numeric, tensors with more than one element, or nested lists.

Fix: Convert outputs to plain numeric scalars in the model wrapper before returning. For torch/numpy scalars, use `.item()` when needed.

## Top-K Slicing Surprises

Symptom: A user expects all retrieved documents to remain available after reranking, but `rerank_results` has only `top_k` docs per query.

Cause: BEIR reranks only the selected candidate slice and returns only that slice.

Fix:

- Increase `top_k` if evaluation requires deeper result lists.
- Keep original retrieval `results` separately for fallback, audit, or merge logic.
- Explain that candidates are selected by original retrieval score, not by corpus order, whenever candidate count exceeds `top_k`.

## Batch Size and Memory

Symptom: CUDA out-of-memory, CPU memory spikes, slow reranking, or process termination.

Cause: Cross-encoders and MonoT5 score query-document pairs jointly, so memory grows with model size, sequence length, and `batch_size`.

Fix:

- Reduce `batch_size` first.
- Reduce `top_k` to limit candidate pairs.
- Prefer smaller cross-encoder checkpoints for broad benchmark sweeps.
- For MonoT5, use smaller checkpoints or CPU-safe test subsets before full reranking.

## Model Downloads and Optional Dependencies

Symptom: model initialization hangs, fails with network errors, or cannot import wrapper dependencies.

Cause: CrossEncoder uses `sentence-transformers`; MonoT5 uses Hugging Face Transformers and torch; both may download weights on first use.

Fix:

- Preload or cache model weights in the target environment.
- Verify package extras before the reranking run.
- Use `scripts/rerank_smoke.py` to separate BEIR reranking mechanics from model availability.
- Avoid treating download failures as BEIR data or result-shape bugs.

## MonoT5 Token Errors

Symptom: MonoT5 fails when indexing true/false token ids or produces unusable scores.

Cause: `token_false` and `token_true` are missing or do not exist in the tokenizer vocabulary.

Fix: Pass the checkpoint-specific token strings. Common examples include `▁false`/`▁true`, `▁no`/`▁yes`, or language-specific alternatives such as `▁não`/`▁sim`.

## Re-Evaluation After Reranking

Symptom: Metrics appear incomparable before and after reranking.

Cause: Different candidate depths or `k_values` are used.

Fix:

- Use the same qrels and `k_values` for before/after comparisons.
- Ensure `top_k` is at least as large as the largest k you care about.
- Remember that recall at depths above the reranked candidate count cannot improve beyond the truncated candidate set.

## Hard Usability Cases To Test

- A retrieval result contains `d-missing`, which is absent from `corpus`; the user should get a clear preflight diagnosis instead of blaming the model.
- A query has four retrieved docs, but `top_k=2`; the user should see that only the two highest original retrieval scores are sent to `predict` and returned.
