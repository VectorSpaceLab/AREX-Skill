# Decision optimization

This reference covers causalml 0.17.0 APIs that turn fitted treatment-effect or outcome models into treatment decisions, values, and probability-of-causation bounds.

## PolicyLearner

Import:

```python
from causalml.optimize import PolicyLearner
```

Signature:

```python
PolicyLearner(
    outcome_learner=GradientBoostingRegressor(),
    treatment_learner=GradientBoostingClassifier(),
    policy_learner=DecisionTreeClassifier(),
    clip_bounds=(1e-3, 1 - 1e-3),
    n_fold=5,
    random_state=None,
    calibration=False,
)
```

Workflow:

```python
policy = PolicyLearner(random_state=42)
policy.fit(X=X_np, treatment=w_binary, y=y, p=propensity_scores, dhat=tau_hat)
assignments = policy.predict(X_new)
assignment_scores = policy.predict_proba(X_new)
```

Contract:

- Binary treatment only: `treatment` is a vector with `1` for treated and `0` for control.
- `X` is a numeric feature matrix. The implementation indexes `X` with NumPy fold indices, so a NumPy array is the safest input.
- `y` is a one-dimensional outcome vector.
- `p` is optional user-provided propensity. If omitted, propensity is cross-fit internally and clipped to `clip_bounds`.
- `dhat` is optional user-provided treatment-effect prediction. If supplied, it replaces the internally estimated treatment effect used to build the policy target.
- `policy_learner.fit(X, target, sample_weight=...)` must accept `sample_weight`.
- `predict(X)` delegates to the fitted policy learner.
- `predict_proba(X)` returns the fitted policy learner probability for class column `[:, 1]`; the underlying estimator therefore needs `predict_proba` and a conventional binary class layout.

`PolicyLearner.fit` builds a doubly robust score from outcome estimates, propensity estimates, and treatment effects, then trains the policy classifier on `sign(dr_score)` with absolute DR score as sample weight. Inspect the trained policy for interpretability the same way you would inspect the supplied `policy_learner`.

## CounterfactualUnitSelector

Import:

```python
from causalml.optimize import CounterfactualUnitSelector
```

Signature:

```python
CounterfactualUnitSelector(
    learner,
    nevertaker_payoff,
    alwaystaker_payoff,
    complier_payoff,
    defier_payoff,
    organic_conversion=None,
)
```

Workflow:

```python
selector = CounterfactualUnitSelector(
    learner=base_classifier,
    nevertaker_payoff=0.0,
    alwaystaker_payoff=0.0,
    complier_payoff=1.0,
    defier_payoff=-1.0,
)
selector.fit(data=df_with_features_w_y, treatment="w", outcome="y")
payoff = selector.predict(data=df_with_features_w_y, treatment="w", outcome="y")
```

Contract:

- This implementation is explicitly experimental.
- `data` is a DataFrame containing feature columns plus the treatment and outcome columns.
- `treatment` and `outcome` are column names. Both columns are assumed binary with `1` and `0` values.
- `learner` is cloned and fit internally. It must support classifier-style `fit` and `predict_proba`, and expose `classes_` after fitting.
- `fit(data, treatment, outcome)` mutates the selector and does not return `self`.
- `predict(data, treatment, outcome)` returns an estimated individual-level payoff array.
- If `complier_payoff + defier_payoff == alwaystaker_payoff + nevertaker_payoff`, the exact benefit path is used. Otherwise, conditional-probability models are fit and the midpoint between counterfactual bounds is returned.
- If `organic_conversion` is omitted on the non-gain-equality path, the control-group conversion probability is used and a warning is emitted.

The selector creates four observed segments from treatment/outcome combinations: `AC`, `AD`, `ND`, and `NC`. Keep enough samples in each observed segment for the base classifier to learn all required classes.

## CounterfactualValueEstimator

Imports:

```python
from causalml.optimize import CounterfactualValueEstimator
from causalml.optimize.utils import get_treatment_costs, get_actual_value, get_uplift_best
```

Signature:

```python
CounterfactualValueEstimator(
    treatment,
    control_name,
    treatment_names,
    y_proba,
    cate,
    value,
    conversion_cost,
    impression_cost,
)
```

Data contract:

- `treatment`: observed treatment labels, shape `(n,)`.
- `control_name`: label of the control group and a value present in `treatment`.
- `treatment_names`: list of non-control treatment labels. Its order must match the columns of `cate`.
- `y_proba`: predicted probability of conversion for each row under the observed assignment, shape `(n,)`.
- `cate`: CATE predictions relative to control, shape `(n, len(treatment_names))`.
- `value`: per-row conversion value, shape `(n,)`.
- `conversion_cost`: cost paid on conversion for each condition, shape `(n, 1 + len(treatment_names))`.
- `impression_cost`: cost paid regardless of conversion for each condition, shape `(n, 1 + len(treatment_names))`.

The condition order inside the estimator is `[control_name] + treatment_names`. Keep this same order for cost matrices and downstream index-to-label mapping.

Workflow:

```python
conversion_cost, impression_cost, conditions = get_treatment_costs(
    treatment=df["treatment_group_key"],
    control_name="control",
    cc_dict={"control": 0.0, "treatment1": 2.5, "treatment2": 5.0},
    ic_dict={"control": 0.0, "treatment1": 0.0, "treatment2": 0.02},
)

cve = CounterfactualValueEstimator(
    treatment=df_test["treatment_group_key"],
    control_name="control",
    treatment_names=conditions[1:],
    y_proba=y_proba,
    cate=cate_pred,
    value=conversion_value,
    conversion_cost=conversion_cost_test,
    impression_cost=impression_cost_test,
)
best_idx = cve.predict_best()
best_labels = [conditions[i] for i in best_idx]
expected_values = cve.predict_counterfactuals()
```

`predict_best()` returns integer indices into `[control_name] + treatment_names`, not treatment labels. `predict_counterfactuals()` returns the expected value matrix for each row and condition.

`get_treatment_costs(...)` builds conversion/impression cost matrices from dictionaries and returns `conditions` with control first and other conditions sorted. Make sure dictionary insertion order and sorted condition order match the labels you intend; if you build cost arrays manually, use the estimator condition order.

`get_actual_value(treatment, observed_outcome, conversion_value, conditions, conversion_cost, impression_cost)` computes observed assignment value for benchmarking a policy.

`get_uplift_best(cate, conditions)` adds a zero control column to a CATE matrix and returns labels of the maximum-uplift condition. It ignores costs and conversion values, so use `CounterfactualValueEstimator` when treatments are costly.

## PNS, PN, and PS bounds

Import:

```python
from causalml.optimize import get_pns_bounds
```

Signature:

```python
lower, upper = get_pns_bounds(data_exp, data_obs, T="w", Y="y", type="PNS")
```

Contract:

- `data_exp`: experimental/interventional data frame.
- `data_obs`: observational data frame from the same target population or a justifiable random sample of it.
- `T`: binary treatment indicator column name, values `0` and `1`.
- `Y`: binary outcome indicator column name, values `0` and `1`.
- `type`: one of exact strings `"PNS"`, `"PN"`, or `"PS"`.

Definitions:

- `PNS`: probability of necessary and sufficient causation.
- `PN`: probability of necessary causation.
- `PS`: probability of sufficient causation.

The function returns `(lower_bound, upper_bound)`. For `PN`, the observational probability of `(T=1, Y=1)` appears in a denominator; for `PS`, `(T=0, Y=0)` appears in a denominator. Check those cells are non-zero before interpreting the bounds.

## Choosing an optimization API

| Need | Use | Key input |
| --- | --- | --- |
| Learn a binary treatment policy from observational data | `PolicyLearner` | `X`, binary treatment, outcome, optional propensity/CATE |
| Estimate individual payoff from counterfactual unit types | `CounterfactualUnitSelector` | Binary treatment/outcome DataFrame and payoff constants |
| Choose among multiple costly treatments | `CounterfactualValueEstimator` | Observed conversion probability, CATE matrix, per-condition costs/values |
| Bound probability that treatment caused an outcome | `get_pns_bounds` | Experimental and observational binary treatment/outcome data |
| Recommend highest uplift ignoring costs | `get_uplift_best` | CATE matrix and condition labels |
