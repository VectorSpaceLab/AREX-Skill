# Fit workflows for ordinary PySR searches

This reference covers ordinary `PySRRegressor` use from Python. It intentionally avoids advanced custom operators/losses, templates, and artifact-management details; route those to the sibling sub-skills listed in `../SKILL.md`.

## 1. Baseline fit recipe

```python
import numpy as np
from pysr import PySRRegressor

rng = np.random.default_rng(0)
X = rng.normal(size=(200, 3))
y = 1.5 * X[:, 0] - X[:, 1] ** 2

model = PySRRegressor(
    binary_operators=["+", "-", "*"],
    unary_operators=[],
    niterations=100,
    maxsize=12,
    model_selection="best",
    timeout_in_seconds=300,
    input_stream="devnull",  # useful in embedded shells/notebooks
)
model.fit(X, y, variable_names=["x0", "x1", "x2"])

print(model.equations_)
print(model.sympy())
print(model.latex())
yhat = model.predict(X)
```

Use this as the first working pattern unless the user has a domain reason for a larger search space.

## 2. Shape and naming checklist

- `X` must be two-dimensional with shape `(n_samples, n_features)`.
- `y` is `(n_samples,)` for one target or `(n_samples, n_outputs)` for separate multi-output equations.
- If `X` is a pandas DataFrame, PySR uses the DataFrame column names. If `X` is a NumPy array, pass `variable_names=[...]` to `fit` when readable equations matter.
- Keep variable names simple: letters, numbers, and underscores are safest. Avoid spaces, punctuation, braces, and names that collide with common symbolic functions.
- `weights` passed to `fit` must match the shape of `y`. Built-in losses apply weights automatically. If the user wants a custom weighted loss, route to `customization-and-constraints` because the loss signature must match the weighted form.
- For multi-output `y`, `model.equations_`, `sympy`, `latex`, and `predict` may return per-output structures; when selecting explicit rows for multiple outputs, pass a list of row indices in output order.

## 3. Operator/data choice workflow

Symbolic regression cost grows rapidly with features, operators, and allowed expression size. Choose search space before adding compute.

| Domain guess | Starter operators | Notes |
| --- | --- | --- |
| Linear or low-order polynomial | `binary_operators=["+", "-", "*"]`, no unary operators | Fastest robust first pass. `*` can represent powers by repeated multiplication. |
| Ratios or inverse relations | Add `/` only if needed | Division expands the search and can create singular behavior outside the data. |
| Periodic relation | Add `"sin"` and/or `"cos"` | Avoid redundant nested trig unless domain demands it. |
| Exponential growth/decay | Add `"exp"` after a polynomial baseline | Check target scale; MSE can be dominated by large values. |
| Square roots, logs, powers, domain-limited transforms | Prefer built-ins and route constraints/customization as needed | Advanced domain control belongs in `customization-and-constraints`. |

Practical sequence:

1. Subsample to a representative set for setup validation. A few hundred to a few thousand rows is often enough for a first pass.
2. Use the minimal feature set available from domain knowledge.
3. Fit with a narrow operator set and small `maxsize`.
4. Inspect the Pareto front. If the target family is absent but simple candidates are improving, increase time/iterations. If all rows are unrelated, revisit data and operators first.
5. Only widen operators after a successful narrow baseline or a clear domain need.

## 4. Pareto-front selection workflow

After `fit`, `model.equations_` is the main decision object. It stores equations across complexity levels with loss and a score-like measure of loss improvement per added complexity.

```python
eqs = model.equations_
print(eqs[["complexity", "loss", "score", "equation"]])

# Default selected row under model.model_selection:
row = model.get_best()

# Evaluate a specific row instead of the selected row:
idx = eqs["loss"].idxmin()
yhat_accuracy = model.predict(X_test, index=idx)
expr = model.sympy(index=idx)
tex = model.latex(index=idx, precision=4)
```

Selection guidance:

- `model_selection="best"` is the usual reporting default: it balances loss and simplicity by choosing a high-score row among equations close to the best loss.
- `model_selection="accuracy"` chooses the lowest-loss row. Use it when held-out performance matters more than compactness, but watch for overfitting.
- `model_selection="score"` chooses the largest score. Use it to find the sharpest Pareto-front kink, not necessarily the most accurate row.
- Report 2-3 candidate equations when the trade-off is ambiguous.
- Validate selected rows on held-out data if noise, many features, or large operator sets make overfitting plausible.
- Do not claim a global optimum or convergence from one evolutionary run. PySR is stochastic and may discover new families late in a long run.

## 5. Noisy data workflow

For noisy observations, try the least invasive methods first:

1. Use domain-appropriate preprocessing and obvious outlier checks outside PySR.
2. If rows have known uncertainty, pass `weights=1 / sigma**2` to `fit`.
3. If a robust or likelihood-style objective is required, route to `customization-and-constraints` for `elementwise_loss` or `loss_function` details.
4. For simple tabular denoising, set `denoise=True`. PySR applies a Gaussian-process denoising step before the symbolic search. This can help but adds preprocessing cost and is not a substitute for validating equations on original/held-out data.
5. If denoising should predict targets on a resampled grid, pass `Xresampled=` to `fit`; make sure it has the same feature schema as `X`.

```python
model = PySRRegressor(
    binary_operators=["+", "-", "*"],
    unary_operators=["exp"],
    denoise=True,
    niterations=100,
)
model.fit(X, y, weights=weights)  # weights optional
```

## 6. High-dimensional tabular workflow

Feature count is often a bigger bottleneck than row count.

1. Engineer or select physically meaningful features before PySR when possible.
2. For tabular data with many candidate columns, use `select_k_features=k` as a preprocessing fallback. It runs a tree-based feature selector before the Julia search and stores the selected mask on the model.
3. Keep `maxsize` consistent with the number of variables you expect in the equation. A many-term linear model already consumes many complexity nodes.
4. For many rows, subsample for setup; use `batching=True` when a large/noisy dataset really needs broad coverage during evolution. Runtime and parallelism details belong in `runtime-and-scaling`.

```python
model = PySRRegressor(
    binary_operators=["+", "-", "*", "/"],
    unary_operators=["cos"],
    select_k_features=5,
    maxsize=16,
    niterations=200,
)
model.fit(X, y)
print(model.feature_names_in_)  # transformed/selected feature names
```

If the selected variables are surprising, compare against a baseline fit on domain-chosen columns and test candidate equations on held-out data. Feature selection is a helper, not a proof of relevance.

## 7. Warm-start and iterative fitting

`warm_start=True` continues evolution from the previous `fit` call in the same Python process. Use it only when the search space is compatible:

- Safe-ish changes: longer budget, some staged losses/weights, or continuing after a short validation run.
- Risky/incompatible changes: feature count/order, operators, `maxsize`, expression/template specification, or precision. Reset instead of warm-starting.
- Default `warm_start=False` resets previous expressions on each `fit`.

```python
model = PySRRegressor(
    binary_operators=["+", "-", "*"],
    warm_start=True,
    niterations=50,
)
model.fit(X, y)
model.set_params(niterations=200)
model.fit(X, y)  # continues only because warm_start=True and search space is unchanged
```

If the user is changing the scientific hypothesis, start a fresh model and compare fronts rather than carrying over state.

## 8. Fit-quality review checklist

Before handing an equation back to the user:

- Does the equation use plausible variables and operators for the domain?
- Is the selected row on a meaningful Pareto-front kink, or is there a simpler row with nearly identical loss?
- Does held-out or resampled evaluation agree with training-front loss?
- Are singularities or extrapolation behavior acceptable for the intended domain?
- Was the target transformed, weighted, denoised, or feature-selected? Report those choices with the equation.
- Are custom operators/losses/templates involved? If yes, route to the corresponding sub-skill before promising exports or predictions.
