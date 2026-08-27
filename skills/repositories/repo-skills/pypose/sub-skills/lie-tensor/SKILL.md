---
name: lie-tensor
description: "Use for PyPose LieTensor and manifold computation: choose SO3,
  SE3, Sim3, or RxSO3 group/algebra representations; construct, batch, convert,
  compose, act, retract, differentiate, and diagnose their operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyPose LieTensor

Use this skill when a task needs differentiable 3D transformation or tangent-space
math with PyPose: rotations, rigid poses, similarity transforms, scaled rotations,
Lie algebra perturbations, coordinate conversions, manifold batching, or gradients.
Start by deciding whether each value is a **group** element (a transform that can
compose and act on points) or an **algebra** element (a local/tangent vector that
can be exponentiated).

This skill is intentionally limited to the LieTensor surface. Route second-order
optimizer orchestration, GN/LM/solver/scheduler/kernel workflows to
`optimization`; route EKF/UKF/PF, dynamics, controls, IMU, EPnP, and ICP to
`robotics-modules`; route projection, splines, filtering/downsampling, trajectory
metrics, and evaluation to `geometry-evaluation`.

## Operating contract

- Import with `import torch` and `import pypose as pp`.
- Keep the final dimension as the representation embedding dimension and use
  `lshape` for the batch/item shape.
- Use the matching group and algebra type; do not infer an algebra from an
  ordinary tensor after `.tensor()` has removed its `ltype`.
- Keep inputs on one device and in one floating dtype before calling manifold
  operations. Use the bundled `scripts/lietensor_smoke.py` for a small, deterministic
  sanity check before a larger experiment.
- Treat a raw constructor as a typed view of supplied data, not as a validation
  or optimization recipe. Prefer `identity_*`, `randn_*`, or `Exp` for values with
  known manifold semantics.

## Representation and shape rules

A LieTensor has ordinary `shape == lshape + (embedding_dimension,)`. Its
`ltype` carries the embedding dimension (storage), the manifold dimension (local
coordinates), and whether it is a group or algebra. For example, a batch of
`N x M` SE(3) items has `lshape == (N, M)` and `shape == (N, M, 7)`.
`lview(*new_lshape)` changes only the hidden batch shape and retains the type;
ordinary `view` exposes the final representation dimension.

| Object | Kind | Stored final coordinates | Embedding | Manifold/algebra dimension |
|---|---|---|---:|---:|
| `SO3` / `SO3_type` | group | `[qx, qy, qz, qw]` unit quaternion | 4 | 3 |
| `so3` / `so3_type` | algebra | axis-angle `[phi_x, phi_y, phi_z]` | 3 | 3 |
| `SE3` / `SE3_type` | group | `[tx, ty, tz, qx, qy, qz, qw]` | 7 | 6 |
| `se3` / `se3_type` | algebra | `[tau_x, tau_y, tau_z, phi_x, phi_y, phi_z]` | 6 | 6 |
| `Sim3` / `Sim3_type` | group | `[tx, ty, tz, qx, qy, qz, qw, s]` | 8 | 7 |
| `sim3` / `sim3_type` | algebra | `[tau_x, tau_y, tau_z, phi_x, phi_y, phi_z, sigma]` | 7 | 7 |
| `RxSO3` / `RxSO3_type` | group | `[qx, qy, qz, qw, s]` | 5 | 4 |
| `rxso3` / `rxso3_type` | algebra | `[phi_x, phi_y, phi_z, sigma]` | 4 | 4 |

For group types, quaternions are stored in `xyzw` order. `se3` and `sim3`
translation coordinates are Lie-algebra coordinates: `Exp` applies the relevant
left Jacobian (or Sim(3) W matrix) before producing group translation. For
`rxso3` and `sim3`, the final algebra scale coordinate is log-scale and the group
scale is positive after `Exp` (`s = exp(sigma)`). Sim(3) matrices follow
`[s R, t; 0, 1]`, not the alternate convention with `1/s` in the last entry.

## Core API

### Construct, identify, and sample

Use either the explicit constructor or the aliases:

```python
x = pp.LieTensor(data, ltype=pp.se3_type)  # exact typed construction
x = pp.se3(data)                            # preferred algebra alias
X = pp.SE3(data)                            # preferred group alias
I = pp.identity_SE3(2, 3, dtype=torch.float64, device=device)
z = pp.randn_so3(4, requires_grad=True, dtype=dtype, device=device)
Z = pp.randn_SE3(4, dtype=dtype, device=device)
I_like = pp.identity_like(Z)
Z_like = pp.randn_like(Z)
```

The `*lsize` arguments describe `lshape`, not the final embedding. Thus
`pp.identity_SE3(2, 3)` has shape `(2, 3, 7)`, while a single identity has
shape `(7,)`. Explicit `SO3`/`SE3`/`Sim3`/`RxSO3` data should already have a
final dimension of 4/7/8/5. Explicit algebra data should have 3/6/7/4.

### Maps and group operations

- `a.Exp()` or `pp.Exp(a)` maps algebra to the corresponding group and changes
  final dimension (3→4, 6→7, 7→8, 4→5).
- `X.Log()` or `pp.Log(X)` maps group to algebra and reverses that dimension.
  The operation is differentiable and uses stable small-angle branches.
- `X.Inv()` or `pp.Inv(X)` computes a group inverse. `a.Inv()` is the convenient
  algebra negation, not a group-theoretic inverse.
- `X @ Y` or `pp.Mul(X, Y)` composes two matching group types. `X * Y` is also
  supported for matching group LieTensors. Algebra `a * scalar` is elementwise
  tangent scaling; do not use group `*` as a substitute for a scalar update.
- `X @ p`, `X.Act(p)`, or `pp.Act(X, p)` acts on a tensor whose final coordinate
  dimension is 3 (Euclidean point) or 4 (homogeneous point). A 4-vector keeps
  its homogeneous final coordinate. Batch dimensions broadcast, so one transform
  can act on many points or many transforms can act on one point.
- `X.Retr(a)` / `pp.Retr(X, a)` returns `a.Exp() @ X` and requires a group `X`
  with its corresponding algebra direction `a`.
- `X.Adj(a)` transports a matching tangent vector and satisfies
  `X @ a.Exp() == X.Adj(a).Exp() @ X` (up to numerical tolerance).
  `X.AdjT(a)` satisfies `a.Exp() @ X == X @ X.AdjT(a).Exp()`.
- `X.Jinvp(a)` applies the inverse left Jacobian to a matching algebra vector.
  It is useful for local/BCH-style tangent calculations; it is not a generic
  matrix inverse. In the inspected release, `Jr()` is implemented for `so3` and
  `SO3` and returns their right-Jacobian matrix; verify availability before
  requesting it on the other Lie types.
- `pp.add(X, delta)` / `X + delta` is a left tangent perturbation for a group;
  for an algebra it is ordinary addition. The group's embedded storage is wider
  than its tangent dimension, so the unused tail of a group perturbation is
  ignored by the manifold update.

Use `@` for group composition and point action when the operand type makes the
intent clear; use `.Act()` when an explicit point-action call improves readability.
Group-group composition requires matching Lie types; convert explicitly rather
than relying on a raw tensor or an accidental quaternion/scale layout.

### Conversions and views

- `.tensor()` / `pp.tensor(X)` returns the underlying ordinary tensor and removes
  LieTensor semantics. Re-wrap it with the correct alias or `LieTensor(...,
  ltype=...)` before calling manifold methods.
- `.matrix()` / `pp.matrix(X)` returns a batched matrix. SO3/so3 use `(*, 3, 3)`;
  SE3/se3, Sim3/sim3, and RxSO3/rxso3 use `(*, 4, 4)`. For algebra inputs,
  `matrix()` exponentiates first.
- `.translation()`, `.rotation()`, and `.scale()` return the corresponding
  parts while preserving batch shape. Translation has final size 3, rotation is
  an SO3 LieTensor with final size 4, and scale has final size 1. Types without
  a part return a documented neutral value: zero translation for SO3/RxSO3 and
  unit scale for SO3/SE3.
- `.euler()` returns roll, pitch, yaw in radians using x-y-z order. Euler angles
  are not unique and are singular near gimbal lock; use the rotation/group
  representation for stable storage.
- `pp.euler2SO3(euler)` maps `(*, 3)` roll/pitch/yaw to `(*, 4)` SO3. `pp.quat2unit`
  normalizes a group quaternion and rejects an all-zero quaternion.
- `pp.mat2SE3(mat, check=True, rtol=1e-5, atol=1e-5)` accepts `(*,3,3)`,
  `(*,3,4)`, or `(*,4,4)`, takes the top-left rotation and the translation
  column when present, and returns `(*,7)` SE3. The related `mat2SO3`,
  `mat2Sim3`, `mat2RxSO3`, and `from_matrix(mat, ltype=...)` select other group
  types. Keep `check=True` for untrusted matrices; `check=False` only when the
  upstream invariant has already been established. A noncanonical last row in
  a 4x4 input is warned about, not used to compute the pose.
- `pp.vec2skew(v)` maps `(*,3)` to `(*,3,3)`. `pp.is_lietensor` and
  `pp.is_SE3` are checks for typed objects; call them only after establishing
  that the value is a LieTensor.

## Autograd, parameters, dtype, and device

All ordinary PyTorch tensor attributes and autograd operations are supported.
Create differentiable leaves with `requires_grad=True` in a factory or typed
algebra tensor, then call `backward()` on a scalar loss. The gradient of a group
is represented in its embedding storage; tangent updates use the corresponding
manifold coordinates rather than treating quaternion storage as four independent
rotation degrees of freedom.

`pp.Parameter(data=None, requires_grad=True, sjac=False)` is a PyTorch parameter
wrapper. If `data` is a LieTensor, it retains its `ltype`; if `data` is a regular
Tensor, it is an ordinary `nn.Parameter`. `sjac=True` is only for sparse Jacobian
tracing and requires the optional backend; route sparse GN/LM construction to
`optimization` instead of implementing optimizer orchestration here. A LieTensor
parameter can still be used in a normal differentiable module without `sjac`.

Select one floating dtype and device for all related values:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.float64
xi_data = torch.tensor([0.1, -0.2, 0.05, 0.02, 0.03, -0.01],
                       device=device, dtype=dtype, requires_grad=True)
xi = pp.se3(xi_data)
X = xi.Exp()
points = torch.randn(8, 3, device=device, dtype=dtype)
loss = X.Act(points).square().mean()
loss.backward()  # xi_data is the differentiable leaf
```

Factories accept PyTorch `dtype`, `device`, `requires_grad`, and generator-like
arguments. CUDA LieTensor operations are supported when the installed PyTorch
build and device support them; the bundled smoke defaults to CPU and exits with
a clear error if an explicitly requested device is unavailable. Avoid mixing CPU
and CUDA operands or float32 and float64 operands in one operation. Float16 on
CPU and near-singular conversions are not general-purpose validation targets.

Avoid in-place writes on leaves or tensors needed by autograd. For identity
updates use `identity_()` only on a safe mutable buffer. For repeated or batched
operations prefer non-in-place `cumprod`, `cummul`, or `cumops`; their `_`
variants mutate the input. `torch.cat`, `stack`, `split`, indexing, `to`, `view`,
`reshape`, and `lview` preserve LieTensor type where PyPose supports the operation,
but inspect `isinstance(out, pp.LieTensor)` and `out.ltype` after unfamiliar
PyTorch transforms.

## Verification checklist

Before handing a LieTensor workflow to a downstream task:

1. Assert the selected final representation dimension and `lshape`; check that
   group/algebra types are paired (`SE3` with `se3`, etc.).
2. Run `Log(Exp(a))` or `Exp(Log(X))` on a small, non-singular, deterministic
   fixture. Compare typed tensor values with a tolerance appropriate to dtype.
3. Check composition/inverse with the identity and, when relevant, check the
   adjoint identity stated above.
4. Check point action with both a broadcast Euclidean point and a homogeneous
   point if the workflow uses both. Verify the output's final dimension.
5. Check matrix conversion with `mat2SE3(..., check=True)` or the matching
   converter and verify rotation orthogonality/determinant and translation.
6. Backpropagate a scalar point-action or map loss and assert finite, expected
   gradient shapes. If using `Parameter`, assert it remains a typed LieTensor.
7. Repeat the smallest check on the requested dtype/device; do not claim CUDA
   or optional sparse support from a CPU-only run.

Run the bundled `scripts/lietensor_smoke.py --help` through the resolved skill
path from the skill root or any other working directory. The helper has no
network, file-write, random-data, or optimizer dependency.

## Evidence boundary and routing

This skill captures the public PyPose LieTensor API, typed representations,
conversion rules, differentiable operations, and safe synthetic checks. It does
not prescribe optimizer loops, sparse backend setup, robot-state module
composition, projection/trajectory metrics, spline fitting, or evaluation
protocols. Those tasks belong to the sibling ids named at the top of this file.
