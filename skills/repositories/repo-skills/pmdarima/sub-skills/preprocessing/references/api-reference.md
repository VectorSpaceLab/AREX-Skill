# Preprocessing API reference

This reference is a self-contained operating contract for the public
preprocessing classes and `Pipeline` behavior observed at pmdarima `v2.1.1`.
Examples use tiny in-memory data only.

## Shared tuple contract

The public target and feature transformers follow the pmdarima
`BaseTransformer` interface:

```python
fit(y, X=None) -> self
fit_transform(y, X=None, **kwargs) -> (y_transformed, X_transformed)
transform(y, X=None, **kwargs) -> (y_transformed, X_transformed)
```

`fit_transform` is not a one-array sklearn result. Retain both tuple elements
when chaining. Endogenous transformers reject `y=None`; ordinary exogenous
transformers reject missing `X`, while Fourier can synthesize exogenous terms
without `X`. Inputs are checked/copied by the base utilities where the
implementation calls them, so rely on values and schema rather than object
identity. Endogenous `X` is pass-through; exogenous featurizers pass `y` through.

## `BoxCoxEndogTransformer`

Signature:

```python
BoxCoxEndogTransformer(
    lmbda=None, lmbda2=0, neg_action="raise", floor=1e-16
)
```

The transform first computes `z = y + lmbda2`, then applies:

```text
((z ** lmbda) - 1) / lmbda       if lmbda != 0
log(z)                           if lmbda == 0
```

- `lmbda` is the power. If it is `None`, `fit` estimates it by scipy Box-Cox
  maximum likelihood and stores the result in `lam1_`; a supplied value is
  used unchanged.
- `lmbda2` is the additive shift, stored as `lam2_`. It must be non-negative;
  a negative shift raises during `fit`.
- `neg_action` is applied by `transform` to values where `y + lmbda2 <= 0`:
  `"raise"` raises `ValueError`; `"warn"` emits `UserWarning` and replaces
  those entries; `"ignore"` replaces them silently.
- Replacement uses `floor`, which is a replacement value rather than a shift.
  The documented intent is a positive floor; choose one explicitly and do not
  use it as a substitute for deciding the data shift.
- Automatic lambda estimation occurs in `fit` before the transform policy is
  applied. Therefore `lmbda=None` still needs every training value strictly
  positive after `lmbda2`; `neg_action` does not rescue a non-positive series
  during estimation.

`transform(y, X)` returns `(y_boxcox, X_pass_through)`. After fitting,
`inverse_transform(y, X)` undoes the power/log and subtracts `lam2_`; for zero
power it computes `exp(y) - lam2_`. A clean strictly positive series should
round-trip to floating-point tolerance. Rows replaced by `floor` cannot
round-trip to their original values. The supplied `X` is returned as the
pass-through second tuple item.

The implementation branches on the documented values but has no explicit
invalid-string validator: a value other than `"raise"` or `"warn"` falls into
the silent replacement branch. Treat only `raise`, `warn`, and `ignore` as the
supported API. In particular, `neg_action="clip"` is not a documented mode;
its clip-like result is an implementation fallback, not a stable contract.

## `LogEndogTransformer`

Signature:

```python
LogEndogTransformer(lmbda=0, neg_action="raise", floor=1e-16)
```

This is the zero-power Box-Cox case. Here the public `lmbda` means the
additive shift, so the target transform is `log(y + lmbda)` and the inverse is
`exp(y_transformed) - lmbda`. Internally, the class fixes its power at zero and
stores the public shift as `lmbda2`; `get_params()` maps the public name back
to the shift so sklearn cloning and Pipeline fitting preserve it. Non-positive
values after the shift use the same `raise`/`warn`/`ignore`/floor behavior as
Box-Cox.

## `FourierFeaturizer`

Signature:

```python
FourierFeaturizer(m, k=None, prefix=None)
```

`m` is the fixed seasonal period in observations. `k` is the number of
harmonics; each harmonic contributes one sine and one cosine column, so the
new feature block has `2*k` columns. If `k=None`, fit uses `m // 2`. A safe
configuration is a positive integer `m` and integer `1 <= k <= m // 2`.
The implementation explicitly rejects `k < 1` and `2*k > m`, but its check is
not a complete type/finite-value validator; use ordinary positive integers.

`fit(y, X=None)` records the training length in `n_` and computes fitted
harmonic frequencies in `p_`; target values are not used to estimate features.
The source stores `n_` from the original `y.shape[0]` after validation, so a
raw Python list passed directly to `FourierFeaturizer.fit` raises
`AttributeError`; pass a NumPy array/pandas Series (as `Pipeline.fit` does), or
normalize with `np.asarray`. `y` is nevertheless needed so fit can record the
length. `transform(y, X=None, n_periods=0)` uses that fitted index:

- `n_periods=0`: return `n_` training rows.
- `n_periods=h>0`: return only the next `h` rows and permit `y=None`.
- if both `n_periods` and `X` are supplied, `len(X)` must equal `n_periods`.

Fourier terms are appended on the right of existing `X`. With no prefix,
feature names are `FOURIER_S{m}-{i}` and `FOURIER_C{m}-{i}` for `i=0..k-1`;
`prefix` replaces `FOURIER`. If `X` is `None` or a pandas DataFrame, the
resulting exogenous object is a DataFrame. If `X` is an ndarray, the result is
an ndarray. This type behavior matters for Pipeline's later column alignment.

Tiny shape check:

```python
import numpy as np

f = FourierFeaturizer(m=4, k=1, prefix="SEASON")
_, X_fit = f.fit_transform(np.asarray([1., 2., 3., 4., 5., 6.]))
_, X_future = f.transform(None, n_periods=2)
# X_fit.shape == (6, 2), X_future.shape == (2, 2)
# columns: SEASON_S4-0, SEASON_C4-0
```

## `DateFeaturizer`

Signature:

```python
DateFeaturizer(
    column_name, with_day_of_week=True, with_day_of_month=True, prefix=None
)
```

`X` must be a pandas DataFrame in both `fit` and `transform`; the configured
`column_name` must exist and have a pandas `datetime64` dtype. A numpy array,
missing column, or string/object date column fails before feature generation.
Convert the exact column with `pd.to_datetime` before fit and before every
forecast call.

- `with_day_of_week=True` creates seven integer one-hot columns for weekday
  values 0 (Monday) through 6 (Sunday).
- `with_day_of_month=True` creates one integer day-of-month column, 1..31.
- All other input columns are preserved, the source date column is removed
  whenever at least one feature family is enabled, and the output is a
  DataFrame.
- Default names are `DATE-WEEKDAY-0` through `DATE-WEEKDAY-6` and
  `DATE-DAY-OF-MONTH`; `prefix` replaces `DATE`.
- With both feature flags disabled, fit warns that the transformer has no
  effect and transform returns the original DataFrame unchanged, including the
  date column.

Unlike Fourier, DateFeaturizer cannot synthesize future calendar rows. A future
DataFrame with the configured datetime column and one row per forecast period
is mandatory, including in `Pipeline.predict` and `Pipeline.transform`.

## `Pipeline` integration

`Pipeline(steps)` requires unique names, names without `__`, intermediate
`BaseTransformer` instances, and a final pmdarima `ARIMA`/`AutoARIMA` estimator.
A typical tuple flow is:

```text
(y, X)
  -> target transformer:  (y_transformed, X)
  -> Fourier/date stage:  (same y, X_augmented)
  -> final ARIMA fit
```

At `fit`, Pipeline preserves the supplied list order, clones each
intermediate transformer, calls those stages in order, records DataFrame output
columns as `x_feats_`, then fits the supplied final estimator on the
transformed target and exogenous matrix. The final estimator is not cloned by
this implementation. Thus a log/Box-Cox target transform can be composed with
Fourier and/or DateFeaturizer. Use stable, unique stage names and pass
stage-qualified options as `stage__parameter` when supported.

At prediction there is no future `y`, so Pipeline applies only exogenous
transformer stages before calling the final estimator. It sets a featurizer's
`n_periods` from the requested horizon and rejects a conflicting manual
`stage__n_periods`. If `X` is supplied, Pipeline uses its length as the
forecast horizon, overriding a different `n_periods`. If a DataFrame was
present at fit, Pipeline selects the recorded `x_feats_` order before
prediction; missing columns fail rather than being silently created.

`predict(..., inverse_transform=True)` is the default. Pipeline walks fitted
steps in reverse order and calls every endogenous transformer's
`inverse_transform`; point forecasts and each confidence-interval bound are
converted back to the original target scale. With `inverse_transform=False`,
returned values stay on the final model's transformed scale. Exogenous
features are never inverse-transformed by target transformers.

If the final model was fit with exogenous regressors, future `X` is required
and must have compatible rows and columns. Use `pipe.transform(...)` to inspect
future feature shape/order before `predict(...)`. Fourier-only pipelines can
use `pipe.predict(n_periods=h)` without user `X`; DateFeaturizer pipelines
cannot.
