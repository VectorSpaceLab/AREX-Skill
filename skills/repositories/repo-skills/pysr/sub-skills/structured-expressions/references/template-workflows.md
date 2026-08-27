# Template workflow guide

This guide distills the structured-expression workflow for PySR. Use it when the model form is known in advance and the search should fill in the unknown pieces.

## 1) Choose the structure

Use a template when you already know one of these patterns:

- a known outer shell, such as `sin(f(...)) + g(...)`
- category-specific coefficients or offsets
- several outputs that share a latent component
- a differential relation using `D`
- a seeded equation where the search should start from a plausible form

If the structure is not known, route to `fit-and-diagnose` instead.

## 2) Map the constructor fields

| Field | Meaning | Common mistake |
| --- | --- | --- |
| `combine` | Julia code that combines the subexpressions | Writing Python syntax or forgetting Julia indexing rules |
| `expressions` | Placeholder names such as `f`, `g`, `shared` | Leaving out a placeholder that appears in `combine` |
| `variable_names` | Column names visible inside `combine` | Mismatching the order of `X` |
| `parameters` | Named parameter vectors with declared lengths | Treating a learned parameter vector like a scalar |

A valid `combine` body can contain multiple Julia statements, local bindings, reused subexpressions, and a final expression returned from the block.

## 3) Handle indexing deliberately

- Julia indexing starts at 1.
- If the source labels are zero-based categories, shift them before calling `fit`.
- If a template references `class` or `category`, the category column should already be 1-based when the model sees it.
- Parameter vectors are also 1-based inside the template, so use `p[1]`, `p[2]`, etc.

## 4) Use the right guess shape

Template guesses seed the placeholder expressions, not the final model directly.

Recommended form for a single template output:

```python
guesses = [{"f": "#1 + #2"}]
```

For multi-output templates, use a list of guess lists, one per output.

Notes:

- `#1`, `#2`, ... refer to argument positions of the placeholder function.
- The guess key is the placeholder name from `expressions`, not a data column name.
- If a template guess is supplied as free-form strings, re-check the nesting before fitting.

## 5) Vector-valued and shared-expression templates

For structured multi-output problems, a common pattern is to place both the input features and the target components into `X`, use a dummy `y`, and make the elementwise loss return the residual built inside the template.

Minimal shape:

```python
spec = TemplateExpressionSpec(
    expressions=["f1", "f2", "shared"],
    variable_names=["x1", "x2", "y1", "y2"],
    combine="""
        v = shared(x1, x2)
        residual = abs2(y1 - (v + f1(x1, x2))) + abs2(y2 - (v + f2(x1, x2)))
        residual
    """,
)

model = PySRRegressor(
    expression_spec=spec,
    elementwise_loss="(pred, target) -> pred",
)
```

Use this pattern when the objective is naturally written as a per-row residual rather than a direct `y` prediction.

## 6) Differential templates

The differential operator is `D`.

- `D(f, 1)` differentiates with respect to the first argument of `f`.
- `D(f, 2)` differentiates with respect to the second argument of `f`.
- The result can be called like a function inside `combine`.

Typical use case: recovering an antiderivative or enforcing a derivative relation with a known integrand.

## 7) Check export limits up front

Template expressions do not support the full export stack.

Do not promise these exports for templates:

- `model.sympy()`
- `model.latex()`
- `model.jax()`
- `model.pytorch()`
- `model.latex_table()`

Instead, inspect the Julia expression objects stored in `model.equations_` and reassemble the pieces manually if needed.

## 8) After fitting

For template models, inspect the fitted components through the Julia-backed equation rows.

Typical follow-up actions:

- read the selected equation row from `model.equations_`
- inspect `julia_expression`
- inspect the individual component trees under `.trees`
- export or reload only after accounting for the template limitations

## Quick planning checklist

- [ ] Do I know the structural skeleton already?
- [ ] Are all placeholders listed in `expressions`?
- [ ] Do the `variable_names` match the columns in `X`?
- [ ] If categories are present, are they 1-based before `fit`?
- [ ] If the model is vector-valued, am I using dummy `y` and residual-style loss?
- [ ] If guesses are present, are they nested correctly for the number of outputs?
- [ ] Am I avoiding unsupported template export promises?
