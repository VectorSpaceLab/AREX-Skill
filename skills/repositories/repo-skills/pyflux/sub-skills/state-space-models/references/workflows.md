# Workflows

All workflows below are offline and synthetic. Use local pandas DataFrames; do not depend on live notebook data, web CSVs, or remote price feeds.

## 1) Gaussian local level / local trend

Use this when the series is continuous and a Kalman-style fit is appropriate.

1. Build a one-column DataFrame, e.g. a synthetic random walk plus noise.
2. Choose the concrete class directly or through a wrapper:
   - `pf.LLEV(df, target='y')`
   - `pf.LLT(df, target='y')`
   - `pf.LocalLevel(df, pf.Normal(), target='y')`
   - `pf.LocalTrend(df, pf.Normal(), target='y')`
3. Fit with `model.fit('MLE')` or `model.fit('M-H', nsims=...)` if you need Bayesian intervals.
4. Validate:
   - `summary()` prints finite latent variances.
   - `predict(h, intervals=True)` returns `h` rows.
   - `plot_fit(intervals=True)` and `plot_predict(h)` render without NaNs.
   - `predict_is(h)` returns the same horizon length.

## 2) Count-data local level / local trend

Use this for nonnegative counts or intensities.

1. Build a count DataFrame, e.g. Poisson draws with mild trend.
2. Route through the non-Gaussian path:
   - `pf.NLLEV(df, pf.Poisson(), target='y')`
   - `pf.NLLT(df, pf.Poisson(), target='y')`
   - or `pf.LocalLevel(df, pf.Poisson(), target='y')` / `pf.LocalTrend(df, pf.Poisson(), target='y')`
3. Fit with BBVI:
   - keep smoke checks short, e.g. `iterations=50` to `200`
   - use `print_progress=False` for cleaner validation
4. Validate:
   - latent-variable values are finite
   - `predict(h)` returns the requested horizon
   - `plot_predict(h, intervals=True)` is stable enough for a smoke check
   - do not expect the same interval behavior as the Gaussian path

## 3) Dynamic regression with exact formula alignment

Use this for time-varying coefficients on known regressors.

1. Build a DataFrame with explicit columns, for example `y`, `x1`, `x2`.
2. Instantiate the model:
   - `pf.DynReg('y ~ x1 + x2', data=df)` for Gaussian regression
   - `pf.NDynReg('y ~ x1 + x2', data=df, family=pf.Poisson())` for non-Gaussian regression
   - `pf.DynamicGLM(...)` when you want automatic dispatch.
3. Fit with `MLE` for Gaussian or BBVI for non-Gaussian.
4. Forecast with an `oos_data` frame that contains the same column names as the training frame and enough future rows for `h` steps. The response column may be `NaN`.
5. Validate:
   - `predict(h, oos_data=oos)` returns `h` rows
   - `predict_is(h)` works on the truncated prefixes
   - all formula names match exactly; if not, Patsy will fail before forecasting

## 4) Dynamic autoregression

Use this for a univariate series whose AR coefficients should drift over time.

1. Build a single-series DataFrame or array.
2. Instantiate `pf.DAR(data=df, ar=p, target='y')`.
3. Fit with `model.fit()`; the default is MLE.
4. Validate:
   - `predict(h)` returns `h` rows
   - `predict_is(h)` returns `h` rows
   - `x.summary(transformed=False)` is the better view if you need raw variance SEs
5. If the series is short, lower `ar` or provide more observations before differencing.

## 5) Wrapper dispatch check

Use this to confirm the selector picked the concrete class you wanted.

- `pf.LocalLevel(df, pf.Normal())` should behave as `LLEV`.
- `pf.LocalLevel(df, pf.Poisson())` should behave as `NLLEV`.
- `pf.LocalTrend(df, pf.Normal())` should behave as `LLT`.
- `pf.DynamicGLM(formula, df, pf.Normal())` should behave as `DynReg`.
- `pf.DynamicGLM(formula, df, pf.Poisson())` should behave as `NDynReg`.

Check `type(model).__name__` or `model.model_name` after construction if you need to assert the dispatch path.

## Validation checklist

- Forecast horizon matches `h`.
- No NaNs or infinities appear in the fitted latent variables or forecast outputs.
- Formula models receive a correctly named `oos_data` frame.
- BBVI runs are treated as smoke checks unless the iteration count is intentionally high.
- Finish by running the sectioned smoke helper: [`../../../scripts/smoke_pyflux_models.py --section state-space`](../../../scripts/smoke_pyflux_models.py).
