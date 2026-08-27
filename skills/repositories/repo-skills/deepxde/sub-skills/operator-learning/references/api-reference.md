# Operator-learning API reference

The signatures below were checked against the installed PyTorch-backed DeepXDE API during construction and cross-checked with source. Alternative backends may expose extra classes or implementation differences.

## Data families and shape contracts

| API | Signature | Use with | Required shapes |
| --- | --- | --- | --- |
| `dde.data.Triple` | `(X_train, y_train, X_test, y_test)` | `dde.nn.DeepONet` | `X_*=(branch, trunk)`; `branch.shape=(n_samples, n_sensors)`; `trunk.shape=(n_samples, dim_x)`; `y.shape[0]=n_samples` |
| `dde.data.TripleCartesianProd` | `(X_train, y_train, X_test, y_test)` | `dde.nn.DeepONetCartesianProd`, `dde.nn.PODDeepONet` | `X_*=(branch, trunk)`; `branch.shape=(n_func, n_sensors)`; `trunk.shape=(n_points, dim_x)`; single-output `y.shape=(n_func, n_points)` |
| `dde.data.Quadruple` | `(X_train, y_train, X_test, y_test)` | backend-specific MIONet layouts | `X_*=(branch1, branch2, trunk)` sharing a sample axis; `y.shape[0]` matches the sample axis |
| `dde.data.QuadrupleCartesianProd` | `(X_train, y_train, X_test, y_test)` | `dde.nn.MIONetCartesianProd` | `branch1.shape=(n_func, dim1)`; `branch2.shape=(n_func, dim2)`; `trunk.shape=(n_points, dim_x)`; `y.shape=(n_func, n_points)` |
| `dde.data.PDEOperator` | `(pde, function_space, evaluation_points, num_function, function_variables=None, num_test=None)` | `dde.nn.DeepONet` | `evaluation_points.shape=(n_eval_points, function_dim)`; generated branch width is `n_eval_points`; generated `train_x=(v, x)` is flattened across functions and PDE/BC points |
| `dde.data.PDEOperatorCartesianProd` | `(pde, function_space, evaluation_points, num_function, function_variables=None, num_test=None, batch_size=None)` | `dde.nn.DeepONetCartesianProd` | generated `train_x=(func_values, pde_points)` with `func_values.shape=(num_function, n_eval_points)`, `pde_points.shape=(n_pde_points, pde_dim)`, `train_aux_vars.shape=(num_function, n_pde_points)` |
| `dde.zcs.PDEOperatorCartesianProd` | same as `dde.data.PDEOperatorCartesianProd` | `dde.nn.DeepONetCartesianProd` + `dde.zcs.Model` | same Cartesian PI-DeepONet shape; PDE residual must use ZCS `LazyGrad` |

Validation behavior to remember:

- `TripleCartesianProd` raises `ValueError("The training dataset does not have the format of Cartesian product.")` if `len(branch) != y.shape[0]` or `len(trunk) != y.shape[1]`.
- `QuadrupleCartesianProd` requires `len(branch1) == len(branch2)` and a label grid whose size equals `len(branch1) * len(trunk)`; use a two-dimensional `(n_func, n_points)` label array for predictable batching.
- `PDEOperatorCartesianProd(batch_size=...)` mini-batches over sampled functions through the data object. For ordinary supervised Cartesian data, pass batch size through the training call instead.

## Function spaces

All function spaces implement:

| Method | Contract |
| --- | --- |
| `random(size)` | returns feature vectors for `size` sampled functions |
| `eval_one(feature, x)` | evaluates one sampled function at one point |
| `eval_batch(features, xs)` | returns values with shape `(n_functions, n_points)` |

Constructors:

| API | Signature | Notes |
| --- | --- | --- |
| `dde.data.PowerSeries` | `(N=100, M=1)` | samples coefficients for `sum_i a_i x^i`, cheap for smoke tests |
| `dde.data.Chebyshev` | `(N=100, M=1)` | samples Chebyshev coefficients; implementation scales the domain from `[0, 1]` to `[-1, 1]` |
| `dde.data.GRF` | `(T=1, kernel="RBF", length_scale=1, N=1000, interp="cubic")` | 1D Gaussian random field; kernels include `"RBF"`, `"AE"`, and `"ExpSineSquared"`; interpolation `"linear"`, `"quadratic"`, or `"cubic"` |
| `dde.data.GRF_KL` | `(T=1, kernel="RBF", length_scale=1, num_eig=10, N=100, interp="cubic")` | 1D truncated KL expansion; this implementation requires `T=1` |
| `dde.data.GRF2D` | `(kernel="RBF", length_scale=1, N=100, interp="splinef2d")` | 2D Gaussian random field on `[0, 1] x [0, 1]`; points for `eval_batch` have shape `(n_points, 2)` |

## Network constructors

| API | Signature | Data pairing | Output shape |
| --- | --- | --- | --- |
| `dde.nn.DeepONet` | `(layer_sizes_branch, layer_sizes_trunk, activation, kernel_initializer, num_outputs=1, multi_output_strategy=None, regularization=None, dropout_rate=0)` | `Triple` or `PDEOperator` | one output `(batch, 1)`; multi-output `(batch, num_outputs)` |
| `dde.nn.DeepONetCartesianProd` | `(layer_sizes_branch, layer_sizes_trunk, activation, kernel_initializer, num_outputs=1, multi_output_strategy=None, regularization=None, dropout_rate=0)` | `TripleCartesianProd` or `PDEOperatorCartesianProd` | one output `(n_func, n_points)`; multi-output `(n_func, n_points, num_outputs)` |
| `dde.nn.PODDeepONet` | `(pod_basis, layer_sizes_branch, activation, kernel_initializer, layer_sizes_trunk=None, regularization=None, dropout_rate=0)` | `TripleCartesianProd`-style data | `(n_func, n_output_points)` |
| `dde.nn.MIONetCartesianProd` | `(layer_sizes_branch1, layer_sizes_branch2, layer_sizes_trunk, activation, kernel_initializer, regularization=None, trunk_last_activation=False, merge_operation="mul", layer_sizes_merger=None, output_merge_operation="mul", layer_sizes_output_merger=None)` | `QuadrupleCartesianProd` | `(n_func, n_points)` |
| `dde.zcs.Model` | `(data, net)` | `dde.zcs.PDEOperatorCartesianProd` + `DeepONetCartesianProd` | same prediction shapes as the network |
| `dde.zcs.LazyGrad` | `(zcs_parameters, u)` | ZCS PDE residuals | `compute(order_tuple)` returns requested derivative tensor |

`layer_sizes_branch` can be a list of widths or `(dim, callable_network)` in DeepONet-style constructors. For list-based branch/trunk networks, the first element must match the corresponding input dimension and the last element participates in branch/trunk dot-product rules.

## DeepONet branch/trunk width rules

| Case | Required last-layer relationship |
| --- | --- |
| one output, `multi_output_strategy=None` | `branch_last == trunk_last` |
| `num_outputs > 1`, `"independent"` | each independent branch/trunk pair uses the provided compatible widths |
| `"split_both"` | `branch_last == trunk_last` and both are divisible by `num_outputs` |
| `"split_branch"` | `branch_last == trunk_last * num_outputs` |
| `"split_trunk"` | `trunk_last == branch_last * num_outputs` |

Invalid strategy names fail during network construction. Setting a non-`None` strategy when `num_outputs == 1` raises a `ValueError`. Omitting the strategy for `num_outputs > 1` defaults to `"independent"` with a warning.

## PI-DeepONet residual signatures

Standard PI-DeepONet residual:

```python
def pde(x, y, aux_value):
    # x: trunk/PDE coordinates; y: network output; aux_value: input function at x
    return residual
```

ZCS residual:

```python
def pde(zcs_parameters, y, aux_value):
    grad_y = dde.zcs.LazyGrad(zcs_parameters, y)
    return grad_y.compute(required_orders) - aux_value
```

Supported ZCS backends in source are TensorFlow 2.x, PyTorch, and Paddle. ZCS raises `NotImplementedError` for `tensorflow.compat.v1` and JAX. Full ZCS training was not runtime-verified in this construction.
