# Forecasting workflows

This file gives the practical forecasting routes that users most often need.

## 1. End-to-end forecasting search

Use `TimeSeriesForecastingTask.search(...)` when you want Auto-PyTorch to optimize a forecasting pipeline and build the final model for you.

```python
from autoPyTorch.api.time_series_forecasting import TimeSeriesForecastingTask

api = TimeSeriesForecastingTask(seed=42)
api.search(
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
    optimize_metric="mean_MASE_forecasting",
    n_prediction_steps=3,
    freq="1Y",
    start_times=start_times,
    total_walltime_limit=60,
    func_eval_time_limit_secs=50,
)

pred = api.predict(test_sets)
```

Forecasting search usually uses `enable_traditional_pipeline=False` and depends on the forecasting extra.

## 2. Uni-variant versus multi-variant data

### Uni-variant

- `X_train=None`
- targets carry the sequence information
- good for pure target forecasting

### Multi-variant

- feature sequences are present
- use `series_idx` when your feature DataFrame stores series identifiers
- use `known_future_features` when some future covariates are available ahead of time

The validator returns sequence-aware outputs and preserves the order of the series.

## 3. Build the sequence layout correctly

The most important forecasting inputs are:

- `n_prediction_steps` — the forecast horizon
- `freq` — the time resolution or sampling frequency
- `start_times` — one start time per series
- `series_idx` — how to identify series inside a DataFrame
- `known_future_features` — feature columns that are already known in the future

If you give `series_idx`, make sure the feature DataFrame actually contains those columns.

## 4. Predict from prepared sequences or raw future features

`predict(...)` accepts either:

- a list of `TimeSeriesSequence` objects, or
- raw future-features input plus `past_targets`

When you use the raw-feature path, the task converts the inputs into `TimeSeriesSequence` objects internally.

## 5. Single configuration fitting

Use `get_dataset(...)`, `get_search_space(...)`, and `fit_pipeline(...)` when you want to test one forecasting configuration directly.

This route is useful when you want to:

- debug one encoder or decoder setup
- inspect a custom window size
- compare different loss or backbone choices
- check one model family without running the full AutoML search

## 6. Sliding-window and init-model tuning

Forecasting has a few extra tuning hooks that are more common than in tabular work:

- `suggested_init_models`
- `custom_init_setting_path`
- `search_space_updates` for window size and loader batch-related settings

These controls matter when the default sliding window is too short, too long, or not aligned with the problem's horizon.

## 7. Inspecting results

After the search, use the same task-level inspection helpers you would use in tabular workflows:

- `show_models()`
- `sprint_statistics()`
- `get_search_results()`

The output is still task-level, but the underlying predictions are shaped as a forecast horizon.

## 8. When to stop and read troubleshooting

Read `references/troubleshooting.md` if you hit:

- missing forecasting dependencies
- `Targets must be given!`
- `Multi Variant dataset requires X as input!`
- `X must be given as series_idx!`
- sequence-length or start-time mismatches
- sparse or classification targets in a forecasting task
