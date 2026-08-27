# API reference

This sub-skill covers structured optimization helpers and the differentiable
fixed-point utility. It does not define new differentiation semantics; for
`value_and_grad` behavior and scalar-output constraints, see
[differentiation-core](../../differentiation-core/).

## Flatten helpers

### `flatten(value)`

- Accepts arbitrarily nested lists, tuples, and dicts whose leaves are
  array-like values or scalars.
- Returns `(flat_value, unflatten)`.
- `flat_value` is a one-dimensional `numpy.ndarray`.
- `unflatten(flat_value)` reconstructs the original nesting.
- Dict keys are traversed in sorted order.
- Mixed numeric types are not preserved; use a homogeneous numeric tree.

### `flatten_func(func, example)`

- Returns `(flat_func, unflatten, flat_example)`.
- `flat_func(_x, *args)` applies `func(unflatten(_x), *args)` and flattens the
  result.
- Use it when a structured objective must be adapted to a flat optimizer or
  SciPy routine.
- `flat_example` is the flattened version of `example` and is ready to pass as
  the initial vector for a flat API.

## Structured optimizers

### `sgd(grad, x0, callback=None, *args, **kwargs)`
### `rmsprop(grad, x0, callback=None, *args, **kwargs)`
### `adam(grad, x0, callback=None, *args, **kwargs)`

- The public wrappers accept a structured `x0`, such as a dict of arrays or a
  list/tuple tree.
- `grad` must have signature `grad(x, i)` where `i` is the iteration number.
- Internally, the wrapper flattens `x0`, runs the flat optimizer, and
  unflattens the final result.
- `callback`, if provided, is called as `callback(params, i, g)` with
  unflattened parameters and gradient.
- These are ordinary Python optimization loops, not custom primitives.

### Optimizer family notes

- `sgd` uses momentum.
- `rmsprop` maintains an exponential moving average of squared gradients.
- `adam` uses bias-corrected first and second moment estimates.

## Fixed-point helper

### `fixed_point(f, a, x0, distance, tol)`

- `f(a)` must return an update function that maps the current iterate to the
  next iterate.
- `x0` is the initial iterate.
- `distance(x, y)` should return a scalar convergence measure.
- The forward loop repeats until `distance(x, x_prev) <= tol`.
- The helper is differentiable through Autograd's fixed-point VJP rule when the
  update body is itself differentiable.

## SciPy minimize pattern

### Flat scalar objective

```python
result = minimize(value_and_grad(rosenbrock), x0, jac=True, method="CG")
```

- This is the pattern used by `scripts/rosenbrock_minimize.py`.
- `jac=True` tells SciPy that the callable returns both the objective value and
  its gradient.

### Structured objective

```python
flat_objective, unflatten, flat_x0 = flatten_func(objective, params0)
result = minimize(value_and_grad(flat_objective), flat_x0, jac=True, method="CG")
```

- This keeps the SciPy-facing vector flat while the model code remains
  structured.
- The callback can unflatten the current vector before plotting, logging, or
  inspecting nested parameters.
- The `examples/gmm.py` workflow shows the same flattening pattern with a flat
  SciPy objective and explicit unflattening in the callback.

### When to choose which pattern

- Use `value_and_grad` + `jac=True` when the objective is scalar and you want a
  single callable for SciPy.
- Use `grad(flat_objective)` if you want SciPy to call a separate gradient
  function.
- Use `flatten_func` whenever the original parameters are nested containers.
