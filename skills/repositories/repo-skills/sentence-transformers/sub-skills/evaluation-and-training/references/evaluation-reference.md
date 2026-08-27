# Evaluation Reference

Use evaluators both before and after training. The pre-training score is the baseline; the best or final score is meaningful only as a delta from that baseline.

## Shared rules

- Import evaluators from the model-type-specific evaluation package.
- Build the evaluator before training and call it once before `trainer.train()`.
- Set `metric_for_best_model` to the exact trainer metric key, usually `eval_{evaluator.primary_metric}`.
- Use a lightweight evaluator during frequent training evals and a heavier in-domain evaluator at milestones or after training.
- Use `SequentialEvaluator` when multiple metrics matter; make sure the first or configured main score is the metric that should drive checkpoint selection.
- Keep `save_steps` aligned with `eval_steps` when `load_best_model_at_end=True`.

## Dense `SentenceTransformer` evaluators

Import from `sentence_transformers.sentence_transformer.evaluation`.

| Task | Evaluator | Typical best-model key |
| --- | --- | --- |
| Fast retrieval benchmark | `NanoBEIREvaluator` | `eval_NanoBEIR_mean_cosine_ndcg@10` |
| In-domain retrieval with qrels | `InformationRetrievalEvaluator` | `eval_{name}_cosine_ndcg@10` |
| STS / continuous similarity | `EmbeddingSimilarityEvaluator` | `eval_{name}_spearman_cosine` |
| Binary pair classification | `BinaryClassificationEvaluator` | inspect `primary_metric` |
| Triplet accuracy | `TripletEvaluator` | inspect `primary_metric` |
| Reranking with bi-encoder scores | `RerankingEvaluator` | inspect `primary_metric` |
| Embedding distillation | `MSEEvaluator`, `MSEEvaluatorFromDataFrame` | inspect `primary_metric` |
| Paraphrase mining | `ParaphraseMiningEvaluator` | inspect `primary_metric` |
| Cross-lingual alignment | `TranslationEvaluator` | inspect `primary_metric` |
| Classification head accuracy | `LabelAccuracyEvaluator` | inspect `primary_metric` |

`NanoBEIREvaluator` is the fast retrieval default during training. `InformationRetrievalEvaluator` is better for your own corpus, queries, and qrels but can be expensive because it re-encodes the corpus.

Example shape for in-domain IR:

```python
evaluator = InformationRetrievalEvaluator(
    queries={qid: text for qid, text in queries},
    corpus={doc_id: text for doc_id, text in corpus},
    relevant_docs={qid: set(doc_ids) for qid, doc_ids in qrels.items()},
    name="dev-ir",
    ndcg_at_k=[10],
    mrr_at_k=[10],
)
metric_for_best_model = "eval_dev-ir_cosine_ndcg@10"
```

For Matryoshka training, evaluate each target dimension with separate evaluators and drive checkpoint selection from the dimension that matters most for deployment.

## `CrossEncoder` evaluators

Import from `sentence_transformers.cross_encoder.evaluation`.

| Task | Evaluator | Typical best-model key |
| --- | --- | --- |
| Fast reranking benchmark | `CrossEncoderNanoBEIREvaluator` | `eval_NanoBEIR_R100_mean_ndcg@10` |
| Custom query/candidate reranking | `CrossEncoderRerankingEvaluator` | `eval_{name}_ndcg@10` |
| Binary pair classification | `CrossEncoderClassificationEvaluator` with `num_labels=1` | `eval_{name}_average_precision` |
| Multi-class pair classification | `CrossEncoderClassificationEvaluator` with `num_labels>=2` | `eval_{name}_f1_macro` |
| Continuous pair scoring | `CrossEncoderCorrelationEvaluator` | `eval_{name}_spearman` |

`CrossEncoderNanoBEIREvaluator` reranks BM25 top-K candidates. The metric key includes that K: `R100` for `rerank_k=100`, `R50` for `rerank_k=50`, and so on.

For custom reranking, pass samples shaped like:

```python
samples = [
    {"query": "...", "positive": ["gold document"], "documents": ["candidate 1", "candidate 2"]},
]
evaluator = CrossEncoderRerankingEvaluator(samples=samples, name="dev-rerank")
```

Decide `always_rerank_positives` deliberately. `True` isolates reranker quality by forcing positives into the candidate set. `False` reflects end-to-end retrieve-then-rerank quality because missed positives remain missed.

For reranker training, early stopping is strongly recommended because cross-encoders often regress after their peak checkpoint.

## `SparseEncoder` evaluators

Import from `sentence_transformers.sparse_encoder.evaluation`.

| Task | Evaluator | Typical best-model key |
| --- | --- | --- |
| Fast sparse retrieval benchmark | `SparseNanoBEIREvaluator` | `eval_NanoBEIR_mean_dot_ndcg@10` |
| In-domain sparse retrieval with qrels | `SparseInformationRetrievalEvaluator` | `eval_{name}_dot_ndcg@10` |
| STS / continuous sparse similarity | `SparseEmbeddingSimilarityEvaluator` | `eval_{name}_spearman_dot` |
| Binary pair classification | `SparseBinaryClassificationEvaluator` | inspect `primary_metric` |
| Triplet accuracy | `SparseTripletEvaluator` | inspect `primary_metric` |
| Sparse reranking | `SparseRerankingEvaluator` | inspect `primary_metric` |
| Sparse distillation | `SparseMSEEvaluator` | inspect `primary_metric` |
| Cross-lingual sparse alignment | `SparseTranslationEvaluator` | inspect `primary_metric` |
| Hybrid sparse + BM25 | `ReciprocalRankFusionEvaluator` | inspect `primary_metric` |

Sparse evaluators use dot product by default. They also report active-dimension metrics. Track both retrieval metrics and sparsity:

- `query_active_dims`: non-zero entries per query vector.
- `document_active_dims`: non-zero entries per document vector.

Healthy SPLADE-style values are often tens of active dimensions for queries and low hundreds for documents. Thousands of active dimensions usually means FLOPS regularization is too weak, even if nDCG improved.

## Metric-key checklist

Before training:

```python
print(evaluator.primary_metric)
```

Then set:

```python
metric_for_best_model = f"eval_{evaluator.primary_metric}"
```

If a `SequentialEvaluator` wraps multiple evaluators, inspect the returned metric dictionary from a baseline call and choose the exact key that should drive checkpoint selection.

## Evaluation cadence

- During training, prefer fractional `eval_steps=0.1` and `save_steps=0.1` for about ten evals/checkpoints per epoch.
- For expensive in-domain IR over large corpora, evaluate less often or only at the end; use NanoBEIR-style evaluators for frequent checks.
- For `eval_strategy="steps"`, always provide a non-empty `eval_dataset` if the trainer expects one; otherwise set `eval_strategy="no"` and use only the external evaluator calls.
- Keep `greater_is_better=True` for nDCG, MRR, recall, accuracy, F1, AP, and correlations. Only loss-like metrics should minimize.

## Baseline verdicts

At the end of a run, compare the selected metric to baseline:

- `WIN`: clear positive delta on the selected metric and no secondary metric collapse.
- `MARGINAL`: small positive delta or mixed metrics; suggest one controlled iteration.
- `REGRESSION`: selected metric below baseline or sparse active dimensions unhealthy.

For sparse runs, a metric win with dense-like active dimensions is not a clean win. Tune `SpladeLoss`/`FlopsLoss` regularization and re-run.
