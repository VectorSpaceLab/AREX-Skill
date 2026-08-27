# Export reference

PySR exports are built around the Pareto-front rows in `model.equations_`. The fitting workflow owns how those rows were found; this reference owns how to choose, evaluate, and translate them after they exist.

## `equations_` and row selection

### Shape

- Single-output models store `model.equations_` as a pandas DataFrame.
- Multi-output models store `model.equations_` as a list of DataFrames, one per output.
- The core columns are `complexity`, `loss`, and `equation`.
- When the usual log loss scale is used, PySR also computes a `score` column. If `score` is absent, selection falls back to accuracy-based selection.
- Export columns are added from the equation strings and current model parameters: `sympy_format` and `lambda_format` by default; `jax_format` and `torch_format` only when the corresponding optional formats are requested and dependencies/mappings are available.

### `model_selection`

`model_selection` controls which row is chosen when no explicit row index is supplied.

| Value | Selection behavior | Use when |
| --- | --- | --- |
| `"best"` | Chooses the highest-`score` row among equations whose loss is within 1.5x of the minimum loss. | You want PySR's default accuracy/simplicity compromise. |
| `"accuracy"` | Chooses the row with the minimum `loss`. | You want the most accurate row regardless of complexity. |
| `"score"` | Chooses the row with the highest `score`. | You want the sharpest Pareto-front improvement/kink. |

The printed model marks the selected row in a `pick` column. The mark is only the current selection strategy, not proof that other rows are worse for the user's downstream objective.

### Explicit row indices

Use `index=` to override `model_selection`:

```python
best_row = model.get_best()       # uses model.model_selection
row_2 = model.get_best(index=2)   # third row by DataFrame position
last = model.get_best(index=-1)   # last row by DataFrame position

y_hat = model.predict(X_test, index=2)
expr = model.sympy(index=2)
tex = model.latex(index=2, precision=5)
```

For multi-output models, pass one row index per output:

```python
y_hat = model.predict(X_test, index=[2, -1])
exprs = model.sympy(index=[2, -1])
```

Use explicit indices when comparing held-out performance, reporting several candidate equations, matching a published row, or exporting a non-default Pareto-front point.

## NumPy and prediction exports

`lambda_format` is a callable NumPy-style equation derived from `sympy_format`. `model.predict(X, index=...)` evaluates the selected row's `lambda_format` after applying PySR's fitted feature-name and feature-selection handling.

Practical rules:

- Pass columns in the same order used during fitting unless you are using a DataFrame with matching fitted feature names.
- If `select_k_features` was used, the fitted `selection_mask_` determines which columns the export sees. Reloading from CSV requires the same mask to reproduce this behavior.
- If DataFrame columns contain spaces, PySR normalizes them to underscores and warns. Prefer valid feature names before fitting.
- A custom operator must have an `extra_sympy_mappings` entry before `lambda_format`, `predict`, `sympy`, or LaTeX export can work reliably.

## SymPy and LaTeX exports

Use:

```python
expr = model.sympy(index=None)             # SymPy expression or list for multi-output
tex = model.latex(index=None, precision=3) # LaTeX string or list
```

`latex_table` renders a booktabs-style table from the equation DataFrame:

```python
table = model.latex_table(
    indices=[0, 2, 5],
    precision=4,
    columns=["equation", "complexity", "loss", "score"],
)
```

Notes:

- `precision` controls displayed significant figures, not model accuracy.
- `latex_table` returns a string with a short preamble using `booktabs` and `breqn` conventions.
- For multi-output models, `latex_table()` produces one table per output; explicit indices must be a list of index lists.
- For custom symbolic functions, map the operator name to a SymPy function or expression in `extra_sympy_mappings`, then call `model.refresh()` if the model was already loaded or fitted.

## JAX export

Use JAX only when the optional JAX dependency is installed and the equation's operators have JAX equivalents.

```python
jax_model = model.jax(index=2)
y = jax_model["callable"](X_jax, jax_model["parameters"])
```

The result is a dictionary containing:

- `"callable"`: a JAX function accepting `(X, parameters)`.
- `"parameters"`: a JAX array containing learned numeric constants.

The function is differentiable with respect to the parameter array and can be JIT-compiled by JAX. PySR's method sets `output_jax_format=True`, refreshes the equation table, and returns the selected row's `jax_format`.

Custom-operator mapping shape:

```python
import sympy

MyOp = sympy.Function("myop")
model.set_params(
    extra_sympy_mappings={"myop": MyOp},
    extra_jax_mappings={MyOp: "jnp.sin"},
)
model.refresh()
jax_model = model.jax(index=-1)
```

`extra_jax_mappings` maps the SymPy function object to a string of JAX code, such as `"jnp.sin"` or a small JAX-compatible lambda expression string.

## PyTorch export

Use PyTorch only when the optional PyTorch dependency is installed and the equation's operators have Torch equivalents.

```python
torch_module = model.pytorch(index=2)
y = torch_module(X_tensor)
```

The result is a `torch.nn.Module`. Numeric constants become module parameters, so downstream training can fine-tune them. PySR's method sets `output_torch_format=True`, refreshes the equation table, and returns the selected row's `torch_format`.

Custom-operator mapping shape:

```python
import sympy
import torch

MyOp = sympy.Function("myop")
model.set_params(
    extra_sympy_mappings={"myop": MyOp},
    extra_torch_mappings={MyOp: torch.sin},
)
model.refresh()
torch_module = model.pytorch(index=-1)
```

`extra_torch_mappings` maps the SymPy function object to a Torch callable. Built-in common functions already have mappings; user-defined operators do not.

## Mapping responsibilities for custom operators

For a custom Julia operator named `op`, keep the four levels separate:

| Level | Parameter | Key | Value | Needed for |
| --- | --- | --- | --- | --- |
| Search | `unary_operators`, `binary_operators`, or `operators` | Julia operator definition/name | Julia code string | The evolutionary search. |
| SymPy/NumPy/LaTeX | `extra_sympy_mappings` | operator name string | SymPy function/expression callable | `sympy_format`, `lambda_format`, `predict`, `sympy`, `latex`. |
| JAX | `extra_jax_mappings` | SymPy function object | JAX expression string/callable name | `jax_format`, `model.jax()`. |
| PyTorch | `extra_torch_mappings` | SymPy function object | Torch callable | `torch_format`, `model.pytorch()`. |

If the equation was already fit or reloaded before the mappings were supplied, set the params and refresh:

```python
model.set_params(extra_sympy_mappings={"op": sympy_op})
model.refresh()
```

## Template and custom-objective caveats

- The default `ExpressionSpec` supports SymPy, NumPy, LaTeX, JAX, and PyTorch export.
- `TemplateExpressionSpec` evaluates in Julia and does not support the standard `sympy`, `latex`, `jax`, or `pytorch` methods. Read `../structured-expressions/` before guiding template export. Use the DataFrame's component strings or `julia_expression` for manual reconstruction.
- A full custom objective that reinterprets or manipulates the tree can make the printed equation differ from the evaluated formula. In that case, do not promise `predict` or symbolic export unless the objective author also supplied matching export logic.
