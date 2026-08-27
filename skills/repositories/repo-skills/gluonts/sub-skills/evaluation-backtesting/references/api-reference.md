# Evaluation and backtesting API reference

This reference distills the installed GluonTS evaluation APIs needed by a future agent. It intentionally uses importable package names only and does not require opening source-checkout files.

## Classic evaluation APIs

| API | Import | Signature shape | Use when | Important behavior |
| --- | --- | --- | --- | --- |
| `Evaluator` | `from gluonts.evaluation import Evaluator` | `Evaluator(quantiles=(0.1,...,0.9), seasonality=None, alpha=0.05, calculate_owa=False, custom_eval_fn=None, num_workers=..., chunk_size=32, aggregation_strategy=aggregate_no_nan, ignore_invalid_values=True, allow_nan_forecast=False)` | You have aligned target series and forecast objects and need classic GluonTS metrics. | `Evaluator(...)` is callable: `agg_metrics, item_metrics = evaluator(ts_iterator, fcst_iterator, num_series=None)`. |
| `make_evaluation_predictions` | `from gluonts.evaluation import make_evaluation_predictions` | `make_evaluation_predictions(dataset, predictor, num_samples=100) -> (forecast_iterator, target_iterator)` | You have a test dataset containing full targets and a `Predictor`; you want trailing-holdout forecasts. | Strips the trailing `predictor.prediction_length + predictor.lead_time` points before prediction, then returns forecasts plus full target DataFrames for evaluation. |
| `backtest_metrics` | `from gluonts.evaluation import backtest_metrics` | `backtest_metrics(test_dataset, predictor, evaluator=Evaluator(...), num_samples=100, logging_file=None) -> (dict, DataFrame)` | You already have a predictor and want a one-call holdout evaluation. | Internally calculates dataset statistics, calls `make_evaluation_predictions`, evaluates, and optionally logs aggregate metrics to a file. It does not train an estimator. |
| `MultivariateEvaluator` | `from gluonts.evaluation import MultivariateEvaluator` | `MultivariateEvaluator(quantiles=..., seasonality=None, alpha=0.05, eval_dims=None, target_agg_funcs={}, custom_eval_fn=None, num_workers=None)` | Forecasts and targets are multivariate and dimensions require separate or aggregate metrics. | Produces dimension-prefixed metrics such as `0_MSE` plus vector-level metrics; can also compute `m_<agg>_<metric>` over aggregated target dimensions. |

### `Evaluator.__call__` contract

```python
agg_metrics, item_metrics = Evaluator(...)(
    ts_iterator,      # iterable of pandas Series/DataFrame targets
    fcst_iterator,   # iterable of gluonts.model.forecast.Forecast objects
    num_series=None, # optional expected count and progress total
)
```

Operational rules:

- The forecast iterator and target iterator must have the same number of elements and the same order. A mismatch raises an assertion such as `ts_iterator has more elements than fcst_iterator` or the reverse.
- Each target object's index must contain every timestamp in `forecast.index`. If not, extracting the prediction target raises an assertion that the forecast index is outside the target index.
- For MASE, MSIS, OWA, and seasonal-error-dependent metrics, provide target series with history before the forecast window. The iterator returned by `make_evaluation_predictions` already does this by returning full input-plus-label targets.
- Iterators are single-use. Materialize them once with `list(...)` if you need to inspect, save, and evaluate them more than once.
- `num_series`, when provided, must equal the number of forecast/target pairs.

## Trailing holdout behavior

`make_evaluation_predictions(dataset, predictor, num_samples=100)` uses the predictor's own horizon:

```python
window_length = predictor.prediction_length + predictor.lead_time
```

For each series, the predictor receives only the portion before that trailing window. The returned forecast starts at the first held-out period, while the returned target DataFrame contains the full target so `Evaluator` can both cut `forecast.index` and compute seasonal errors from the pre-forecast history.

Alignment invariants to check in custom code:

```python
assert len(forecast.index) == predictor.prediction_length
assert forecast.index.isin(target.index).all()
assert forecast.index[0] == target.index[-predictor.prediction_length]
assert forecast.index.equals(target.index[-predictor.prediction_length:])
```

The last assertion is appropriate for predictors without `lead_time`. If `lead_time > 0`, account for the gap between the prediction input and the forecast horizon.

## Metric outputs

### Aggregate metrics dictionary

Common keys from `Evaluator` include:

| Key | Meaning | Aggregation |
| --- | --- | --- |
| `MSE`, `RMSE`, `NRMSE` | Mean squared error and root/normalized forms using the mean forecast when available. | `MSE` is averaged across items; `RMSE` and `NRMSE` are derived after aggregation. |
| `abs_error`, `abs_target_sum`, `abs_target_mean` | Absolute error and absolute target scale terms. | Errors and target sums are summed; target mean is averaged. |
| `ND` | Normalized deviation: `abs_error / abs_target_sum`. | Derived after aggregation. |
| `MASE`, `MAPE`, `sMAPE`, `MSIS` | Scaled/percentage/symmetric/interval metrics. | Averaged across items. Zero denominators may yield `nan` or `inf`. |
| `QuantileLoss[q]`, `Coverage[q]` | Per-quantile loss and empirical coverage for each configured quantile. | Quantile loss is summed; coverage is averaged. |
| `wQuantileLoss[q]` | Weighted quantile loss divided by aggregate absolute target sum. | Derived after aggregation. |
| `mean_absolute_QuantileLoss`, `mean_wQuantileLoss`, `MAE_Coverage` | Average quantile-loss and coverage summaries across configured quantiles. | Derived after aggregation. |
| `OWA` | Overall weighted average when `calculate_owa=True`; otherwise `nan`. | Derived from naive-2 comparison metrics. |

### Item metrics DataFrame

`item_metrics` has one row per forecast/target pair. Typical columns include:

- `item_id` from the forecast, if present.
- `forecast_start` as the forecast's `pandas.Period` start.
- Base metrics such as `MSE`, `abs_error`, `abs_target_sum`, `abs_target_mean`, `seasonal_error`, `MASE`, `MAPE`, `sMAPE`, `MSIS`, and `num_masked_target_values`.
- Per-quantile columns such as `QuantileLoss[0.5]` and `Coverage[0.5]`.
- Any `custom_eval_fn` metric names.

Use item metrics to identify bad series, alignment mistakes, NaN-heavy labels, or items with zero target scale before trusting aggregate metrics.

## Evaluator configuration details

| Argument | Default | Practical guidance |
| --- | --- | --- |
| `quantiles` | `(0.1, 0.2, ..., 0.9)` | Accepts floats, decimal strings such as `"0.5"`, and percentile strings such as `"p50"`. Configure only the quantiles needed by the task to reduce item-metric columns. |
| `seasonality` | `None` | `None` derives seasonality from the forecast frequency. Set an integer explicitly for unusual frequencies, short histories, or task-specific seasonal scale. |
| `alpha` | `0.05` | Controls the interval width used by MSIS: lower quantile `alpha/2`, upper quantile `1 - alpha/2`. Ensure these quantiles can be obtained from the forecast. |
| `calculate_owa` | `False` | Adds OWA and is slower because it computes naive-2 comparison metrics. Enable only when needed. |
| `custom_eval_fn` | `None` | Dict of `name: [callable, aggregation, fcst_type]`, where `fcst_type` is usually `"mean"` or `"median"`. Callable receives `(target, forecast_array)`. |
| `num_workers` | CPU count | Use `0` or `None` for deterministic single-process evaluation and easier debugging. Multiprocessing is skipped on Windows. |
| `chunk_size` | `32` | Approximate per-worker chunk size when multiprocessing is active. Increase for many tiny series; reduce for memory-heavy forecasts. |
| `ignore_invalid_values` | `True` | Masks `NaN` and `inf` target values before metric computation. Set `False` only when invalid labels should propagate. |
| `allow_nan_forecast` | `False` | If `False`, `NaN` in forecast mean or requested quantiles raises `ValueError`. If `True`, evaluation warns and continues. |
| `aggregation_strategy` | `aggregate_no_nan` | Options include `aggregate_no_nan`, `aggregate_all`, and `aggregate_valid`. `aggregate_valid` filters both `nan` and `inf` from numeric item metrics. |

## Newer `gluonts.ev` metrics

GluonTS also exposes lower-level metric definitions under `gluonts.ev.metrics` and model-level helpers under `gluonts.model`:

```python
from gluonts.model import evaluate_forecasts, evaluate_model
from gluonts.ev.metrics import MSE, RMSE, NRMSE, ND, MASE, MSIS, WeightedSumQuantileLoss
```

| API | Use | Notes |
| --- | --- | --- |
| `gluonts.model.evaluate_model(model, test_data, metrics, axis=None, batch_size=100, mask_invalid_label=True, allow_nan_forecast=False, seasonality=None)` | Let a predictor generate forecasts for `test_data.input` and evaluate them with `gluonts.ev` metric definitions. | Marked experimental in the installed API; returns a pandas DataFrame. |
| `gluonts.model.evaluate_forecasts(forecasts, test_data, metrics, axis=None, ...)` | Evaluate forecasts you already generated for a `TestData` object. | Forecasts must align exactly with `test_data.label`. |
| `gluonts.ev.evaluate(metrics, data_batches, axis=None)` | Manually update metric definitions over batches of NumPy arrays. | Requires data keys such as `label`, `mean`, `0.5`, and `seasonal_error`. |

Metric definitions are instantiated classes, not already-computed values. Pass a list to `evaluate_model` or `evaluate_forecasts`, for example:

```python
metrics = [
    MSE(),
    RMSE(),
    NRMSE(),
    ND(),
    WeightedSumQuantileLoss(0.5),
]
```

Axis semantics for `evaluate_model`/`evaluate_forecasts`:

- `axis=None`: aggregate over all available axes and return scalar metrics.
- `axis=0`: aggregate over the dataset axis but keep time or target-dimension structure.
- `axis=1`: aggregate over the first data dimension, often forecast time for univariate data, and keep per-item rows.
- `axis=()` or omitting all axes in a tuple: keep element-level metric arrays.

Forecast access is by string key. `BatchForecast` requests arrays such as `forecast["mean"]`, `forecast["0.5"]`, or `forecast["0.9"]`; if a forecast cannot provide a requested key, metric computation fails or yields invalid values.
