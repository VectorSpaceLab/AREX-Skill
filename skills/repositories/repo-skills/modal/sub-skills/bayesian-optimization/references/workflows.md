# BayesianOptimizer Workflows

## Purpose

Read this reference to build self-contained Bayesian optimization workflows with modAL's `BayesianOptimizer`. It distills the package's Bayesian optimization examples, model docs, source implementation, and tests into runnable patterns that do not require the original repository checkout.

## Core mental model

`BayesianOptimizer` is an `ActiveLearner`-style wrapper for maximization of expensive scalar functions. The estimator models the scalar objective from evaluated points; the query strategy chooses the next candidate by an acquisition rule; `teach()` adds the newly evaluated point and updates `X_max`/`y_max`.

Use it for **maximization**. To minimize a loss, teach the optimizer the negative loss or another score where larger is better.

## Initialization pattern

```python
import numpy as np
from modAL.models import BayesianOptimizer
from modAL.acquisition import max_EI
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

X_grid = np.linspace(-4.0, 4.0, 81).reshape(-1, 1)  # (n_candidates, n_features)
X_initial = X_grid[[0, 40, 80]]                      # already evaluated rows

def objective(X):
    X = np.asarray(X).reshape(-1, 1)
    return (np.sin(X[:, 0]) - 0.05 * (X[:, 0] - 1.5) ** 2).reshape(-1)

y_initial = objective(X_initial)                     # one scalar per row, shape (3,)

optimizer = BayesianOptimizer(
    estimator=GaussianProcessRegressor(
        kernel=Matern(length_scale=1.0),
        alpha=1e-6,
        normalize_y=True,
        optimizer=None,
    ),
    query_strategy=max_EI,
    X_training=X_initial,
    y_training=y_initial,
)
```

Shape rules:

- `X_training` and `X_pool` should usually be 2-D: `(n_samples, n_features)`. For a one-dimensional objective, still use `(n, 1)`.
- `y_training` should contain one numeric scalar per evaluated row. A 1-D shape `(n,)` is easiest to keep compatible with `y_max`; a column vector `(n, 1)` also appears in examples but can make scalar comparisons and printing less convenient.
- A single objective result should be normalized to shape `(1,)` before `teach()`.
- `bootstrap_init` and `on_transformed` are accepted by the initializer because `BayesianOptimizer` inherits the learner interface. For Gaussian-process optimization, prefer `bootstrap_init=False` unless you intentionally want a bootstrap fit. Built-in acquisition functions call the estimator's `predict(X, return_std=True)` on the candidate representation they receive; do not rely on `on_transformed` as an acquisition-specific preprocessing step.

## Bounded objective loop

For expensive objectives, query first and evaluate only the selected row(s):

```python
budget = 5
X_pool = X_grid.copy()

for step in range(budget):
    query_idx, query_inst = optimizer.query(X_pool)
    query_idx = np.asarray(query_idx).reshape(-1)     # indices are relative to X_pool
    query_inst = np.asarray(query_inst).reshape(len(query_idx), -1)

    y_new = objective(query_inst).reshape(-1)         # one scalar per queried row
    optimizer.teach(query_inst, y_new)

    # Optional for pure candidate-grid optimization: avoid re-querying evaluated rows.
    X_pool = np.delete(X_pool, query_idx, axis=0)

X_max, y_max = optimizer.get_max()
```

Operational rules:

- Do **not** evaluate `objective(X_pool)` inside the loop unless this is a toy benchmark where the full grid is intentionally known. In real Bayesian optimization, evaluating the whole pool defeats the purpose.
- Treat `query_idx` as row indices into the exact pool passed to `optimizer.query()`, not global design IDs unless you maintain that mapping yourself.
- If `n_instances > 1`, evaluate every row in `query_inst` and teach one scalar per row.
- Cache objective evaluations by a stable candidate key when the objective is expensive or candidates can repeat.
- Stop at a fixed budget, target score, time limit, or no-improvement rule; modAL itself does not enforce an objective budget.

## 1-D candidate grid recipe

Use a dense grid only as the candidate set; evaluate single selected points:

```python
X_pool = np.linspace(-3.0, 3.0, 121).reshape(-1, 1)
seed_idx = np.array([0, 60, 120])
X_initial = X_pool[seed_idx]
y_initial = objective(X_initial)
X_pool = np.delete(X_pool, seed_idx, axis=0)
```

This mirrors the package example's 1-D synthetic function while removing plotting and full-grid objective calls from the runtime workflow.

## Multidimensional candidate grid recipe

For a bounded 2-D or higher-dimensional search space, create candidate rows with `meshgrid` or an explicit design matrix:

```python
axis_1 = np.linspace(-2.0, 2.0, 17)
axis_2 = np.linspace(-1.0, 3.0, 17)
grid_1, grid_2 = np.meshgrid(axis_1, axis_2, indexing="ij")
X_pool = np.column_stack([grid_1.ravel(), grid_2.ravel()])  # (289, 2)
```

For non-grid design spaces, `X_pool` can be any finite candidate matrix such as random Latin-hypercube samples, a hand-curated hyperparameter table, or encoded categorical choices. Keep the row order stable so `query_idx` remains meaningful.

## Comparing EI, PI, and UCB under one budget

Use `functools.partial` to set exploration parameters without changing modAL's query-strategy contract:

```python
from functools import partial
from modAL.acquisition import max_PI, max_EI, max_UCB

strategies = {
    "PI": partial(max_PI, tradeoff=0.05),
    "EI": partial(max_EI, tradeoff=0.05),
    "UCB": partial(max_UCB, beta=1.5),
}
```

For a fair comparison, reinitialize a fresh `BayesianOptimizer` for each strategy with the same initial evaluated points and the same candidate pool copy. Run the same budget and compare only observed `get_max()` values, not optimistic predictions over unevaluated points.

## Inspecting acquisition scores without evaluating the objective

The `optimizer_PI`, `optimizer_EI`, and `optimizer_UCB` functions score all rows in a candidate matrix using the current fitted estimator. Use them to diagnose why a candidate was selected:

```python
from modAL.acquisition import optimizer_EI

ei_scores = np.asarray(optimizer_EI(optimizer, X_pool, tradeoff=0.05)).reshape(-1)
best_score_idx = int(np.argmax(ei_scores))
```

These scores are model utilities, not measured objective values. They can be logged or plotted in a notebook, but they should not replace `teach()` with real observations.

## Evidence distilled

This reference is grounded in the `BayesianOptimizer` model docs, acquisition-function docs, `BayesianOptimizer` and acquisition source implementations, the 1-D and multidimensional Bayesian optimization examples, and the repository's Bayesian optimizer/acquisition tests. Those sources were distilled here so future agents do not need to open or run original repository files.
