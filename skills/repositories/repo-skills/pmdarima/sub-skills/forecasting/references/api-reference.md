# Forecasting API reference

This reference describes the public forecasting surface represented by the inspected pmdarima package. Keep examples small and verify behavior in the active runtime before depending on backend-specific details.

## Evidence and provenance

The operating facts were extracted from the tagged v2.1.1 source anchor (`ARIMA`
implementation and validation in `pmdarima/arima/arima.py` and
`pmdarima/arima/_validation.py`; automatic search in `auto.py`; differencing
helpers in `utils.py`, `seasonality.py`, and `stationarity.py`). Behavior was
cross-checked against the focused ARIMA/auto/seasonality/stationarity tests,
README/quickstart examples, and the no-successful-model and seasonal-
differencing guidance. The verified inspection environment returned the
signatures below but reported installed version `0.0.0`; this mismatch remains
explicit and is not normalized into a v2.1.1 runtime claim.

## `ARIMA`

```python
pmdarima.ARIMA(
    order,
    seasonal_order=(0, 0, 0, 0),
    start_params=None,
    method="lbfgs",
    maxiter=50,
    suppress_warnings=False,
    out_of_sample_size=0,
    scoring="mse",
    scoring_args=None,
    trend=None,
    with_intercept=True,
    **sarimax_kwargs,
)
```

- `order=(p, d, q)` contains non-seasonal AR lag order, ordinary differencing order, and MA order. Values are non-negative integers.
- `seasonal_order=(P, D, Q, m)` contains seasonal AR order, seasonal differencing order, seasonal MA order, and the number of observations per cycle. The default has no seasonal component. Use `m > 1` only when the sampling frequency has a defensible seasonal cycle; `m=1` disables seasonal differencing/search in `auto_arima`.
- `with_intercept=True` includes the intercept by default for fixed `ARIMA`; `trend` can be passed to the underlying state-space model. Do not add a duplicate constant column to `X`.
- `method` selects the scipy optimizer (the inspected implementation accepts values such as `lbfgs`, `newton`, `nm`, `bfgs`, `powell`, `cg`, `ncg`, and `basinhopping`). `maxiter` bounds fit iterations, but it does not guarantee convergence.
- `suppress_warnings` controls many statsmodels warnings; do not use it as a substitute for checking fit quality.
- `out_of_sample_size` reserves tail observations for scoring and then incorporates them into the fitted state. It must be less than the number of observations; this is validation behavior, not a replacement for a separate holdout design.

Primary methods:

```python
model.fit(y, X=None, **fit_args) -> model
model.predict(
    n_periods=10, X=None, return_conf_int=False, alpha=0.05, **kwargs
)
model.predict_in_sample(
    X=None, start=None, end=None, dynamic=False,
    return_conf_int=False, alpha=0.05, **kwargs
)
model.update(y, X=None, maxiter=None, **kwargs) -> model
```

`fit` expects finite one-dimensional `y`; `X`, when present, is a two-dimensional exogenous array with one row per `y` observation. `predict` returns an array of shape `(n_periods,)`. With `return_conf_int=True`, it returns `(forecast, conf_int)`, where `conf_int` has shape `(n_periods, 2)` and `alpha` is the non-covered probability (for example, `alpha=0.05` targets 95% intervals). `n_periods` must be an integer. A model fitted with `X` requires future `X` for prediction, with exactly `n_periods` rows and the trained number of columns.

`predict_in_sample` returns fitted/in-sample predictions. `start` and `end` are inclusive observation positions (or supported non-integer labels when `y` was a pandas Series with an object-like index). For integer `start`, values below `d` are invalid. With `dynamic=True`, later in-sample predictions use forecasts instead of observed lags; confidence intervals are not available for dynamic mode, so the implementation warns and uses `dynamic=False` when intervals are requested.

After fitting, useful delegated methods include `summary()`, `resid()`, `fittedvalues()`, `params()`, `pvalues()`, `aic()`, `aicc()`, `bic()`, `hqic()`, `conf_int()`, and `plot_diagnostics(variable=0, lags=10, fig=None, figsize=None)`. Residuals are an inspection signal, not proof of forecast validity. Check their length/finite values and use an appropriate downstream autocorrelation or whiteness check if required.

## `auto_arima` and `AutoARIMA`

Verified call signatures in the inspection environment:

```python
pmdarima.auto_arima(
    y, X=None, start_p=2, d=None, start_q=2, max_p=5, max_d=2,
    max_q=5, start_P=1, D=None, start_Q=1, max_P=2, max_D=1,
    max_Q=2, max_order=5, m=1, seasonal=True, stationary=False,
    information_criterion="aic", alpha=0.05, test="kpss",
    seasonal_test="ocsb", stepwise=True, n_jobs=1,
    start_params=None, trend=None, method="lbfgs", maxiter=50,
    offset_test_args=None, seasonal_test_args=None,
    suppress_warnings=True, error_action="trace", trace=False,
    random=False, random_state=None, n_fits=10,
    return_valid_fits=False, out_of_sample_size=0, scoring="mse",
    scoring_args=None, with_intercept="auto", sarimax_kwargs=None,
    **fit_args
) -> ARIMA or list[ARIMA]
```

```python
pmdarima.arima.AutoARIMA(
    start_p=2, d=None, start_q=2, max_p=5, max_d=2, max_q=5,
    start_P=1, D=None, start_Q=1, max_P=2, max_D=1, max_Q=2,
    max_order=5, m=1, seasonal=True, stationary=False,
    information_criterion="aic", alpha=0.05, test="kpss",
    seasonal_test="ocsb", stepwise=True, n_jobs=1,
    start_params=None, trend=None, method="lbfgs", maxiter=50,
    offset_test_args=None, seasonal_test_args=None,
    suppress_warnings=True, error_action="trace", trace=False,
    random=False, random_state=None, n_fits=10,
    out_of_sample_size=0, scoring="mse", scoring_args=None,
    with_intercept="auto", **kwargs
)
```

`AutoARIMA.fit(y, X=None, **fit_args)` delegates order search to `auto_arima` and stores the selected fitted `ARIMA` in `model_`. Its `predict`, `predict_in_sample`, `update`, and `summary` delegate to that selected model. The standalone function returns one fitted `ARIMA` by default; `return_valid_fits=True` returns the sorted valid fits rather than one model.

Search controls:

- `d` and `D`: set ordinary and seasonal differencing explicitly when domain evidence is stronger than tests; leave `None` to estimate them. `max_d` and `max_D` bound estimates.
- `max_p`, `max_q`, `max_P`, `max_Q`, and `max_order`: bound search cost. `max_order` limits the combined non-seasonal/seasonal AR and MA orders when non-stepwise search is used.
- `seasonal=True, m=k`: search seasonal models at period `k`. `seasonal=False` makes the validation layer set the internal period to zero; `m` should not be used to imply seasonality in that mode.
- `stepwise=True` is the practical default. `stepwise=False` permits random/exhaustive candidate generation and can be much more expensive; if `random=True`, use a fixed `random_state` and positive `n_fits`.
- `information_criterion` accepts `aic`, `aicc`, `bic`, `hqic`, or `oob`. `oob` requires a nonzero `out_of_sample_size`; otherwise the implementation warns and falls back to AIC.
- `error_action` accepts `warn`, `raise`, `ignore`, `trace`, or `None`. Use `trace` during diagnosis, `ignore` only when failed candidates are expected and the final result will still be checked.
- `trace` controls search logging; higher values show more candidate detail. `suppress_warnings` only affects warnings from fitting/search and can hide useful signals.

## `StepwiseContext`

```python
pmdarima.arima.StepwiseContext(max_steps=None, max_dur=None)
```

Use it as a context manager around a stepwise call. `max_steps` must be an integer from 1 through 1000. `max_dur` must be positive seconds and is a soft duration limit. Nested contexts combine their effective limits. When a limit is reached, the best model found so far is returned with a warning; treat that as a bounded search result, not evidence of global optimality.

```python
from pmdarima import StepwiseContext, auto_arima

with StepwiseContext(max_steps=20, max_dur=30):
    model = auto_arima(
        y, seasonal=True, m=12, stepwise=True,
        max_p=2, max_q=2, max_P=1, max_Q=1,
        error_action="trace", suppress_warnings=False,
    )
```

## Cross-link: observation updates

`ARIMA.update` and `AutoARIMA.update` append newly observed values and refit from existing parameters for additional iterations. For production update policy, persistence, serialization, or artifact compatibility, hand off to `persistence-update`; retain only the shape rule here: if the original fit used exogenous `X`, update requires matching `X` rows and the same feature count.
