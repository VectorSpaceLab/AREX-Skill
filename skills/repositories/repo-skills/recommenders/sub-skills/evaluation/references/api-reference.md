# Evaluation API Reference

## Purpose

Read this for verified Recommenders metric function names, signatures, column defaults, and when each metric family is appropriate.

## Common columns

| Meaning | Default |
|---|---|
| User id | `userID` |
| Item id | `itemID` |
| True rating/relevance | `rating` |
| Predicted score | `prediction` |

True and predicted dataframes must use the same id columns and compatible dtypes. Most errors come from mismatched names or types.

## Rating metrics

Use these when the model predicts a numeric rating for known true pairs:

- `rmse(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction')`
- `mae(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction')`
- `rsquared(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction')`
- `exp_var(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction')`

## Classification metrics

- `auc(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction')`
- `logloss(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction')`

Use these when `rating` is a binary label and `prediction` is a probability-like score.

## Ranking metrics

Use these when each user has a ranked list of predicted item scores:

- `precision_at_k(rating_true, rating_pred, col_user='userID', col_item='itemID', col_prediction='prediction', relevancy_method='top_k', k=10, threshold=10, **_)`
- `recall_at_k(rating_true, rating_pred, col_user='userID', col_item='itemID', col_prediction='prediction', relevancy_method='top_k', k=10, threshold=10, **_)`
- `r_precision_at_k(...)`
- `ndcg_at_k(rating_true, rating_pred, col_user='userID', col_item='itemID', col_rating='rating', col_prediction='prediction', relevancy_method='top_k', k=10, threshold=10, score_type='binary', discfun_type='loge', **_)`
- `map(rating_true, rating_pred, ...)`
- `map_at_k(rating_true, rating_pred, col_user='userID', col_item='itemID', col_prediction='prediction', relevancy_method='top_k', k=10, threshold=10, **_)`

Important parameters:

- `relevancy_method='top_k'` treats the top `k` predicted items as relevant candidates.
- With `relevancy_method="by_threshold"`, `threshold` is a prediction-score cutoff: rows with `prediction < threshold` are dropped before the top-k cutoff.
- Recommenders' `precision_at_k` divides hits by `k`, not by the number of threshold-retained predictions. If fewer than `k` candidates remain, maximum precision can be below 1 even when every retained prediction is a hit.
- `score_type='binary'` for `ndcg_at_k` binarizes relevance; use raw relevance only when that is the intended metric.

## Top-k helper

- `get_top_k_items(dataframe, col_user='userID', col_rating='rating', k=10)` returns each user's top-k rows by a score column and adds rank information internally before returning the selected items.

Use it to trim predictions before reporting, but keep the untrimmed candidate set if another metric needs it.

## Diversity, novelty, and serendipity

The Python evaluation module also includes catalog coverage, distributional coverage, item novelty, user/item diversity, and serendipity helpers. These require item-feature or historical-interaction context beyond true/pred pairs. If a user asks for beyond-accuracy metrics, first confirm the available catalog and item-feature data.

## Error classes

- `ColumnMismatchError` indicates the compared dataframes do not have required columns or column sets.
- `ColumnTypeMismatchError` indicates required columns exist but have incompatible dtypes.

## Optional Spark evaluation

Optional Spark classes include:

- `SparkRatingEvaluation`
- `SparkRankingEvaluation`
- `SparkDiversityEvaluation`

Use them only after the Spark extra and runtime are verified. Do not call them in a base CPU-only environment.
