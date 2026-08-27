# Time-Series Troubleshooting

Use this guide for AutoGluon forecasting failures after package-level install/import checks have passed. For installation, version, and backend checks, use the root troubleshooting reference.

## Schema and Construction Errors

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `data must have a item_id column` | Flat input lacks `item_id`, or the real series key has another name | Pass `id_column="..."` or rename the column before `TimeSeriesDataFrame`. |
| `data must have a timestamp column` | Flat input lacks `timestamp`, or date column has another name | Pass `timestamp_column="..."` or rename before construction. |
| Timestamp dtype error | Timestamp values were not parsed as pandas datetime | Use `pd.to_datetime(raw["timestamp"])`; check invalid/null values. |
| `item_id` dtype error | IDs are floats, mixed objects, null, or unsupported dtype | Cast IDs to string or integer and remove nulls. |
| MultiIndex name error | Indexed frame levels are not exactly `item_id` and `timestamp` | Rename index levels before constructing `TimeSeriesDataFrame`. |
| Iterable construction error | Items do not contain `target` and pandas `Period` `start` | Convert each item to `{ "target": values, "start": pd.Period(..., freq=...) }`. |

Bundled validator:

```bash
python sub-skills/time-series-forecasting/scripts/validate_timeseries_frame.py --input data.csv --id-column sku --timestamp-column date --target demand
```

## Irregular or Missing Frequency

Symptoms:

- `ts_df.freq` is `None`.
- `infer_frequency(raise_if_irregular=True)` raises an error.
- `predictor.fit` reports an expected data frequency issue.

Fixes:

1. Sort and validate: `ts_df = ts_df.sort_index()`.
2. If the data should be regular, resample with `ts_df.convert_frequency("D")` or the appropriate pandas alias.
3. Fill missing values created by resampling with `fill_missing_values()` or a domain-specific imputation.
4. If the user wants AutoGluon to resample all predictor inputs, construct `TimeSeriesPredictor(freq="D", ...)`.
5. Avoid mixing items with different natural frequencies in one predictor unless they can be resampled to a common frequency.

## Series Too Short

Symptoms:

- Many items ignored during `fit`.
- Validation split errors.
- Poor leaderboard because few series survive filtering.

Rules:

- With default `num_val_windows=1`, series with length `<= 2 * prediction_length` are ignored.
- With more validation windows, threshold is `<= (num_val_windows + 1) * prediction_length`.
- Internal validation also needs at least `max(prediction_length + 1, 5)` training observations per fold.

Fixes:

- Reduce `prediction_length`.
- Reduce `num_val_windows` or use explicit `tuning_data`.
- Drop or separately handle very short items.
- Aggregate to a coarser frequency only if it does not make series too short.

## Known Covariates Missing at Prediction

Symptoms:

- `predict` fails after a predictor was created with `known_covariates_names`.
- Future covariate frame has missing rows or columns.

Fix:

```python
future = predictor.make_future_data_frame(train_data)
future["promotion"] = planned_values
future["holiday"] = future["timestamp"].dt.weekday.isin([5, 6]).astype(int)
predictions = predictor.predict(train_data, known_covariates=future)
```

Checklist:

- Training data includes every declared known covariate column.
- Prediction `known_covariates` includes every declared column.
- Future frame covers all forecast `item_id`/`timestamp` combinations.
- Covariate values have compatible dtypes; convert categorical covariates to `category`, string, or object dtype when appropriate.

## Static Feature Index Mismatch

Symptoms:

- Error listing item IDs missing from `static_features`.
- Static features silently disappear after slicing a single item.
- Integer-coded categories behave like continuous values.

Fixes:

```python
static = static_df.set_index("item_id")
missing = ts_df.item_ids.difference(static.index)
assert missing.empty, missing.to_list()
static["store_type"] = static["store_type"].astype("category")
ts_df.static_features = static
```

- Include every item in the static-feature index.
- Drop or ignore extra static rows only after confirming they are not needed.
- Reattach static features after manual pandas operations that lose `TimeSeriesDataFrame` metadata.

## Predictor Path and Save/Load Issues

- `TimeSeriesPredictor(path=...)` expects a local directory for model artifacts. S3-style predictor paths are warned as unsupported.
- Use `predictor.save()` and `TimeSeriesPredictor.load(path, require_version_match=True)` for persistence.
- If load fails after moving machines, first verify AutoGluon versions and optional dependencies through root package troubleshooting, then check whether the selected model family needs torch, statsforecast, transformers, Chronos, or GPU backends.

## Chronos, Chronos-2, and Toto Failures

Common causes:

- Network access is unavailable but pretrained weights are not cached.
- Hugging Face-compatible model paths are blocked or private.
- CUDA is unavailable for a model requiring GPU.
- Torch/transformers/Chronos optional packages are missing or incompatible.
- Time limit is too short for model download, initialization, fine-tuning, or inference.

Fixes:

- For no-network CPU workflows, switch to `hyperparameters={"Naive": {}, "SeasonalNaive": {}, "Theta": {}, "ETS": {}}` or `presets="fast_training"`.
- Use `chronos2_small` or `bolt_tiny` only when model artifacts and backend dependencies are confirmed.
- Avoid `Toto` unless the user has a CUDA-compatible GPU and the required model artifacts.
- Fine-tune Chronos/Chronos-2 only with enough series/history and a realistic time limit.

## Metrics Look Wrong

- Leaderboard scores for losses are often negative because AutoGluon ranks higher-is-better.
- `MAPE` and `SMAPE` are poor choices for zero, sparse, or intermittent demand.
- `MASE`, `RMSSE`, and `SQL` rely on historical seasonal errors and can be undefined for constant series.
- If the user cares about prediction intervals, choose quantile metrics (`WQL` or `SQL`) and inspect quantile columns.
- If different horizons have different business values, use `horizon_weight` with length equal to `prediction_length`.

## Feature Importance Surprises

- Importance estimates require a fit predictor and meaningful covariate/static feature columns.
- `method="permutation"` is more robust but slower; `method="naive"` is faster for rough diagnostics.
- Foundation models may ignore or use covariates differently, so compare feature importance by model when needed.
- If `relative_scores=True`, interpret values relative to baseline score rather than absolute metric units.

## Renamed Columns, Missing Future Covariates, and Static Mismatch Case

For a user dataset with `sku`, `date`, `sales`, planned promotions, and item metadata:

1. Build with `TimeSeriesDataFrame.from_data_frame(raw, id_column="sku", timestamp_column="date")`.
2. Set `target="sales"` on `TimeSeriesPredictor`.
3. Validate `static_features` covers exactly all item IDs.
4. Create `future = predictor.make_future_data_frame(train_data)` and fill every known covariate for the future horizon.
5. Run the bundled validator with `--id-column sku --timestamp-column date --target sales --known-covariates promotion --static-features static.csv --prediction-length H` before fitting.
