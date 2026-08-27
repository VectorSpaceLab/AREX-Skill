# Persistence and refresh API reference

This reference records pmdarima 2.1.1 source behavior at commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`. Verify the installed package before
applying it to a persisted model; a development build or a different
dependency stack can have different compatibility behavior.

## `Pipeline`

Import with:

```python
from pmdarima.pipeline import Pipeline
```

Construct an ordered list whose intermediate stages are pmdarima
`BaseTransformer` objects and whose last stage is a `BaseARIMA` implementation:

```python
Pipeline([
    ("transformer-name", transformer),
    ("arima", ARIMA(order=(1, 0, 0))),
])
```

Validation is strict: names must be unique, must not contain `__`, and must not
conflict with constructor parameters (`steps`). Every non-final stage must be a
pmdarima transformer and the final stage must be `ARIMA`/`AutoARIMA` compatible.
The fit path clones intermediate transformers and stores fitted objects in
`pipeline.steps_`. Inspect `steps_`, not the original transformer objects in
`pipeline.steps` or the `named_steps` mapping, when recording fitted state.

Important signatures:

```text
Pipeline.fit(self, y, X=None, **fit_kwargs)
Pipeline.predict(self, n_periods=10, X=None, return_conf_int=False,
                 alpha=0.05, inverse_transform=True, **kwargs)
Pipeline.predict_in_sample(self, X=None, start=None, end=None,
                 dynamic=False, return_conf_int=False, alpha=0.05,
                 inverse_transform=True, **kwargs)
Pipeline.update(self, y, X=None, maxiter=None, **kwargs)
Pipeline.transform(self, n_periods=10, X=None, **kwargs)
```

Fit keyword routing uses `stage__parameter`, for example
`arima__maxiter=5`. Prediction, transform, and update keyword routing uses the
same stage names. `Pipeline.fit` stores DataFrame feature order in `x_feats_`
when the transformed exogenous data are a DataFrame. During prediction and
update it re-selects that order before calling the final estimator; it cannot
repair a missing column or a changed feature meaning.

`Pipeline.predict` sends only exogenous data through intermediate stages because
future endogenous values are unavailable. Endogenous transformers are reversed
by default so forecasts and intervals return to the raw scale. Set
`inverse_transform=False` only when the transformed scale is intentional. A
Fourier featurizer receives the effective forecast horizon as `n_periods` and
rejects a conflicting manually routed `stage__n_periods`. When `X` is supplied,
the pipeline derives its effective horizon from `len(X)` if it differs from the
requested `n_periods`; callers should still make `len(X) == h` explicit rather
than rely on that adjustment.

`Pipeline.update` is an in-place operation over the fitted `steps_`. After
fitted endog/exog stages are visited, each intermediate stage with
`update_and_transform` receives the new batch and may advance state; other
stages only call `transform`. The transformed batch is column-reordered using
`x_feats_`, then the final estimator's `update` is called. The method returns
the final estimator (`ARIMA`/`AutoARIMA`), not the pipeline object; continue to
use the mutated pipeline for subsequent predictions. New `y` is raw scale when
an endog transformer is present; do not pre-transform it.

## `ARIMA`

Import with `from pmdarima.arima import ARIMA` or use `pmdarima.ARIMA`.
The relevant constructor and methods are:

```text
ARIMA(order, seasonal_order=(0, 0, 0, 0), start_params=None,
      method='lbfgs', maxiter=50, suppress_warnings=False,
      out_of_sample_size=0, scoring='mse', scoring_args=None,
      trend=None, with_intercept=True, **sarimax_kwargs)
ARIMA.fit(self, y, X=None, **fit_args)
ARIMA.predict(self, n_periods=10, X=None, return_conf_int=False,
              alpha=0.05, **kwargs)
ARIMA.update(self, y, X=None, maxiter=None, **kwargs)
```

`fit` validates a one-dimensional finite `y`. Optional `X` is two-dimensional.
If `X` was present at fit time, it is required for every corresponding
prediction and update. For direct `ARIMA.predict`, `X.shape[0]` must equal
`n_periods`; for direct `ARIMA.update`, `X.shape[0]` must equal the number of
new `y` values and `X.shape[1]` must equal the fitted exogenous width. A direct
forecast has shape `(h,)`; with `return_conf_int=True`, the result is
`(forecast, intervals)` where `intervals.shape == (h, 2)`.

`ARIMA.update` accepts a scalar or iterable, appends the observations to the
stored statsmodels data, and calls the internal fit seeded with the old
parameters. It returns `self`. With `maxiter=None`, the source uses
`max(5, n_new // 10)`. It does not run `auto_arima` order selection and is not
a clean refit. A small explicit `maxiter` bounds local optimization but can
leave convergence incomplete.

After a fit, `pkg_version_` records `pmdarima.__version__`. During unpickle,
`ARIMA.__setstate__` compares that value with the installed version and emits a
`UserWarning` when they differ. A fitted old state without `pkg_version_` also
warns; an unfitted state may not contain enough information to detect its
origin. A warning means compatibility is unproven, not that loading is safe.

## Transformer behavior relevant to persistence

- `BoxCoxEndogTransformer(lmbda=..., lmbda2=..., neg_action=..., floor=...)`
  learns `lam1_`/`lam2_` at fit. A later transform uses that fitted lambda and
offset; it does not relearn them during `Pipeline.update`. With the default
  `neg_action="raise"`, values with `y + lmbda2 <= 0` raise
  `ValueError("Negative or zero values present in y")`. `warn`/`ignore`
  truncate to `floor` and lose exact inverse-transformability.
- `FourierFeaturizer` is an updatable exogenous featurizer. Its
  `update_and_transform` generates exactly `len(y)` new Fourier rows, then
  increments fitted `n_`; later forecasts start at that advanced time index.
  If external `X` is present, its rows must align with the batch and its
  feature width/meaning must remain stable.
- An ordinary intermediate transformer without `update_and_transform` only
  transforms the new batch. It does not relearn fitted parameters. Refit when
  those parameters or the transformation domain must change.

## Persistence contract

Standard binary `pickle` and `joblib.dump`/`joblib.load` are usable for trusted
artifacts, but both are Python object deserialization mechanisms. Store a
separate manifest containing at least:

- pmdarima, Python, statsmodels, NumPy/SciPy, and scikit-learn versions;
- model class, `order`, `seasonal_order`, fitted transformer classes and
  configuration, and `x_feats_`/exogenous names and width;
- training row count and range, raw/transformed-scale convention, expected
  forecast horizon, update policy, and artifact checksum/timestamps.

Write a new file in a same-directory temporary path, validate loading that file
and a known-shape forecast, and only then use `os.replace` to promote it. Keep
the last-known-good artifact if validation fails. A round-trip forecast only
proves that this exact environment can load and use the artifact now. It does
not prove compatibility with another pmdarima release, Python ABI, statsmodels
result layout, NumPy/SciPy binary ABI, or compiled extension. When compatibility
is uncertain, recreate the environment or rebuild from a trusted training
recipe rather than editing pickle bytes.
