# IV, DRIV, TMLE, and serialization

This reference covers classical ATE/LATE estimation paths outside the ordinary
S/T/X/R/DR meta-learner families and the shared persistence API.

## TMLELearner

`TMLELearner` estimates ATE with targeted maximum likelihood. In CausalML 0.17.0
it exposes `estimate_ate` and does **not** expose `fit`, `predict`, or
`fit_predict` as public runtime methods.

```python
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from causalml.inference.meta import TMLELearner

p = propensity_scores  # shape (n_samples,), values strictly inside (0, 1)
tmle = TMLELearner(
    learner=LinearRegression(),
    control_name=0,
    cv=KFold(n_splits=3, shuffle=True, random_state=42),  # optional
)
ate, lb, ub = tmle.estimate_ate(X=X, treatment=treatment, y=y, p=p)
```

Contracts and limitations:

- `learner` must implement `fit(X_augmented, y)` and `predict(X_augmented)`.
  TMLE internally appends a treatment indicator column to `X`.
- `p` is required; it can be a single array/Series for one non-control group or
  a dictionary for multiple treatment groups. Values must be strictly inside
  `(0, 1)`.
- `segment=` may be a one-dimensional integer-like array with one value per row.
  With segments, returned arrays are nested by treatment group and segment.
- The method converts inputs to NumPy before constructing augmented matrices;
  avoid object columns and mixed feature dtypes.
- `return_ci` is present in the signature, but the current implementation
  returns `(ate, lb, ub)` either way.

Segmented TMLE example:

```python
segments = cohort_ids  # shape (n_samples,)
ate_by_segment, lb_by_segment, ub_by_segment = tmle.estimate_ate(
    X=X,
    treatment=treatment,
    y=y,
    p=p,
    segment=segments,
)
```

## IVRegressor

Use `IVRegressor` for a linear two-stage least squares estimate with an
endogenous treatment and an instrument. The current package does not expose a
`BaseIVRegressor` class.

```python
from causalml.inference.iv import IVRegressor

iv = IVRegressor()
iv.fit(X=X, treatment=treatment, y=y, w=instrument)
ate, standard_error = iv.predict()
```

Contracts:

- `X`: feature matrix.
- `treatment`: endogenous treatment vector.
- `y`: outcome vector.
- `w`: instrument vector.
- `predict()` takes no `X`; it returns the fitted treatment coefficient and its
  standard error from the fitted IV model.
- There is no `fit_predict` or `estimate_ate` on `IVRegressor` in this version.

## DRIV learners

Use DRIV when the assignment/instrument changes treatment uptake and the target
is a complier treatment effect. Current entry points are `BaseDRIVLearner`,
`BaseDRIVRegressor`, and `XGBDRIVRegressor`. There is no
`BaseDRIVClassifier` class in CausalML 0.17.0.

```python
from sklearn.linear_model import LinearRegression
from causalml.inference.iv import BaseDRIVLearner

# assignment: binary instrument, e.g. randomized encouragement
# treatment: realized treatment uptake
# p: tuple where element 0 is Pr(treatment | unassigned), element 1 is
#    Pr(treatment | assigned)
p = (p_unassigned, p_assigned)

learner = BaseDRIVLearner(
    learner=LinearRegression(),
    treatment_effect_learner=LinearRegression(),
    control_name=0,
)
learner.fit(
    X=X,
    assignment=assignment,
    treatment=treatment,
    y=y,
    p=p,
    pZ=assignment_probability,
    seed=42,
)
cate_for_compliers = learner.predict(X=X_new)
ate, lb, ub = learner.estimate_ate(
    X=X,
    assignment=assignment,
    treatment=treatment,
    y=y,
    p=p,
    pZ=assignment_probability,
    seed=42,
)
```

DRIV contracts:

- `assignment` is the instrument and is expected to be binary in the usual
  encouraged/assigned design.
- `treatment` is the realized treatment vector and must include `control_name`
  plus at least one non-control group.
- `p` is a two-element tuple `(p0, p1)`:
  - `p0`: propensity of treatment among unassigned units.
  - `p1`: propensity of treatment among assigned units.
  Each element may be an array/Series for a single non-control group, or a
  dictionary keyed by non-control treatment group for multi-treatment settings.
- `pZ` is the assignment probability vector. If omitted, the learner estimates
  assignment probability internally.
- `predict(X=...)` returns a CATE array of shape
  `(n_samples, n_treatment_groups)` for compliers.
- `fit_predict(..., return_ci=True)` returns `(cate, lb, ub)` with matching
  shapes; `estimate_ate(..., bootstrap_ci=True)` returns bootstrap ATE bounds.

For the safest behavior when you already have custom `pZ`, call `fit` with all
keyword arguments and then call `predict`; this avoids ambiguity around optional
arguments in the higher-level convenience methods.

## Serialization API

Most classical CausalML learners inherit a shared joblib-backed persistence API:

```python
from causalml.inference.meta import BaseTRegressor
from causalml.inference.serialization import load_learner

learner = BaseTRegressor(learner=LinearRegression(), control_name=0)
learner.fit(X=X, treatment=treatment, y=y)

model_path = "models/t_learner.causalml"
learner.save(model_path)

loaded_t = BaseTRegressor.load(model_path)  # class-checked load
loaded_any = load_learner(model_path)       # generic load without class check
```

Behavior:

- `save(path)` requires a fitted learner and raises a `ValueError` for unfitted
  models.
- `save(path)` creates parent directories when needed and overwrites an existing
  file at the same path.
- The file stores the model plus metadata: CausalML version, Python version,
  learner class, learner module, and save timestamp.
- `ClassName.load(path)` checks that the saved class matches `ClassName` and
  raises `ValueError` on class mismatch.
- `load_learner(path)` is generic and skips the class-match check.
- Loading a file saved by a different CausalML version emits
  `CausalMLVersionMismatchWarning`; consider retraining if prediction stability
  matters.
- Loading a raw joblib model without CausalML metadata is allowed through the
  generic loader, but emits a metadata/version warning.
- Classical estimators use `save`, `load`, and `load_learner`; do not assume
  `save_model` or `load_model` functions are available for them.

Serialization applies to fitted meta-learners, `IVRegressor`, DRIV learners, and
other estimator families that inherit the shared mixin. Backend-specific neural
save/load behavior is routed to [../../deep-models/](../../deep-models/).
