# Preprocessing troubleshooting

Use the symptom, diagnosis, and bounded action below. Do not hide a schema or
lossy-transform error by changing unrelated ARIMA settings. The source contract
is pmdarima v2.1.1; check the installed distribution and its compiled extensions
before attributing an import or signature failure to preprocessing behavior.

## Installation or optional-dependency failure

**Symptom:** importing `pmdarima.preprocessing`, `Pipeline`, or a Fourier stage
fails with a missing package, `__check_build._check_build`, or a compiled
extension error.

**Diagnosis:** Preprocessing imports the core project dependencies NumPy,
pandas, SciPy, and scikit-learn. Box-Cox additionally uses SciPy; DateFeaturizer
uses pandas; Fourier imports the built `_fourier` extension. Pipeline's final
ARIMA estimator also relies on the pmdarima model stack, including statsmodels.
The repository's `test`/`dev`/`all` extras are not required for ordinary
preprocessing use; matplotlib is a test/dev extra, not a Date/Fourier runtime
requirement.

**Action:** Install a built pmdarima distribution with its declared runtime
dependencies, or complete the project's supported build before importing. Do
not run the source checkout as if it were an installed wheel: an unbuilt
checkout can raise the `__check_build` error even when Python dependencies are
present. If only target transforms are needed, still verify the base package
imports; do not bypass the package build by substituting private modules. For
an installed package, capture `pmdarima.__version__` and dependency versions
when a signature mismatch remains; the source tag alone does not prove the
runtime package is the same release.

## Input data or row-count failure

**Symptom:** a transformer rejects `y`/`X`, an append operation raises a shape
error, or the final ARIMA reports inconsistent observations.

**Diagnosis:** `y` must be one-dimensional for the base checker. Ordinary
exogenous transformers require a 2-D `X`; target transformers may pass `X`
through. The preprocessing classes do not provide a universal semantic row
alignment check for every direct call, so a mismatched `len(y)`/`len(X)` can
surface late (or as an append/model error). Fourier direct `fit` uses
`y.shape[0]`, so a raw Python list is not accepted there even though
`Pipeline.fit` first normalizes `y`.

**Action:** Normalize direct Fourier input with `np.asarray(y)` or a pandas
Series, keep `y` one-dimensional, and assert `len(y) == len(X)` before fit or
training-shaped transform. For forecast data, assert the requested horizon
matches future rows; for a Fourier call with `X`, pass `n_periods=len(X)`. Keep
all DataFrame date/covariate columns present and in the intended schema.

## Box-Cox/log rejects a non-positive value

**Symptom:** `ValueError: Negative or zero values present in y` during
`transform`.

**Diagnosis:** At least one `y + lmbda2` value is `<= 0` (for
`LogEndogTransformer`, `lmbda2` is its public `lmbda`) and `neg_action` is
`"raise"`.

**Action:** Prefer correcting the additive shift or input data and retain
`raise`. If replacement is deliberate, use `neg_action="warn"` to expose it or
`"ignore"` to silence it, and choose a documented positive `floor`. Both modes
replace the offending rows before applying the transform; the inverse returns a
floor-derived value, not the original row.

For `y=[-1, 0, 1]`, fixed Box-Cox `lmbda=2`, and no shift, `raise` fails;
`warn` succeeds with one `UserWarning`; `ignore` succeeds without a warning.
A string such as `"clip"` is not a supported public mode: the implementation's
fallback branch happens to silently floor values for unrecognized strings, but
future code should not depend on that behavior.

## Automatic Box-Cox fit fails on non-positive training data

**Symptom:** fitting `BoxCoxEndogTransformer(lmbda=None)` raises a scipy
positivity error before the configured `neg_action` can help.

**Diagnosis:** MLE estimation runs during `fit` on `y + lmbda2`; the transform
policy is only evaluated later by `transform`.

**Action:** Use a sufficient non-negative shift so all training values are
strictly positive, or provide a fixed power. A negative `lmbda2` is rejected.
Verify the fitted `lam1_` and `lam2_` values after fit.

## Inverse output does not equal the input

**Symptom:** `inverse_transform(transform(y))` differs for selected rows, or a
pipeline forecast is on an unexpected scale.

**Diagnosis:** Non-positive rows were replaced by `floor`, or the caller
requested `inverse_transform=False`. A transform cannot reconstruct values that
were clipped/replaced.

**Action:** For a reversible data path, use strict positivity and
`neg_action="raise"`; compare only clean positive rows to the original. Leave
Pipeline's default `inverse_transform=True` for original-scale forecasts, and
remember that confidence-interval bounds are also inverse-transformed.

## Fourier fit rejects `m` or `k`

**Symptom:** `ValueError` says `k` must be a positive integer not greater than
`m//2`, or a later error occurs while constructing terms.

**Diagnosis:** `k < 1`, `2*k > m`, `m < 2` with `k=None`, or an unusual/non-integer
period was supplied. The source check enforces bounds but is not a complete type
validator.

**Action:** Use positive integer `m` and integer `1 <= k <= m//2`; start with a
small `k`. Remember that each harmonic adds two regressors. For a direct future
transform with user `X`, require `n_periods == len(X)`. In Pipeline, let the
requested forecast horizon supply `n_periods` and remove a stale manual
`fourier__n_periods` override.

## Fourier future rows do not align

**Symptom:** `ValueError` reports that `n_periods` and `X` dimensions differ, or
the final ARIMA rejects the exogenous matrix.

**Diagnosis:** Fourier was asked for a different horizon than the supplied
future rows, or a fitted exogenous schema was not reproduced.

**Action:** Generate Fourier-only rows with `transform(None, n_periods=h)`.
When supplying `X`, use `transform(None, X_future, n_periods=len(X_future))` and
check the final row count and `2*k` added columns. In Pipeline, use
`pipe.transform(...)` before `predict(...)`.

## DateFeaturizer rejects the input

**Symptom:** `TypeError` says `X` must be a DataFrame, or `ValueError` says the
configured column must exist as a pandas Timestamp type.

**Diagnosis:** `X` is `None`/an ndarray, the configured name is absent, or the
column still contains strings/objects.

**Action:** Copy the frame and convert the exact column before fit and every
forecast call:

```python
frame = frame.copy()
frame["date"] = pd.to_datetime(frame["date"])
```

The future frame must include that column even when only the date-derived
features are needed. DateFeaturizer cannot infer dates from `n_periods`.

## Installed API signature or behavior differs from the source anchor

**Symptom:** a constructor rejects a documented parameter, a method has a
different return shape, or a smoke test disagrees with this reference.

**Diagnosis:** the running distribution is not the inspected v2.1.1 build, or
an unbuilt source checkout is shadowing the intended installed package. The
source checkout's commit/tag and the runtime package version are separate
pieces of evidence.

**Action:** run the signature probe from the inspection environment (or an
isolated environment with the intended install), record
`pmdarima.__file__`, `pmdarima.__version__`, and signatures for the affected
class/method, then stop using this route until the version discrepancy is
resolved. Do not silently adapt a production workflow to an unverified private
or older API.

## Pipeline construction or fit is rejected

**Symptom:** `Pipeline(...)` raises for steps, or fit fails in a transformer or
ARIMA stage.

**Diagnosis:** Names are duplicated, contain `__`, or collide with Pipeline
parameters; an intermediate stage is not a `BaseTransformer`; the final stage
is not pmdarima `ARIMA`/`AutoARIMA`; or a target/exog schema is missing.

**Action:** Use unique names such as `"log"`, `"fourier"`, `"dates"`, and
`"arima"`, put all transformers before the final estimator, and retain the
`(y, X)` tuple after every stage. Ensure target transforms receive `y`, ordinary
exog transforms receive `X`, and the final estimator receives the intended
transformed matrix.

## Prediction reports missing or misordered exogenous columns

**Symptom:** `predict` or `transform` fails while applying a date stage, selecting
`x_feats_`, or fitting the final ARIMA.

**Diagnosis:** The model was fit with exogenous columns that are absent at
forecast time, future row count is wrong, the DateFeaturizer source date was
omitted, or a DataFrame's generated/user columns differ from fit.

**Action:** Supply one future row per period and every covariate used at fit.
For a DateFeaturizer, include a datetime `column_name`; for Fourier-only
features, generate via the horizon. Inspect:

```python
Xt = pipe.transform(X=future_frame)  # or n_periods=h for Fourier-only
assert len(Xt) == h
assert list(Xt.columns) == pipe.x_feats_
```

Do not silently add a constant or reorder a numpy matrix by guesswork. A model
fit with exogenous features requires compatible `X` for prediction (and for
observed-value updates, where that lifecycle is managed elsewhere).

## No date features appear

**Symptom:** fit warns and transformed `X` is unchanged, including the source
`date` column.

**Diagnosis:** Both `with_day_of_week` and `with_day_of_month` were disabled.

**Action:** Enable at least one feature family, or retain the no-op deliberately
as a schema-preserving stage. Do not expect the source column to be dropped in
this no-op configuration.
