# LieTensor workflows

These recipes are deliberately small and device/dtype explicit. They cover the
most common decisions without entering optimizer orchestration or robotics
module design.

## 1. Choose a representation and round-trip a pose

Use an algebra for a local perturbation and a group for a reusable transform:

```python
import torch
import pypose as pp

dtype = torch.float64
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
xi_data = torch.tensor([0.10, -0.05, 0.20, 0.02, 0.03, -0.04],
                        dtype=dtype, device=device)
xi = pp.se3(xi_data)
X = xi.Exp()
assert X.ltype is pp.SE3_type
assert X.shape == (7,) and X.lshape == torch.Size([])
assert torch.allclose(X.Log().tensor(), xi.tensor(), rtol=1e-7, atol=1e-8)
```

For a batch, place only batch dimensions before the final embedding:

```python
xi = pp.randn_se3(2, 8, dtype=dtype, device=device)
X = xi.Exp()                       # (2, 8, 7), lshape (2, 8)
assert X.Log().lshape == xi.lshape
```

Keep rotation vectors away from the branch near π while debugging round-trip
numerics. For Sim(3), remember that algebra scale is `sigma` and group scale is
`exp(sigma)`; for SE(3), algebra translation is not the same storage field as
the group translation until `Exp`/`Log` applies the Jacobian.

## 2. Apply transforms with broadcasting

A transform's batch shape and a point tensor's leading shape broadcast in the
same way as PyTorch tensors:

```python
X = pp.identity_SE3(2, dtype=torch.float64)
points = torch.tensor([1., 2., 3.], dtype=torch.float64)
result = X.Act(points)             # (2, 3)

homogeneous = torch.cat([points, torch.ones(1, dtype=points.dtype)])
result_h = X @ homogeneous          # (2, 4), final coordinate remains 1
```

A point batch can be paired with a transform batch when dimensions are
broadcast-compatible. For a transform-specific point, use shape `(N, 3)` or
`(N, 4)` with an `(N, ...)` transform. `Act` accepts only a final point size 3
or 4; a matrix or a point with the wrong final dimension is a shape error, not a
conversion request.

## 3. Convert a validated homogeneous matrix

Construct a known rigid matrix, validate it, and retain gradients through the
used matrix entries:

```python
T = torch.eye(4, dtype=torch.float64)
T[:3, 3] = torch.tensor([0.2, -0.3, 0.4], dtype=T.dtype)
T = T.requires_grad_()
X = pp.mat2SE3(T, check=True, rtol=1e-5, atol=1e-5)
assert X.ltype is pp.SE3_type
assert torch.allclose(X.translation(), T[:3, 3])
loss = X.translation().square().sum()
loss.backward()
assert torch.isfinite(T.grad).all()
```

The converter validates only the rotation block (and warns about an invalid
4×4 last row); it does not repair a noisy matrix. For a matrix that is close but
not within the chosen tolerance, decide whether to reject it, project it using a
separate geometry procedure, or call `check=False` only with a documented
upstream guarantee. `mat2Sim3` expects a scaled rotation block and follows the
`[sR, t; 0, 1]` convention.

## 4. Use adjoint, transpose-adjoint, retraction, and Jacobians

Use matching group/algebra pairs and batch them identically or with broadcastable
leading shapes:

```python
X = pp.randn_SE3(4, dtype=torch.float64)
a = pp.randn_se3(4, dtype=torch.float64)
left = X.Adj(a).Exp() @ X
right = X @ a.Exp()
assert torch.allclose(left.tensor(), right.tensor(), rtol=1e-7, atol=1e-8)

b = X.AdjT(a)
assert torch.allclose((X @ b.Exp()).tensor(), (a.Exp() @ X).tensor(),
                      rtol=1e-7, atol=1e-8)

retracted = X.Retr(a)
assert torch.allclose(retracted.tensor(), (a.Exp() @ X).tensor())
jinvp = X.Jinvp(a)
assert jinvp.ltype is pp.se3_type
assert jinvp.shape == a.shape
# Jr is implemented for so3/SO3 in the inspected release.
rotations = pp.randn_so3(4, dtype=torch.float64)
Jr = rotations.Jr()
assert Jr.shape == (4, 3, 3)
```

`Adj` and `AdjT` are not interchangeable. The equations above are the quickest
way to catch a left/right convention error. `Jinvp` is the inverse-left-Jacobian
product used by local tangent calculations; it is not a replacement for a
solver's Jacobian routine.

## 5. Differentiate through a point action

Create a leaf algebra, map it to a group, act on a point, and backpropagate a
scalar:

```python
xi_data = torch.tensor([0.10, -0.05, 0.02, 0.01, -0.02, 0.03],
                         dtype=torch.float64, requires_grad=True)
xi = pp.se3(xi_data)
point = torch.tensor([0.3, -0.4, 2.0], dtype=xi.dtype)
loss = xi.Exp().Act(point).square().sum()
loss.backward()
assert xi.grad is not None
assert xi.grad.shape == xi.shape
assert torch.isfinite(xi.grad).all()
```

For a trainable module parameter:

```python
from torch import nn
class PoseLayer(nn.Module):
    def __init__(self):
        super().__init__()
        self.pose = pp.Parameter(pp.randn_so3(2, sigma=0.1))
    def forward(self, points):
        return self.pose.Exp().Act(points)
```

The parameter retains `ltype` when initialized from a LieTensor. Normal
`torch.optim` use can update a manifold parameter through PyPose's typed
`add_` behavior, but selecting an optimizer, solver, sparse tracing, or stopping
policy belongs to `optimization`.

## 6. Preserve type through batching and reshaping

```python
A = pp.randn_SO3(2, 2)
B = pp.randn_SO3(2, 1)
C = torch.cat([A, B], dim=1)
assert isinstance(C, pp.LieTensor) and C.lshape == (2, 3)
D = C.lview(3, 2)
assert D.shape == (3, 2, 4)
E, F = torch.split(C, [1, 2], dim=1)
assert E.ltype is pp.SO3_type and F.ltype is pp.SO3_type
```

Do not concatenate different types or concatenate along the final embedding
dimension. If a third-party tensor operation returns a plain Tensor, restore the
known type explicitly rather than guessing from its length.

## 7. Run the deterministic smoke

From the resolved `pypose` skill directory, run:

```bash
python sub-skills/lie-tensor/scripts/lietensor_smoke.py --help
python sub-skills/lie-tensor/scripts/lietensor_smoke.py --device cpu --dtype float64
# only when CUDA is available:
python sub-skills/lie-tensor/scripts/lietensor_smoke.py --device cuda --dtype float32
```

The helper can also be invoked by its resolved absolute path from any working
directory. It imports the installed public `pypose` package and never depends
on the current working directory.

The helper checks typed construction, Exp/Log, point action, matrix conversion,
batching, and a finite gradient. It has no external-data or optimizer dependency
and returns nonzero on a failed assertion.
