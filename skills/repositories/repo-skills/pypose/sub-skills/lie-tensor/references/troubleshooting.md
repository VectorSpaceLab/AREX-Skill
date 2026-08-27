# LieTensor troubleshooting

Diagnose the type, final dimension, batch shape, dtype, and device before
changing numerical tolerances. Most LieTensor failures are representation or
broadcasting mismatches rather than PyTorch arithmetic failures.

## Constructor and type errors

**Symptom:** `The last dimension of a LieTensor has to be corresponding to their
LieType`.

- Inspect `data.shape[-1]` and the intended representation.
- Use 3/4/6/7/7/8/4/5 for `so3/SO3/se3/SE3/sim3/Sim3/rxso3/RxSO3` respectively.
- Remember the repeated `7`: `se3` is a 6-dimensional algebra and `Sim3` is an
  8-dimensional group; `sim3` is 7-dimensional algebra.
- Use `pp.LieTensor(data, ltype=pp.se3_type)` only when the data is genuinely
  algebra coordinates. A raw 7-vector is not automatically disambiguated.

**Symptom:** `.Exp()` or `.Log()` raises an attribute/type error.

- `Exp` accepts algebra types only; `Log` accepts group types only.
- Check `x.ltype` and `x.ltype.on_manifold`.
- Do not call `.Exp()` on a plain Tensor. Wrap it with the correct algebra alias.

**Symptom:** a downstream operation says the object is not a LieTensor.

- `.tensor()` intentionally returns a plain Tensor and drops `ltype`.
- Restore it with `pp.so3(t)`, `pp.se3(t)`, or the exact matching group alias.
- Avoid inferring a type only from the final size when group and algebra storage
  sizes overlap (`se3` and `Sim3` both use 7).

## Group/algebra and convention mistakes

**Symptom:** a pose has unexpected translation after `Log`/`Exp`.

- `SE3` stores physical group translation `[tx,ty,tz]`; `se3` stores tangent
  translation `[tau_x,tau_y,tau_z]`. The SO(3) left Jacobian relates them.
- `Sim3` similarly uses a W matrix coupling translation, rotation, and scale.
- Check whether the task wants a left or right perturbation. `Retr(a)` is
  `a.Exp() @ X`, while `Adj` and `AdjT` encode different side identities.

**Symptom:** scale is inverted, negative, or inconsistent between APIs.

- `rxso3`/`sim3` algebra stores `sigma = log(s)`; group `RxSO3`/`Sim3` stores
  `s = exp(sigma)`.
- PyPose's Sim(3) matrix convention is `[sR, t; 0, 1]`. Do not feed a matrix
  using the alternate `[R, t; 0, 1/s]` convention without converting it.
- Group scale must be nonzero for inversion and positive for the exponential map.

**Symptom:** a quaternion looks different but represents the same rotation.

- `q` and `-q` represent the same SO(3) rotation. Compare `matrix()` or compare
  quaternions up to sign, not raw vector equality.
- Group aliases use `xyzw`, not `wxyz`.
- Use `pp.quat2unit` for normalization. It raises on zero quaternion content.

## Point action and batching

**Symptom:** `Invalid Tensor Dimension` from `Act`.

- Point input must end in 3 (Euclidean) or 4 (homogeneous) coordinates.
- A group acts on points; an algebra does not. Call `a.Exp().Act(p)`.
- For homogeneous points, the final coordinate is carried through; do not pass a
  3×3/4×4 matrix as if it were a point.

**Symptom:** output shape is surprising or broadcasting fails.

- The final LieTensor embedding is not a batch dimension. Use `lshape` to reason
  about item batches and inspect `points.shape[:-1]` for point batches.
- Transform and point leading shapes must be broadcast-compatible. An `(N, 3)`
  point batch and `(N, 7)` SE3 batch pair itemwise; a `(1, N, 7)` batch can
  broadcast over `(M, 1, 3)` points.
- Group-group composition requires the same Lie type; it does not convert SO3
  to SE3 or raw matrices to typed groups.

**Symptom:** `cumprod` result order is wrong.

- `left=True` computes `x_i @ ... @ x_0`; `left=False` computes
  `x_0 @ ... @ x_i`.
- Use a batch/sequence dimension, never the final embedding dimension.
- `_` variants mutate their input. Use functional variants while retaining values
  needed for a gradient or a comparison.

## Conversion and validation failures

**Symptom:** `mat2SE3` rejects a matrix.

- Input must be at least 2D with shape ending in `(3,3)`, `(3,4)`, or `(4,4)`.
- With `check=True`, the top-left 3×3 block must be orthogonal with determinant 1
  within `rtol`/`atol`. A noisy matrix is not silently projected.
- For `(4,4)`, the last row should be `[0,0,0,1]`; PyPose warns if it is not,
  although the row is not used. Keep validation enabled for external data.
- If the matrix is intentionally approximate, document why `check=False` is safe
  and test the resulting quaternion/rotation matrix separately.

**Symptom:** Sim(3) conversion fails or gives NaN.

- The 3×3 block must have a nonzero determinant and decompose into a positive
  scale times a proper rotation.
- Confirm the matrix uses `[sR,t]` and not a project-specific alternate scale
  convention. A reflection or zero-scale block is invalid.

**Symptom:** Euler round-trip is not exact.

- Euler representation is nonunique and has gimbal-lock singularities near pitch
  ±π/2. Compare matrices or use a quaternion/rotation vector for identity tests.
- `euler2SO3` uses roll, pitch, yaw in x-y-z order and returns one valid solution.

## Autograd and parameter failures

**Symptom:** `.grad` is `None`, has an unexpected shape, or contains NaN.

- Backpropagate a scalar loss and retain the original leaf; a non-leaf result such
  as `a.Exp()` will not receive a leaf `.grad` unless `retain_grad()` is used.
- If using a factory, pass `requires_grad=True` at creation. If using a raw tensor,
  call `.requires_grad_()` before the manifold operation.
- Assert `grad.shape == a.shape` for an algebra leaf and check `torch.isfinite`.
- Keep rotations away from the logarithm branch near π and avoid zero scale,
  invalid quaternions, and unsupported low-precision CPU kernels.
- Do not mutate a leaf or an intermediate needed for backward. Use clones and
  functional operations instead of in-place updates.

**Symptom:** `Parameter` is plain `nn.Parameter` and has no `.Exp()`.

- Only a LieTensor input preserves `ltype`:
  `pp.Parameter(pp.randn_SE3(1))` is typed, while
  `pp.Parameter(torch.zeros(1, 7))` is an ordinary parameter.
- `sjac=True` enables optional sparse tracing and may require the optional
  backend. It is not required for ordinary autograd and is outside this skill's
  optimizer workflow.
- Never wrap a typed value in `.tensor()` before constructing a typed parameter if
  the module needs manifold methods.

## Dtype, device, and installation

**Symptom:** device or dtype mismatch.

- Print `x.device`, `x.dtype`, `points.device`, and `points.dtype`; align them
  before `Act`, composition, or conversion.
- Use `x.to(device=device, dtype=dtype)` and create new points with the same
  `device`/`dtype`. The identity/factory APIs accept those keyword arguments.
- CPU is the baseline. CUDA requires a CUDA-enabled PyTorch build and an available
  device; generic CUDA LieTensor operations are not evidence that optional sparse
  optimization is configured.
- The public package requires PyTorch 2.x (the inspected package uses PyTorch
  2.13.0+cu130). Check the installed package and PyTorch version before assuming
  a kernel is available.

**Symptom:** `pp.Parameter(..., sjac=True)` or sparse code raises an import error.

- The optional BAE backend is separate from ordinary LieTensor use. Install and
  validate the documented compatible backend only when the `optimization` skill
  explicitly requires sparse Jacobian/LM support.
- Do not hide a required-backend failure by switching a sparse task to a dense
  workflow without revising the task contract.

## Minimal diagnostic

Run the bundled deterministic helper first:

```bash
python scripts/lietensor_smoke.py --help
python scripts/lietensor_smoke.py --device cpu --dtype float64
```

It exercises `Exp`/`Log`, point action, matrix conversion, batching, and an
assertion-backed gradient. A failure in the helper narrows the problem to base
import, typed dimensions, numeric conversion, broadcast, or autograd before a
larger model introduces additional variables.
