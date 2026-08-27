# Meta-learners

This reference covers the classical meta-learner families in CausalML 0.17.0.
All examples use keyword arguments because current positional calls warn and a
future major version changes positional order.

## Shared workflow

```python
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from causalml.inference.meta import BaseTRegressor

learner = BaseTRegressor(learner=LinearRegression(), control_name=0)
learner.fit(X=X, treatment=treatment, y=y)
cate = learner.predict(X=X)
ate, lb, ub = learner.estimate_ate(X=X, treatment=treatment, y=y)
```

Shared contracts:

- `X`: rows are units; columns are features. Meta-learners accept NumPy arrays,
  pandas DataFrames, Polars DataFrames, and Polars LazyFrames for `X`.
- `treatment`: one value per row. `control_name` must be present.
- `y`: one outcome value per row. Regressor learners target continuous outcomes;
  classifier learners target binary outcomes and require models with
  `predict_proba` where outcome probabilities are used.
- `p`: optional propensity scores for X/R/DR-style learners; see
  [api-contracts.md](api-contracts.md#propensity-score-contracts).
- Output CATE arrays have shape `(n_samples, n_treatment_groups)`. Column `i`
  corresponds to `learner.t_groups[i]`, the sorted non-control treatment labels.

## Family routing

| Need | Use | Base models | Propensity use | Notes |
| --- | --- | --- | --- | --- |
| Simple baseline CATE/ATE; one outcome model with treatment prepended | `BaseSRegressor`, `BaseSClassifier`, `LRSRegressor` | One learner per non-control treatment group | Ignored for S except signature compatibility | Good first pass; S-classifier needs `predict_proba`. |
| Separate response surfaces by treatment and control | `BaseTRegressor`, `BaseTClassifier`, `XGBTRegressor`, `XGBTClassifier`, `MLPTRegressor` | Shared control model plus one treatment model per group | `p` is unused | Use when response functions differ strongly by arm. |
| Imbalanced treatment groups or strong response-surface asymmetry | `BaseXRegressor`, `BaseXClassifier` | Outcome models plus treatment-effect models | Uses `p` or estimates it | Classifier variant uses classifiers for outcomes and regressors for effects. |
| Orthogonalized residual-on-residual estimation | `BaseRRegressor`, `BaseRClassifier`, `XGBRRegressor`, `XGBRClassifier` | Outcome model, effect model, propensity model | Uses `p` or estimates it | Effect learner must accept `sample_weight` when sample weights are used. |
| Doubly robust pseudo-outcome with cross-fitting | `BaseDRRegressor`, `BaseDRClassifier`, `XGBDRRegressor` | Outcome models plus treatment-effect model | Uses `p` or estimates it | `seed` controls the three-fold cross-fitting split and bootstrap reproducibility. |

## Constructor choices

### S-learner

```python
from causalml.inference.meta import BaseSRegressor, BaseSClassifier, LRSRegressor

s_reg = BaseSRegressor(learner=LinearRegression(), control_name=0)
s_clf = BaseSClassifier(learner=LogisticRegression(max_iter=1000), control_name=0)
lr_s = LRSRegressor(control_name=0)
```

- `BaseSRegressor` defaults to a dummy regressor if no learner is supplied.
- `BaseSClassifier` should be passed a classifier with `predict_proba`.
- `LRSRegressor` is a linear S-learner backed by a statsmodels OLS helper.
  Its `estimate_ate` always returns `(ate, lb, ub)`.

### T-learner

```python
from causalml.inference.meta import BaseTRegressor, BaseTClassifier, XGBTRegressor

# Same model class for control and all treatment arms.
t_reg = BaseTRegressor(learner=LinearRegression(), control_name=0)

# Or supply separate model objects for control and treatment outcomes.
t_custom = BaseTRegressor(
    control_learner=LinearRegression(),
    treatment_learner=LinearRegression(),
    control_name=0,
)

xgb_t = XGBTRegressor(control_name=0, n_estimators=50, random_state=42)
```

- Passing `learner=` creates a control outcome model and one treatment outcome
  model per non-control group.
- Passing `control_learner=` and `treatment_learner=` lets the control and
  treatment surfaces differ.
- `XGBTClassifier` stores XGBoost parameters in `xgb_kwargs`, for example
  `XGBTClassifier(xgb_kwargs={"n_estimators": 30, "random_state": 42})`.

### X-learner

```python
from causalml.inference.meta import BaseXRegressor, BaseXClassifier

x_reg = BaseXRegressor(learner=LinearRegression(), control_name=0)
x_reg.fit(X=X, treatment=treatment, y=y, p=p)
cate = x_reg.predict(X=X, p=p)

x_clf = BaseXClassifier(
    outcome_learner=LogisticRegression(max_iter=1000),
    effect_learner=LinearRegression(),
    control_name=0,
)
```

- Regressor path: pass one `learner=` or all four specialized learners:
  `control_outcome_learner`, `treatment_outcome_learner`,
  `control_effect_learner`, `treatment_effect_learner`.
- Classifier path: pass `outcome_learner` and `effect_learner`, or all four
  specialized learners. Outcome learners need `predict_proba`; effect learners
  are regressors.
- If `p` is omitted, the learner estimates propensity internally and stores
  `propensity`/`propensity_model` for later prediction.

### R-learner

```python
from causalml.inference.meta import BaseRRegressor

r_reg = BaseRRegressor(
    outcome_learner=LinearRegression(),
    effect_learner=LinearRegression(),
    random_state=42,
    control_name=0,
)
r_reg.fit(X=X, treatment=treatment, y=y, p=p, verbose=False)
cate = r_reg.predict(X=X, p=p)
te, yhat, p_dict = r_reg.predict(X=X, p=p, return_components=True)
```

- Pass one `learner=` for both nuisance outcome and effect models, or pass
  `outcome_learner=` and `effect_learner=` separately.
- `propensity_learner` defaults to an elastic-net propensity model. A supplied
  propensity learner is used on the first fit when `p=None`.
- `predict` intentionally has signature `predict(X, p=None,
  return_components=False)` and does not take `treatment` or `y`.
- `return_components=True` returns `(te, yhat, p_dict)` where `yhat` has shape
  `(n_samples,)` and each `p_dict[group]` has shape `(n_samples,)`.

### DR-learner

```python
from causalml.inference.meta import BaseDRRegressor

dr_reg = BaseDRRegressor(
    learner=LinearRegression(),
    treatment_effect_learner=LinearRegression(),
    control_name=0,
)
dr_reg.fit(X=X, treatment=treatment, y=y, p=p, seed=42)
cate = dr_reg.predict(X=X)
ate, lb, ub = dr_reg.estimate_ate(X=X, treatment=treatment, y=y, p=p, seed=42)
```

- Pass one `learner=` for all nuisance/effect roles or specialized outcome and
  treatment-effect learners.
- `fit` uses three-fold cross-fitting; pass `seed=` for deterministic splits.
- `fit_predict(..., return_ci=True, seed=...)` and
  `estimate_ate(..., bootstrap_ci=True, seed=...)` use the seed for reproducible
  bootstrap intervals.

## CATE and ATE recipes

### Fit then predict CATE

```python
learner.fit(X=X_train, treatment=w_train, y=y_train, p=p_train)
cate_test = learner.predict(X=X_test, p=p_test)
```

Use `p=` at prediction for X/R learners when you did not let the learner fit a
propensity model, or when you need externally calibrated propensities on the
new rows. S/T/DR `predict` can be called without `p` after fit.

### One-call CATE

```python
cate = learner.fit_predict(X=X, treatment=treatment, y=y, p=p)
```

For S/T/X/R/DR meta-learners, `fit_predict` returns a NumPy CATE array of shape
`(n_samples, n_treatment_groups)`. With `return_ci=True`, it returns
`(cate, cate_lower, cate_upper)` with matching shapes. Avoid combining
`return_ci=True` and `return_components=True`; some families reject that
combination and it is hard to consume consistently.

### ATE

```python
ate, lb, ub = learner.estimate_ate(X=X, treatment=treatment, y=y, p=p)
```

Family-specific return details:

- `BaseSRegressor`/`BaseSClassifier`: default `return_ci=False` returns only
  `ate`; use `return_ci=True` to receive `(ate, lb, ub)`.
- `LRSRegressor`: returns `(ate, lb, ub)` and has no `return_ci` parameter.
- T/X/R/DR families: return `(ate, lb, ub)` by default; pass
  `bootstrap_ci=True` for bootstrap intervals where supported.
- `pretrain=True` reuses the existing fitted model. Call `fit` first, or call an
  ATE method once with `pretrain=False` before reusing `pretrain=True`.

### Stored bootstrap intervals for T-learners

`BaseTRegressor` and `BaseTClassifier` can train a bootstrap ensemble during
`fit` and use it later in `predict(return_ci=True)`:

```python
t = BaseTRegressor(learner=LinearRegression(), control_name=0)
t.fit(
    X=X,
    treatment=treatment,
    y=y,
    store_bootstraps=True,
    n_bootstraps=20,
    bootstrap_size=min(1000, len(y)),
    random_state=42,
    n_jobs=1,
)
cate, lb, ub = t.predict(X=X_new, return_ci=True)
```

Calling `predict(return_ci=True)` without `fit(..., store_bootstraps=True)`
raises an error.

## Multi-treatment routing

For multiple active treatment groups, keep `control_name` explicit and pass a
propensity dictionary for X/R/DR learners:

```python
control_name = "control"
p = {
    "email": p_email,      # shape (n_samples,), values strictly inside (0, 1)
    "coupon": p_coupon,
}
learner = BaseXRegressor(learner=LinearRegression(), control_name=control_name)
learner.fit(X=X, treatment=treatment_labels, y=y, p=p)
cate = learner.predict(X=X_new, p={"email": p_email_new, "coupon": p_coupon_new})

for group, column in learner._classes.items():
    group_cate = cate[:, column]
```

Do not infer columns by label order from the original data. Use `learner.t_groups`
or `learner._classes` after fitting.
