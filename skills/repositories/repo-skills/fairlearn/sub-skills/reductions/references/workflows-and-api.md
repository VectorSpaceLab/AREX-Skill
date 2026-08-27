# Reductions workflows and API

Reductions mitigation turns constrained fairness problems into a sequence or grid of ordinary supervised-learning problems. Fairlearn provides sklearn-style meta-estimators around a base estimator.

## Algorithm choice

| Need | Use |
| --- | --- |
| Iterative constrained optimization with mixtures over classifiers | `ExponentiatedGradient` |
| A finite set of Lagrange multipliers and explicit grid diagnostics | `GridSearch` |
| Regression or multiclass-style loss parity | `BoundedGroupLoss` with a loss moment such as `SquareLoss` or `AbsoluteLoss` |
| Binary classification parity | `DemographicParity`, `EqualizedOdds`, or another classification moment |

## ExponentiatedGradient

Verified constructor:

```text
ExponentiatedGradient(
    estimator,
    constraints,
    *,
    objective=None,
    eps=0.01,
    max_iter=50,
    nu=None,
    eta0=2.0,
    run_linprog_step=True,
    sample_weight_name="sample_weight",
)
```

Example:

```python
from sklearn.linear_model import LogisticRegression
from fairlearn.reductions import DemographicParity, ExponentiatedGradient

base = LogisticRegression(solver="liblinear", random_state=0)
mitigator = ExponentiatedGradient(base, DemographicParity(), eps=0.02, max_iter=50)
mitigator.fit(X_train, y_train, sensitive_features=A_train)
pred = mitigator.predict(X_test)
```

Important fitted attributes often useful for debugging include predictor mixtures, weights, gaps, and internal oracle calls. Attribute names can change across versions, so use them for inspection rather than as stable serialized outputs.

## GridSearch

Verified constructor:

```text
GridSearch(
    estimator,
    constraints,
    selection_rule="tradeoff_optimization",
    constraint_weight=0.5,
    grid_size=10,
    grid_limit=2.0,
    grid_offset=None,
    grid=None,
    sample_weight_name="sample_weight",
)
```

Example:

```python
from sklearn.tree import DecisionTreeClassifier
from fairlearn.reductions import EqualizedOdds, GridSearch

base = DecisionTreeClassifier(max_depth=3, random_state=0)
mitigator = GridSearch(base, EqualizedOdds(), grid_size=10, constraint_weight=0.6)
mitigator.fit(X_train, y_train, sensitive_features=A_train)
pred = mitigator.predict(X_test)
```

The inspected source supports only `selection_rule="tradeoff_optimization"`. That rule minimizes a weighted combination of error rate and constraint violation using `constraint_weight`.

## Constraint classes

| Constraint / moment | Typical use |
| --- | --- |
| `DemographicParity()` | Allocation-style parity of selection or prediction rate. |
| `EqualizedOdds()` | Conditional parity given true label; balances false-positive/true-positive behavior. |
| `TruePositiveRateParity()` | Equal-opportunity-style recall parity. |
| `FalsePositiveRateParity()` | False-positive-rate parity. |
| `ErrorRateParity()` | Equalized error rates across groups. |
| `BoundedGroupLoss(loss=SquareLoss(...))` or `AbsoluteLoss` | Regression or loss-bounded quality-of-service workflows. |
| `ErrorRate()` / `MeanLoss()` | Objectives or moments when building lower-level custom reductions workflows. |

Use the constraint that matches the user's stated harm and fairness metric. Do not switch constraints solely because one optimizes faster.

## Base estimator contract

The base estimator should implement:

```text
fit(X, y, sample_weight=weights)
predict(X)
```

If the sample-weight parameter has another name, set `sample_weight_name`.

Pipeline example:

```python
mitigator = ExponentiatedGradient(
    pipeline,
    DemographicParity(),
    sample_weight_name="classifier__sample_weight",
)
```

Here `classifier` is the name of the pipeline step that accepts sample weights.

## Evaluation pattern

Always compare against a baseline:

```python
from sklearn.metrics import accuracy_score
from fairlearn.metrics import MetricFrame, selection_rate, demographic_parity_difference

baseline.fit(X_train, y_train)
pred_base = baseline.predict(X_test)
pred_mitigated = mitigator.predict(X_test)

for label, pred in {"baseline": pred_base, "mitigated": pred_mitigated}.items():
    mf = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
        y_true=y_test,
        y_pred=pred,
        sensitive_features=A_test,
    )
    print(label)
    print(mf.overall)
    print(mf.by_group)
    print("dp difference", demographic_parity_difference(y_test, pred, sensitive_features=A_test))
```

## Practical parameter guidance

- Start with a small `max_iter` or `grid_size` for smoke checks.
- Increase iterations/grid size only after the base estimator and sensitive-feature alignment are verified.
- Set `random_state` on the base estimator where possible.
- Keep `eps`, `constraint_weight`, and objective choices visible in reports.
- Use assessment plots to communicate trade-offs, but keep the mitigation code here.
