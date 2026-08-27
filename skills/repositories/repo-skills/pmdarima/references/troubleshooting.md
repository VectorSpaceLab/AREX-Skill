# Cross-cutting troubleshooting

Read this when a pmdarima workflow fails before a focused sub-skill gives a more
specific diagnosis.

## Install/import/build failures

- **`ImportError` from `pmdarima.__check_build` or a missing compiled symbol**:
  use a wheel for the target Python/platform, or install the documented build
  prerequisites (Python, NumPy, Cython, a compiler/build backend) before a
  source build. Do not debug ARIMA parameters until `import pmdarima` works.
- **Dependency resolver or binary ABI errors**: inspect `python --version`,
  `python -m pip show pmdarima numpy scipy pandas statsmodels`, and
  `python -m pip check` in the same environment. Recreate an isolated
  environment rather than upgrading a working project in place blindly.
- **Source tag and runtime version disagree**: a source build from this
  v2.1.1 checkout was observed to expose distribution metadata `0.0.0` in the
  private inspection environment. Treat `pm.__version__`, package metadata,
  and the intended release as separate facts; repair the build metadata or
  install a published release before making version-sensitive artifact claims.

## Data and API validation

- **`ValueError` for `y`**: check that the target is one-dimensional, finite,
  ordered, and long enough for requested differencing, seasonal lags, and
  holdout geometry. Handle missing values before pmdarima; do not silently
  interpolate without recording the policy.
- **Forecast-time `X` errors**: a model fit with `X` needs future rows for every
  forecast period and the same feature width/order. Validate `X_future.shape`
  before `predict`; for updates, append matching `X_new` rows.
- **Tuple or shape confusion**: transformer `fit_transform` often returns a
  `(y_transformed, X_transformed)` pair. `predict(..., return_conf_int=True)`
  returns `(forecast, interval)`. Assert shapes at route boundaries.
- **Seasonality appears wrong**: verify the observation frequency and set `m`
  to observations per cycle. `m` is not an arbitrary tuning knob or horizon.

## Search, convergence, and validation

- **No successful model / convergence warnings**: preserve the trace, reduce
  `max_p/max_q/max_P/max_Q/max_order`, use `stepwise=True`, bound `maxiter`,
  increase history, simplify differencing or seasonality, and test a fixed
  low-order baseline. Do not silently claim that a different fallback has the
  same specification.
- **Validation is optimistic**: use chronological train/test, rolling, or
  sliding splits; fit transforms inside the estimator/pipeline for each fold;
  never shuffle temporal rows or fit on future data.
- **A score is not comparable**: record horizon, fold geometry, metric
  direction, missing-value policy, exogenous availability, and whether the
  score is a raw fold value or an aggregate.

## Optional visualization

`plot_acf`, `plot_pacf`, `tsdisplay`, and decomposition plotting may require
Matplotlib and a usable backend. In a headless runner, set a non-interactive
backend before importing plotting APIs, or use the numeric diagnostics instead.
Do not make a forecast workflow depend on opening a GUI.

## Persistence and update

Read [persistence-update](../sub-skills/persistence-update/SKILL.md) before
loading an artifact. Pickle/joblib deserialization is code execution; load only
trusted files in a compatible environment. A version mismatch warning means
“verify or refit”, not “ignore”. Keep the old artifact until an updated model
passes a shape/value smoke check and write replacement artifacts atomically.
