# Forecasting API Reference

This reference covers the forecasting surface owned by this sub-skill: `VARIMA` and `AutoVARIMA` from `tslearn.forecasting`, implemented by the `_arima` module.

## Verified public surface

| Symbol | Verified signature | Use |
| --- | --- | --- |
| `VARIMA` | `VARIMA(p=1, d=0, q=0, with_constant=True, seasonal_period=None, max_iter=50, verbose=0)` | Fit a chosen vector ARIMA model and forecast future timestamps. |
| `AutoVARIMA` | `AutoVARIMA(max_p=5, max_d=2, max_q=5, default_d_for_non_stationarity=0, seasonal_period=None, max_iter=50, verbose=0)` | Select a `VARIMA` order, fit it, and delegate forecasting to the selected model. |
| `VARIMA.fit` | `fit(self, X, y=None)` | Fit on a time-series dataset; `y` is ignored. |
| `VARIMA.predict` | `predict(self, X=None, n=1)` | Forecast `n` timestamps from fitted data or from a supplied fresh dataset. |
| `AutoVARIMA.fit` | `fit(self, X, y=None)` | Determine differencing, search candidate `VARIMA` models, and store `best_estimator_`. |
| `AutoVARIMA.predict` | `predict(self, X=None, n=1)` | Delegate to `best_estimator_.predict(X, n)`. |

Both estimators also expose `fit_predict(X, y=None, n=1)`, equivalent to `fit(X).predict(n=n)` when you do not need to keep intermediate control between fitting and forecasting.

## Input and output contract

- `X` is a time-series dataset with shape `(n_ts, sz, d)`.
- Variable-length datasets are accepted when shorter series are padded with trailing `NaN` values in the common-length array.
- The implementation converts inputs with `to_time_series_dataset`, computes per-series real lengths, and allows NaN padding.
- `predict(X=...)` must receive the same feature dimension `d` used at fit time.
- Forecast output shape is `(n_ts, n, d)`, where `n` is the forecast horizon.
- `predict(X=None, n=...)` forecasts from the fitted training data; `predict(X=fresh_data, n=...)` applies the fitted model to another valid dataset.

## Minimum-length rules

For `VARIMA`, every individual series must contain at least:

```text
p + q + d + 1 + seasonal_period
```

real timestamps, where `seasonal_period` contributes `0` when it is `None`.

This check is applied during `fit` and again during `predict(X=...)`. If any series is too short, the estimator raises a `ValueError` with text like `2 timestamps are required per TS`.

For `AutoVARIMA`:

- Fit starts with a seasonal-period guard and then performs KPSS-based differencing selection.
- The selected `best_estimator_` is a fitted `VARIMA`, so its `p + q + d + 1 + seasonal_period` rule is the effective predict-time minimum.
- Candidate `VARIMA` models that cannot be fitted because of length or configuration constraints can be skipped during model search.

## Fitted attributes and behavior

`VARIMA.fit` stores:

- `intercept_`
- `ar_coeffs_`
- `ma_coeffs_`
- `lle_`
- `n_ts_`, `n_samples_`, and `n_features_in_`

When `q > 0`, fitting optimizes moving-average terms with SciPy's Nelder-Mead optimizer. When `seasonal_period` is set, the model uses naïve seasonal differencing before ARIMA differencing.

`AutoVARIMA.fit` stores `best_estimator_`, a fitted `VARIMA` instance. Use `model.best_estimator_.p`, `.d`, `.q`, `.with_constant`, and `.seasonal_period` to inspect the selected model before interpreting forecast behavior.

## Smallest reproducible inputs

Use these sizes before scaling up:

- Known-order `VARIMA(1, 0, 0, with_constant=False)`: a variable-length constant random-walk dataset with three series and real lengths `[4, 3, 2]`; the model minimum is two timestamps.
- Fresh-dataset forecasting: after that fit, predict on a second variable-length constant random-walk dataset with real lengths `[3, 2]` and the same feature dimension.
- Fit-time minimum-length failure: call `VARIMA(1, 0, 0).fit(...)` on any series with only one real timestamp.
- Predict-time minimum-length failure: fit a `VARIMA(1, 0, 0)` on valid data, then call `predict(X=...)` with a one-timestamp series.
- Small `AutoVARIMA` smoke: use low-noise random walks with lengths `[7, 6, 5]` and a bounded search such as `AutoVARIMA(max_p=1, max_q=1, max_d=1, default_d_for_non_stationarity=0)`.
