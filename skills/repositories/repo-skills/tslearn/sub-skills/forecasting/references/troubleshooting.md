# Forecasting Troubleshooting

Use this when `VARIMA` or `AutoVARIMA` fails, is slow, or produces confusing behavior on variable-length datasets.

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ValueError: ... timestamps are required per TS` during `fit` | At least one series is shorter than the model minimum. For `VARIMA`, the minimum is `p + q + d + 1 + seasonal_period`. | Increase every series length, reduce `p`, `q`, or `d`, remove or shrink `seasonal_period`, or route data shaping to `../../data-preparation/`. |
| `ValueError: ... timestamps are required per TS` during `predict(X=...)` | The fitted model is valid, but the fresh prediction dataset has at least one series shorter than the fitted model's minimum. | Keep `X` as `None` to forecast fitted data, or provide a fresh dataset whose every series satisfies the fitted `VARIMA` rule, or the `AutoVARIMA.best_estimator_` rule, and feature count. |
| `AutoVARIMA(..., default_d_for_non_stationarity=None)` raises `ValueError: Maximum differencing order reached` | KPSS-based stationarity checks could not find an acceptable differencing order within `max_d`, and no fallback `d` was allowed. | Increase `max_d`, set `default_d_for_non_stationarity` to an acceptable fallback such as `0` or `1`, or choose a manual `VARIMA(p, d, q)`. |
| Statsmodels/KPSS warnings or NaN-related `ValueError` on very short, constant, or seasonal data | The stationarity test has too little usable data, especially when `seasonal_period` leaves an empty or nearly empty differenced series. Constant zero series can also make KPSS degenerate. | Use longer/non-degenerate data for `AutoVARIMA`, start with manual `VARIMA` for constant-smoke checks, or remove/shrink `seasonal_period`. |
| Seasonal model fails or forecasts do not use enough history | `seasonal_period` adds to the minimum-length rule and changes the modeled signal to `x_t - x_{t-seasonal_period}` before ARIMA differencing. | Confirm every real series is longer than the seasonal lag and preferably has multiple cycles. For tiny checks, use a small period such as `2` or disable seasonality. |
| Fit is slow, noisy, or appears not to converge when `q > 0` | Moving-average terms are optimized with SciPy's Nelder-Mead optimizer. Large `p/q` values and wide AutoVARIMA searches can be unstable on small data. | Start with smaller orders, reduce `max_p`/`max_q`, lower or raise `max_iter` deliberately, try `with_constant=False` for degenerate data, and set `verbose=1` or `verbose=2` to see model-search and optimizer progress. |
| `predict(X=...)` raises a shape/feature error | The fresh dataset has a different feature dimension from the fitted dataset. | Rebuild `X` so its final dimension matches `model.n_features_in_`, or refit on data with the intended feature dimension. |

## Debugging checklist

1. Count real timestamps per series after NaN padding; do not rely on the padded array length alone.
2. For `VARIMA`, compute `p + q + d + 1 + seasonal_period` before fitting.
3. For `AutoVARIMA`, inspect `model.best_estimator_` after fitting; its selected order controls predict-time limits.
4. Use manual `VARIMA` on constant data before asking `AutoVARIMA` to run KPSS-based stationarity checks.
5. Enable `verbose=1` on `AutoVARIMA` to see model search; use `verbose=2` when you also need child `VARIMA` optimizer logs.
