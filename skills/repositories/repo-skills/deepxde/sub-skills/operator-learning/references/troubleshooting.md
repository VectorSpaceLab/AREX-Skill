# Operator-learning troubleshooting

Use this when DeepXDE raises shape, branch/trunk width, function-space, PDE auxiliary variable, MIONet, or ZCS errors. For optimizer schedules, saving, restoring, callbacks, or prediction batching, route to `../training-workflows/SKILL.md`. For backend installation or global backend selection, route to `../backend-and-configuration/SKILL.md`.

## Fast shape triage

Print these values before constructing the data and network:

```python
print("branch", X_train[0].shape)
print("trunk", X_train[1].shape)
print("y", y_train.shape)
```

For two-input MIONet data:

```python
print("branch1", X_train[0].shape)
print("branch2", X_train[1].shape)
print("trunk", X_train[2].shape)
print("y", y_train.shape)
```

Then apply the relevant row of `api-reference.md`.

## `The training dataset does not have the format of Cartesian product`

Likely causes:

- `TripleCartesianProd`: `y_train.shape` is not `(len(branch_values), len(trunk_points))` for one output.
- The trunk array was flattened to `(n_points,)` instead of `(n_points, dim_x)`.
- A non-Cartesian flattened label vector was passed to `TripleCartesianProd`; use `Triple` or reshape labels into a function-by-location grid.
- For multi-output Cartesian DeepONet, labels omitted the final output axis: use `(n_func, n_points, n_outputs)`.

Checks:

```python
assert y_train.shape[0] == len(X_train[0])
assert y_train.shape[1] == len(X_train[1])
assert X_train[1].ndim == 2
```

For `QuadrupleCartesianProd`, also check:

```python
assert len(X_train[0]) == len(X_train[1])
assert y_train.shape == (len(X_train[0]), len(X_train[2]))
```

## Branch/trunk network width errors

Messages such as `Output sizes of branch net and trunk net do not match` or width divisibility assertions come from the final branch/trunk dot product.

Fix by strategy:

- One output: set `layer_sizes_branch[-1] == layer_sizes_trunk[-1]`.
- `split_both`: make the shared last width divisible by `num_outputs`.
- `split_branch`: set `branch_last = trunk_last * num_outputs`.
- `split_trunk`: set `trunk_last = branch_last * num_outputs`.
- `independent`: first make a valid one-output pair, then set `num_outputs` and `multi_output_strategy="independent"`.

Also ensure first-layer widths match data dimensions:

```python
assert layer_sizes_branch[0] == X_train[0].shape[1]
assert layer_sizes_trunk[0] == X_train[1].shape[1]
```

## Multi-output labels look transposed or have an extra singleton dimension

DeepONet and Cartesian DeepONet use different output layouts:

- `DeepONet` with `Triple`: `(batch, num_outputs)`.
- `DeepONetCartesianProd` with `TripleCartesianProd`: `(n_func, n_points, num_outputs)`.
- Single-output Cartesian labels should be `(n_func, n_points)`, not `(n_func, n_points, 1)`, unless you explicitly use a multi-output strategy with `num_outputs=1` avoided.

When in doubt, run a zero/one-iteration model and print `model.predict(...) .shape` on a tiny input before launching a long run.

## Branch input width is wrong for function-space data

Symptoms include matrix multiplication shape errors at the branch network first layer.

Fixes:

- `layer_sizes_branch[0]` must equal the number of branch sensor/evaluation points, not the number of sampled functions.
- For PI-DeepONet, `evaluation_points.shape[0]` becomes the branch input width for scalar function evaluations.
- `space.eval_batch(features, evaluation_points)` returns `(n_functions, n_eval_points)`; pass that array as the branch input.
- Keep `evaluation_points` two-dimensional: `(n_eval_points, function_dim)`.

## PI-DeepONet residual receives the wrong auxiliary variable

Standard `PDEOperator` and `PDEOperatorCartesianProd` call the PDE as `pde(x, y, aux_value)`, where `aux_value` is the sampled input function evaluated at the PDE/trunk points.

Common mistakes:

- Defining `pde(x, y)` with no third argument.
- Treating `aux_value` as branch sensor values instead of values at PDE points.
- Forgetting `function_variables=[0]` for a function over only `x` in a space-time PDE coordinate `(x, t)`.
- Passing sensor points from the branch domain as PDE collocation points.

Shape probes after data construction:

```python
print(data.train_x[0].shape)       # branch discretizations
print(data.train_x[1].shape)       # PDE/trunk points
print(data.train_aux_vars.shape)   # input function values at PDE/trunk points
```

## Function-space interpolation or domain errors

- `GRF_KL` supports `T=1` in this implementation; other `T` values raise an error.
- `GRF`/`GRF2D` interpolation expects query points inside the configured domain.
- For smoke tests, reduce `N`, `num_eig`, and the number of functions before increasing model size.
- If `eval_batch` returns a transposed-looking array, remember that its contract is `(n_functions, n_points)`.

## MIONet merge errors

Symptoms:

- `Output sizes of branch1 net and branch2 net do not match.`
- `Output sizes of merger net and trunk net do not match.`
- activation dictionary key errors when optional merger networks are enabled.

Fixes:

- With `merge_operation="add"` or `"mul"`, branch1 and branch2 final widths must match.
- With `merge_operation="cat"`, the merger/trunk widths must be planned around the concatenated branch width.
- If `layer_sizes_merger` is set, supply an activation dictionary containing `"merger"`.
- If `layer_sizes_output_merger` is set, supply an activation dictionary containing `"output merger"` and validate the final output reshaping on a tiny batch.

## ZCS errors

ZCS is optional and full ZCS training was not runtime-verified in this construction. Source support covers TensorFlow 2.x, PyTorch, and Paddle. `tensorflow.compat.v1` and JAX raise `NotImplementedError` for ZCS.

Checklist:

1. Use `dde.zcs.PDEOperatorCartesianProd`, not `dde.data.PDEOperatorCartesianProd`.
2. Use `dde.zcs.Model`, not `dde.Model`.
3. Keep `dde.nn.DeepONetCartesianProd` as the network class.
4. Write the PDE residual as `def pde(zcs_parameters, y, aux_value): ...`.
5. Construct `dde.zcs.LazyGrad(zcs_parameters, field)` for each scalar output field whose derivatives are needed.
6. Use `LazyGrad.compute(order_tuple)` with tuple length equal to the trunk coordinate dimension.

Example derivative order mapping:

- 1D coordinate `x`: `u_xx` is `compute((2,))`.
- 2D coordinate `(x, t)`: `u_xx` is `compute((2, 0))`, `u_t` is `compute((0, 1))`.
- 2D coordinate `(x, y)`: `u_xy` is `compute((1, 1))`.
