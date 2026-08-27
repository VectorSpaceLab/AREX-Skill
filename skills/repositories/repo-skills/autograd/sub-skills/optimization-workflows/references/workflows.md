# Workflows

All bundled scripts use tiny synthetic fixtures only. They do not download data,
open plots, or depend on a CLI entry point.

## 1. Round-trip a nested parameter tree

1. Build a small nested dict/list/tuple tree of arrays and scalars.
2. Call `flat, unflatten = flatten(params0)`.
3. Check that `unflatten(flat)` reconstructs the original structure.
4. If you need a flat adapter for a structured objective, call
   `flatten_func(objective, params0)`.
5. Keep dict keys stable and leaves array-like so the round-trip is predictable.

Example shape:

```python
params0 = {
    "encoder": [np.array([2.0, -1.5]), {"bias": np.array([0.5])}],
    "decoder": (np.array([1.0, -3.0]),),
}
```

## 2. Optimize structured parameters with built-in wrappers

1. Write the loss as `loss(params, i)` even if `i` is unused.
2. Build `gradient = grad(loss)`.
3. Pass the structured initial tree directly to `adam`, `rmsprop`, or `sgd`.
4. Use a callback `callback(params, i, g)` to inspect the unflattened state.
5. Start with a small quadratic objective and confirm the loss decreases before
   swapping in a real model.

Example smoke:

```python
trained = adam(gradient, init_params, num_iters=80, step_size=0.05, callback=callback)
```

## 3. Use SciPy minimize with `value_and_grad`

### Flat objective

```python
result = minimize(value_and_grad(rosenbrock), x0, jac=True, method="CG")
```

- This is the pattern demonstrated in `scripts/rosenbrock_minimize.py`.
- It is the simplest way to hand SciPy a scalar objective and gradient in one
  callable.

### Structured objective

```python
flat_objective, unflatten, flat_x0 = flatten_func(objective, params0)
result = minimize(value_and_grad(flat_objective), flat_x0, jac=True, method="CG")
```

- Use this when the model state is nested.
- In a callback, unflatten the current vector before logging or plotting.
- If SciPy appears to ignore gradients, check that `jac=True` is present and
  that the callable really returns value plus gradient.

### Troubleshooting tips

- If the optimizer stalls, reduce the step size or start from a better initial
  point.
- If the callback sees the wrong shapes, verify that you are using the wrapped
  optimizer from this sub-skill and not a raw flat optimizer.
- If the objective is not scalar, fix that first in `differentiation-core`.

## 4. Differentiate through a fixed point

1. Define an update map with the shape `update = lambda a: lambda x: ...`.
2. Choose a scalar `distance(x, y)` and a tolerance `tol`.
3. Make sure the forward recurrence converges from the chosen initial guess.
4. Differentiate the fixed point with `grad` or higher-order `grad` calls.
5. For a smoke test, use a small analytic case such as `sqrt(a)` and compare
   against the known derivative.

Example shape:

```python
root = fixed_point(newton_update, a, guess, distance, 1e-12)
```

## Recommended tiny fixtures

- A nested quadratic tree for `adam`, `rmsprop`, and `sgd`.
- Rosenbrock in two dimensions for SciPy `minimize`.
- Newton's method for `sqrt(a)` as a fixed-point recurrence.
