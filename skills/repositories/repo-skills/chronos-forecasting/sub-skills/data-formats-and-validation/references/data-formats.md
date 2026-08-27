# Chronos data formats

Chronos-2 and the shared `df_utils` helpers accept a small set of predictable
input layouts. The key rule is that series are stored in **long format** unless
you are already using tensors or per-series dictionaries.

## 1) Long-format DataFrame inputs

Use a DataFrame when your data is arranged as one row per
`(series_id, timestamp)` pair.

### Required columns

| Role | Default name | Notes |
| --- | --- | --- |
| Series ID | `item_id` | Any hashable value repeated across rows for the same series. |
| Timestamp | `timestamp` | Must be datetime-like; parseable strings are accepted and normalized. |
| Target | `target` | One or more numeric target columns. |

Additional columns are treated as covariates.

### Common context schema

```text
item_id | timestamp | target | covariate_1 | covariate_2 | ...
```

### `future_df` schema

`future_df` is optional and is only for future covariates.

```text
item_id | timestamp | covariate_1 | covariate_2 | ...
```

Rules:
- `future_df` must contain the same series IDs as the context DataFrame.
- `future_df` must have exactly `prediction_length` rows per series.
- `future_df` must not contain target columns.
- `future_df` must not introduce new columns that are absent from the context DataFrame.
- Any column that appears in both `df` and `future_df` is treated as a known future covariate.
- Columns that appear only in `df` are past-only covariates.

If future values are not available, use `known_covariates_names` with
`from_data_frame` instead of `future_df`.

## 2) Frequency and ordering rules

Chronos expects every series to have a regular timestamp frequency.

- `normalize_df` coerces timestamps to datetime, keeps the first-appearance item
  order, and sorts timestamps within each series.
- `infer_freq_from_df` skips series shorter than 3 rows, infers frequency from
  the remaining regular series, and requires all qualifying series to agree.
- If no series has at least 3 regularly spaced observations, explicit `freq`
  must be supplied by the caller that generates future timestamps.
- `make_future_df` creates `prediction_length` timestamps after the last
  observed timestamp for each series, using the same item order as the context
  DataFrame.
- `future_df` item order may differ from the context order; Chronos normalizes
  it back to the context order before preprocessing.

When `validate_inputs=False`, the caller is responsible for already-normalized
frames and exact future-timestamp alignment.

## 3) Accepted preprocessing families

### Tensor / list-of-tensors

Use these when there are no covariates.

- `from_tensor`: expects shape `(n_series, n_variates, history_length)`.
- `from_list_of_tensors`: expects each element to be 1D or 2D.

All variates are treated as targets. Future covariate rows are NaN-filled.

### List of dicts

Use this when your source system already stores per-series arrays.

Each item should look like:

```python
{
  "target": ...,  # 1D or 2D history array
  "past_covariates": {"feat": ...},
  "future_covariates": {"feat": ...},
}
```

Rules:
- `target` is required.
- `past_covariates` and `future_covariates` must be dicts when present.
- All past covariates must share the same keys across series.
- Future covariate keys must be a subset of past covariate keys.
- A future covariate value may be `None` or empty to mean “known, but values unavailable”.

## 4) Output schema from `predict_df`

`Chronos2Pipeline.predict_df(...)` returns a DataFrame with:
- `id_column`
- `timestamp_column`
- `target_name`
- `predictions`
- one column per quantile level, named with the string form of the level
  (for example `0.1`, `0.5`, `0.9`)

For multivariate targets, rows are repeated per target column in target-list
order, and timestamps remain aligned to the generated future frame.
