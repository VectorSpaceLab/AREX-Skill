---
name: structured-expressions
description: "Use when PySR needs TemplateExpressionSpec, parametric templates,
  shared or vector-valued expressions, differential operators, or seeded
  template guesses."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Structured expressions

Use this sub-skill when the equation shape is partly known and PySR should search only the unknown pieces.

## Use this sub-skill for
- `TemplateExpressionSpec` planning or repair
- parametric expressions with category-specific learned constants
- shared subexpressions or vector-valued residual templates
- differential templates that use `D`
- seeded guesses for known template placeholders

## Route to another sub-skill when
- the task is a free-form fit without known structure → `fit-and-diagnose`
- the task needs custom losses, operator constraints, or tree walks → `customization-and-constraints`
- the task needs SymPy / LaTeX / JAX / PyTorch exports or reload handling → `export-and-artifacts`

## Operating rules
1. Keep the template shape explicit: `combine`, `expressions`, `variable_names`, and optional `parameters`.
2. Treat category indices as Julia indices inside the template. If the source labels are 0-based, shift them before `fit`.
3. For vector-valued templates, move the extra targets into `X`, use a dummy `y`, and make the elementwise loss return the residual from the template.
4. For differential templates, use `D` and verify the argument index.
5. Do not promise template export methods that are unsupported. Use `model.equations_["julia_expression"]` and component trees instead.
6. If the template also needs a custom objective, hand off to `customization-and-constraints` and use `loss_function_expression`.

## Bundled assets
- `references/template-workflows.md`
- `references/api-reference.md`
- `references/troubleshooting.md`
- `scripts/template_spec_builder.py`

## Verification target
A later agent should be able to build a valid template plan, explain indexing and parameters, seed guesses correctly, and identify unsupported exports without running a search.
