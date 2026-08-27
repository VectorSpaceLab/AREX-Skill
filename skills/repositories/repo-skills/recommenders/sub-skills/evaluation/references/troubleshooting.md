# Evaluation Troubleshooting

## ColumnMismatchError

Symptoms:
- A metric raises `ColumnMismatchError`.
- True and predicted dataframes look valid but use different names such as `user`, `item`, `score`.

Fix:
1. Rename columns to `userID`, `itemID`, `rating`, and `prediction`, or pass explicit `col_*` parameters.
2. For rating metrics, ensure predictions contain the same user-item pairs that exist in true data.
3. For ranking metrics, ensure predictions contain candidate item scores per user.

## ColumnTypeMismatchError

Symptoms:
- User or item ids are strings in one dataframe and integers in the other.

Fix:
- Cast id columns to the same dtype before calling metrics.
- Avoid casting item ids through floats; string ids are safer when ids may contain leading zeros.

## Ranking metric values are unexpectedly low

Likely causes:
- Training-seen items were not removed before recommending.
- `k` is too small or larger than available candidates per user.
- `by_threshold` prediction-score cutoff removes many candidates, so `precision_at_k` still divides by `k` and may be below 1 even when retained predictions are all hits.
- The test split removed many users/items through filtering.

Fix:
- Route to modeling to use `remove_seen=True` where available.
- Report `k`, candidate counts, and whether `threshold` is being used as a prediction-score cutoff.
- Revisit split/filter choices in data-preparation.

## nDCG confusion

Symptoms:
- nDCG differs from another implementation.

Fix:
- Check `score_type` (`binary` versus raw relevance) and `discfun_type`.
- Confirm whether recommendations are selected by top-k rank or by `by_threshold` prediction-score cutoff before top-k.
- Document the exact settings in the report.

## Duplicate predictions

Symptoms:
- Multiple rows for the same `(userID, itemID)` appear in predictions.

Fix:
- Deduplicate or aggregate predictions before metric calls.
- If duplicates come from model scoring candidate pairs, fix candidate generation upstream.

## Empty top-k output

Symptoms:
- Ranking metrics are zero or fail because a user has no predictions.

Fix:
- Check whether `remove_seen=True` removed all items for users with tiny catalogs.
- Increase candidate catalog size or evaluate only users with valid candidates.
- For a smoke test, use a fixture with unseen items per user.

## Spark metric failures

Symptoms:
- Missing `pyspark`, Java gateway errors, unresolved Spark functions/classes.

Fix:
- Install `recommenders[spark]`, verify Java/JDK and Spark session, and rerun Spark-specific checks.
- Do not count Python metric success as Spark verification.
