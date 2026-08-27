# PINN problem-setup troubleshooting

Use this guide for failures while defining geometry, residuals, conditions, point sets, data objects, exact constraints, and adaptive sampling. For install/backend selection failures, route to `../backend-and-configuration/SKILL.md`; for optimizer, callback, checkpoint, and long training failures, route to `../training-workflows/SKILL.md`.

## Backend tensor mismatch in `pde`

Symptoms:

- `TypeError` from `np.sin`, `np.exp`, or NumPy arithmetic inside `pde`.
- TensorFlow symbols imported while `DDE_BACKEND=pytorch`, or PyTorch symbols used under a TensorFlow/JAX/Paddle backend.
- Residual works in a NumPy callback but fails during `Model.compile`, `Model.train`, or `model.predict(..., operator=pde)`.

Fix:

1. Set the backend before importing DeepXDE. The verified path in this construction is PyTorch CPU:

   ```python
   import os
   os.environ.setdefault("DDE_BACKEND", "pytorch")
   import deepxde as dde
   from deepxde.backend import torch
   ```

2. In `pde`, use backend tensor ops:

   ```python
   def pde(x, y):
       dy_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
       return -dy_xx - torch.sin(x[:, 0:1])
   ```

3. Keep NumPy operations in callbacks that receive NumPy arrays, such as `solution`, Dirichlet values, initial values, and point-set value generation.

## Wrong derivative or residual shape

Symptoms:

- `ValueError: i and j cannot be both None`.
- A multi-output model trains but one equation is clearly using the wrong derivative.
- Loss count does not match expected residuals and BCs.

Fix:

- Use `dde.grad.jacobian(y, x, i=<output>, j=<input>)` for first derivatives.
- Use `dde.grad.hessian(y, x, component=<output>, i=<input>, j=<input>)` for second derivatives.
- For 1D+time, the usual input columns are `x[:, 0:1]` for space and `x[:, 1:2]` for time.
- Return one tensor per PDE equation. A two-equation system should return `[eq1, eq2]`, not concatenate unless you deliberately want one loss term.
- If you pass a list of custom losses or loss weights during compile, count all PDE residuals first and then all BC/IC conditions in the order passed to the data constructor.

## BC or IC value shape errors

Symptoms:

- `DirichletBC function should return an array of shape N by 1`.
- `IC function should return an array of shape N by 1 for each component`.
- A vector-valued network applies all conditions to output component 0.

Fix:

- For a single component, return a 2D array with one column:

  ```python
  def value(x):
      return np.sin(np.pi * x[:, 0:1])
  ```

- For vector-valued outputs, create one condition per component:

  ```python
  bc_u = dde.icbc.DirichletBC(geom, u_value, on_boundary, component=0)
  bc_v = dde.icbc.DirichletBC(geom, v_value, on_boundary, component=1)
  ```

- Use `dde.utils.isclose` in boundary predicates instead of exact floating-point equality.

## Boundary predicate selects no points or too many points

Symptoms:

- A BC loss is always zero because no points are selected.
- A side-specific BC unexpectedly applies to every boundary.
- Neumann/Robin errors appear at corners or vertices.

Fix:

- Predicate signature is `on_boundary(x, on_boundary) -> bool` for each point. Use both arguments:

  ```python
  def right(x, on_boundary):
      return on_boundary and dde.utils.isclose(x[0], 1.0)
  ```

- For `GeometryXTime`, boundary predicates see full `(space..., time)` coordinates. Time is the last coordinate.
- Exclude singular points, corners, or vertices with `exclusions=` if normals are undefined or averaged.
- For point-cloud domains, provide `boundary_points` for `on_boundary` and `boundary_normals` for Neumann/Robin.

## PointSetBC and PointSetOperatorBC shape mistakes

Symptoms:

- Point-set observations do not affect training.
- `PointSetOperatorBC should output 1D values`.
- Component-list usage fails on a non-PyTorch backend.
- Point-set mini-batches repeat or fail to advance.

Fix:

- `points` must be shape `(N, input_dim)` even for 1D: use `x[:, None]` or `.reshape(-1, 1)`.
- Single-component `values` should be shape `(N, 1)`.
- For inverse problems, include observation coordinates both as a point-set condition and often as `anchors=observe_x` so the PDE residual is also evaluated there.
- Component lists are implemented for PyTorch; otherwise create separate `PointSetBC` objects per component.
- If using `batch_size`, use a backend that supports it and add `dde.callbacks.PDEPointResampler(bc_points=True)` during training.

## OperatorBC / custom operator failures

Symptoms:

- Operator condition works during training but fails during test-loss evaluation.
- Operator returns a vector with too many columns.
- The operator uses stale NumPy coordinates.

Fix:

- `OperatorBC.func(inputs, outputs, X)` and `PointSetOperatorBC.func(inputs, outputs, X)` must return a backend tensor with shape `(N, 1)` for the selected points.
- Use DeepXDE gradient helpers inside the operator, not raw backend autograd unless you have a backend-specific reason.
- If an `OperatorBC` callback uses the NumPy `X` argument, leave `num_test=None` in `dde.data.PDE`/`TimePDE` to avoid DeepXDE's known test-time indexing problem.

## Geometry and sampling errors

Symptoms:

- CSG constructor fails with a dimension mismatch.
- Time-dependent residual indexes the wrong coordinate.
- `train_x` shapes do not match the expected input dimension.
- Metrics look inconsistent with visual predictions.

Fix:

- CSG (`|`, `-`, `&`) requires both geometries to have the same dimension.
- `GeometryXTime` appends time as the last coordinate. A 2D spatial problem plus time has input dimension 3.
- `anchors` and `exclusions` must have shape `(N, input_dim)` and a dtype compatible with DeepXDE's configured real type.
- `num_test` combines BC/IC training points with sampled domain points; for reliable solution error, make a manual evaluation grid and call `model.predict`.

## `num_bcs` changed during resampling

Symptoms:

- `ValueError: num_bcs changed! Please update the loss function by model.compile.`
- The error appears after using `PDEPointResampler` or changing anchors/exclusions.

Fix:

- Keep boundary predicates and boundary point counts stable when resampling BC points.
- If a data mutation changes the number of BC/IC points, re-run `model.compile(...)` before continuing training.
- For point-set batches, use `PDEPointResampler(bc_points=True)` and avoid simultaneously changing the list/order of BC objects.

## Hard constraint / output transform failures

Symptoms:

- Exact boundary values are not exact.
- Output transform raises backend tensor errors.
- Training has redundant or contradictory boundary losses.

Fix:

- `net.apply_output_transform(fn)` receives backend tensors. Use backend tensor operations inside `fn`.
- Verify the ansatz at the boundary analytically. Example for `u(0)=0`, `u(pi)=pi`:

  ```python
  def output_transform(x, y):
      return x * (np.pi - x) * y + x
  ```

- If a transform enforces the boundary exactly, use `bcs=[]` for those conditions or ensure any remaining soft BC is consistent.
- `boundary_constraint_factor` expects backend tensors and only exists for supported geometries/smoothness options.

## Inverse variable is not learned

Symptoms:

- A `dde.Variable` stays at its initial value.
- Parameter appears in the residual but is absent from optimizer updates.
- Unknown field and unknown scalar patterns are mixed up.

Fix:

- Pass every scalar/tensor unknown to the training compile step:

  ```python
  C = dde.Variable(2.0)
  # model.compile("adam", lr=1e-3, external_trainable_variables=C)
  ```

- Use a list for multiple unknowns: `[kf, D]`.
- For an unknown spatial field, make it a network output component and use that component in `pde`; do not use `dde.Variable` for every collocation point unless you have a custom design.
- Add observation data with `PointSetBC`/`PointSetOperatorBC` and consider `anchors=observe_x` so the PDE residual is evaluated at measured points.

## IDE/FPDE backend and matrix issues

Symptoms:

- `int_mat` multiplication fails or sparse matrix conversion is backend-specific.
- Static FPDE mesh errors on non-interval geometry.
- Fractional inverse variables do not refresh discretization.

Fix:

- IDE residuals use `def ide(x, y, int_mat): ...`; FPDE residuals use `def fpde(x, y, int_mat): ...`.
- Verify backend support before relying on IDE/FPDE. This construction verified the basic PyTorch `PDE` path, while IDE/FPDE examples and sparse matrix operations are backend-limited.
- For `FPDE(..., meshtype="static")`, use interval geometry; dynamic mesh is broader but still needs backend verification.
- If `alpha` is a learnable `dde.Variable`, ensure it is passed as an external trainable variable during compile and expect data matrices to be regenerated rather than cached.

## Quick self-check

When problem assembly is suspect, run the bundled smoke:

```bash
python scripts/smoke_poisson_1d.py --iterations 2
```

If this smoke fails under the same environment, triage backend/import first. If it passes, reduce your problem to: geometry shape, residual output shape, BC/IC value shape, point-set shape, then data-constructor arguments.
