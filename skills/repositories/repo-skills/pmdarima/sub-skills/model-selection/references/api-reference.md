# Model-selection API reference

This reference records public behavior verified against pmdarima v2.1.1,
commit `4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`. It is runtime
self-contained; the source checkout is not needed.

## Verified signatures

```python
train_test_split(*arrays, test_size=None, train_size=None)
RollingForecastCV(h=1, step=1, initial=None)
SlidingWindowForecastCV(h=1, step=1, window_size=None)
check_cv(cv=None)
cross_validate(estimator, y, X=None, scoring=None, cv=None,
                verbose=0, error_score=np.nan)
cross_val_score(estimator, y, X=None, scoring=None, cv=None,
                verbose=0, error_score=np.nan)
cross_val_predict(estimator, y, X=None, cv=None, verbose=0,
                  averaging="mean", return_raw_predictions=False)
smape(y_true, y_pred)
```

`pmdarima.model_selection` exports these names through its package initializer.
The validation functions clone the estimator once per fold. The estimator must
support the pmdarima protocol `fit(y, X=...)` and
`predict(n_periods=len(test), X=...)`, as `ARIMA` and compatible pmdarima
pipelines do.

## Positional sequential holdout

`train_test_split` delegates to scikit-learn's splitter with
`shuffle=False` and `stratify=None`. It accepts one or more equally long
indexables (lists, NumPy arrays, sparse matrices, or pandas-like objects) and
returns train/test pieces in argument order. Integer `test_size` or `train_size`
is an absolute count; a float is a fraction. With both omitted, the wrapped
default test fraction is 0.25. It does not join timestamp labels or sort data:
positions are the contract.

```python
from pmdarima.model_selection import train_test_split

y_train, y_final, X_train, X_final = train_test_split(y, X, test_size=12)
assert len(y_final) == X_final.shape[0] == 12
```

Prefer one call for paired arrays so the same boundary is applied. Validate
`len(y) == X.shape[0]` yourself before splitting. Preserve chronological
concatenation: `y == concatenate([y_train, y_final])` for array-like data.

## Common temporal splitter contract

`RollingForecastCV` and `SlidingWindowForecastCV` inherit the temporal
validator with positive integer-like `h` and `step` checks. `horizon` is a
read-only property equal to `h`. `split(y, X=None)` first applies positional
`indexable` validation and yields integer NumPy arrays `(train_index,
test_index)`. `X` is not used to calculate boundaries, but its row count must
match `y` when it is supplied.

Every yielded fold has:

```text
train_index[-1] < test_index[0]
len(test_index) == h
train and test are disjoint contiguous positions
```

The actual `folds = list(cv.split(y, X))` are authoritative. A default splitter
can yield no folds for a short series; never call an evaluator on an empty
fold collection.

## RollingForecastCV: expanding history

```python
RollingForecastCV(h=1, step=1, initial=None)
```

- `h` is the number of future rows in every test fold.
- `step` increases the training endpoint by that many positions.
- With explicit `initial`, fold 0 trains on `[0, initial)`.
- With `initial=None`, the implementation uses
  `max(1, n_samples // 3)` for the input length.
- Fold `j` trains on `[0, initial + j * step)` and tests on the next `h`
  positions `[initial + j * step, initial + j * step + h)`.
- The final fold is the last origin with a complete horizon. The observed fold
  count for valid explicit geometry is
  `1 + floor((n - initial - h) / step)`.
- An explicit `initial < 1` is invalid, and explicit `initial + h > n` raises
  when splitting. The default may instead produce zero folds on very short
  input.

Example for `n=10, initial=4, h=2, step=2`:

```text
train [0, 1, 2, 3]          test [4, 5]
train [0, 1, 2, 3, 4, 5]     test [6, 7]
train [0, 1, 2, 3, 4, 5, 6, 7] test [8, 9]
```

## SlidingWindowForecastCV: fixed recent history

```python
SlidingWindowForecastCV(h=1, step=1, window_size=None)
```

- `window_size` is the fixed number of training rows.
- With `window_size=None`, it uses `max(3, n_samples // 5)` for that input.
- `window_size < 3` raises `ValueError` when splitting.
- An explicit `window_size + h > n` raises when splitting.
- Fold `j` trains on
  `[j * step, j * step + window_size)` and tests on the immediately following
  `h` positions. The fold count is
  `1 + floor((n - window_size - h) / step)` when valid.
- The window moves by `step`; training length remains fixed.

Example for `n=10, window_size=4, h=2, step=2`:

```text
train [0, 1, 2, 3] test [4, 5]
train [2, 3, 4, 5] test [6, 7]
train [4, 5, 6, 7] test [8, 9]
```

## CV selection and scoring

`check_cv(None)` creates the default `RollingForecastCV()`; an existing
`BaseTSCrossValidator` is returned unchanged. A string, sklearn K-fold, or
other object raises `TypeError`.

`scoring` is required in practice: `_check_scoring(None)` raises `TypeError`.
The exact supported strings are:

| name | implementation | direction |
|---|---|---|
| `mean_absolute_error` | scikit-learn MAE | lower is better |
| `mean_squared_error` | scikit-learn MSE | lower is better |
| `smape` | `pmdarima.metrics.smape` | lower is better |
| callable | `metric(y_true, y_pred)` | document explicitly |

`cross_val_score` returns a 1-D NumPy array with one `test_score` per fold.
`cross_validate` returns `test_score`, `fit_time`, and `score_time` arrays.
Scores are raw error values, not negated utility scores. `verbose=0` is quiet;
higher values only print progress.

`error_score` accepts `'raise'` or a numeric value. `'raise'` propagates an
estimator fit error. A numeric value records that value and emits
`ModelFitWarning`; it does not convert a post-fit prediction/scoring failure.
Invalid values, including `None`, raise `ValueError` before evaluation.

## SMAPE

```python
smape(y_true, y_pred)
```

Both inputs are validated as numeric endogenous arrays. The returned scalar is
the mean of:

```text
200 * abs(y_pred - y_true) / (abs(y_pred) + abs(y_true))
```

Thus the usual defined range is 0--200 (percentage-like). A perfect forecast is
`0.0`; a pair `(0, 0)` has a zero denominator and produces `NaN` under the
package's NumPy arithmetic. Decide and record a zero-pair policy rather than
silently replacing it.

## Cross-validated predictions and alignment

`cross_val_predict` checks `cv.step <= cv.horizon` before fitting. If the step
is larger, it raises `ValueError` because prediction positions would be
uncovered between folds. It fits one clone per fold and constructs a
`(n_samples, n_folds)` matrix at the original integer test positions.

- `averaging="mean"` applies `np.nanmean` row-wise.
- `averaging="median"` applies `np.nanmedian` row-wise.
- A callable averaging function must support an `axis` keyword.
- Default output contains only rows covered by at least one test fold, in
  original positional order. It is not necessarily length `len(y)` and has no
  timestamp/index.
- `return_raw_predictions=True` returns a sparse `(n_samples, h)` NumPy
  matrix. Each fold's prediction block is stored at the row for that fold's
  first test position; rows that are not forecast origins remain `NaN` (this
  includes training, uncovered, and non-origin positions). Its
  horizon-column layout should be interpreted together with the materialized
  folds; do not treat it as a dense forecast vector.

To align the averaged result:

```python
folds = list(cv.split(y, X))
covered = sorted({int(i) for _, test in folds for i in test})
pred = cross_val_predict(estimator, y, X=X, cv=cv)
forecast_by_position = dict(zip(covered, pred))
```

For paired evaluation, retain each `(pred_block, test_index)` from a manual
fold record when an overlapping or sparse geometry needs custom metrics.
