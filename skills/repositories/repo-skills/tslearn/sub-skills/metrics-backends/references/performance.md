# Performance Metrics

## Purpose

Read this for `tslearn.metrics.performance`: forecasting/regression-style error
metrics over time-series datasets. These are metric/evaluation helpers, not
estimator training workflows.

## APIs

| Function | Signature | Meaning |
| --- | --- | --- |
| `mae` | `mae(y_true, y_pred, ts_weights=None, timestamps_weights=None, multioutput="uniform_average")` | Mean absolute error over time series, timestamps, and dimensions. |
| `mse` | `mse(y_true, y_pred, ts_weights=None, timestamps_weights=None, multioutput="uniform_average")` | Mean squared error over the same axes. |
| `mase` | `mase(y_true, y_pred, train_data, seasonal_period=1, ts_weights=None, timestamps_weights=None, multioutput="uniform_average")` | Mean absolute scaled error, using in-sample `train_data` for the naive seasonal scaling denominator. |

## Input and weighting rules

- `y_true` and `y_pred` are normalized as time-series datasets, normally shaped
  `(n_ts, sz, d)` after conversion. Lists and univariate arrays are accepted if
  tslearn can convert them.
- `ts_weights` has shape `(n_ts,)` and weights the series axis.
- `timestamps_weights` has shape `(sz,)` and weights time positions.
- `multioutput` controls the feature axis:
  - `"uniform_average"` returns one scalar.
  - `"raw_values"` returns one value per feature dimension.
  - An array-like of shape `(d,)` performs a weighted feature average.
- These helpers are correctness/evaluation utilities. Do not use them as
  PyTorch training losses; use torch-native losses or `SoftDTWLossPyTorch` for
  autograd.

## MASE-specific caveats

`mase` divides MAE by the average absolute difference between `train_data` and
its `seasonal_period` lag. Therefore:

- `train_data` must cover the in-sample history, not just the forecast horizon.
- `seasonal_period=1` is the default one-step naive scale.
- If the training data is constant or the seasonal difference is zero, the
  denominator is zero; tslearn/numpy will warn about divide-by-zero and return
  `inf` for the scaled error.
- If `multioutput="raw_values"`, scaling is performed per feature; otherwise it
  is aggregated.

## Minimal examples

```python
from tslearn.metrics import performance

y_true = [[[1, 2], [2, 3], [3, 4]]]
y_pred = [[[0, 1], [1, 2], [2, 3]]]
train = [[[3, 4], [5, 5], [5, 6], [6, 7], [7, 8]]]

assert performance.mae(y_true, y_pred) == 1
assert performance.mse(y_true, y_pred) == 1
assert performance.mase(y_true, y_pred, train) == 1
raw_mae = performance.mae(y_true, y_pred, multioutput="raw_values")
```

For a no-download check that also exercises metric APIs, run
[`../scripts/metrics_smoke.py performance`](../scripts/metrics_smoke.py).
