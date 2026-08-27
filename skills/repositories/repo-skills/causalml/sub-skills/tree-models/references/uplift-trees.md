# Uplift trees

This reference covers binary-outcome uplift trees and uplift forests, plus their fill, prune, and visualization helpers.

## Core contract

| Class / helper | Contract | Notes |
| --- | --- | --- |
| `UpliftTreeClassifier` | `fit(X, treatment, y, X_val=None, treatment_val=None, y_val=None, sample_weight=None, check_input=True)`<br>`predict(X, check_input=True)` | `predict` returns per-group `P(Y=1 | T=g)` with the control group in column 0. `fill`, `prune`, `fitted_uplift_tree`, `feature_importances_`, `save`, and `load` are available. |
| `UpliftRandomForestClassifier` | `fit(X, treatment, y, X_val=None, treatment_val=None, y_val=None, sample_weight=None)`<br>`predict(X, full_output=False)` | `predict` returns uplift deltas by default. `full_output=True` returns a DataFrame with per-group probabilities, a recommended-treatment column, delta columns, and `max_delta`. `uplift_forest`, `save`, and `load` are available. |
| `uplift_tree_string` | `uplift_tree_string(tree.fitted_uplift_tree, x_names)` | Prints a text rendering of the tree. It does not return a string object. |
| `uplift_tree_plot` | `uplift_tree_plot(tree.fitted_uplift_tree, x_names)` | Returns a `pydotplus` graph object. Rendering methods such as `create_png()` need Graphviz support. |

## Criterion families

- Multi-treatment choices: `KL`, `ED`, `Chi`, `CTS`
- Two-class choices: `DDP`, `IT`, `CIT`, `IDDP`
- `DDP`, `IT`, `CIT`, and `IDDP` reject multi-treatment input.
- `IDDP` forces `honesty=True`.

## Typical tree workflow

```python
from causalml.inference.tree import UpliftTreeClassifier

model = UpliftTreeClassifier(
    control_name="control",
    evaluationFunction="KL",
    honesty=False,
    random_state=42,
)
model.fit(X=X_train, treatment=treatment_train, y=y_train)
proba = model.predict(X_test)
```

If you want a validation refresh without changing structure, call `fill(...)` with a new batch of rows.
If you want the tree structure itself simplified on held-out data, call `prune(...)`.

```python
model.fill(X=X_val, treatment=treatment_val, y=y_val)
model.prune(X=X_val, treatment=treatment_val, y=y_val, minGain=0.0001, rule="maxAbsDiff")
```

`prune_fraction` moves part of the training rows into an internal holdout before the honest split. `prune_fraction` may be `None` to disable this behavior; `estimation_sample_size` must always be a strict fraction in `(0, 1)`.

## Forest workflow

```python
from causalml.inference.tree import UpliftRandomForestClassifier

forest = UpliftRandomForestClassifier(control_name="control", n_estimators=50, random_state=42)
forest.fit(X=X_train, treatment=treatment_train, y=y_train)
delta = forest.predict(X_test)
full = forest.predict(X_test, full_output=True)
```

`full_output=True` is the easiest way to inspect the class-order probabilities and the recommended treatment chosen by the forest.

## Visualization

For the text helper, pass the legacy-shaped tree node:

```python
from causalml.inference.tree import uplift_tree_string

uplift_tree_string(model.fitted_uplift_tree, x_names)
```

For a rendered graph:

```python
from causalml.inference.tree import uplift_tree_plot

graph = uplift_tree_plot(model.fitted_uplift_tree, x_names)
image = graph.create_png()
```

`uplift_tree_plot` depends on both Python `pydotplus` and the Graphviz runtime. If PNG generation fails, check those dependencies first.

## Persistence

Tree and forest models save through the shared persistence mixin.

```python
model.save("uplift.causalml")
loaded = UpliftTreeClassifier.load("uplift.causalml")
```

Load with the same class you saved. Class-mismatched loads raise an error.

## Quick reminders

- `y` is coerced to binary for uplift trees.
- `feature_importances_` on `UpliftTreeClassifier` is normalized and non-negative.
- `X_val` / `treatment_val` / `y_val` are accepted by the forest for compatibility, but validation-set early stopping is not implemented.
