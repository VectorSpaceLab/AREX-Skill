# Forecasting troubleshooting

Use the smallest recovery change that addresses the observed symptom. Preserve the original error, chosen parameters, sample length, package/environment provenance, and whether the returned model was search-limited.

## Installation, import, and compiled-extension failures

**Symptoms**

- Installation fails, `import pmdarima` raises `ImportError`, or the error names `__check_build` / a missing compiled extension.
- `pmdarima.__file__` points at an unintended source checkout or a partially built tree.
- The source anchor is v2.1.1, but the active environment reports `pmdarima.__version__ == '0.0.0'`.

**Recovery**

- Run the root environment/provenance check and inspect `pmdarima.__file__`, Python, NumPy, SciPy, statsmodels, and the compiled-extension import before fitting. Repair or reinstall the prepared environment when build artifacts are absent; do not bypass `__check_build` or import source files as a runtime substitute.
- Treat a source-vs-installed version mismatch as unresolved provenance. Record both values and the active module path; verify signatures and a tiny fit in the actual runtime before making version-sensitive claims. The source checkout must not become a runtime dependency.
- If only plotting imports fail in a headless environment, keep plotting optional and use numeric diagnostics instead.

## Invalid `y`, `X`, or order arguments

**Symptoms**

- Fit rejects `y` because it is not a finite one-dimensional numeric series, or `X` because it is not two-dimensional, has non-finite values, or has a row mismatch.
- A constructor or `auto_arima` call rejects `order`, `seasonal_order`, `m`, `d`, `D`, or a start/max bound.

**Recovery**

- Convert `y` to a finite numeric vector and assert `y.ndim == 1`; handle missing values in the caller's preprocessing route rather than silently imputing here.
- Validate `X_train.shape == (len(y), n_features)` and, for a horizon `h`, `X_future.shape == (h, n_features)`. Keep feature order and any scaling identical between training and forecasting; do not add a duplicate constant when the model already has an intercept.
- Keep `order=(p,d,q)` and `seasonal_order=(P,D,Q,m)` as non-negative integer tuples, require `m > 0` for seasonal search, and ensure each `max_* >= start_*`. Use `error_action` only from `{warn, raise, ignore, trace, None}`.

## No viable model / candidate failures

**Symptoms**

- `ValueError: Could not successfully fit a viable ARIMA model to input data.`
- Auto search emits many candidate errors or returns no fit.
- Trace output mentions roots near the non-invertible boundary, non-stationarity, or statsmodels failures.

**Likely causes**

- Overly broad or high AR/MA orders relative to the series length.
- Near non-invertibility / unit-root behavior, numerical scaling, missing/non-finite input, or a simple polynomial after differencing.
- A seasonal order or differencing choice consumes the usable observations.

**Recovery**

1. Validate finite numeric `y`, record `len(y)`, and fit a bounded non-seasonal baseline such as `ARIMA(order=(0, 1, 0), seasonal_order=(0, 0, 0, 0))`.
2. Reduce `max_p`, `max_q`, `max_P`, `max_Q`, `max_d`, `max_D`, and `max_order`; use `stepwise=True` and a `StepwiseContext` limit.
3. Set `error_action='trace'`, `trace=2`, and temporarily `suppress_warnings=False` to identify candidate-specific failures. Use `error_action='ignore'` only after diagnosing expected bad candidates.
4. Try an explicitly lower differencing order (`d=0/1`, `D=0`) only when domain evidence supports it. If differencing makes the transformed data constant or polynomial, treat that as a data/model limitation, not a reason to increase order.
5. If convergence remains poor, try a different supported optimizer (`method`) or a bounded `maxiter`; do not call an unconverged result production-ready without residual/forecast checks.

## Non-convergence or near-boundary warnings

**Symptoms**

- Optimizer convergence warning, non-invertible roots warning, NaN/unstable parameters, or highly unstable intervals.
- Different starting values/optimizers yield materially different forecasts.

**Likely causes**

- Too many AR/MA terms, over-differencing, short history, constant/near-constant data, unscaled regressors, or a weakly identified seasonal model.

**Recovery**

- Fit a lower-order model and compare its residuals and forecast behavior.
- Reduce seasonal terms first (`P=Q=0`, then reconsider `D`), or use a non-seasonal baseline if history does not support a cycle.
- Increase `maxiter` modestly only after reducing model complexity; alternatively try `method='nm'` or `method='powell'` for diagnosis, knowing optimizer behavior and speed differ.
- Scale very large-magnitude exogenous columns consistently outside the model, keeping the same transformation for future `X`.
- Check `model.params()`, `model.resid()`, and `model.summary()`; warnings suppressed by `suppress_warnings=True` are still unresolved evidence.

## Seasonal `m` mistakes or seasonal differencing exhaustion

**Symptoms**

- `m must be a positive integer (> 0)`.
- `The seasonal differencing order, D=... was too large ... there are no samples remaining`.
- `There are no more samples after a first-order seasonal differencing` or stationarity-test linear algebra errors.

**Likely causes**

- `m` does not match the data cadence (for example, using 12 for a short quarterly-like sample).
- `D` is too high for the available history; a large `m` and `D` remove most/all rows.
- The seasonal test sees a seasonal unit root but the series has too few complete cycles.

**Recovery**

1. Confirm the observation frequency and choose `m` from that cadence. `m=1` means no seasonal cycle; do not infer `m` from horizon length.
2. Prefer a longer training history. As a lower-cost fallback, reduce `m`, set `D=0`, or use `seasonal=False` only when justified and documented; manually setting `D=0` skips a potentially useful test.
3. Reduce seasonal `P/Q` and set `max_D=1`; constrain `max_P/max_Q`. Check `len(y) - D*m - d` before expecting a complex seasonal model to work.
4. With exogenous regressors, verify that seasonal and ordinary differencing does not make a regressor constant or rank-deficient.

## Too-short series

**Symptoms**

- Stationarity/seasonality tests raise linear algebra or negative-dimension errors.
- No candidate fits after applying `d`/`D` and lags.
- Forecast appears to fit but is numerically fragile.

**Likely causes**

- Insufficient observations for the requested non-seasonal/seasonal lags and differencing, especially fewer than roughly two seasonal cycles.
- Exogenous feature count is large relative to history.

**Recovery**

- Collect more observations or use a simple low-order model (`p=q=P=Q=0`, low `d`, `D=0`).
- Disable seasonality for a short-history baseline and report that it cannot identify a cycle reliably.
- Reduce exogenous features and avoid fitting an intercept twice.
- For auto search, lower all maxima and use explicit `d`/`D` only with evidence. Do not treat `suppress_warnings=True` as a fix.

## Exogenous horizon or shape mismatch

**Symptoms**

- `When an ARIMA is fit with an X array, it must also be provided one for predicting or updating observations.`
- `X array dims (n_rows) != n_periods`.
- Update errors report mismatched sample or feature dimensions.

**Likely causes**

- Future `X` was omitted, has a row count different from `n_periods`, or has a different number/order of features.
- `y_new` and `X_new` have different row counts during update.

**Recovery**

- Validate `X_train.shape == (len(y), n_features)` before fit.
- Build or forecast `X_future` with shape `(horizon, n_features)` and pass `n_periods=horizon`.
- Preserve feature order, dtype, and any scaling/encoding. If covariates are not available for the horizon, remove exogenous modeling or create an explicitly documented scenario.
- For update, pass `X_new` whenever training used `X`; row count must equal `len(y_new)` and column count must equal training `X`.

## Invalid orders and search arguments

**Symptoms**

- `max_* must be >= start_*`, negative differencing/order errors, invalid `error_action`, or invalid `m`.
- Non-integer `n_periods` raises `TypeError`.

**Recovery**

- Keep `p,d,q,P,D,Q,m` non-negative/valid integers; ensure every `max_* >= start_*`.
- Use `max_order=None` only when you intentionally accept an unbounded combined-order search; otherwise keep it finite.
- Use `error_action` in `{warn, raise, ignore, trace, None}`.
- Pass an integer `n_periods`; check the returned forecast and interval shapes.

## Forecast shape and confidence intervals

**Symptoms**

- `predict` rejects a non-integer horizon, returns an unexpected tuple, or a downstream consumer sees the wrong length.
- Confidence intervals are absent or have an unexpected shape.

**Recovery**

- Pass a Python `int` `n_periods=h`; assert the forecast shape is `(h,)`. If `return_conf_int=True`, unpack `(forecast, conf_int)` and assert `conf_int.shape == (h, 2)` before consuming it.
- Confirm that `X` has exactly `h` rows for an exogenous forecast. Check finite values and retain the requested `alpha`; interval bounds are uncertainty estimates, not a forecast-accuracy guarantee.
- For in-sample intervals, do not combine `dynamic=True` with `return_conf_int=True`: the implementation warns and uses non-dynamic interval calculation. If behavior differs, rerun the tiny smoke script in the active environment.

## Optional plotting failures

**Symptoms**

- Diagnostic plotting fails in headless environments, a backend is unavailable, or `plot_diagnostics` blocks execution.

**Recovery**

- Treat plotting as optional. Use `resid()`, `fittedvalues()`, `predict_in_sample()`, `summary()`, and numeric assertions in automated/headless runs.
- If a plot is needed, select a non-interactive backend before importing pyplot and save it to a caller-controlled path. Never make a network-backed dataset or interactive `show()` call part of a smoke test.

## Provenance/version discrepancy

The source evidence was inspected at tag `v2.1.1` / commit `4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`, but the verified inspection environment reports `pmdarima.__version__ == '0.0.0'`. Record this discrepancy in reports and avoid making release-specific claims. If signatures or runtime behavior differ, treat the installed environment as the execution authority and escalate the mismatch to the root skill's environment/provenance handling.
