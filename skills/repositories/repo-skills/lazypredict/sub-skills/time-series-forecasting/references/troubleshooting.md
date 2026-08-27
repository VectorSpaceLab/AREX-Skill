# Time-series Troubleshooting

## Too little data for lag features

**Symptoms:** `InsufficientDataError`, empty lag matrix, or errors mentioning
`n_lags` and available observations.

**Likely cause:** ML forecasters need enough history to build lag and rolling
features. Large `n_lags` or rolling windows can consume most of a short series.

**Recovery:** lower `n_lags`, shrink `n_rolling`, start with `Naive` or
`SeasonalNaive`, and only add ML forecasters after the fixture passes.

## Exogenous shape mismatch

**Symptoms:** model errors during `fit()` or `predict()` when `X_train`/`X_test`
are supplied.

**Recovery:** assert these lengths immediately before calling `fit()`:

```python
assert len(X_train) == len(y_train)
assert len(X_test) == len(y_test)
```

Keep the same number and order of exogenous columns in train and forecast
periods.

## Missing optional forecasters

**Symptoms:** `AutoARIMA`, Holt/SARIMAX, XGBoost/LightGBM/CatBoost, LSTM/GRU, or
TimesFM does not appear or fails immediately.

**Likely cause:** optional extras are not installed. Base Lazy Predict does not
install every statistical, boosting, deep-learning, or foundation dependency.

**Recovery:** install only the needed extra (`timeseries`, `boost`,
`deeplearning`, or `foundation`) and re-run a small selected model list before
running `forecasters='all'`.

## Invalid sort or tuning metric

`sort_by` should name one of the forecast score columns, commonly `RMSE`, `MAE`,
`MAPE`, `SMAPE`, `MASE`, or `R-Squared`. Tuning metrics are similarly validated;
invalid values raise `ValueError` before fitting. Correct the metric string
before debugging models.

## GPU requested but not verified

`use_gpu=True` requests GPU parameters for supported optional model families.
Lazy Predict falls back for many paths when CUDA is unavailable. For a hard GPU
requirement, verify the exact backend package first: XGBoost/LightGBM/CatBoost,
PyTorch CUDA for LSTM/GRU or TimesFM, or other vendor packages as needed.

## TimesFM and offline weights

TimesFM may require a compatible Python version, optional package install, and
model weights. If the environment cannot download weights, pre-stage them and
use `foundation_model_path`. If no weights are available, route to base or
statistical forecasters instead of treating TimesFM failure as a full package
failure.

## Plotting failures

Plotting requires optional visualization dependencies. If `plot_results()` fails
with a matplotlib import error, install the `viz` extra or skip plotting and use
the returned `scores` and `predictions` DataFrames for text-only analysis.

## Empty prediction output

`predictions_df` is empty when `predictions=False`. Reconstruct the forecaster
with `predictions=True` before fitting if downstream ensemble, plotting, or
manual forecast inspection needs per-model predictions.

## Slow or unstable all-model runs

Time-series all-model sweeps may invoke optional statistical order searches,
boosting libraries, deep-learning models, or foundation models. For an agent
workflow, start with:

```python
LazyForecaster(forecasters=['Naive', 'Ridge_TS'], max_models=2, timeout=30)
```

Then add one model family at a time after the base fixture passes.
