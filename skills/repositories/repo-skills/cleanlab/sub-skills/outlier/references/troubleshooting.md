# Troubleshooting

## Feature or probability shape errors

- **Feature vectors must be 2D.** `features` should have shape `(N, M)`.
- **Predicted probabilities must be 2D.** `pred_probs` should have shape `(N, K)`.
- **Row counts must match.** The number of examples in `features`, `pred_probs`, and `labels` must agree when they are used together.
- **Only one input family per call.** Do not pass both `features` and `pred_probs` in the same `fit`, `score`, or `fit_score` call.

## Labels for adjusted pred_probs scoring

- If `adjust_pred_probs=True` and you do not supply `confident_thresholds`, you must pass `labels` so cleanlab can estimate the thresholds.
- If you want a labels-free probability workflow, set `adjust_pred_probs=False`.
- If you already have thresholds, you can reuse them instead of recomputing them.

## KNN configuration problems

- `k` must be smaller than the number of examples in the feature set.
- If you pass a prefit `NearestNeighbors` object, its `n_neighbors` must be large enough for the requested `k`.
- If the metric seems odd, remember the default metric depends on the feature dimensionality; for custom behavior, provide your own KNN estimator.

## Score interpretation problems

- A **low** score is the warning sign; it means the point is less typical.
- A **high** score is usually fine and means the point looks in-distribution.
- Low scores are not hard errors. They are candidate outliers that should be inspected.
- If you need a shortlist, use `cleanlab.rank.find_top_issues(scores, top=n)`.

## Fit / score misuse

- `score(features=...)` needs a fitted neighbor graph first.
- `score(pred_probs=...)` only needs prior fitting when adjustment is enabled.
- Use `fit_score(...)` when you want one call for fitting and scoring the same dataset.
- For feature inputs, `fit_score(features=X)` and `fit(features=X); score(features=X)` should agree on the ranking, but may not be numerically identical. Compare the worst indices or sort order instead of exact arrays.

## GEN / advanced probability scoring

- `method="gen"` is an advanced option and works best when you know why you need it.
- If GEN behaves unexpectedly, try `adjust_pred_probs=False` first and compare against entropy-based scoring.

## When the task actually belongs elsewhere

- If you are doing a general dataset audit, switch to `datalab`.
- If you are cleaning label noise or doing dataset-health work, switch to `classification`.
- If the data is structured, tabular, or multiannotator, use the matching router for that task family.
