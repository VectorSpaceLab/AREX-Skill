---
name: customization-and-constraints
description: "Customize PySR search space, custom operators, losses,
  constraints, units, and mutation or plugin behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# customization-and-constraints

Use this sub-skill when the user wants to change how PySR searches, scores, or rejects expressions rather than simply fitting a standard model.

## Route here for
- custom unary or binary operators, or arity 3+ operators via `operators`
- Float32/Float64-safe Julia operator definitions
- typed `NaN` guards for invalid operator domains
- `extra_sympy_mappings` for custom operators
- `elementwise_loss`, `loss_function`, or `loss_function_expression`
- operator constraints, `nested_constraints`, or complexity shaping
- dimensional constraints, `X_units`, `y_units`, or `dimensionless_constants_only`
- mutation and plugin configuration objects

## Route elsewhere for
- ordinary fitting, Pareto selection, or search debugging -> `fit-and-diagnose`
- known algebraic skeletons, templates, or structured expressions -> `structured-expressions`
- export, reload, JAX, PyTorch, SymPy, or LaTeX artifacts -> `export-and-artifacts`
- startup, threading, backend, or cluster issues -> `runtime-and-scaling`

## Working rules
1. Match operator arity to the constructor path before drafting code.
2. Require a SymPy mapping for every custom operator that must export cleanly.
3. Guard invalid domains with typed `NaN`, not Python-style exceptions.
4. Keep custom losses type-stable; use `loss_scale="linear"` when negative losses are possible.
5. Prefer finite structural penalties over all-or-nothing `Inf` whenever evolution needs a gradient toward compliance.
6. Leave slack in `maxsize`, operator constraints, and units so intermediate expressions remain reachable.
7. Use `mutations` / `default_mutations` and `plugins` / `default_plugins` when the user wants runtime tuning objects instead of legacy weight knobs.

## Start here
- `references/operators-and-losses.md` for custom operators and loss modes.
- `references/constraints-and-units.md` for constraints, complexity shaping, and units.
- `references/api-reference.md` for current constructor and fit signatures.
- `references/troubleshooting.md` for common failures and fixes.
- `scripts/validate_custom_operator.py` for a safe static checklist before implementation.

## Expected outcome
Return a concrete customization plan or validated operator/loss/constraint draft, and state any unresolved domain, export, or unit caveats explicitly.
