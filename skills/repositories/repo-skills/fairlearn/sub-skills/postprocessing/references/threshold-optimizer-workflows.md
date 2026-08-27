# ThresholdOptimizer workflows

`ThresholdOptimizer` postprocesses the outputs of a predictor to satisfy parity constraints as closely as possible under a chosen objective.

## Constructor and fit

Verified constructor:

```text
ThresholdOptimizer(
    *,
    estimator=None,
    constraints="demographic_parity",
    objective="accuracy_score",
    grid_size=1000,
    flip=False,
    prefit=False,
    predict_method="auto",
    tol=None,
)
```

Fit/predict signatures:

```text
fit(X, y, *, sensitive_features, **kwargs)
predict(X, *, sensitive_features, random_state=None)
```

Minimal example:

```python
from sklearn.linear_model import LogisticRegression
from fairlearn.postprocessing import ThresholdOptimizer

optimizer = ThresholdOptimizer(
    estimator=LogisticRegression(solver="liblinear"),
    constraints="demographic_parity",
    objective="accuracy_score",
    predict_method="predict_proba",
    prefit=False,
)
optimizer.fit(X_train, y_train, sensitive_features=A_train)
pred = optimizer.predict(X_test, sensitive_features=A_test, random_state=0)
```

## Constraint and objective options

Constraints verified from source:

- `demographic_parity` and `selection_rate_parity` match selection rates across groups.
- `false_negative_rate_parity`
- `false_positive_rate_parity`
- `true_negative_rate_parity`
- `true_positive_rate_parity`
- `equalized_odds` matches both false-positive and true-positive behavior.

Objectives verified from source:

- `accuracy_score` and `balanced_accuracy_score` are allowed for all constraint types.
- `selection_rate`, `true_positive_rate`, and `true_negative_rate` are allowed for simple constraints, but not for `equalized_odds`.

`tol` relaxes simple constraints by allowing a bounded range in the constraint metric. The inspected source raises an error if `tol` is used with `equalized_odds`.

## Choosing `predict_method`

| Option | Meaning | Use when |
| --- | --- | --- |
| `auto` | Try `predict_proba`, then `decision_function`, then `predict`. | Quick use with standard sklearn classifiers. |
| `predict_proba` | Use the second probability column as positive-outcome score. | Binary classifiers with calibrated or meaningful probabilities. |
| `decision_function` | Use raw decision scores. | Margin-based estimators such as SVMs. |
| `predict` | Use hard predictions or regression values. | Only when no better score method exists or to match the original Hardt-style setup. |

Prefer scores over hard predictions when available; threshold optimization has more freedom when the base estimator outputs a continuum of values.

## `prefit` decision

Use `prefit=True` when:

- the estimator has already been fitted on the intended training data;
- you do not want `ThresholdOptimizer.fit` to refit it; and
- the optimizer will not be cloned by cross-validation or model-selection utilities.

Use `prefit=False` when:

- building a normal sklearn workflow;
- running cross-validation or `GridSearchCV`; or
- you are not certain the estimator is fitted.

## Plotting the optimizer

`plot_threshold_optimizer` requires matplotlib and a fitted optimizer:

```python
import matplotlib.pyplot as plt
from fairlearn.postprocessing import plot_threshold_optimizer

fig, ax = plt.subplots()
plot_threshold_optimizer(optimizer, ax=ax, show_plot=False)
fig.savefig("threshold-optimizer.png", bbox_inches="tight")
```

The inspected plotting function draws on the provided axes and does not return an axes object. Use this plot to inspect trade-off curves and selected thresholds. It is not a substitute for a `MetricFrame` report on held-out predictions.

## Evaluation pattern

```python
from sklearn.metrics import accuracy_score
from fairlearn.metrics import MetricFrame, selection_rate

pred_base = base_estimator.predict(X_test)
pred_post = optimizer.predict(X_test, sensitive_features=A_test, random_state=0)

for label, pred in {"base": pred_base, "postprocessed": pred_post}.items():
    mf = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate},
        y_true=y_test,
        y_pred=pred,
        sensitive_features=A_test,
    )
    print(label, mf.overall)
    print(mf.by_group)
    print(mf.difference())
```

## Reporting checklist

- State base estimator type and score method.
- State constraint, objective, grid size, `tol`, `flip`, and `prefit`.
- Report subgroup metrics before and after postprocessing.
- If predictions are randomized, state the `random_state` used.
- Do not claim the threshold plot alone demonstrates fairness.
