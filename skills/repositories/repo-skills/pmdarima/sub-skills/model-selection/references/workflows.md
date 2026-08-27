# Model-selection workflows

These workflows provide a reproducible, leakage-safe evaluation procedure for
pmdarima v2.1.1 at commit `4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`. Runtime
instructions are self-contained and do not link to a source checkout.

## 1. Fix the evaluation boundary

Before constructing a split, record:

- the chronological row order and observation frequency;
- finite numeric `y` and its length;
- `X` column order, meaning, row count, missing-value policy, and whether every
  test-time value is knowable at the forecast origin;
- production horizon `h`;
- the final untouched holdout interval and selection rule;
- a fixed estimator configuration and maximum fold/fit budget.

Take the final holdout off the end first. Tune split geometry, model settings,
and feature handling only on the earlier prefix. Do not use a target-derived
future feature, even if it is passed through `X` without an error.

## 2. Create one chronological holdout

```python
from pmdarima.model_selection import train_test_split

y_tune, y_final, X_tune, X_final = train_test_split(
    y, X, test_size=h)
assert len(y_tune) > 0
assert len(y_final) == X_final.shape[0] == h
```

Use one call for paired inputs. The API is positional, not label-aware: sort and
record the intended order before splitting. If a separate validation holdout
is desired, reserve the final holdout first and split only the prefix.

## 3. Choose and inspect fold geometry

Use expanding history when old observations remain relevant:

```python
from pmdarima.model_selection import RollingForecastCV
cv = RollingForecastCV(h=4, step=2, initial=12)
```

Use a fixed recent information set when drift or regime changes make a growing
history inappropriate:

```python
from pmdarima.model_selection import SlidingWindowForecastCV
cv = SlidingWindowForecastCV(h=4, step=2, window_size=12)
```

Materialize before fitting:

```python
folds = list(cv.split(y_tune, X_tune))
if not folds:
    raise ValueError("CV geometry produced no complete folds")
for train_idx, test_idx in folds:
    assert len(test_idx) == cv.horizon
    assert train_idx[-1] < test_idx[0]
    assert not set(train_idx).intersection(test_idx)
```

For explicit valid geometry, the count is
`1 + floor((n - initial - h) / step)` for rolling and
`1 + floor((n - window_size - h) / step)` for sliding. These are planning
bounds, not a replacement for the actual fold list. Ensure `initial >= 1`,
`window_size >= 3`, `initial + h <= n`, and `window_size + h <= n`.

## 4. Enforce `X` alignment and causal availability

Validate `len(y) == X.shape[0]` and preserve one fixed column order. pmdarima
slices `y` and `X` by integer positions, then calls each clone as:

```python
estimator.fit(y_train, X=X_train)
pred = estimator.predict(n_periods=len(test_idx), X=X_test)
```

So `X_test` must have exactly `h` rows and the same feature width as
`X_train`. Feature transforms, imputers, scalers, date regressors, and
hyperparameter-dependent feature choices must be fit inside the estimator or
pipeline for each fold. Route their construction to
[preprocessing](../../preprocessing/SKILL.md). If future `X` is unavailable,
obtain a causal feature forecast, remove the feature, or stop; do not fill from
realized test targets.

## 5. Compare scalar errors

Use the same scorer and geometry for every candidate:

```python
from pmdarima.model_selection import cross_val_score
scores = cross_val_score(
    estimator, y_tune, X=X_tune, cv=cv,
    scoring="mean_absolute_error", error_score="raise")
mean_error = float(scores.mean())
```

Supported names are `smape`, `mean_absolute_error`, and
`mean_squared_error`. A custom scorer must be `metric(y_true, y_pred)` and
return one numeric result. Select the lower error, not the maximum as with a
negated scikit-learn utility. Report per-fold values and dispersion, not just a
mean.

Use `cross_validate` to retain `fit_time` and `score_time`:

```python
result = cross_validate(
    estimator, y_tune, X=X_tune, cv=cv,
    scoring="smape", error_score="raise")
assert result["test_score"].shape == result["fit_time"].shape
```

Use `error_score="raise"` for a strict gate. A numeric sentinel is appropriate
only when fit failures are intentionally part of a candidate comparison; keep
the warning, fold, exception type, and sentinel in the record. It does not
protect against scorer failures.

For SMAPE, report the 0--200 percentage-like scale and inspect zero/zero
observations that create `NaN`. Choose a documented zero policy or use MAE/MSE;
do not silently coerce the metric.

## 6. Recover and align forecasts

```python
from pmdarima.model_selection import cross_val_predict
pred = cross_val_predict(
    estimator, y_tune, X=X_tune, cv=cv, averaging="median")
```

If `step > h`, prediction evaluation must stop before fitting. The default
averaged result is only the union of test positions. Map it using the same
materialized folds:

```python
covered = sorted({int(i) for _, test in folds for i in test})
assert len(pred) == len(covered)
forecast_by_position = dict(zip(covered, pred))
```

Overlapping folds are combined by mean or median; choose deliberately. For
`return_raw_predictions=True`, retain the sparse `(n_samples, h)` array and
fold indices. Each prediction block is stored beginning at the row for its
first test position, with horizon in columns; rows that are not fold origins
remain `NaN`. For custom metrics, it is safer to calculate from each
`(pred_block, test_idx)` pair than to assume every non-NaN matrix cell has an
independent time alignment.

## 7. Select, refit, and evaluate once

After selecting a candidate under one fixed geometry, refit it on the intended
pre-final data and forecast exactly the untouched final horizon with its future
`X`. Record source/version, estimator options, splitter parameters, all fold
boundaries, `X` schema and availability, scorer and aggregation, per-fold
errors, warnings/timings, covered positions, final error, and elapsed/runtime
bounds. Hand the final order, seasonality, interval request, and forecast call to
[forecasting](../../forecasting/SKILL.md); hand feature construction and inverse
transforms to [preprocessing](../../preprocessing/SKILL.md).

## 8. Bounded smoke procedure

Use the bundled [cross_validate_forecast.py](../scripts/cross_validate_forecast.py):

```bash
python path/to/cross_validate_forecast.py --help
python path/to/cross_validate_forecast.py --cv rolling
python path/to/cross_validate_forecast.py --cv sliding --scoring custom-mae \
  --raw-predictions
```

It uses a tiny deterministic in-memory series, low-order bounded ARIMA, no
network, plots, credentials, or output files, and asserts geometry, alignment,
scoring, and prediction shapes.
