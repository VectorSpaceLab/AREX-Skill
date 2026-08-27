# Operators and losses

## Custom operators

PySR accepts custom Julia operators as strings. Keep the search space small and only add operators that are physically or algebraically plausible.

### Arity rules
- Unary operators belong in `unary_operators`.
- Binary operators belong in `binary_operators`.
- Operators with arity 3 or more must use `operators={arity: [...]}`.
- Do not mix `operators` with the unary or binary lists for the same model.

### Safety rules
- The operator must accept any real input that PySR may probe.
- Invalid inputs should return a typed `NaN`, not throw.
- Use `2.5f0` or `T(2.5)`-style literals so the operator stays type-stable in the default Float32 pipeline.
- If you set `precision=64`, Float64 literals are acceptable, but keep the function type-stable.
- A custom operator that only works on part of the real line should signal invalid evaluations with `NaN`.

### Export rule
- If you define a custom operator, also supply `extra_sympy_mappings` for that symbol when you want symbolic export or reload to work cleanly.
- Use SymPy callables, not NumPy or SciPy callables.

### Common pattern

```python
from pysr import PySRRegressor
import sympy

model = PySRRegressor(
    binary_operators=["+", "*"],
    unary_operators=["inv(x) = 1/x"],
    extra_sympy_mappings={"inv": lambda x: 1 / x},
)
```

For a domain-restricted operator:

```julia
my_sqrt(x) = x >= 0 ? sqrt(x) : convert(typeof(x), NaN)
```

## Loss modes

### `elementwise_loss`
Use this when the loss is a simple per-sample scalar.
- Accepts `(prediction, target)`.
- Accepts `(prediction, target, weight)` when `weights` are passed to `fit`.
- Can be a Julia function string or a LossFunctions.jl object.
- Keep it deterministic and scalar-valued.

Typical uses:
- L2 / L1 / Huber / robust residuals
- weighted residuals
- simple custom log-space losses

### `loss_function`
Use this when the loss needs the full tree, the whole prediction vector, derivatives, or structural penalties.
- Signature: `(tree, dataset, options)`.
- Always check the completion flag from `eval_tree_array` before using predictions.
- Return `L(Inf)` for invalid numerical evaluations.
- Use finite penalties for soft structural preferences so evolution can still move toward valid candidates.

### `loss_function_expression`
Use this for template expressions or when the objective should see the full expression object instead of the inner tree.
- Signature: `(expression, dataset, options)`.
- This is the full-objective route that pairs naturally with structured templates.

### Negative losses
If the objective can be negative, set `loss_scale="linear"`. The default `"log"` mode is intended for non-negative losses.

## Recommended selection

| Need | Use |
| --- | --- |
| Simple per-row residual | `elementwise_loss` |
| Weighted residual with one row at a time | `elementwise_loss` with weights |
| Whole-tree penalties or tree traversal | `loss_function` |
| Template-level objective or structured residual logic | `loss_function_expression` |
| Negative losses / likelihood-style score | `loss_scale="linear"` |

## Checklist before running
- Every custom operator has a SymPy mapping.
- Every custom operator is valid on the real line or returns typed `NaN` on invalid inputs.
- Every custom loss is deterministic and type-stable.
- The chosen loss mode matches the amount of context you need.
- Any custom constants are written in the current precision type.
