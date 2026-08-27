# Data Formats and Schemas

## Purpose

Read this before mapping user data into Recommenders package functions. Most failures in data preparation come from column-name drift, missing timestamps, insufficient interactions for a chosen splitter, or assuming a sparse/LibFFM format when the data is still a long dataframe.

## Long-form interactions

The safest canonical format is one row per observed user-item interaction:

| userID | itemID | rating | timestamp |
|---|---|---:|---:|
| `u1` | `i1` | 5.0 | 1 |
| `u1` | `i2` | 4.0 | 2 |
| `u2` | `i1` | 3.0 | 1 |

Rules:

- `userID` and `itemID` can be strings or integers, but keep types stable across train, test, predictions, and metrics.
- `rating` should be numeric for rating prediction, SAR, sparse matrices, and most metric calls. For implicit data, use `1` or a chosen positive feedback value and document it.
- `timestamp` is required for chronological and time-decay workflows. If absent, use random or stratified splitters instead of inventing time order.
- Duplicate `(userID, itemID)` rows can break model assumptions. Aggregate or drop duplicates before fitting unless the chosen model explicitly supports repeated events.

## Prediction dataframes

A model prediction dataframe should usually contain:

| userID | itemID | prediction |
|---|---|---:|
| `u1` | `i3` | 0.82 |

For rating metrics, predictions should line up with true `(userID, itemID)` pairs. For ranking metrics, predictions can include candidate items per user and are usually top-k filtered before metric calculation.

## Train/test split readiness

Use this decision table:

| Situation | Preferred action |
|---|---|
| Tiny smoke fixture and no ordering requirement | `python_random_split` |
| User asks for time-aware validation or data has meaningful event time | `python_chrono_split` with `timestamp` |
| Each user or item must appear in train and test | `python_stratified_split` with `filter_by='user'` or `'item'` |
| Many users/items have fewer than `min_rating` interactions | filter with `min_rating_filter_pandas` or lower/narrow the split requirement |
| Spark dataframe or large cluster workflow | optional Spark splitters after `[spark]` and Spark runtime are verified |

## Negative sampling and candidate pairs

For implicit-feedback ranking or binary classification:

- Keep observed positives in a positive feedback column.
- Use `negative_feedback_sampler` to sample unobserved user-item pairs.
- Set `ratio_neg_per_user` or `n_neg_per_user` deliberately; too many negatives can dominate metrics and training.
- Keep sampled negatives out of held-out positives.

## Sparse matrices

Use `AffinityMatrix` when a downstream model expects a user-by-item matrix. Keep the original long dataframe because you often need it again for evaluation, filtering seen interactions, or mapping sparse outputs back to item ids.

## LibFFM rows

A field-aware factorization machine row typically contains:

```text
<label> <field>:<feature>:<value> <field>:<feature>:<value> ...
```

Use `LibffmConverter` instead of hand-writing the mapping. Validate that all columns used during `transform` were present or handled during `fit`.

## Text/content item data

Content-based TF-IDF workflows use item metadata with a stable id column plus one or more text columns:

| item_id | title | abstract |
|---|---|---|
| `paper-a` | `graph recommenders` | `collaborative filtering on graphs` |

Route model fitting and TF-IDF choices to the modeling sub-skill, but validate here that the id column is unique and text columns are not all empty.

## External datasets

MovieLens, Criteo, MIND, Amazon Reviews, CORD-19, and Wikidata helpers can fetch or query public resources. For reproducible or offline work:

- Prefer a user-supplied local cache path.
- Use a small fixture first.
- Record the dataset size/version and whether a download was required.
- Stop before network access if credentials, dataset licenses, or bandwidth are unclear.
