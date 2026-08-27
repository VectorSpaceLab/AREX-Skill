# Troubleshooting causal estimation

This guide covers common failures for CausalML 0.17.0 classical estimators.

## Import errors and stale class names

### `ModuleNotFoundError: causalml.inference.nn`

Do not use `causalml.inference.nn` for current runtime code. That module path is
stale and absent in CausalML 0.17.0. Route neural estimator work to
[../../deep-models/](../../deep-models/) and use the current backend namespaces there.

### `ImportError: cannot import name 'BaseIVRegressor'`

Use `IVRegressor`:

```python
from causalml.inference.iv import IVRegressor
```

The current IV estimator has `fit(X=X, treatment=treatment, y=y, w=instrument)`
and `predict()`.

### `ImportError: cannot import name 'BaseDRIVClassifier'`

CausalML 0.17.0 exposes `BaseDRIVLearner`, `BaseDRIVRegressor`, and
`XGBDRIVRegressor`; it does not expose `BaseDRIVClassifier`.

```python
from causalml.inference.iv import BaseDRIVLearner, BaseDRIVRegressor
```

### Missing optional estimator dependencies

Convenience classes may require optional libraries:

- `XGBTRegressor`, `XGBTClassifier`, `XGBRRegressor`, `XGBRClassifier`,
  `XGBDRRegressor`, and `XGBDRIVRegressor` require XGBoost.
- Some interpretation methods use LightGBM or SHAP when selected.
- Neural backends are outside this sub-skill; route them to
  [../../deep-models/](../../deep-models/).

If an optional dependency is missing, switch to a base learner backed by an
available scikit-learn estimator or install the matching optional dependency in
the active environment.

## Argument-order warnings

Symptom:

```text
FutureWarning: Passing `treatment` and/or `y` ... by position is deprecated ...
```

Fix every CausalML estimator call to use keywords:

```python
# Before
learner.fit(X, treatment, y)

# After
learner.fit(X=X, treatment=treatment, y=y)
```

Apply the same pattern to `predict`, `fit_predict`, `estimate_ate`, `bootstrap`,
`IVRegressor.fit`, and DRIV methods. Do not silence this warning globally; it is
pointing at code that can silently train on swapped arrays in a later major
version.

## Propensity validation errors

### `p must be an np.ndarray, pd.Series, pl.Series ... or dict type`

Use a one-dimensional array/Series or a dictionary keyed by treatment group.
Lists should be converted explicitly:

```python
p = np.asarray(p, dtype=float)
```

### `If p is passed as an array/Series, there must be only 1 unique non-control group`

For multi-treatment data, use a dictionary:

```python
p = {"email": p_email, "coupon": p_coupon}
learner.fit(X=X, treatment=treatment, y=y, p=p)
```

### `The values of p should lie within the (0, 1) interval`

The validation is strict: exact `0` and exact `1` are invalid. Clip calibrated
scores away from the boundaries before fitting:

```python
eps = 1e-3
p = np.clip(p, eps, 1 - eps)
```

For DRIV, clip both elements of the tuple and keep assignment probabilities
away from the boundaries as well:

```python
p = (np.clip(p0, eps, 1 - eps), np.clip(p1, eps, 1 - eps))
pZ = np.clip(pZ, eps, 1 - eps)
```

## Treatment/control label problems

### `Control group level ... not found in treatment vector`

Set `control_name` to the actual control label:

```python
learner = BaseTRegressor(learner=model, control_name="control")
```

Do not convert labels in one split but not another. Fit and predict calls should
use consistent treatment labels and consistent `control_name`.

### Output column appears to correspond to the wrong treatment

CATE columns are ordered by `learner.t_groups`, not by the order labels appeared
in the data. Inspect after fitting:

```python
for group, col in learner._classes.items():
    print(group, cate[:, col])
```

## Shape and split failures

### Different row counts

Check all row-aligned inputs before fitting:

```python
n = X.shape[0]
assert len(treatment) == n
assert len(y) == n
if p is not None and not isinstance(p, dict):
    assert len(p) == n
```

### Cross-fitting fails on small or degenerate data

R/DR/DRIV learners use cross-fitting and per-arm masks. They can fail when one
fold has no control rows or no treatment rows for a group. Increase sample size,
reduce the number of rare treatment arms, or switch to an S/T learner for a
small smoke test.

### Classifier learner has no `predict_proba`

`BaseSClassifier`, `BaseTClassifier`, and classifier outcome components in
X/DR-style learners use class probabilities. Use a classifier that implements
`predict_proba`, or wrap/calibrate the model before passing it as an outcome
learner.

### R-learner sample-weight failure

When passing `sample_weight`, the R-learner effect model must accept
`sample_weight` in its `fit` method. If it does not, choose an effect learner
that supports weighted fitting or omit sample weights.

## DataFrame and Polars issues

### Polars LazyFrame surprises

Meta-learners collect a Polars LazyFrame once at method entry. If a lazy query
contains non-deterministic operations or columns with unsupported dtypes,
collect and validate it yourself before fitting.

### Object or mixed dtypes

TMLE, IV, and DRIV convert features to NumPy internally. Ensure the feature
matrix is numeric:

```python
X_numeric = X[feature_cols].astype(float)
```

For pandas/Polars meta-learner usage, keep `X` as a DataFrame only when the
underlying base estimator can consume that DataFrame format.

## Method availability mistakes

### `TMLELearner` has no `fit_predict`

Use `estimate_ate`:

```python
tmle = TMLELearner(learner=model, control_name=0)
ate, lb, ub = tmle.estimate_ate(X=X, treatment=treatment, y=y, p=p)
```

### `IVRegressor` has no `fit_predict` or `estimate_ate`

Use `fit` followed by `predict()`:

```python
iv = IVRegressor()
iv.fit(X=X, treatment=treatment, y=y, w=instrument)
ate, se = iv.predict()
```

### `BaseRRegressor.predict()` rejects `treatment=` or `y=`

R-learner prediction uses only `X`, optional `p`, and `return_components`:

```python
cate = r_learner.predict(X=X_new, p=p_new)
```

## Confidence interval issues

### T-learner `predict(return_ci=True)` says no bootstrap ensemble exists

Train with stored bootstraps first:

```python
learner.fit(
    X=X,
    treatment=treatment,
    y=y,
    store_bootstraps=True,
    n_bootstraps=20,
    bootstrap_size=min(1000, len(y)),
    random_state=42,
)
cate, lb, ub = learner.predict(X=X_new, return_ci=True)
```

### Bootstrap intervals are slow

Lower `n_bootstraps` and `bootstrap_size` for smoke tests, then raise them for
analysis. For deterministic checks, pass `random_state` where available for
stored T-learner bootstraps or `seed` for DR/DRIV cross-fitting paths.

## Serialization issues

### `Cannot save an unfitted model`

Call `fit` before `save`:

```python
learner.fit(X=X, treatment=treatment, y=y)
learner.save("models/learner.causalml")
```

### Class mismatch on load

Load with the same class used to save the model, or use the generic loader when
you do not know the class:

```python
from causalml.inference.serialization import load_learner
loaded = load_learner("models/learner.causalml")
```

### Version mismatch warning

A saved file records the CausalML version that created it. If loading warns that
the saved version differs from the current version, predictions may still run,
but retraining is safer for production or exact reproducibility.

### Looking for `save_model` or `load_model`

Classical estimators use `save`, class `load`, and `load_learner`. Do not look
for top-level `save_model` or `load_model` functions for the meta/IV/DRIV
estimators covered here.
