# Data Preparation Troubleshooting

## Missing required columns

Symptoms:
- A splitter, model, or metric reports a missing `userID`, `itemID`, `rating`, `timestamp`, or custom column.
- The bundled validator reports `missing_columns`.

Fix:
1. Rename user data into Recommenders defaults or pass custom `col_*` arguments everywhere.
2. Do not rename only for the splitter and then call a model/metric with defaults.
3. Re-run `validate_interactions.py` with matching `--user-col`, `--item-col`, `--rating-col`, and `--timestamp-col` options.

## Duplicate user-item rows

Symptoms:
- SAR may reject duplicated training rows.
- Metrics over-count repeated `(userID, itemID)` predictions.

Fix:
- Aggregate duplicates by the user's intended semantics: latest timestamp, max rating, mean rating, or count-as-strength.
- Keep the aggregation rule in the task notes because it changes evaluation meaning.

## Stratified split cannot satisfy every user or item

Symptoms:
- Empty train/test partitions for low-activity users.
- Errors or surprising row counts from stratified/chronological splitters.

Fix:
1. Count interactions per user/item.
2. Lower `min_rating`, filter sparse users/items deliberately, or switch to random split for a smoke test.
3. Tell the user that filtered-out cold-start entities are not evaluated.

## Timestamp problems

Symptoms:
- Chronological split fails because `timestamp` is absent or non-sortable.
- Time-aware evaluation looks random.

Fix:
- Use `python_chrono_split` only when timestamps are meaningful and sortable.
- If no timestamp exists, use random or stratified splitters and state that the evaluation is not time-aware.

## Dataset download/cache failures

Symptoms:
- HTTP errors, timeouts, corrupt ZIP files, or missing extracted files.

Fix:
1. Prefer a user-provided local cache or small fixture for initial work.
2. Use download helpers only after network and license constraints are acceptable.
3. If a ZIP is corrupt, delete the corrupt cached artifact and re-download when allowed.
4. Do not silently substitute a different dataset size/version.

## Spark splitter/import failures

Symptoms:
- `ModuleNotFoundError: pyspark`, Java gateway errors, or Spark session startup failures.

Fix:
- Install `recommenders[spark]` and verify Java/JDK plus PySpark before running Spark workflows.
- Use pandas splitters for CPU-only smoke tests, but do not count them as Spark verification.

## LibFFM conversion errors

Symptoms:
- Missing label/rating column.
- Feature mapping learned on one dataframe does not apply to another.

Fix:
- Fit the `LibffmConverter` on representative training columns.
- Keep train/test feature columns aligned.
- Decide how unseen categorical values should be handled before scoring.

## Sparse map-back mistakes

Symptoms:
- Mapped predictions contain wrong item ids or unexpected columns.

Fix:
- Preserve the `AffinityMatrix` object and mapping arrays from matrix creation.
- Use the correct `kind` in `map_back_sparse` for ratings versus predictions.
