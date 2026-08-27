# Troubleshooting

The bundled scripts are designed to expose the most common failure surfaces for
this sub-skill.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Nested dict/list parameters do not round-trip through `flatten` | A leaf is not array-like, the tree shape changed, or the dict keys are unstable | Use arrays or scalars at the leaves, keep keys sortable/stable, and rebuild the adapter with `flatten_func` when you need a flat objective |
| The optimizer callback sees the wrong shape or flat vectors | The callback is being used on the raw flat optimizer rather than the wrapped `sgd` / `rmsprop` / `adam` helper | Use the wrapped optimizers from this sub-skill; their callback signature is `callback(params, i, g)` with unflattened values |
| The optimizer loss does not decrease | Step size, momentum, or update scale is too aggressive; the gradient tree may also be mismatched | Start with the bundled quadratic smoke, reduce the step size, and inspect the unflattened gradient before moving to a real model |
| SciPy `minimize` appears to ignore gradients | The objective is not paired with `jac=True`, or you passed only a value-returning callable | Use `value_and_grad(...), jac=True` for the one-call pattern, or pass an explicit gradient callable such as `grad(flat_objective)` |
| `flatten_func` seems to return an array instead of a Python scalar | `flatten_func` deliberately flattens the objective output for the flat SciPy-facing API | Treat the result as the flat SciPy output and compare it with `.item()` or `np.array([value])` as needed |
| The fixed-point loop never stops or stops too early | The recurrence is not contracting enough, the initial guess is poor, or `tol` is not appropriate | Tighten the update map, change the initial guess, or adjust `tol` after checking the forward iterates |
| Higher-order differentiation through `fixed_point` is noisy | The update body or distance metric is not smooth enough, or the recurrence is not converged tightly enough | Use a smooth recurrence, avoid side effects in `f(a)`, and verify the forward fixed point before differentiating |
| The question is really about `value_and_grad` semantics or scalar-output rules | Core differentiation behavior | Route to [differentiation-core](../../differentiation-core/) |
| The question is about SciPy wrapper behavior rather than optimization integration | General `autograd.scipy` surface | Route to [numpy-scipy-primitives](../../numpy-scipy-primitives/) |
| The user needs custom gradient rules for the objective itself | Custom primitive mechanics | Route to `extend-primitives` |

## Useful quick checks

- `flatten(init)` should reconstruct the same nested tree.
- `flatten_func(objective, init)` should produce a flat objective and a flat
  example vector.
- `minimize(value_and_grad(rosenbrock), x0, jac=True, method="CG")` should
  reach the Rosenbrock minimum near `[1, 1]`.
- `grad` and `grad(grad(...))` of a convergent fixed-point recurrence should
  agree with the analytic derivative on a tiny scalar fixture.
