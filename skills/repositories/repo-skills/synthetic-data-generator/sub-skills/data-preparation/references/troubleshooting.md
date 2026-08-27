# Data-preparation troubleshooting

## Metadata check failures

- `Primary Key ... not Exist in columns`: call `metadata.update_primary_key` with only columns in `metadata.column_list`.
- `Primary Key ... should has ID DataType`: add the primary key to `id_columns` or clear primary keys if the table has no true key for a single-table synthesis task.
- `Undefined data type for column ...`: inspect with broader inspectors or manually add the column to the correct `*_columns` set.
- `Found undefined column ...`: remove stale type entries after dropping/renaming columns.
- Invalid `categorical_encoder` or `categorical_threshold`: keys must be discrete column names or positive integer thresholds, and values must be one of `onehot`, `label`, or `frequency`.

## Datetime issues

`DatetimeInspector` can identify parseable object columns but format detection is conservative. `DatetimeFormatter` can remove datetime columns without a format. Always set a format for date columns you need preserved:

```python
metadata.datetime_format = {"event_date": "%Y-%m-%d"}
```

## Fixed and specific combinations

- Automatic fixed-combination detection uses covariance and one-to-one mapping heuristics. Tiny tables can over-detect numeric relationships.
- For semantic relationships, prefer explicit `specific_combinations`.
- If generated rows violate a relationship, inspect `metadata.get("specific_combinations")`, `metadata.get("fixed_combinations")`, and whether the relevant transformer was included.

## PII columns

PII generators remove detected PII columns before modeling and synthesize new values afterward. They do not prove privacy protection of the remaining columns. If a column is sensitive but not detected, manually classify it or remove it before fitting.

## Cache issues

- `GeneratorConnector` plus `NoCache` raises `DataLoaderInitError`; use `DiskCache`.
- If a CSV changed but cached parquet blocks persist unexpectedly, use a fresh `cache_dir` or clear cache through `loader.finalize(clear_cache=True)`.
- `DiskCache.load` requires chunksize to be a multiple of its blocksize.
