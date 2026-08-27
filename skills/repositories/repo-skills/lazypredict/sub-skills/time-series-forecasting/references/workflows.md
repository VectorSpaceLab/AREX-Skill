# Time-series Workflows

## Quick start with a bounded model list

```python
import numpy as np
from lazypredict.TimeSeriesForecasting import LazyForecaster

np.random.seed(42)
t = np.arange(120, dtype=float)
y = 10 + 0.05 * t + 2 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 0.5, len(t))

y_train, y_test = y[:100], y[100:]
fcst = LazyForecaster(forecasters=['Naive', 'Ridge_TS'], n_lags=5, verbose=0)
scores, predictions = fcst.fit(y_train, y_test)
```

Use `predictions=True` when downstream work needs forecast values in a DataFrame.

## Exogenous variables

`X_train` must have `len(y_train)` rows and `X_test` must have `len(y_test)` rows:

```python
X = np.column_stack([np.sin(t), np.cos(t)])
scores, predictions = fcst.fit(y_train, y_test, X[:100], X[100:])
```

Exogenous features are used by SARIMAX/AutoARIMA when those optional packages
are installed and by ML lag-feature forecasters.

## Seasonal period

`seasonal_period=None` asks Lazy Predict to auto-detect seasonality. Override it
when domain knowledge is stronger:

```python
fcst = LazyForecaster(seasonal_period=12)  # monthly data with annual pattern
```

Set `seasonal_period=1` to effectively disable seasonal models.

## Cross-validation and custom metrics

```python
fcst = LazyForecaster(
    forecasters=['Naive', 'Ridge_TS'],
    cv=3,
    custom_metric=lambda y_true, y_pred: float(np.median(np.abs(y_true - y_pred))),
)
```

Cross-validation uses expanding-window splits and can multiply runtime. Keep
model lists small before using `cv` on large data.

## Horizon strategies

ML forecasters can use different strategies:

```python
LazyForecaster(horizon_strategy='recursive')     # default autoregressive loop
LazyForecaster(horizon_strategy='direct')        # one model per horizon step
LazyForecaster(horizon_strategy='multi_output')  # MultiOutputRegressor pattern
```

Use `direct` or `multi_output` when recursive error accumulation matters, but
expect more computation and stricter data-length requirements.

## Ensembles

After `fit(predictions=True)`, combine predictions:

```python
fcst = LazyForecaster(predictions=True, forecasters=['Naive', 'Ridge_TS'])
scores, pred_df = fcst.fit(y_train, y_test)

simple = fcst.ensemble(method='simple_average')
weighted = fcst.ensemble(method='weighted_average', y_true=y_test)
stacked = fcst.ensemble(method='stacking', y_true=y_test)
```

Stacking needs enough validation observations for a meta-model. Prefer simple or
weighted averages for tiny smoke fixtures.

## Diagnostics and plotting

If the optional plotting dependencies are installed, use:

```python
fig = fcst.plot_results(y_train=y_train, y_test=y_test, plot_type='forecast')
fig = fcst.plot_results(plot_type='comparison', metric='RMSE', top_k=10)
fig = fcst.plot_results(plot_type='residuals', model_name='Ridge_TS')
```

Diagnostics can be accessed through `fcst.diagnose(model_name, y_test)` and the
`lazypredict.ts_diagnostics` helpers.

## Save, load, and forecast again

```python
fcst.save_models('saved_forecasters')
fcst2 = LazyForecaster()
fcst2.load_models('saved_forecasters')
future = fcst2.predict(y_history=y_train, horizon=20, model_name='Ridge_TS')
```

Persisted wrappers depend on compatible versions of Lazy Predict, sklearn, and
any optional model packages used by the fitted forecasters.

## Foundation model and offline use

TimesFM requires the `foundation` extra and model weights. In air-gapped
environments, pre-download weights outside the critical workflow and pass their
local path with `foundation_model_path`. Do not let an agent assume network
access during a time-sensitive recovery task.
