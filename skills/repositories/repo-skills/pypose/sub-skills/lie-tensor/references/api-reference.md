# LieTensor API reference

This is the compact lookup for the `lie-tensor` skill. All examples assume:

```python
import torch
import pypose as pp
```

## Types and storage dimensions

A LieTensor stores one typed item in its last dimension. `x.shape` includes that
embedding dimension; `x.lshape` hides it. `x.ltype` identifies the group/algebra
and exposes its `dimension`, `embedding`, `manifold`, and `on_manifold` properties.

| Alias | `ltype` | Kind | Final storage | Local dimension | Representation |
|---|---|---|---:|---:|---|
| `SO3` | `SO3_type` | group | 4 | 3 | quaternion `[x,y,z,w]` |
| `so3` | `so3_type` | algebra | 3 | 3 | axis-angle |
| `SE3` | `SE3_type` | group | 7 | 6 | translation + quaternion |
| `se3` | `se3_type` | algebra | 6 | 6 | tangent translation + axis-angle |
| `Sim3` | `Sim3_type` | group | 8 | 7 | translation + quaternion + scale |
| `sim3` | `sim3_type` | algebra | 7 | 7 | tangent translation + axis-angle + log-scale |
| `RxSO3` | `RxSO3_type` | group | 5 | 4 | quaternion + scale |
| `rxso3` | `rxso3_type` | algebra | 4 | 4 | axis-angle + log-scale |

Examples of shapes:

```python
pp.randn_SO3(2, 3).shape       # (2, 3, 4)
pp.randn_SO3(2, 3).lshape      # (2, 3)
pp.randn_se3(2, 3).shape       # (2, 3, 6)
pp.randn_Sim3().shape          # (8,)
```

Use `LieTensor(data, ltype=...)` when the type is known exactly. The aliases are
preferred because they make the representation visible. Supplying integer size
arguments to an alias allocates a shape; it does not initialize a meaningful
manifold value, so use `identity_*` or `randn_*` for initialized values.

## Constructors and factories

| Purpose | APIs | Notes |
|---|---|---|
| typed construction | `LieTensor(data, ltype=pp.SE3_type)` | final dimension must match `ltype.dimension` |
| group/algebra aliases | `SO3`, `so3`, `SE3`, `se3`, `Sim3`, `sim3`, `RxSO3`, `rxso3` | preserve ordinary tensor dtype/device |
| random group/algebra | `randn_SO3`, `randn_so3`, `randn_SE3`, `randn_se3`, `randn_Sim3`, `randn_sim3`, `randn_RxSO3`, `randn_rxso3` | `*lsize` is `lshape`; accepts `sigma`, `dtype`, `device`, `requires_grad` |
| identity group/algebra | `identity_SO3`, `identity_so3`, `identity_SE3`, `identity_se3`, `identity_Sim3`, `identity_sim3`, `identity_RxSO3`, `identity_rxso3` | one item if no size is supplied |
| like factories | `identity_like(x)`, `randn_like(x)` | match the input's `ltype` and `lshape` unless overridden |
| parameter | `Parameter(data=None, requires_grad=True, sjac=False)` | LieTensor input retains `ltype`; `sjac` is optional sparse tracing |

Factory sigma conventions are representation-specific. A scalar applies to all
parts. `se3` accepts a scalar, a translation/rotation pair, or four independent
translation/rotation sigmas. `sim3` accepts scalar, translation/rotation/scale,
or five-part values. `rxso3` accepts scalar or rotation/scale. Do not confuse
these standard-deviation controls with the stored Sim(3) scale.

## Maps and operators

| Operation | Input → output | Typical call |
|---|---|---|
| exponential | algebra → matching group | `X = pp.Exp(a)` or `a.Exp()` |
| logarithm | group → matching algebra | `a = pp.Log(X)` or `X.Log()` |
| inverse | group → group; algebra → negated algebra | `X.Inv()`, `a.Inv()` |
| multiplication | matching group → matching group | `X @ Y`, `pp.Mul(X, Y)` |
| scalar algebra product | algebra → algebra | `a * 0.1` |
| point action | group + `(*,3)`/`(*,4)` tensor → tensor | `X.Act(points)`, `X @ points` |
| retraction | group + algebra → group | `X.Retr(delta)` |
| adjoint | group + matching algebra → algebra | `X.Adj(delta)` |
| transpose adjoint | group + matching algebra → algebra | `X.AdjT(delta)` |
| inverse Jacobian product | group + matching algebra → algebra | `X.Jinvp(delta)` |
| right Jacobian | `so3`/`SO3` → ordinary 3×3 matrix tensor | `a.Jr()` or `X.Jr()` |
| typed addition | group + tangent tensor, or algebra + tensor | `X + delta`, `a + delta` |

For matching `X` and `a`, the useful identities are:

```python
X @ a.Exp() == X.Adj(a).Exp() @ X
X.AdjT(a).Exp() @ X == a.Exp() @ X
X.Retr(a) == a.Exp() @ X
```

Use tolerances rather than exact equality. `Adj`, `AdjT`, and `Jinvp` broadcast
batch dimensions and return the matching algebra type. In the inspected release, `Jr` is implemented for `so3` and `SO3` and returns
shape `lshape + (3, 3)`. Do not assume the method is implemented for `se3`,
`sim3`, or `rxso3` without probing the installed version.

## Conversion and component access

| API | Output and conventions |
|---|---|
| `x.tensor()` / `pp.tensor(x)` | ordinary tensor; `ltype` is intentionally removed |
| `x.matrix()` / `pp.matrix(x)` | SO3 3×3; SE3/Sim3/RxSO3 4×4; algebra is exponentiated first |
| `x.translation()` | `(*,3)`; zero for SO3/RxSO3 |
| `x.rotation()` | SO3 LieTensor `(*,4)` |
| `x.scale()` | `(*,1)`; one for SO3/SE3 |
| `x.euler()` | roll/pitch/yaw `(*,3)` in radians, x-y-z sequence |
| `euler2SO3(euler)` | `(*,3)` Euler tensor → SO3 `(*,4)` |
| `quat2unit(x)` | normalized group quaternion; all-zero quaternion raises `ValueError` |
| `vec2skew(v)` | `(*,3)` → `(*,3,3)` |

Matrix converters accept batched `(*, 3, 3)`, `(*, 3, 4)`, or `(*, 4, 4)` as
applicable:

```python
so3 = pp.mat2SO3(R, check=True, rtol=1e-5, atol=1e-5)
se3 = pp.mat2SE3(T, check=True, rtol=1e-5, atol=1e-5)
sim3 = pp.mat2Sim3(S, check=True, rtol=1e-5, atol=1e-5)
rxso3 = pp.mat2RxSO3(S, check=True, rtol=1e-5, atol=1e-5)
se3_again = pp.from_matrix(T, ltype=pp.SE3_type)
```

`mat2SE3` reads the top-left 3×3 rotation and, when the input has a fourth
column, the top three entries of that column as translation. Validation checks
orthogonality and determinant of the rotation. A 4×4 input with a noncanonical
last row may emit a warning because the row is not used. Keep `check=True` for
external or numerically noisy data and tune `rtol`/`atol` deliberately.

## Type-aware PyTorch behavior

- `to`, `cpu`, `cuda`, `float`, `double`, `detach`, `clone`, slicing, `cat`,
  `stack`, `split`, `reshape`, `view`, and `lview` are supported in the typed
  surface. Confirm `ltype` after an unfamiliar operation.
- `lview(*shape)` appends the current embedding dimension; `view` takes the full
  storage shape. The final dimension is never a batch dimension.
- `torch.Tensor` points are not LieTensors. Only a group acts on points.
- A group parameter is not four/seven/eight/five unconstrained Euclidean
  coordinates. Use its tangent algebra for updates and preserve the typed value.
- `pp.is_lietensor(x)` is a safe type check. `pp.is_SE3(x)` expects a typed object
  with `ltype`; do not call it on arbitrary tensors.

## Batch and cumulative operations

For a sequence of same-type group values along dimension `dim`:

```python
left_products = pp.cumprod(sequence, dim=dim, left=True)   # x_i @ ... @ x_0
right_products = pp.cumprod(sequence, dim=dim, left=False) # x_0 @ ... @ x_i
left_products2 = pp.cummul(sequence, dim=dim, left=True)  # `*` group product
```

`cumops` accepts a user operation. The underscore forms mutate their input;
prefer the functional forms in differentiable code. Never use the final storage
dimension as the sequence dimension.
