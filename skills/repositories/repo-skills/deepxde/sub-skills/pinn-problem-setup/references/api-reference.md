# PINN setup API reference

This file summarizes the DeepXDE APIs needed to assemble PINN problems. Signatures reflect installed API inspection plus source/docstring review. Basic `PDE` assembly was verified with the PyTorch CPU backend in this construction; APIs marked backend-limited should be rechecked in the target backend before use.

## Residual and gradient APIs

| API | Signature | Use |
| --- | --- | --- |
| PDE residual | `pde(x, y)` | Standard `dde.data.PDE` and `dde.data.TimePDE` residual callback. Return a tensor or a list/tuple of tensors. |
| IDE/FPDE residual | `pde(x, y, int_mat)` | Used by `dde.data.IDE`, `dde.data.FPDE`, and time FPDE classes; `int_mat` is the integration/discretization matrix. |
| `dde.grad.jacobian` | `jacobian(ys, xs, i=None, j=None)` | First derivatives. `i` selects output component, `j` selects input coordinate. |
| `dde.grad.hessian` | `hessian(ys, xs, component=0, i=0, j=0)` | Second derivatives of output component `component` with respect to input coordinates `i`, `j`. |

Shape notes:

- `xs` has shape `(N, input_dim)`.
- `ys` has shape `(N, output_dim)`.
- `jacobian(..., i=0, j=0)` and `hessian(..., component=0, i=0, j=0)` return shape `(N, 1)` for ordinary PINNs.
- If either input or output has more than one dimension, do not call `jacobian` with both `i=None` and `j=None`; choose at least one index.
- For a multi-output PDE, use `component=` in `hessian` and `i=` in `jacobian` to avoid differentiating the wrong output.

PyTorch-safe residual pattern:

```python
from deepxde.backend import torch

def pde(x, y):
    u_x = dde.grad.jacobian(y, x, i=0, j=0)
    u_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
    return u_xx + torch.sin(x[:, 0:1])
```

## Geometry APIs

| Geometry | Constructor | Notes |
| --- | --- | --- |
| `Interval` | `dde.geometry.Interval(l, r)` | 1D interval; supports endpoint boundary normals and periodic point pairing. |
| `Rectangle` | `dde.geometry.Rectangle(xmin, xmax)` | 2D axis-aligned rectangle; `xmin`/`xmax` are coordinate lists. |
| `Disk` | `dde.geometry.Disk(center, radius)` | 2D disk with radial normals. |
| `Ellipse` | `dde.geometry.Ellipse(center, semimajor, semiminor, angle=0)` | 2D ellipse; angle rotates the ellipse. |
| `Triangle` | `dde.geometry.Triangle(x1, x2, x3)` | 2D triangle from three vertices. |
| `Polygon` | `dde.geometry.Polygon(vertices)` | 2D polygon from vertex list. |
| `StarShaped` | `dde.geometry.StarShaped(center, radius, coeffs_cos, coeffs_sin)` | 2D star-shaped boundary. |
| `Cuboid` | `dde.geometry.Cuboid(xmin, xmax)` | 3D axis-aligned box. |
| `Sphere` | `dde.geometry.Sphere(center, radius)` | 3D sphere. |
| `Hypercube` | `dde.geometry.Hypercube(xmin, xmax)` | nD axis-aligned box. |
| `Hypersphere` | `dde.geometry.Hypersphere(center, radius)` | nD sphere. |
| `PointCloud` | `dde.geometry.PointCloud(points, boundary_points=None, boundary_normals=None)` | Point-cloud geometry; boundary points are required for boundary detection, normals for Neumann/Robin. |
| `TimeDomain` | `dde.geometry.TimeDomain(t0, t1)` | 1D time interval with `on_initial`. |
| `GeometryXTime` | `dde.geometry.GeometryXTime(geometry, timedomain)` | Combined space-time domain; time is the last coordinate. |

CSG operations are available on same-dimensional geometries:

```python
union = geom1 | geom2           # or geom1.union(geom2)
difference = geom1 - geom2     # or geom1.difference(geom2)
intersection = geom1 & geom2   # or geom1.intersection(geom2)
```

Useful geometry methods for PINN setup:

| Method | Use |
| --- | --- |
| `inside(x)` | Boolean mask for points inside the geometry. |
| `on_boundary(x)` | Boolean mask for boundary predicates. |
| `boundary_normal(x)` | Unit normal for Neumann/Robin/normal derivative conditions. |
| `uniform_points(n, boundary=True)` | Equispaced points for diagnostics or manual metrics. |
| `random_points(n, random="pseudo")` | Interior/domain samples; distribution name matches data constructor distributions. |
| `uniform_boundary_points(n)` / `random_boundary_points(n, random=...)` | Boundary sampling for diagnostics, fixed measurements, or operators. |
| `periodic_point(x, component)` | Paired periodic locations for `PeriodicBC`. |
| `boundary_constraint_factor(x, smoothness=...)` | Backend tensor factor for hard constraints where implemented. |

## Boundary and initial condition APIs

| Condition | Signature | Callback contract |
| --- | --- | --- |
| `DirichletBC` | `dde.icbc.DirichletBC(geom, func, on_boundary, component=0)` | `func(X)` returns values with shape `(N, 1)` for the selected output component. |
| `NeumannBC` | `dde.icbc.NeumannBC(geom, func, on_boundary, component=0)` | `func(X)` returns target normal derivative values. |
| `RobinBC` | `dde.icbc.RobinBC(geom, func, on_boundary, component=0)` | `func(X, y)` returns target expression for `dy/dn`; `y` is backend output slice. |
| `PeriodicBC` | `dde.icbc.PeriodicBC(geom, component_x, on_boundary, derivative_order=0, component=0)` | `component_x` is the input coordinate to pair; `derivative_order` supports `0` or `1`. |
| `OperatorBC` | `dde.icbc.OperatorBC(geom, func, on_boundary)` | `func(inputs, outputs, X)` returns an `(N, 1)` tensor residual on boundary points. |
| `PointSetBC` | `dde.icbc.PointSetBC(points, values, component=0, batch_size=None, shuffle=True)` | Fixed point-value observations. |
| `PointSetOperatorBC` | `dde.icbc.PointSetOperatorBC(points, values, func, batch_size=None, shuffle=True)` | Fixed point custom operator observations. |
| `IC` | `dde.icbc.IC(geom, func, on_initial, component=0)` | Initial values for `GeometryXTime`; `func(X)` returns `(N, 1)`. |

Predicate callbacks:

```python
def on_left(x, on_boundary):
    return on_boundary and dde.utils.isclose(x[0], -1.0)

def on_initial(_, on_initial):
    return on_initial
```

Point-set details:

- `points`: 2D NumPy array with shape `(N, input_dim)`.
- `values`: scalar or 2D array. For one component, use shape `(N, 1)`.
- `component`: integer for one output component. A list of components is implemented for the PyTorch backend.
- `batch_size`: implemented for PyTorch and Paddle. If using it, add `dde.callbacks.PDEPointResampler(bc_points=True)` during training so batches refresh.
- `PointSetOperatorBC.func(inputs, outputs, X)` should return a tensor with one column; non-scalar multi-column values raise shape errors.

`OperatorBC` warning: when `func` uses the NumPy `X` argument, leave `num_test=None` in `PDE`/`TimePDE` or test-time callback indexing can fail.

## Data class APIs

| Data class | Signature | Use |
| --- | --- | --- |
| `PDE` | `dde.data.PDE(geometry, pde, bcs, num_domain=0, num_boundary=0, train_distribution="Hammersley", anchors=None, exclusions=None, solution=None, num_test=None, auxiliary_var_function=None)` | ODE or time-independent PDE. |
| `TimePDE` | `dde.data.TimePDE(geometryxtime, pde, ic_bcs, num_domain=0, num_boundary=0, num_initial=0, train_distribution="Hammersley", anchors=None, exclusions=None, solution=None, num_test=None, auxiliary_var_function=None)` | Time-dependent PDE with initial points. |
| `IDE` | `dde.data.IDE(geometry, ide, bcs, quad_deg, kernel=None, num_domain=0, num_boundary=0, train_distribution="Hammersley", anchors=None, solution=None, num_test=None)` | 1D integro-differential equations of form `int_0^x K(x,t)y(t)dt`. Backend support should be verified. |
| `FPDE` | `dde.data.FPDE(geometry, fpde, alpha, bcs, resolution, meshtype="dynamic", num_domain=0, num_boundary=0, train_distribution="Hammersley", anchors=None, solution=None, num_test=None)` | Fractional PDEs using auxiliary-point discretization. Backend support should be verified. |

Common data arguments:

| Argument | Meaning |
| --- | --- |
| `geometry` / `geometryxtime` | Domain object controlling sampling and boundary tests. |
| `pde` / `ide` / `fpde` | Residual callback or list of residual callbacks; `None` means no global PDE residual. |
| `bcs` / `ic_bcs` | One condition or a list of conditions. Use `[]` if no soft condition is needed. |
| `num_domain` | Number of residual/collocation points sampled inside the domain. |
| `num_boundary` | Number of points sampled on the boundary for BC losses. |
| `num_initial` | Number of initial points for `TimePDE`. |
| `train_distribution` | One of `"uniform"`, `"pseudo"`, `"LHS"`, `"Halton"`, `"Hammersley"`, `"Sobol"`. |
| `anchors` | Additional fixed training points, shape `(N, input_dim)`. |
| `exclusions` | Points to remove from sampled training sets. |
| `solution` | Optional NumPy reference solution used for test labels/metrics. |
| `num_test` | Interior test points for PDE loss; BC/IC test points reuse training condition points. |
| `auxiliary_var_function` | Optional function mapping `train_x`/`test_x` to auxiliary variables for residuals. |

Data object attributes and mutation methods useful for setup/debugging:

| Attribute/method | Use |
| --- | --- |
| `train_x_all` | PDE training points, unordered, no duplicates; does not include BC duplicates. |
| `train_x_bc` | Condition points built from `train_x_all`; not automatically refreshed when `train_x_all` changes. |
| `num_bcs` | List of point counts per BC/IC. |
| `train_x` | Full network input training array: BC/IC points first, then PDE points; may contain duplicates. |
| `test_x` | Test network input array. |
| `resample_train_points(pde_points=True, bc_points=True)` | Resample PDE and/or BC points. |
| `add_anchors(anchors)` | Add PDE training anchors without changing BC points. |
| `replace_with_anchors(anchors)` | Replace PDE training points with anchors without changing BC points. |

`num_test` caveat: the test set combines condition points and domain points with different densities. For reliable solution metrics, sample your own evaluation grid and call `model.predict` in the training workflow.

## Inverse-parameter APIs

| API | Signature | Use |
| --- | --- | --- |
| `dde.Variable` | `dde.Variable(initial_value, dtype=None)` | Backend trainable variable for unknown scalar/tensor parameters. |
| `Model.compile` hook | `external_trainable_variables=None` | Pass a variable or list of variables so the optimizer updates them. |

Pattern:

```python
unknown = dde.Variable(1.0)

def pde(x, y):
    return dde.grad.jacobian(y, x, i=0, j=1) - unknown * dde.grad.hessian(y, x)

# Later: model.compile("adam", lr=1e-3, external_trainable_variables=unknown)
```

If an unknown is represented as an output field, no `dde.Variable` is required; create a multi-output network and use the field component in the residual.

## Hard-constraint APIs

| API | Use |
| --- | --- |
| `net.apply_output_transform(fn)` | Replaces raw network output with `fn(x, y)`; use for exact boundary/initial constraints. |
| `geom.boundary_constraint_factor(x, smoothness=...)` | Backend tensor distance factor that is zero on the boundary for supported geometries. |

Output transforms run on backend tensors, so their math must use backend tensor operations. A common scalar ansatz is:

```python
def output_transform(x, y):
    return known_boundary_extension(x) + geom.boundary_constraint_factor(x) * y
```

## Adaptive sampling APIs

| API | Signature | Use |
| --- | --- | --- |
| `dde.callbacks.PDEPointResampler` | `PDEPointResampler(period=100, pde_points=True, bc_points=False)` | Resample PDE and optionally BC points every `period` iterations. |
| `data.add_anchors` | `add_anchors(anchors)` | Add residual-selected points for RAR. |
| `data.replace_with_anchors` | `replace_with_anchors(anchors)` | Replace PDE training set with selected anchors. |
| `model.predict(..., operator=pde)` | `predict(x, operator=None, callbacks=None)` | Evaluate the PDE residual on candidate points for diagnostics/refinement. |

Training callbacks and compile/train calls belong in `../training-workflows/SKILL.md`; this sub-skill only identifies which data methods and callback names are relevant to sampling design.
