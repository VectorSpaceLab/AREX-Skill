# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Custom operator works in search but not in export | Missing or wrong `extra_sympy_mappings` | Provide a SymPy callable for every custom operator symbol. |
| Custom operator crashes on some inputs | Domain-restricted definition without a typed `NaN` guard | Return `NaN` of the input type for invalid inputs instead of throwing. |
| Custom operator behaves oddly in the default pipeline | Bare Float64 literals or integer promotion | Use `2.5f0` or `T(2.5)`-style literals and keep the function type-stable. |
| `elementwise_loss` errors when weights are passed | Loss only accepts two arguments | Accept `(prediction, target, weight)` when `weights` is supplied to `fit`. |
| `loss_function` or `loss_function_expression` fails signature checks | Wrong objective mode | Use `elementwise_loss` for scalar per-point losses, `loss_function` for tree-level objectives, and `loss_function_expression` for template-level objectives. |
| Search becomes unstable or impossible with custom penalties | Returning `Inf` for soft structural preferences | Use finite graded penalties for structure; reserve `Inf` for invalid numerical evaluations. |
| `constraints` raises tuple-length or symmetry errors | Constraint shape does not match arity, or `+` / `-` sides differ | Make tuple length match the operator arity and keep plus/minus sides equal. |
| `^` causes a huge or noisy search space | Exponentiation left unconstrained | Add a restrictive `constraints` entry or remove the operator. |
| Units are rejected or silently underfit | `X_units` / `y_units` mismatch, or the penalty is too strict | Check unit lengths and use a finite `dimensional_constraint_penalty`. |
| Constants absorb units unexpectedly | Wildcard constant units are allowed | Set `dimensionless_constants_only=True`. |
| Mutation or plugin knobs seem ignored | Legacy `weight_*` knobs mixed with object configs, or the wrong config bucket was edited | Prefer `mutations` / `default_mutations` and `plugins` / `default_plugins`, and keep warm-start expectations in mind. |
| Template-level customization feels awkward | The problem is really a known expression skeleton | Route to `structured-expressions` instead of forcing everything through constraints. |
| You are just trying to fit a standard dataset | No custom operator or structural rule is needed | Route to `fit-and-diagnose`. |

## Quick checks
- Confirm the operator name is valid and matches the mapping key.
- Confirm the operator arity matches the constructor path.
- Confirm the domain notes mention a guard if the operator is not total on the reals.
- Confirm the loss mode matches how much context the objective needs.
- Confirm the unit and complexity settings leave enough slack for intermediate expressions.

## Safe helper
Use `scripts/validate_custom_operator.py` before declaring a custom operator ready for use.
