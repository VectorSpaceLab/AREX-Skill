# Time-series Forecasting API Reference

## Verified constructor

Installed-package inspection verified this `LazyForecaster` constructor shape
for Lazy Predict `0.3.0`:

```python
LazyForecaster(
    verbose=0, ignore_warnings=True, custom_metric=None, predictions=False,
    random_state=42, forecasters="all", cv=None, timeout=None,
    n_lags=10, n_rolling=(3, 7), seasonal_period=None, sort_by="RMSE",
    n_jobs=-1, max_models=None, progress_callback=None, use_gpu=False,
    foundation_model_path=None,
    tune=False, tune_top_k=5, tune_trials=30, tune_timeout=None,
    tune_metric="RMSE", tune_seasonal=False,
    horizon_strategy="recursive",
)
```

The main method is:

```python
scores, predictions_df = fcst.fit(y_train, y_test, X_train=None, X_test=None)
```

- `y_train` and `y_test` are ordered one-dimensional numeric arrays.
- The forecast horizon is `len(y_test)`.
- `X_train` and `X_test` are optional exogenous feature matrices aligned to the
  train and forecast periods.
- The method returns `(scores, predictions_df)`. The predictions DataFrame is
  empty unless `predictions=True`.

## Result columns

Forecast score tables include:

- `MAE`
- `RMSE`
- `MAPE`
- `SMAPE`
- `MASE`
- `R-Squared`
- `Time Taken`

When `cv` is set, cross-validation mean/std columns are added. `sort_by`
defaults to `RMSE`; lower error metrics sort ascending while `R-Squared` sorts
higher first.

## Model categories

Always available or base-friendly:

- `Naive`
- `SeasonalNaive`
- sklearn lag-feature models such as `LinearRegression_TS`, `Ridge_TS`,
  `Lasso_TS`, `ElasticNet_TS`, `KNeighborsRegressor_TS`, tree/forest/boosting
  sklearn variants, and `SVR_TS` depending on the installed package list.

Optional categories:

- `statsmodels` forecasters: `SimpleExpSmoothing`, `Holt`, Holt-Winters,
  `Theta`, `SARIMAX`.
- `pmdarima`: `AutoARIMA`.
- boosting extras: XGBoost, LightGBM, CatBoost time-series wrappers.
- PyTorch deep learning: `LSTM_TS`, `GRU_TS`.
- foundation model: `TimesFM`, with local weights recommended for offline use.

Select a small list with `forecasters=[...]` for deterministic tasks. Use
`max_models` only as a coarse smoke-test guardrail.

## Helper APIs

Important helper signatures verified from installed inspection and source:

```python
from lazypredict.ts_preprocessing import detect_seasonal_period, create_lag_features, recursive_forecast
from lazypredict.metrics import compute_forecast_metrics
from lazypredict.horizon import direct_forecast, multi_output_forecast
from lazypredict.ensemble import ensemble_simple_average, ensemble_weighted_average, ensemble_stacking
```

- `detect_seasonal_period(y)` estimates a seasonal period with autocorrelation
  and may return `None` for short or non-seasonal data.
- `create_lag_features(y, n_lags=10, n_rolling=(3, 7), X_exog=None)` converts a
  series into a supervised feature matrix.
- `compute_forecast_metrics(y_true, y_pred, y_train, seasonal_period=1)` returns
  `mae`, `rmse`, `r_squared`, `mape`, `smape`, and `mase`.
- `direct_forecast(...)` and `multi_output_forecast(...)` support alternative
  multi-step horizon strategies for sklearn-compatible estimators.

## Fitted forecasters

`LazyForecaster` stores fitted wrappers in `fcst.models` and errors in
`fcst.errors`. It exposes `provide_models()`, `predict(y_history, horizon,
model_name=None, X_test=None)`, `save_models(path)`, and `load_models(path)` for
reusing successful forecasters.
