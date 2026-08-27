# Evaluation Workflows

## Purpose

Use these recipes after a model has produced predictions or top-k recommendations. If the user has not created train/test data or predictions yet, route to data-preparation or modeling first.

## Rating prediction evaluation

```python
from recommenders.evaluation.python_evaluation import rmse, mae, rsquared, exp_var

rating_true = test[["userID", "itemID", "rating"]]
rating_pred = predictions[["userID", "itemID", "prediction"]]

scores = {
    "rmse": rmse(rating_true, rating_pred),
    "mae": mae(rating_true, rating_pred),
    "r2": rsquared(rating_true, rating_pred),
    "exp_var": exp_var(rating_true, rating_pred),
}
```

Use this when predictions correspond to held-out user-item pairs with numeric true ratings.

## Top-k ranking evaluation

```python
from recommenders.evaluation.python_evaluation import precision_at_k, recall_at_k, ndcg_at_k, map_at_k

ranking_scores = {
    "precision@10": precision_at_k(test, topk_predictions, k=10),
    "recall@10": recall_at_k(test, topk_predictions, k=10),
    "ndcg@10": ndcg_at_k(test, topk_predictions, k=10),
    "map@10": map_at_k(test, topk_predictions, k=10),
}
```

Checklist:

1. `topk_predictions` must contain `userID`, `itemID`, and `prediction`.
2. Remove training-seen items before evaluation when the task is recommending novel items.
3. Keep `k` no larger than the candidate list size per user unless you intentionally evaluate sparse output.
4. Decide whether recommendations are selected by top-k rank or a prediction-score `by_threshold` cutoff, and whether true relevance should be treated as binary or rating-valued for metrics such as nDCG.

## Classification-style evaluation

Use `auc` and `logloss` when the true column is a binary click/label and predictions are probabilities. Do not use them for arbitrary ranking scores unless they are calibrated to a probability-like scale.

## Beyond-accuracy metrics

For diversity, novelty, serendipity, and coverage:

1. Confirm the user has catalog metadata or item-feature vectors.
2. Confirm whether novelty is relative to the training interactions or a global popularity estimate.
3. Compute ranking metrics first; beyond-accuracy metrics are usually complementary, not replacements.

## Spark evaluation path

Use Spark evaluation only after `[spark]`, Java, and a Spark session are verified. Keep Python and Spark metrics separate in reports because dataframe semantics and runtime failure modes differ.

## Run the bundled tiny smoke

```bash
python sub-skills/evaluation/scripts/metrics_tiny_smoke.py --k 2
```

The script builds small true/pred dataframes, computes rating and ranking metrics, and asserts that all outputs are finite and in valid ranges. It is a skill helper, not a substitute for validating the user's actual data.

## Report template

When handing results to a user, include:

```text
Data split: random/chronological/stratified, ratio, filters
Prediction source: model and remove_seen setting
Metrics: names, k, prediction-score threshold if using by_threshold, relevancy method
Results: values with reasonable rounding
Caveats: cold-start filtering, duplicates removed, optional backend or skipped beyond-accuracy data
```
