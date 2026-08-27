# DeepXDE PINN problem-assembly workflows

This reference is for assembling DeepXDE PINN problem objects. It intentionally stops before optimizer schedules, checkpointing, long training, plotting, and model lifecycle details; for those steps, hand off to `../training-workflows/SKILL.md` after the `data` and `net` objects exist.

## 1. Residual callbacks and backend tensor ops

The standard residual signature for ODEs, time-independent PDEs, and time-dependent PDEs is:

```python
def pde(x, y):
    ...
    return residual          # tensor with shape (N, 1), or list of such tensors
```

- `x` is the backend tensor of input collocation points with shape `(N, input_dim)`.
- `y` is the network output tensor with shape `(N, output_dim)`.
- For scalar-output problems, `y[:, 0:1]` is the predicted solution.
- For systems, use output components explicitly: `u = y[:, 0:1]`, `v = y[:, 1:2]`, or use gradient `component=` arguments.
- Use backend tensor math inside `pde`. In the PyTorch backend verified for this construction:

```python
import numpy as np
import deepxde as dde
from deepxde.backend import torch

def pde(x, y):
    # x[:, 0:1] is the first spatial coordinate, x[:, 1:2] is often time.
    dy_x = dde.grad.jacobian(y, x, i=0, j=0)
    dy_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
    return -dy_xx - (np.pi**2) * torch.sin(np.pi * x[:, 0:1])
```

Do **not** apply NumPy elementwise functions to backend tensors inside `pde`; use `torch.sin`, `torch.exp`, `torch.square`, or the corresponding backend operation. NumPy functions belong in reference-solution and boundary-value callbacks that receive NumPy arrays.

Gradient helpers:

```python
# First derivatives / Jacobian entries.
dy_dx = dde.grad.jacobian(y, x, i=0, j=0)     # d y_0 / d x_0, shape (N, 1)
dv_dt = dde.grad.jacobian(y, x, i=1, j=2)     # d y_1 / d x_2

# Second derivatives / Hessian entries for one output component.
d2u_dx2 = dde.grad.hessian(y, x, component=0, i=0, j=0)
d2u_dxdt = dde.grad.hessian(y, x, component=0, i=0, j=1)
```

Return a list for multi-equation systems:

```python
def pde(x, y):
    u, v = y[:, 0:1], y[:, 1:2]
    u_t = dde.grad.jacobian(y, x, i=0, j=1)
    v_t = dde.grad.jacobian(y, x, i=1, j=1)
    u_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
    v_xx = dde.grad.hessian(y, x, component=1, i=0, j=0)
    return [u_t - u_xx + u * v, v_t - v_xx - u * v]
```

Each returned residual contributes one loss term before the BC/IC loss terms. If you later use loss weights, the expected order is all PDE residuals first, then conditions in the order provided to `dde.data.*`.

## 2. Geometry and time-domain selection

Choose geometry by input dimension and boundary semantics:

| Problem shape | Typical construction | Notes |
| --- | --- | --- |
| 1D spatial domain | `geom = dde.geometry.Interval(a, b)` | Boundary points are the two endpoints. |
| 2D rectangle | `dde.geometry.Rectangle([xmin, ymin], [xmax, ymax])` | Good for rectangular PDEs and separable side predicates. |
| 2D disk/ellipse/polygon/triangle/star | `Disk`, `Ellipse`, `Polygon`, `Triangle`, `StarShaped` | Use boundary predicates with `dde.utils.isclose` for side/arc selection. |
| 3D box/sphere | `Cuboid`, `Sphere` | Neumann/Robin conditions use geometry normals. |
| nD box/sphere | `Hypercube`, `Hypersphere` | Useful for higher-dimensional parametric PDEs. |
| sampled domain | `PointCloud(points, boundary_points, boundary_normals)` | Needed when the domain is point-cloud-defined; supply boundary normals for Neumann/Robin. |
| Boolean domain | `geom1 | geom2`, `geom1 - geom2`, `geom1 & geom2` | CSG union/difference/intersection require matching dimensions. |

For time-dependent problems, make time the last coordinate:

```python
geom = dde.geometry.Interval(-1.0, 1.0)
timedomain = dde.geometry.TimeDomain(0.0, 1.0)
geomtime = dde.geometry.GeometryXTime(geom, timedomain)

def pde(x, y):
    dy_t = dde.grad.jacobian(y, x, i=0, j=1)      # last coordinate is time in 1D+time
    dy_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
    return dy_t - dy_xx
```

Boundary predicates receive one point and a precomputed geometry flag:

```python
def left_boundary(x, on_boundary):
    return on_boundary and dde.utils.isclose(x[0], -1.0)

def all_boundary(_, on_boundary):
    return on_boundary
```

Initial-condition predicates receive `on_initial` instead of `on_boundary`:

```python
ic = dde.icbc.IC(geomtime, initial_value, lambda _, on_initial: on_initial)
```

## 3. Boundary, initial, operator, and point-set constraints

Soft constraints are appended to the data object. For scalar outputs, the default `component=0` is usually correct. For systems, always set `component`.

```python
bc_left = dde.icbc.DirichletBC(geom, lambda x: np.zeros((len(x), 1)), left_boundary)
bc_right = dde.icbc.NeumannBC(geom, lambda x: np.ones((len(x), 1)), right_boundary)
```

Common choices:

- `DirichletBC(geom, func, on_boundary, component=0)`: enforce `y_component = func(x)`.
- `NeumannBC(geom, func, on_boundary, component=0)`: enforce normal derivative `dy/dn = func(x)` using geometry normals.
- `RobinBC(geom, func, on_boundary, component=0)`: enforce `dy/dn = func(X, y)`; the callback receives NumPy boundary coordinates and backend output tensor slices.
- `PeriodicBC(geom, component_x, on_boundary, derivative_order=0, component=0)`: pair periodic boundary points along input coordinate `component_x`; derivative order may be `0` or `1`.
- `OperatorBC(geom, func, on_boundary)`: enforce a custom tensor expression `func(inputs, outputs, X) = 0` on boundary points.
- `IC(geomtime, func, on_initial, component=0)`: enforce initial values on `t=t0` for `GeometryXTime`.

Shape rules that prevent most BC errors:

```python
# Good: NumPy callback returns N by 1 for one component.
def u_boundary(x):
    return np.sin(np.pi * x[:, 0:1])

# Good: component-specific conditions for a 2-output network.
bc_u = dde.icbc.DirichletBC(geom, u_boundary, all_boundary, component=0)
bc_v = dde.icbc.DirichletBC(geom, v_boundary, all_boundary, component=1)
```

### Point-set observations

Point-set constraints inject measured values or custom operator values at fixed coordinates. They are especially useful for inverse PINNs and data-assimilation PINNs.

```python
observe_x = np.linspace(-1.0, 1.0, 20)[:, None]      # shape (N, input_dim)
observe_u = np.sin(np.pi * observe_x)                # shape (N, 1)
observe_bc = dde.icbc.PointSetBC(observe_x, observe_u, component=0)
```

- `points` must be a 2D NumPy array with shape `(N, input_dim)`.
- Single-component `values` should be a scalar or a 2D array with shape `(N, 1)`.
- A list of `component` indices is implemented for the PyTorch backend; then values should match the selected components.
- `batch_size` for `PointSetBC` and `PointSetOperatorBC` is backend-limited to PyTorch/Paddle and requires `dde.callbacks.PDEPointResampler(bc_points=True)` during training so batches advance.

For derivative/flux measurements at fixed points:

```python
def measured_flux(inputs, outputs, X):
    return dde.grad.jacobian(outputs, inputs, i=0, j=0)

points = np.array([[1.0]])
values = np.array([[2.0]])
flux_obs = dde.icbc.PointSetOperatorBC(points, values, measured_flux)
```

For `OperatorBC`, avoid setting `num_test` if the operator callback uses the NumPy `X` argument; otherwise DeepXDE can evaluate the operator against test arrays with incompatible indexing.

## 4. Forward PINN recipes

### Time-independent PDE / ODE

```python
geom = dde.geometry.Interval(-1.0, 1.0)

bc = dde.icbc.DirichletBC(geom, lambda x: np.sin(np.pi * x), lambda _, on: on)

data = dde.data.PDE(
    geom,
    pde,
    bc,
    num_domain=32,
    num_boundary=2,
    train_distribution="Hammersley",
    solution=lambda x: np.sin(np.pi * x),   # optional reference
    num_test=100,
)
```

Use `bcs=[]` if an exact output transform handles all boundary values or if the problem has no boundary condition.

### Time-dependent PDE

```python
geom = dde.geometry.Interval(-1.0, 1.0)
time = dde.geometry.TimeDomain(0.0, 1.0)
geomtime = dde.geometry.GeometryXTime(geom, time)

def exact(x):
    return np.sin(np.pi * x[:, 0:1]) * np.exp(-x[:, 1:2])

bc = dde.icbc.DirichletBC(geomtime, exact, lambda _, on_boundary: on_boundary)
ic = dde.icbc.IC(geomtime, exact, lambda _, on_initial: on_initial)

data = dde.data.TimePDE(
    geomtime,
    pde,
    [bc, ic],
    num_domain=40,
    num_boundary=20,
    num_initial=10,
    train_distribution="Hammersley",
    solution=exact,
    num_test=200,
)
```

Coordinates are ordered as spatial dimensions followed by time. For 1D+time, use `j=0` for space and `j=1` for time.

### IDE and FPDE setup

IDE and FPDE residuals receive an integration/discretization matrix as a third argument:

```python
def ide(x, y, int_mat):
    # Matrix application is backend-specific. Verify backend support first.
    ...
    return residual

data = dde.data.IDE(
    geom,
    ide,
    bcs,
    quad_deg=16,
    kernel=kernel,          # optional; default is 1
    num_domain=16,
    num_boundary=2,
)
```

```python
def fpde(x, y, int_mat):
    ...
    return residual

data = dde.data.FPDE(
    geom,
    fpde,
    alpha=1.5,              # may be a learnable dde.Variable in inverse problems
    bcs=bcs,
    resolution=[100],
    meshtype="dynamic",
    num_domain=20,
    num_boundary=2,
)
```

IDE currently targets one-dimensional problems with integrals of the form `int_0^x K(x, t) y(t) dt`. FPDE discretizes fractional Laplacian terms using auxiliary points and an `int_mat`; static mesh support is constrained to intervals. The construction here verified only the basic PyTorch `PDE` path, so verify backend behavior before relying on IDE/FPDE in a downstream run.

## 5. Inverse PINN patterns

### Unknown scalar parameter

Create a `dde.Variable`, use it in the residual, and later pass it to `Model.compile`:

```python
C = dde.Variable(2.0)

def pde(x, y):
    dy_t = dde.grad.jacobian(y, x, i=0, j=1)
    dy_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
    return dy_t - C * dy_xx

# Build data with enough observations to identify C.
observe_x = np.column_stack([np.linspace(-1, 1, 10), np.ones(10)])
observe_y = dde.icbc.PointSetBC(observe_x, exact(observe_x), component=0)
data = dde.data.TimePDE(geomtime, pde, [bc, ic, observe_y], anchors=observe_x, ...)

# In the training workflow:
# model.compile("adam", lr=1e-3, external_trainable_variables=C)
```

Use a list for multiple unknowns: `external_trainable_variables=[kf, D]`.

### Unknown field as network output

For inverse fields, make the network output include both the state and the unknown field:

```python
def pde(x, y):
    u = y[:, 0:1]
    q = y[:, 1:2]                         # inferred field
    u_xx = dde.grad.hessian(y, x, component=0, i=0, j=0)
    return -u_xx + q

bc_u = dde.icbc.DirichletBC(geom, exact_u, all_boundary, component=0)
observe_u = dde.icbc.PointSetBC(observe_x, exact_u(observe_x), component=0)
data = dde.data.PDE(geom, pde, [bc_u, observe_u], anchors=observe_x, ...)

# Choose a network with output_dim=2; PFNN is useful when each output needs capacity.
```

The output-component field is trainable through normal network weights; no `external_trainable_variables` are needed unless additional scalar/tensor unknowns exist.

## 6. Anchors, exclusions, train distributions, and test points

Data constructors support:

```python
data = dde.data.PDE(
    geom,
    pde,
    bcs,
    num_domain=100,
    num_boundary=20,
    train_distribution="Hammersley",   # uniform, pseudo, LHS, Halton, Hammersley, Sobol
    anchors=must_include_points,        # extra training points, shape (N, input_dim)
    exclusions=points_to_skip,          # remove exact points from sampled training set
    solution=reference_solution,
    num_test=1000,
)
```

Important caveats:

- `anchors` are added to the PDE training points; for observations, also create `PointSetBC` or `PointSetOperatorBC` so measured values affect the loss.
- `exclusions` are exact point exclusions using all-close comparisons; use them for singularities, corners, or vertices that cause invalid normals.
- `num_test` test points include BC/IC training points plus sampled interior points. They may not be uniformly distributed, so compute high-quality metrics manually with `geom.uniform_points(...)` and `model.predict(...)` when accuracy matters.
- Parallel Horovod training is optional and backend-limited; if used, `train_distribution` must be `"pseudo"` and scaling semantics change. Treat this as a backend/configuration concern.

## 7. Hard constraints / exact boundary transforms

Soft BCs add losses. Exact or hard constraints embed the boundary condition in the network output.

```python
geom = dde.geometry.Interval(0.0, np.pi)
net = dde.nn.FNN([1, 32, 32, 1], "tanh", "Glorot uniform")

def output_transform(x, y):
    # Boundary values: u(0)=0, u(pi)=pi.
    return x * (np.pi - x) * y + x

net.apply_output_transform(output_transform)
data = dde.data.PDE(geom, pde, [], num_domain=64, solution=exact, num_test=200)
```

For supported geometries, `geom.boundary_constraint_factor(x, smoothness=...)` can provide a backend tensor distance factor that is zero on the boundary. This is useful for transforms such as:

```python
def output_transform(x, y):
    return boundary_value(x) + geom.boundary_constraint_factor(x) * y
```

`boundary_value(x)` must be written with backend tensor ops when it is evaluated inside `output_transform`. Do not simultaneously add a contradictory soft BC for the same output component.

## 8. Adaptive and residual-aware sampling

Two common patterns are available:

1. Periodic resampling of collocation points during training:

```python
resampler = dde.callbacks.PDEPointResampler(period=100, pde_points=True, bc_points=False)
# Pass `callbacks=[resampler]` to Model.train in the training workflow.
```

2. Residual-based adaptive refinement (RAR) by evaluating residuals, selecting high-error candidates, and adding anchors:

```python
candidate_x = geom.random_points(1000)
residual = np.abs(model.predict(candidate_x, operator=pde))
new_points = candidate_x[np.argsort(residual[:, 0])[-10:]]
data.add_anchors(new_points)
# Recompile if BC point counts or loss structure changed; then continue training.
```

If you resample BC point batches (`bc_points=True`) or use point-set mini-batches, the number of BC points must remain consistent with the compiled loss structure. If DeepXDE reports that `num_bcs` changed, recompile the model after updating the data.
