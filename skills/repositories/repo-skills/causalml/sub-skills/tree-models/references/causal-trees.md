# Causal trees

This reference covers the continuous-outcome causal tree and causal forest stack.

## Core contract

| Class | Fit | Predict | Other methods | Notes |
| --- | --- | --- | --- | --- |
| `CausalTreeRegressor` | `fit(X, treatment, y, sample_weight=None, check_input=True, prepare_data=True)` | `predict(X, with_outcomes=False, check_input=True)` | `fit_predict`, `estimate_ate`, `bootstrap`, `bootstrap_pool`, `save`, `load` | `predict` returns treatment-effect columns; for a single treatment contrast the result may be 1D. `with_outcomes=True` prepends the per-group potential outcomes. |
| `CausalRandomForestRegressor` | `fit(X, treatment, y, sample_weight=None)` | `predict(X, with_outcomes=False)` | `calculate_error`, `save`, `load` | No `fit_predict` or `estimate_ate`; fit first, then predict. `calculate_error` is only available when the forest has one treatment contrast. |

## What to remember

- `control_name` identifies the control group label.
- `sample_weight` is the place to pass inverse-propensity weights for observational data.
- Supported tree criteria are `causal_mse`, `standard_mse`, and `t_test`.
- `criterion="causal_mse"` requires `min_impurity_decrease=-inf`.
- `ccp_alpha="cv"` requires `honesty=True`.
- `honesty=True` is the default for both classes.

## Typical tree workflow

```python
from causalml.inference.tree import CausalTreeRegressor

model = CausalTreeRegressor(control_name=0, honesty=True, random_state=42)
model.fit(X=X_train, treatment=treatment_train, y=y_train)
ite = model.predict(X_test)
```

If you need a summary of the average treatment effect, use the tree helper:

```python
ate, ate_lb, ate_ub = model.estimate_ate(X=X_train, treatment=treatment_train, y=y_train)
```

If you need bootstrap intervals from a single tree, use `fit_predict(..., return_ci=True)`.

## Forest workflow

```python
from causalml.inference.tree import CausalRandomForestRegressor

forest = CausalRandomForestRegressor(control_name=0, n_estimators=100, random_state=42)
forest.fit(X=X_train, treatment=treatment_train, y=y_train)
ite = forest.predict(X_test)
```

Use `with_outcomes=True` on either class when you want the potential-outcome columns before the treatment-effect columns.

## Visualization

Use the matplotlib helper for causal trees when you want an axis-based figure.

```python
from causalml.inference.tree.plot import plot_causal_tree

plot_causal_tree(model, ax=ax, pvalue=True)
```

- Fit the tree with `node_pvalues=True` if you want node p-values to appear in the plot.
- `pvalue=True` on the plot helper only shows p-values that were computed during fit.
- `plot_dist_tree_leaves_values(...)` is a quick way to inspect the leaf-effect distribution.

## Persistence

Tree and forest models save through the shared persistence mixin.

```python
model.save("tree.causalml")
loaded = CausalTreeRegressor.load("tree.causalml")
```

Load with the same class you saved. Class-mismatched loads raise an error.
