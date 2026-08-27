# AutoGluon Time-Series API Reference

This reference summarizes the AutoGluon time-series APIs a future agent usually needs. Prefer these package APIs over source-repo examples.

## Imports

```python
import pandas as pd
from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor
```

## `TimeSeriesDataFrame`

Constructor:

```python
TimeSeriesDataFrame(data, static_features=None, id_column=None, timestamp_column=None, num_cpus=-1)
```

Accepted `data` inputs:

- A pandas `DataFrame` with `item_id` and `timestamp` columns, or renamed columns specified through `id_column` and `timestamp_column`.
- A pandas `DataFrame` indexed by a two-level `MultiIndex` named exactly `item_id` and `timestamp`.
- A local or remote CSV/Parquet path with the same flat columns.
- An iterable of dictionaries with `target` and `start`, where `start` is a `pandas.Period`.

Convenience constructors:

```python
TimeSeriesDataFrame.from_data_frame(df, id_column=None, timestamp_column=None, static_features_df=None)
TimeSeriesDataFrame.from_path(path, id_column=None, timestamp_column=None, static_features_path=None)
TimeSeriesDataFrame.from_iterable_dataset(iterable_dataset, num_cpus=-1)
```

Useful properties and methods:

- `ts_df.item_ids`: unique item identifiers.
- `ts_df.num_items`: number of time series.
- `ts_df.num_timesteps_per_item()`: observations per item.
- `ts_df.freq`: fast inferred frequency or `None` for irregular data.
- `ts_df.infer_frequency(num_items=None, raise_if_irregular=False)`: robust frequency inference; returns `IRREG` or raises when requested.
- `ts_df.train_test_split(prediction_length, end_index=None, suffix=None)`: creates a horizon-aware split.
- `ts_df.slice_by_timestep(start_index=None, end_index=None)`: selects per-item time ranges by position.
- `ts_df.convert_frequency(freq, agg_numeric="mean", agg_categorical="first", num_cpus=-1, chunk_size=100)`: resamples each item to a regular frequency.
- `ts_df.fill_missing_values(method="auto", value=0.0)` and `ts_df.dropna(how="any")`: handle missing values after conversion/resampling.
- `ts_df.to_data_frame()`: returns a plain pandas `DataFrame` with the time-series index.
- `ts_df.get_model_inputs_for_scoring(prediction_length, known_covariates_names=None)`: splits past target context and future known covariates from a full test dataframe.

Validation facts:

- `item_id` values must be strings or integers and cannot be null.
- `timestamp` must convert to pandas datetime and cannot be null.
- MultiIndex input must have index names exactly `("item_id", "timestamp")`; the timestamp level must be datetime typed.
- Static features must be a pandas `DataFrame` or path. Their index, or an `item_id` column, must contain every item in the time-series frame. Extra static-feature rows are silently subset to the time-series items.
- If a non-default `id_column` or `timestamp_column` collides with an existing default column, AutoGluon renames the existing default column with a `__` prefix before using the requested column.

## `TimeSeriesPredictor`

Constructor:

```python
TimeSeriesPredictor(
    target=None,
    known_covariates_names=None,
    prediction_length=1,
    freq=None,
    eval_metric=None,
    eval_metric_seasonal_period=None,
    horizon_weight=None,
    path=None,
    verbosity=2,
    log_to_file=True,
    log_file_path="auto",
    quantile_levels=None,
    cache_predictions=True,
    label=None,
    **kwargs,
)
```

Important constructor behavior:

- `target` defaults to `"target"`; `label` is an alias. Do not pass both.
- `prediction_length` is the number of future time steps to forecast.
- `freq=None` asks AutoGluon to infer a frequency. Set `freq` when timestamps are irregular or when data should be resampled.
- `known_covariates_names` can be a string or list of strings, but cannot include the target column.
- Default `eval_metric` is `"WQL"`; default `quantile_levels` are `[0.1, 0.2, ..., 0.9]`.
- `path` must be local for predictor artifacts. S3-style predictor paths are warned as unsupported; save locally and upload separately if needed.

Core methods:

```python
predictor.fit(
    train_data,
    tuning_data=None,
    time_limit=None,
    presets=None,
    hyperparameters=None,
    hyperparameter_tune_kwargs=None,
    excluded_model_types=None,
    ensemble_hyperparameters=None,
    num_val_windows=1,
    val_step_size=None,
    refit_every_n_windows=1,
    refit_full=False,
    enable_ensemble=True,
    skip_model_selection=False,
    random_seed=123,
    verbosity=None,
)
```

- `train_data` accepts `TimeSeriesDataFrame`, pandas `DataFrame`, path, or string path.
- Series with length `<= (num_val_windows + 1) * prediction_length` are ignored during training.
- If `known_covariates_names` was set, training/evaluation data must include those columns aligned with the target history.
- Columns other than target and known covariates are treated as past covariates.
- Numeric/bool columns become continuous features; object/string/category columns become categorical features; other dtypes are ignored.
- If `tuning_data` is supplied, validation uses its last `prediction_length` rows per series, disables multi-window backtesting on `train_data`, sets `num_val_windows=0`, and sets `refit_full=False`.

```python
predictions = predictor.predict(data, known_covariates=None, model=None, use_cache=True, random_seed=123)
```

- Forecasts start after the end of each item in `data`.
- Returns a `TimeSeriesDataFrame` with one row per forecast horizon step per item.
- Output columns include `mean` and quantile columns named by quantile level strings such as `0.1`, `0.5`, `0.9`.
- If known covariates were declared, pass `known_covariates` containing at least the requested covariate columns for all forecast-horizon `item_id`/`timestamp` combinations.
- `predictor.make_future_data_frame(data)` creates the required future `item_id`/`timestamp` grid for filling known covariates.

```python
scores = predictor.evaluate(data, model=None, metrics=None, cutoff=None, display=False, use_cache=True)
leaderboard = predictor.leaderboard(data=None, cutoff=None, extra_info=False, extra_metrics=None, display=False, use_cache=True)
fi = predictor.feature_importance(data=None, model=None, metric=None, features=None, time_limit=None, method="permutation", subsample_size=50, num_iterations=None, random_seed=123, relative_scores=False, include_confidence_band=True, confidence_level=0.99)
predictor.save()
loaded = TimeSeriesPredictor.load(path, require_version_match=True)
```

Evaluation notes:

- `evaluate` and `leaderboard` need data with the actual future target values; by default they score the last `prediction_length` steps per series.
- Scores are reported so that higher is better in the leaderboard; loss metrics usually appear as negative scores.
- `feature_importance` is most useful when covariates or static features are present. Use `method="naive"` for a faster, less robust estimate and `method="permutation"` for the default perturbation-based estimate.

## Minimal Pattern

```python
raw = pd.DataFrame({
    "item_id": ["A"] * 8 + ["B"] * 8,
    "timestamp": list(pd.date_range("2024-01-01", periods=8, freq="D")) * 2,
    "target": [1, 2, 3, 4, 5, 6, 7, 8, 2, 3, 2, 4, 5, 5, 6, 7],
})
data = TimeSeriesDataFrame(raw)
train_data, test_data = data.train_test_split(prediction_length=2)
predictor = TimeSeriesPredictor(prediction_length=2, eval_metric="WQL", verbosity=0)
predictor.fit(train_data, hyperparameters={"Naive": {}, "SeasonalNaive": {}}, time_limit=30)
predictions = predictor.predict(train_data)
scores = predictor.evaluate(test_data)
```
