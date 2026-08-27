# API reference

This sub-skill covers direct outlier / OOD scoring only.

## `OutOfDistribution`

Constructor signature:

```python
OutOfDistribution(params: Optional[dict] = None) -> None
```

### Supported parameter families

`params` is a single dictionary that must stay within one of these families:

- **Feature-based scoring**: `k`, `t`, `knn`
- **Pred-probability scoring**: `method`, `adjust_pred_probs`, `confident_thresholds`, `M`, `gamma`

### Feature-based scoring

Use this path when you have numeric embeddings or feature vectors.

- `fit(features=...)` learns a KNN graph or reuses a supplied `knn` estimator.
- `score(features=...)` reuses the fitted neighbor graph to score new rows.
- `fit_score(features=...)` is the convenience path for a single dataset.

Behavior notes:

- Scores are in `[0, 1]`.
- Smaller scores mean the point is less typical under the dataset.
- Distances are aggregated over KNN neighborhoods and then transformed into scores.
- The default neighbor metric depends on the feature dimension; the public router should still treat these as numeric embeddings, not structured/tabular fields.

### Pred-probability scoring

Use this path when you already have classifier probabilities.

- `fit(pred_probs=..., labels=...)` learns confident thresholds when adjustment is enabled.
- `score(pred_probs=...)` scores new rows using the cached thresholds, or directly if adjustment is disabled.
- `fit_score(pred_probs=..., labels=...)` is the convenience path for a single dataset.

Behavior notes:

- `method` can be `"entropy"`, `"least_confidence"`, or `"gen"`.
- `adjust_pred_probs=True` is the default and requires `labels` or precomputed `confident_thresholds`.
- `adjust_pred_probs=False` makes labels optional because no threshold adjustment is applied.
- `method="gen"` is intended for specialized advanced use; it is usually clearer to keep `adjust_pred_probs=False` with GEN.

### Ranking and thresholds

- Use `cleanlab.rank.find_top_issues(scores, top=n)` to return the lowest scores first.
- For outlier scoring, low values are the concerning ones.
- If you need a cutoff, choose one from the score distribution you trust, such as a percentile of a clean reference set.

### Datalab bridge

Datalab’s `outlier` issue type reuses the same scoring ideas but adds issue orchestration, thresholds, and dataset-level reporting. Use direct `OutOfDistribution` when you only need the score vector or ranking.
