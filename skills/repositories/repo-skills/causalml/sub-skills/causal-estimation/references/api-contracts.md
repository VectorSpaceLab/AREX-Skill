# API contracts

Use this reference before wiring data into CausalML 0.17.0 estimators. The most
important safety rule is to pass public estimator arguments by keyword.

## Argument-order migration

Current callable signatures still accept the historical order, but positional
calls that include `treatment` and/or `y` emit a `FutureWarning`. Write keyword
calls now:

```python
# Preferred and future-safe.
learner.fit(X=X, treatment=treatment, y=y, p=p)
learner.fit_predict(X=X, treatment=treatment, y=y, p=p)
learner.estimate_ate(X=X, treatment=treatment, y=y, p=p)

# Avoid: warns now and will be unsafe after the v1.0 positional flip.
learner.fit(X, treatment, y)
```

Current and future positional shapes to remember:

| Family | Current positional shape | Future-safe way |
| --- | --- | --- |
| Meta-learners `fit`, `fit_predict`, `estimate_ate`, most `predict` methods | `X, treatment, y, p, ...` | Always pass `X=`, `treatment=`, `y=`, `p=`. |
| R-learner `predict` | `X, p, return_components` | It has no `treatment`/`y`; `predict(X=X, p=p)` is still clearest. |
| `IVRegressor.fit` | `X, treatment, y, w` | `fit(X=X, treatment=treatment, y=y, w=w)`. |
| DRIV `fit`/`fit_predict`/`estimate_ate` | `X, assignment, treatment, y, p, pZ, ...` | `fit(X=X, assignment=assignment, treatment=treatment, y=y, p=p, pZ=pZ)`. |
| `TMLELearner.estimate_ate` | `X, treatment, y, p, ...` | `estimate_ate(X=X, treatment=treatment, y=y, p=p)`. |

The future positional convention moves `y` immediately after `X` and moves
`treatment` after `y`. Other arguments keep their relative order; for DRIV,
`assignment` lands after `treatment` in that future convention. Keyword calls
avoid every branch of this migration.

## Treatment and control labels

- `control_name` defaults to `0`; set it explicitly when treatment labels are
  strings or when the control arm is not zero.
- `treatment` must contain at least two unique values and must include
  `control_name`.
- After fitting, `learner.t_groups` is the sorted array of non-control groups.
  CATE and ATE result columns follow that order.
- Multi-treatment code should map outputs by `learner.t_groups` or
  `learner._classes`, not by the order labels appeared in the source data.

Example:

```python
learner = BaseTRegressor(learner=model, control_name="control")
learner.fit(X=X, treatment=treatment_labels, y=y)
cate = learner.predict(X=X_new)

for treatment_group, col in learner._classes.items():
    print(treatment_group, cate[:, col].mean())
```

## Feature, outcome, and vector shapes

- `X.shape[0]`, `len(treatment)`, `len(y)`, and all provided propensity vectors
  must match.
- Meta-learner outputs are NumPy arrays, even when inputs are pandas or Polars.
- CATE: `(n_samples, n_treatment_groups)`.
- ATE arrays: `(n_treatment_groups,)` when no segmentation is used.
- Confidence interval outputs mirror the primary output shape.
- `return_components=True` is family-specific:
  - S/T/DR: `(te, yhat_cs, yhat_ts)` where the component dictionaries are keyed
    by treatment group.
  - X: `(te, dhat_cs, dhat_ts)` where the dictionaries hold imputed treatment
    effects from the control and treated sides.
  - R: `(te, yhat, p_dict)`.
  - DRIV: `(te, yhat_cs, yhat_ts)`.

## Propensity-score contracts

`p` is validated by `check_p_conditions` in the meta-learner utilities.

### Single non-control treatment group

Use an array/Series with shape `(n_samples,)`:

```python
p = np.clip(raw_propensity, 1e-3, 1 - 1e-3)
learner.fit(X=X, treatment=treatment, y=y, p=p)
```

Requirements:

- Values must be strictly greater than `0` and strictly less than `1`.
- Array/Series `p` is valid only when there is exactly one non-control group.
- pandas Series and Polars Series are accepted for meta-learners.

### Multiple non-control treatment groups

Use a dictionary whose keys are exactly the non-control treatment groups:

```python
p = {
    "treatment_a": p_a,
    "treatment_b": p_b,
}
learner.fit(X=X, treatment=treatment, y=y, p=p)
```

Each value must have shape `(n_samples,)` and values strictly inside `(0, 1)`.
If a dictionary key is missing for a fitted treatment group, propensity
formatting will fail.

### DRIV propensity tuple

DRIV uses a tuple instead of a single `p` object:

```python
p = (p_unassigned, p_assigned)
learner.fit(
    X=X,
    assignment=assignment,
    treatment=treatment,
    y=y,
    p=p,
    pZ=p_assignment,
)
```

- `p[0]`: propensity of treatment under unassigned/instrument-off state.
- `p[1]`: propensity of treatment under assigned/instrument-on state.
- Each element may be a single array/Series or a dictionary keyed by treatment
  group, following the same single-treatment and multi-treatment rules above.
- `pZ` is the assignment-probability vector. Keep it bounded away from `0` and
  `1` for stable inverse-probability weights.

## pandas, Polars, and conversion boundaries

Meta-learners support native DataFrame input for `X`:

- `numpy.ndarray`
- `pandas.DataFrame`
- `polars.DataFrame`
- `polars.LazyFrame` collected once at public method entry

Vector-like inputs are normalized to NumPy where needed:

- `treatment`
- `y`
- `p`
- `sample_weight`

Practical guidance:

```python
# Good: X remains a DataFrame; y/treatment may be Series.
learner.fit(X=df[feature_cols], treatment=df[treatment_col], y=df[outcome_col])

# Good: Polars feature matrix and Series vectors.
learner.fit(X=pl_features, treatment=pl_treatment, y=pl_outcome)
```

`convert_pd_to_np` is a backward-compatible alias for the vector conversion
helper. Do not use it as a general-purpose feature-matrix conversion step unless
you are at a legacy boundary such as TMLE, IV, or DRIV that already converts
inputs internally.

TMLE, IV, and DRIV convert their inputs to NumPy internally. For those paths,
avoid object columns, mixed string/numeric features, and extension dtypes that
cannot form a numeric matrix.

## Class-specific method constraints

| Class/family | Methods and constraints |
| --- | --- |
| `BaseSRegressor`, `BaseSClassifier` | `fit`, `predict`, `fit_predict`, `estimate_ate`; S `estimate_ate` returns only `ate` unless `return_ci=True`. |
| `LRSRegressor` | `estimate_ate(X, treatment, y, p=None, pretrain=False)` returns `(ate, lb, ub)`; no `return_ci` argument. |
| `BaseTRegressor`, `BaseTClassifier` | `predict(return_ci=True)` requires `fit(..., store_bootstraps=True)` first; `return_ci` and `return_components` cannot both be true. |
| `BaseXRegressor`, `BaseXClassifier` | Need `p` or an internally fitted propensity model; classifier variant needs outcome learners with `predict_proba` and effect learners with `predict`. |
| `BaseRRegressor`, `BaseRClassifier` | `predict` does not accept `treatment` or `y`; `return_components=True` requires either supplied `p` or an internally fitted propensity model. |
| `BaseDRRegressor`, `BaseDRClassifier` | `fit` and bootstrap paths accept `seed`; three-fold cross-fitting can fail on tiny or degenerate treatment splits. |
| `TMLELearner` | Exposes `estimate_ate`; no `fit_predict`; requires `p`; returns `(ate, lb, ub)`. |
| `IVRegressor` | Exposes `fit(X, treatment, y, w)` and `predict()`; no `fit_predict` or `estimate_ate`; current class name is not `BaseIVRegressor`. |
| `BaseDRIVLearner`, `BaseDRIVRegressor`, `XGBDRIVRegressor` | Expose `fit`, `predict`, `fit_predict`, `estimate_ate`; current package has no `BaseDRIVClassifier`. |
| Serialization mixin | Fitted learners expose `.save(path)` and class `.load(path)`; generic `load_learner(path)` loads without class checking. |

## Safe import patterns

```python
from causalml.inference.meta import (
    BaseSRegressor,
    BaseTRegressor,
    BaseXRegressor,
    BaseRRegressor,
    BaseDRRegressor,
    LRSRegressor,
    TMLELearner,
)
from causalml.inference.iv import IVRegressor, BaseDRIVLearner, BaseDRIVRegressor
from causalml.inference.serialization import load_learner
```

Avoid stale imports that are not available in CausalML 0.17.0, such as
`causalml.inference.nn`, `BaseIVRegressor`, or `BaseDRIVClassifier`.
