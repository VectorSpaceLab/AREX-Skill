# API reference

## TemplateExpressionSpec contract

| Item | Current contract | Notes |
| --- | --- | --- |
| Constructor | `TemplateExpressionSpec(combine, *, expressions, variable_names, parameters=None)` | Preferred form for new work. |
| Legacy constructor | `TemplateExpressionSpec(function_symbols, combine, num_features=None)` | Compatibility path only; keep new skill content on the current form. |
| `combine` | Julia code string | Can contain multiple statements, local bindings, and `D`. |
| `expressions` | `list[str]` | Placeholder names such as `f`, `g`, `shared`. |
| `variable_names` | `list[str]` | Names for the columns visible inside `combine`. |
| `parameters` | ``dict[str, int] | None`` | Each entry declares the length of a learned parameter vector. |

## PySRRegressor usage with templates

| Topic | Contract | Notes |
| --- | --- | --- |
| Attach template | `PySRRegressor(expression_spec=spec, ...)` | The template constrains the search structure. |
| Ordinary fit | `fit(X, y)` | Use this for standard template-constrained regression. |
| Category columns | Shift zero-based categories before `fit` | Julia indexing inside the template is 1-based. |
| Template guesses | `guesses=[{"f": "#1 + #2"}]` | One dict per output; use nested lists for multi-output. |
| Vector-valued templates | Append target components to `X`, use dummy `y`, and set `elementwise_loss="(pred, target) -> pred"` | This is the residual-template pattern. |

## What the fitted equations expose

Template rows in `model.equations_` are Julia-backed:

- `julia_expression` is present for each row
- `lambda_format` is available for numeric evaluation
- component trees are reachable from the Julia expression object when the template has multiple named subexpressions

Typical inspection shape:

```python
expr = model.equations_.loc[idx, "julia_expression"]
# expr.trees.<name> gives the named component tree
```

## Unsupported template exports

Template expression specs do **not** provide these export methods:

- `model.sympy()`
- `model.latex()`
- `model.jax()`
- `model.pytorch()`
- `model.latex_table()`

The template can still be evaluated numerically through the Julia-backed callable stored in the equations table, but the symbolic export pipeline is intentionally not exposed.

## Adjacent APIs you may need to hand off to

| API | Why it matters | Route |
| --- | --- | --- |
| `loss_function_expression` | Custom objective over expression objects, useful when a template needs objective logic | `customization-and-constraints` |
| `loss_function` | Full custom objective over trees | `customization-and-constraints` |
| `D(f, i)` | Differential operator inside `combine` | `structured-expressions` |
| `from_file(...)` | Reloads stored runs, but template workflows should still treat the spec code as the source of truth | `export-and-artifacts` |

## Reload caution

For template workflows, keep the spec-construction code and the saved equation CSV together. If you need a durable artifact story, route the export/reload request to `export-and-artifacts`.
