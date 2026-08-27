---
name: optimization-workflows
description: "Route users who need flatten/unflatten helpers, structured
  optimizers, fixed-point differentiation helpers, and SciPy minimize
  integration using value_and_grad."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optimization Workflows

Use this sub-skill for optimization tasks built from nested parameter trees,
fixed-point recurrences, or SciPy minimization loops.

## Route here when the user needs

- `flatten` or `flatten_func` to turn nested dict/list/tuple parameter trees
  into flat arrays and back.
- Structured optimizers such as `sgd`, `rmsprop`, or `adam` on nested
  containers.
- `fixed_point` for differentiable iterative updates.
- `scipy.optimize.minimize` combined with `value_and_grad`.

## Route elsewhere when the question is really about

- `value_and_grad` semantics, scalar-output constraints, or Jacobian/Hessian
  selection: [differentiation-core](../differentiation-core/SKILL.md).
- General `autograd.scipy` wrapper behavior or SciPy wrapper coverage:
  [numpy-scipy-primitives](../numpy-scipy-primitives/SKILL.md).
- Custom primitive or staged VJP/JVP mechanics:
  [extend-primitives](../extend-primitives/SKILL.md).

## Bundled runtime helpers

- `scripts/structured_optimizer_smoke.py`
- `scripts/rosenbrock_minimize.py`
- `scripts/fixed_point_smoke.py`

These scripts use tiny synthetic fixtures only; they do not download data and
there is no CLI entry point to discover.

## What this sub-skill does not own

- Ordinary differentiation operators and higher-order autodiff semantics.
- Custom primitive registration or gradient-rule authoring.
- General NumPy/SciPy wrapper troubleshooting outside optimization workflows.
