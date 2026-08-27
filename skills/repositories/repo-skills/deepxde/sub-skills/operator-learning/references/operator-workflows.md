# Operator-learning workflows

This reference is self-contained for DeepXDE operator-learning tasks. Set the intended backend before importing `deepxde`; the bundled smoke script defaults to PyTorch CPU. For backend installation or global autodiff/dtype configuration, route to `../backend-and-configuration/SKILL.md`.

## Pick the data family first

| Goal | Data class | Matching network | Main shape contract |
| --- | --- | --- | --- |
| Supervised aligned DeepONet data where every input function is evaluated at the same output locations | `dde.data.TripleCartesianProd` | `dde.nn.DeepONetCartesianProd` | branch values `(n_func, n_sensors)`, trunk/output locations `(n_points, dim_x)`, labels `(n_func, n_points)` for one output |
| Supervised unaligned DeepONet data where each row is one `(function, location, value)` sample | `dde.data.Triple` | `dde.nn.DeepONet` | branch values `(n_samples, n_sensors)`, trunk locations `(n_samples, dim_x)`, labels `(n_samples, 1)` or `(n_samples, n_outputs)` |
| Two-input-function operator with a shared output grid | `dde.data.QuadrupleCartesianProd` | `dde.nn.MIONetCartesianProd` | branch1 `(n_func, dim1)`, branch2 `(n_func, dim2)`, trunk `(n_points, dim_x)`, labels `(n_func, n_points)` |
| Two-input-function unaligned samples | `dde.data.Quadruple` | backend-specific MIONet support | branch1/branch2/trunk share a row axis; labels share that row axis |
| Physics-informed DeepONet on a PDE/TimePDE residual | `dde.data.PDEOperator` | `dde.nn.DeepONet` | data flattens each sampled function across PDE and BC/IC points |
| Physics-informed DeepONet on a Cartesian-product grid | `dde.data.PDEOperatorCartesianProd` | `dde.nn.DeepONetCartesianProd` | branch sampled functions `(n_func, n_eval_points)`, PDE/trunk points `(n_pde_points, dim_x)`, auxiliary values `(n_func, n_pde_points)` |
| PI-DeepONet with ZCS | `dde.zcs.PDEOperatorCartesianProd` | `dde.nn.DeepONetCartesianProd` plus `dde.zcs.Model` | same Cartesian PI-DeepONet data shape; PDE residual uses `dde.zcs.LazyGrad` |

Use a Cartesian-product data class when each function should be paired with every trunk location. Use the non-Cartesian data class when rows are already flattened into individual pairs.

## Supervised aligned DeepONet recipe

1. Build branch input values by evaluating each input function at `n_sensors` sensor points. The resulting array must be two-dimensional: `(n_func, n_sensors)`.
2. Build trunk input locations as points where the output function is observed: `(n_points, dim_x)`. For a 1D coordinate, keep the trailing column dimension, e.g. `(100, 1)`, not `(100,)`.
3. Build labels as the output function values on the Cartesian product of functions and trunk points:
   - single output: `(n_func, n_points)`;
   - `num_outputs > 1`: `(n_func, n_points, num_outputs)`.
4. Construct `dde.data.TripleCartesianProd(X_train=(branch_train, trunk_train), y_train=y_train, X_test=(branch_test, trunk_test), y_test=y_test)`.
5. Construct `dde.nn.DeepONetCartesianProd([n_sensors, ... , width], [dim_x, ... , width], activation, initializer)`.
6. Hand the data and network to `dde.Model`. Compile/train details are in `../training-workflows/SKILL.md`.

Validation checklist before training:

```python
assert X_train[0].ndim == 2
assert X_train[1].ndim == 2
assert y_train.shape[:2] == (len(X_train[0]), len(X_train[1]))
assert layer_sizes_branch[0] == X_train[0].shape[1]
assert layer_sizes_trunk[0] == X_train[1].shape[1]
```

For a concrete minimal pattern, use `scripts/smoke_deeponet_aligned.py`.

## Supervised unaligned DeepONet recipe

Use `dde.data.Triple` when each row is already one pair `(v_i, x_i)` with target `u_i = G(v_i)(x_i)`. The branch and trunk arrays must have the same first dimension.

```python
X_train = (branch_values, trunk_locations)
data = dde.data.Triple(X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test)
net = dde.nn.DeepONet([n_sensors, 64, 64], [dim_x, 64, 64], "tanh", "Glorot normal")
```

Shape checklist:

- `branch_values.shape == (n_samples, n_sensors)`;
- `trunk_locations.shape == (n_samples, dim_x)`;
- `y_train.shape[0] == n_samples` and usually `y_train.shape[1] == 1` for one scalar observation per row.

If the same `n_func` functions and `n_points` locations can be represented compactly, prefer the Cartesian-product class to avoid manually repeating/tileing arrays.

## Physics-informed DeepONet flow

PI-DeepONet replaces supervised labels with a PDE/BC/IC residual loss while still learning an operator from sampled input functions to solution functions.

1. Define a `dde.data.PDE` or `dde.data.TimePDE` object exactly as for a PINN, but write the residual with an auxiliary input function value argument:

   ```python
   def equation(x, y, aux_value):
       # x is the trunk/PDE coordinate tensor, y is the DeepONet output,
       # aux_value is the sampled input function evaluated at x.
       return residual
   ```

2. Choose a function space for the input functions, e.g. `dde.data.PowerSeries`, `Chebyshev`, `GRF`, `GRF_KL`, or `GRF2D`.
3. Choose `evaluation_points` of shape `(n_eval_points, function_dim)`. These points discretize each sampled function for the branch network; `layer_sizes_branch[0]` must equal `n_eval_points` for scalar-valued function evaluations.
4. Create the operator data:

   ```python
   data = dde.data.PDEOperatorCartesianProd(
       pde, function_space, evaluation_points, num_function=n_train_functions,
       function_variables=None, num_test=None, batch_size=None,
   )
   ```

   Use `PDEOperator` instead when the non-Cartesian `dde.nn.DeepONet` layout is required.
5. If the function domain is a subset of the PDE coordinate variables, pass `function_variables`. Example: a source or initial-condition function over `x` in a space-time PDE with coordinates `(x, t)` uses `function_variables=[0]`.
6. Construct `dde.nn.DeepONetCartesianProd([n_eval_points, ...], [pde_coordinate_dim, ...], ...)`.
7. Predict a new operator output by sampling features and evaluating them at branch sensors:

   ```python
   features = function_space.random(n_new)
   branch_values = function_space.eval_batch(features, evaluation_points)
   y_pred = model.predict((branch_values, trunk_query_points))
   ```

PI-DeepONet training can be more expensive than the supervised smoke path. Treat L-BFGS, callbacks, and long optimizer schedules as training-workflow concerns.

## Function-space sampling

All DeepXDE function spaces follow the same pattern:

```python
space = dde.data.GRF(length_scale=0.2)
features = space.random(n_func)             # (n_func, n_features)
values = space.eval_batch(features, points) # (n_func, n_points)
```

Operational notes:

- `PowerSeries(N, M)` and `Chebyshev(N, M)` are cheap deterministic-shape choices for synthetic PI-DeepONet tests.
- `GRF` and `GRF2D` depend on covariance matrix setup and interpolation; keep `N` small for smoke tests.
- `GRF_KL` uses a truncated Karhunen-Loeve representation and supports `T=1` in this implementation.
- Always use points inside the function-space domain; interpolation failures often come from out-of-domain trunk or sensor points.

## POD-DeepONet workflow

`dde.nn.PODDeepONet` is for Cartesian-product operator data. It replaces or augments the learned trunk representation with a POD basis.

- `pod_basis` should have shape `(n_output_points, n_pod_modes)`.
- With `layer_sizes_trunk=None`, the branch network last width must equal `n_pod_modes`; output shape is `(n_func, n_output_points)`.
- With a learned trunk network, DeepXDE concatenates the POD basis and trunk encoding, so the branch network last width must equal `n_pod_modes + trunk_last_width`.
- Use the same `TripleCartesianProd` label shape rules as `DeepONetCartesianProd`.

## MIONet Cartesian-product workflow

`dde.nn.MIONetCartesianProd` learns operators with two input functions. Under the PyTorch-verified API, pair it with `dde.data.QuadrupleCartesianProd`.

Shape checklist:

```python
X_train = (branch1_values, branch2_values, trunk_locations)
assert len(branch1_values) == len(branch2_values)
assert y_train.shape == (len(branch1_values), len(trunk_locations))
```

Constructor knobs:

- `merge_operation`: `"mul"`, `"add"`, or `"cat"` for merging the two branch encodings.
- If `merge_operation` is `"add"` or `"mul"`, the two branch output widths must match.
- If `layer_sizes_merger` is supplied, the activation dictionary must include `"merger"`.
- If `layer_sizes_output_merger` is supplied, the activation dictionary must include `"output merger"`, and `output_merge_operation` may be `"mul"`, `"add"`, or `"cat"`.
- The final merged branch width must match the trunk width unless an output merger changes the contract.

## Multi-output DeepONet strategy rules

DeepXDE strategy names are exact: `"independent"`, `"split_both"`, `"split_branch"`, and `"split_trunk"`. Leave `multi_output_strategy=None` only for one output.

| Strategy | Width rule | Non-Cartesian output | Cartesian-product output |
| --- | --- | --- | --- |
| `None` | branch last width equals trunk last width | `(batch, 1)` | `(n_func, n_points)` |
| `independent` | each independent DeepONet uses the provided widths | `(batch, n_outputs)` | `(n_func, n_points, n_outputs)` |
| `split_both` | branch last equals trunk last and is divisible by `n_outputs` | `(batch, n_outputs)` | `(n_func, n_points, n_outputs)` |
| `split_branch` | branch last equals `trunk_last * n_outputs` | `(batch, n_outputs)` | `(n_func, n_points, n_outputs)` |
| `split_trunk` | trunk last equals `branch_last * n_outputs` | `(batch, n_outputs)` | `(n_func, n_points, n_outputs)` |

If `num_outputs > 1` and the strategy is omitted, DeepXDE selects `"independent"` and prints a warning. Prefer setting the strategy explicitly so label shape and width rules are reviewable.

## ZCS PI-DeepONet notes

ZCS is an optional acceleration path for PI-DeepONet. Source and docs support TensorFlow 2.x, PyTorch, and Paddle for ZCS; `tensorflow.compat.v1` and JAX raise `NotImplementedError` in the ZCS model implementation. This construction did not runtime-verify full ZCS training.

To convert a Cartesian PI-DeepONet to ZCS:

1. Keep `dde.nn.DeepONetCartesianProd`.
2. Replace `dde.data.PDEOperatorCartesianProd` with `dde.zcs.PDEOperatorCartesianProd`.
3. Replace `dde.Model` with `dde.zcs.Model`.
4. In the PDE residual, treat the first argument as ZCS parameters and pass it to `dde.zcs.LazyGrad`:

   ```python
   def pde(zcs_parameters, u, aux_value):
       grad_u = dde.zcs.LazyGrad(zcs_parameters, u)
       u_xx = grad_u.compute((2,))      # one-dimensional trunk coordinate
       return u_xx - aux_value
   ```

For a two-dimensional trunk coordinate `(x, t)`, derivative orders are tuples such as `(2, 0)` or `(0, 1)`. The tuple length must equal the trunk coordinate dimension.
