# Backtesting workflows

## Purpose

Use this file when the task is to compare Orbit models with rolling or expanding backtests, inspect the split scheme, collect predictions, or score a forecast with one or more metrics.

## When to use `TimeSeriesSplitter`

Use the splitter directly when you only need fold construction or a visual split summary. When you pass `date_col`, the splitter still slices by discrete position and uses the datetime labels mainly for readable fold summaries and plots.

Typical triggers:

- "show me the train/test windows"
- "how many folds do I get with this horizon"
- "compare expanding vs rolling windows"
- "check the split scheme before fitting"

### Minimal pattern

```python
from orbit.diagnostics.backtest import TimeSeriesSplitter

splitter = TimeSeriesSplitter(
    df=df,
    date_col="week",
    min_train_len=100,
    incremental_len=20,
    forecast_len=20,
    window_type="expanding",
)

print(splitter.n_splits)
print(splitter.get_scheme())
for train_df, test_df, scheme, split_key in splitter.split():
    print(split_key, len(train_df), len(test_df))
```

### Rolling vs expanding

- `window_type="expanding"` keeps the first observation fixed and grows the training window.
- `window_type="rolling"` keeps the window length fixed and moves the start forward.

When `n_splits` is supplied, the splitter derives `min_train_len` from the full length, the forecast horizon, and the step size.

### Visualizing the scheme

Call `splitter.plot()` or `backtester.plot_scheme()` to see the train/test bars for every fold. Use `show_index=True` when you want numeric indices instead of formatted dates.

## When to use `BackTester`

Use `BackTester` when you want to fit a model on each split, gather predictions, and score them with Orbit's metric utilities. The backtester deep-copies the supplied model for each fold, so the model object should be deepcopy-safe and expose `fit(train_df)` plus `predict(df)`. It also reads `date_col` and `response_col` from the model to build the backtest dataframe.

Typical triggers:

- "run a rolling backtest"
- "score the forecast on each fold"
- "compare multiple metrics without refitting"
- "retrieve fitted models for each split"

### Minimal pattern

```python
from orbit.diagnostics.backtest import BackTester
from orbit.diagnostics.metrics import smape, wmape

bt = BackTester(
    model=model,
    df=df,
    min_train_len=100,
    incremental_len=20,
    forecast_len=20,
    window_type="rolling",
)

bt.fit_predict()
pred_df = bt.get_predicted_df()
score_df = bt.score(metrics=[smape, wmape])
print(score_df)
```

### Two-phase use

`fit_predict()` is the expensive step. Run it once, then call `score()` as many times as needed with different metric sets. If you leave `metrics=None`, Orbit uses its built-in list: `smape`, `wmape`, `mape`, `mse`, `mae`, and `rmsse`.

### Retrieving artifacts

- `get_predicted_df()` returns all split predictions and training rows.
- `get_fitted_models()` returns the deep-copied fitted models, one per split.
- `get_scheme()` returns the fold metadata list.
- `get_splitter()` returns the splitter object if you want to inspect or plot it.

### Split output columns

The backtest prediction dataframe always includes:

- `date`
- `split_key`
- `training_data`
- `actual`
- `prediction`

If the fitted model emits intervals or component columns, they are preserved.

## Custom metrics

Orbit accepts simple metric callables without extra glue code.

### Supported signatures

- `metric(actual, prediction)`
- `metric(test_actual, test_prediction, train_actual)`
- `metric(test_actual, test_prediction, train_actual, train_prediction)`

### Good example

```python
def mse_naive(test_actual):
    actual = test_actual[1:]
    prediction = test_actual[:-1]
    return ((actual - prediction) ** 2).mean()
```

### Training metrics

Set `include_training_metrics=True` only for metrics that use the simple `actual`/`prediction` signature. The training-side evaluation skips metrics that require train/test-specific arrays.

## Comparing models

A common pattern is to backtest each candidate model separately, then concatenate the resulting score tables with a model label column.

For horizon-by-horizon comparison, reshape the resulting metric table into a dataframe with `model`, `pred_horizon`, and a metric column, then feed it to `metric_horizon_barplot()`.

## Useful checks before scoring

- Ensure the dataframe is ordered by time before fitting or plotting.
- Ensure the forecast horizon is positive.
- Ensure the split configuration leaves enough rows for both training and test.
- If using `date_col`, make sure the column exists and is parseable as datetime.
