# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `model.sympy()`, `model.latex()`, `model.jax()`, `model.pytorch()`, or `model.latex_table()` raises `ValueError` | Template expression specs do not support the symbolic export stack | Use the Julia expression rows in `model.equations_` instead, or route the export request to `export-and-artifacts`. |
| `TemplateExpressionSpec` construction fails with a name or arity error | A placeholder appears in `combine` but is missing from `expressions`, or the `variable_names` list does not match the data columns | Sync the three lists before fitting and keep the Julia-side order explicit. |
| A category-specific expression is shifted by one class | Source categories were zero-based but the template expects 1-based indexing | Add 1 to the category column before `fit`. |
| Template guesses are rejected or ignored | The guess shape is wrong for a template, or a placeholder mapping is missing | Use placeholder-to-expression dicts such as `{"f": "#1 + #2"}`; use nested lists for multi-output. |
| A vector-valued template behaves like an ordinary regression fit | The residual template pattern was not set up correctly | Put the extra target columns into `X`, use a dummy `y`, and make `elementwise_loss` return the per-row residual. |
| The template body parses but the equation is numerically unstable | Bare Float64 literals or non-type-stable Julia code are present in `combine` | Use Float32-safe literals such as `0.5f0` or explicit type-preserving conversions. |
| A template also needs custom objective logic | `loss_function` was used when the template needs expression-level objective control | Route to `customization-and-constraints` and use `loss_function_expression`. |
| A differential template gives the wrong derivative | The `D(f, i)` argument index was chosen incorrectly | Count the placeholder arguments from 1, then re-check the template body. |
| `X_units` is requested together with a template | Template expressions are incompatible with dimensional constraints | Remove the units requirement or route the problem to `customization-and-constraints`. |
| Reload or export behavior is unclear | Template workflows should not rely on the symbolic export stack as the source of truth | Save the spec-construction code and the equation CSV together; use `export-and-artifacts` for the durable artifact story. |

## Quick checks

- Confirm the placeholder names in `expressions` appear exactly in `combine`.
- Confirm any category or class labels are already 1-based before the fit call.
- Confirm template guesses are nested for the number of outputs you are modeling.
- Confirm you are not promising unsupported template exports.
