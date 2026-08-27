# Evaluation and backtesting troubleshooting

## Quick symptom map

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Cannot extract prediction target since the index of forecast is outside the index of target` | Forecast start/frequency/horizon does not match the target index. | Check `entry["start"]`, dataset frequency, target length, `forecast.start_date`, and `forecast.index`; use `make_evaluation_predictions` for trailing holdout. |
| `ts_iterator has more elements than fcst_iterator` or the reverse | One iterator was consumed, filtered, or generated from a different dataset. | Materialize both iterators once, compare lengths, and preserve dataset order. |
| `num_series=... did not match number of elements=...` | The optional count was stale or a one-shot iterator yielded fewer elements. | Omit `num_series` until debugging is complete, or pass `len(forecasts)` after materializing. |
| Forecast contains `NaN` values | Model emitted invalid mean or requested quantiles; quantile forecast lacks required keys; upstream data produced invalid samples. | Keep `allow_nan_forecast=False` for strict runs, inspect `forecast.mean` and `forecast.quantile(q)`, then repair the model/data or explicitly allow NaNs only for diagnosis. |
| Aggregate metrics contain `nan` or `inf` | Zero target scale, zero seasonal error, all-masked labels, or invalid item metrics. | Inspect item metrics: `abs_target_sum`, `seasonal_error`, `num_masked_target_values`, `MASE`, `MAPE`, `MSIS`; consider `aggregation_strategy=aggregate_valid` for reporting valid numeric items. |
| `MASE` or `MSIS` is unexpectedly `nan`/`inf` | Seasonal error denominator is zero or unavailable. | Pass explicit `seasonality`, use longer/nonconstant history, or report that scaled metrics are undefined for constant/too-short series. |
| Metrics look shifted by one horizon | Forecasts were generated from full targets instead of history-only inputs, or target iterator contains the wrong window. | Use `make_evaluation_predictions` or `split(...).generate_instances(...)`; assert `forecast.index.equals(target.index[-prediction_length:])` for no-lead-time holdouts. |
| Item metrics have wrong or missing `item_id` | Predictor did not propagate item ids, or input entries omitted `item_id`. | Include `item_id` in dataset entries when item-level traceability matters. |
| Multiprocessing hangs or pickling fails | Default `num_workers` is too high or a custom metric is not process-pickleable. | Use `Evaluator(num_workers=0)` while debugging; increase workers only for large, stable workloads. |
| `gluonts.ev` metric raises a key error such as `0.5` or `mean` | Requested metric needs a forecast quantile or mean that the forecast object cannot provide. | Ensure `SampleForecast` has samples or `QuantileForecast` includes needed keys; choose metrics matching available forecast fields. |
| `backtest_metrics` returns poor results on training data | It was given a dataset whose trailing horizon is not a real holdout or whose predictor was trained/leaked incorrectly. | Evaluate on a proper test dataset containing full target history plus holdout; train estimators before calling `backtest_metrics`. |

## Alignment debugging checklist

Before calling `Evaluator`, run these checks:

```python
forecasts = list(forecast_it)
targets = list(target_it)
assert len(forecasts) == len(targets)

for i, (forecast, target) in enumerate(zip(forecasts, targets)):
    if not forecast.index.isin(target.index).all():
        raise AssertionError((i, forecast.index, target.index))
    if len(forecast.index) != len(forecast.mean):
        raise AssertionError((i, len(forecast.index), len(forecast.mean)))
```

For a simple no-lead-time trailing holdout, also check:

```python
assert forecast.index.equals(target.index[-prediction_length:])
```

If this fails, inspect whether the predictor has `lead_time`, the dataset was split with the same `prediction_length`, and the target index frequency matches the forecast frequency.

## NaNs and invalid labels

`Evaluator(ignore_invalid_values=True)` masks invalid target values but does not silently accept invalid forecasts. By default, forecast NaNs raise `ValueError`.

Recommended posture:

1. Keep `allow_nan_forecast=False` for production-quality checks.
2. If diagnosing a broken model, rerun with `allow_nan_forecast=True` and inspect item metrics.
3. If target labels contain `NaN` or `inf`, keep `ignore_invalid_values=True` and report `num_masked_target_values`.
4. If a metric denominator is zero, report the metric as undefined instead of hiding it.

## Frequency and seasonality

GluonTS derives default seasonality from the forecast frequency string. This can surprise users for unusual frequencies or tiny synthetic datasets.

Use explicit seasonality when:

- The series is shorter than the natural seasonal period.
- The data has a task-specific seasonality different from the timestamp frequency default.
- Constant histories make `seasonal_error` zero and scaled metrics become undefined.
- The timestamp frequency is custom or ambiguous.

Example:

```python
evaluator = Evaluator(seasonality=7, num_workers=0)
```

For local seasonal-naive predictors, keep `season_length` and evaluator `seasonality` conceptually aligned but remember they affect different steps: `season_length` controls the forecast, while `seasonality` controls scaled metric denominators.

## Quantile and interval failures

MSIS uses `alpha/2` and `1 - alpha/2` quantiles. Default `alpha=0.05` therefore requests `0.025` and `0.975`. `SampleForecast` can derive these from samples; `QuantileForecast` must be able to provide or interpolate them. A `QuantileForecast` with only a `mean` key cannot supply meaningful quantiles and may lead to NaNs or forecast-validation failure.

When using `Evaluator(quantiles=...)`, make sure every requested quantile is valid and available from the forecast object. Decimal strings, floats, and percentile strings are accepted, but metric column names normalize to strings such as `Coverage[0.5]`.

## Target length mismatch

A test dataset item must contain at least enough history plus the forecast horizon. With `make_evaluation_predictions`, the withheld window is `prediction_length + lead_time`; if the target is too short, the predictor may receive too little context, and seasonal metrics may be undefined.

For split-generated windows, keep one shared variable:

```python
prediction_length = 24
# Use the same prediction_length in split instance generation and predictor construction.
test_data = test_template.generate_instances(prediction_length=prediction_length)
predictor = estimator.train(training_data)  # estimator configured with prediction_length
assert predictor.prediction_length == prediction_length
```

## Aggregate strategy choices

- `aggregate_no_nan` drops `nan` item values but keeps `inf`; this is the default.
- `aggregate_all` propagates both `nan` and `inf` into aggregate metrics.
- `aggregate_valid` filters both `nan` and `inf` for numeric columns and can be useful for reporting valid items, but do not use it to hide systemic invalid data.

Always inspect item metrics and document how invalid values were handled.

## Optional and legacy backends

The selected verification scope covers installed core evaluation, local predictors, and selected PyTorch dependencies. CUDA is optional acceleration and not needed for evaluation. MXNet-based examples are legacy/unverified here; do not promise MXNet evaluation behavior unless the user provides a compatible MXNet environment and asks for a separate check.
