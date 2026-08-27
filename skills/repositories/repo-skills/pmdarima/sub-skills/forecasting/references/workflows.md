# Forecasting workflows

The procedures below are intentionally bounded. Use a chronological holdout or rolling evaluation from the `model-selection` skill when comparing forecasts; this sub-skill only covers fitting and forecast generation.

These recipes adapt the repository's simple-fit and auto-ARIMA examples into
self-contained caller code. Their order, seasonal, exogenous, interval, and
update rules follow the inspected `ARIMA`/`auto_arima` implementations and
focused tests; no source checkout is needed at runtime.

## 1. Fixed-order forecast

Use this when domain evidence or an upstream selection step provides the order.

```python
import numpy as np
from pmdarima import ARIMA

y = np.asarray(y, dtype=float)
model = ARIMA(
    order=(1, 1, 1),
    seasonal_order=(0, 0, 0, 0),
    maxiter=100,
    suppress_warnings=False,
).fit(y)
forecast, interval = model.predict(
    n_periods=12, return_conf_int=True, alpha=0.05
)
assert forecast.shape == (12,)
assert interval.shape == (12, 2)
```

Prefer a modest order and inspect `model.summary()`, `model.aic()`, and `model.resid()` rather than silently increasing `p`, `d`, or `q`. Explicit differencing consumes observations; do not use high `d` merely to force a fit.

## 2. Seasonal fixed-order forecast

Choose `m` from the sampling cadence (for example, 12 for monthly annual seasonality or 4 for quarterly annual seasonality), not from the number of observations. A seasonal model is expressed as `(p,d,q)(P,D,Q)m`:

```python
from pmdarima import ARIMA

model = ARIMA(
    order=(1, 1, 0),
    seasonal_order=(0, 1, 1, 4),
    maxiter=100,
    suppress_warnings=False,
).fit(y)
forecast = model.predict(n_periods=4)
```

For a known seasonal cycle, check that the training history contains enough cycles to support the selected differencing and lags. If history is short, start with `D=0`, smaller seasonal orders, or a non-seasonal baseline and document the limitation instead of fitting a heavily seasonal model.

## 3. Automatic order search

Use explicit, small bounds first. The automatic procedure estimates `d` using `test` (default KPSS) and `D` using `seasonal_test` (default OCSB) when those orders are `None`. The selected model is ranked by `information_criterion` (AIC by default).

```python
from pmdarima import auto_arima

model = auto_arima(
    y,
    seasonal=True,
    m=12,
    start_p=0,
    start_q=0,
    max_p=2,
    max_q=2,
    start_P=0,
    start_Q=0,
    max_P=1,
    max_Q=1,
    max_d=1,
    max_D=1,
    max_order=5,
    stepwise=True,
    error_action="trace",
    suppress_warnings=False,
    trace=True,
    maxiter=50,
)
print(model.order, model.seasonal_order)
forecast, conf_int = model.predict(6, return_conf_int=True)
```

For deterministic bounded operations, wrap the call in `StepwiseContext(max_steps=..., max_dur=...)`. A time/step-limited result is the best candidate encountered before termination. For a non-stepwise random search, set `random_state` and `n_fits`; otherwise do not claim reproducibility.

Constant input is a special case: the implementation warns and returns an `(0,0,0)` non-seasonal ARMA-style fit. Treat this as a baseline result and validate that constant behavior is actually intended.

## 4. Exogenous regressors (`X`)

`X` is a regressor matrix, not a constant or trend column. Keep the feature order and count stable:

```python
import numpy as np
from pmdarima import ARIMA

n = len(y)
X_train = np.column_stack((np.arange(n), np.sin(np.arange(n) / 3.0)))
X_future = np.column_stack((
    np.arange(n, n + 5),
    np.sin(np.arange(n, n + 5) / 3.0),
))
model = ARIMA(order=(1, 0, 0), suppress_warnings=True).fit(y, X=X_train)
pred = model.predict(n_periods=5, X=X_future)
```

The fit requires `X_train.shape[0] == len(y)`. Future prediction requires `X_future.shape[0] == n_periods`; missing `X`, wrong rows, or wrong columns should be treated as input errors. For `auto_arima`, apply the same invariant. If future covariates are unknown, use a scenario or forecast for `X` outside this skill, or fit a model without exogenous variables.

## 5. In-sample fit and residual diagnostics

```python
fitted, fitted_interval = model.predict_in_sample(
    return_conf_int=True, alpha=0.05
)
residuals = np.asarray(model.resid(), dtype=float)
assert fitted.shape[0] == residuals.shape[0]
assert np.isfinite(residuals).all()
print(model.summary())
```

Use `predict_in_sample(dynamic=False)` for fitted values based on observed lagged values. Use `dynamic=True` only when simulating a recursively forecasted in-sample path; confidence intervals with dynamic mode are not supported by the implementation. `plot_diagnostics` is optional and backend/display dependent; in headless runs prefer numeric residual checks and avoid making plotting a required path.

Useful checks include residual mean/scale, finite values, obvious trend/seasonality remaining in residuals, and an appropriate autocorrelation/whiteness test. A low AIC or a successful optimizer does not establish that residuals are white or that intervals are calibrated.

## 6. New observations (handoff)

After observations arrive, a fitted model can call `update(y_new, X_new, maxiter=...)` and then forecast again. `X_new` must be present if the model was fit with exogenous variables, have the same number of columns, and have one row per new `y`. Route policy around persistence, artifact loading, and update safety to `persistence-update`.
