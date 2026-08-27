# IMU, PnP, ICP, and rotation loss

## IMUPreintegrator

### Constructor and defaults

```python
pp.module.IMUPreintegrator(
    pos=torch.zeros(3),
    rot=pp.identity_SO3(),
    vel=torch.zeros(3),
    gravity=9.81007,
    gyro_cov=(3.2e-3)**2,
    acc_cov=(8e-2)**2,
    prop_cov=True,
    reset=False,
)
```

Scalar `gyro_cov`/`acc_cov` values become three-axis diagonal variances. A
three-element tensor supplies per-axis diagonal entries. The constructor rejects
`prop_cov=False, reset=False` together because non-propagated covariance cannot
be retained across a non-resetting accumulation.

### Forward contract

```python
state = integrator(
    dt, gyro, acc, rot=None,
    gyro_cov=None, acc_cov=None, init_state=None,
)
```

`dt`, `gyro`, and `acc` can be `(B,F,1/3)`, `(F,3)`, or `(3)`-like inputs after
normalization, with the normal sensor use being `(B,F,1)` for `dt` and `(B,F,3)`
for rates/accelerations. `rot` is an optional known body orientation (`SO3`
LieTensor) used to compensate gravity. `init_state` is a dict containing
`pos`, `rot`, `vel`, and optionally `cov`/`Rij`; it overrides constructor state
for that call.

The result is a dict containing `pos`, `rot`, and `vel` for each integrated
frame. With `prop_cov=True`, `cov` is included. The accumulated covariance is
`(B,9,9)` at the final frame, ordered **rotation, velocity, position**. The
integration follows

```text
Dr[k+1] = Dr[k] * Exp(gyro[k] * dt[k])
Dv[k+1] = Dv[k] + Dr[k] @ acc_without_gravity[k] * dt[k]
Dp[k+1] = Dp[k] + Dv[k] * dt[k]
                    + 0.5 * Dr[k] @ acc_without_gravity[k] * dt[k]**2
```

The raw acceleration is body-frame acceleration including gravity. PyPose uses
the configured gravity vector `[0, 0, gravity]`, and rotation to compensate it.
`gyro` is angular rate in radians per second, `acc` is acceleration in distance
units per second squared, and `dt` is seconds. Keep these units consistent; a
millisecond value passed as seconds creates squared position errors.

With initial state `(p_i,R_i,v_i)`, the implementation's `predict` combines
`R_j=R_i*Dr`, `v_j=v_i+R_i*Dv`, and
`p_j=p_i+R_i*Dp+v_i*Dt`. Gravity affects `acc_without_gravity` during
`integrate` (using the configured gravity and orientation), so validate the
full convention on a zero-rate/known-gravity fixture rather than adding a
second gravity term at the consumer.

### Accumulation and reset

- `reset=False` (default) stores the last frame's `pos`, `rot`, `vel`, `cov`, and
  incremental rotation state for the next call. It accumulates across calls.
- `reset=True` leaves constructor state as the next-call initial state; use it
  for independent windows. A call-level `init_state` takes precedence over the
  constructor/reset state.
- If covariance propagation is disabled, request reset semantics; otherwise the
  constructor intentionally raises.
- Before comparing two runs, use a new integrator or an explicit `init_state`.
  Do not assume calling `torch.nn.Module.reset` exists; this module's `reset` is a
  boolean configuration, not a reset method.

Use `state['pos'][..., -1, :]`, `state['vel'][..., -1, :]`, and
`state['rot'][..., -1, :]` for the last integrated frame. If the input was
single-frame, preserve the frame axis in downstream code until the contract is
checked. Validate covariance finiteness and the expected order before slicing
position blocks (`cov[...,6:9,6:9]`).

## EPnP

Construct `EPnP(intrinsics=None, refine=True)` and call:

```python
pose = epnp(points, pixels, intrinsics=None)
```

`points` are world/object 3D points `(...,N,3)` and `pixels` are corresponding
2D image points `(...,N,2)`, with identical `N >= 4`; leading batches broadcast.
The return is an `SE3` LieTensor pose. A call-level `intrinsics` overrides a
constructor buffer. If no intrinsics are provided at either point, the module
will fail when it needs `intrinsics`; set them explicitly.

The implementation supports batched **rectified** intrinsics in the form
`[[fx,0,cx],[0,fy,cy],[0,0,1]]`. It reads focal/principal-point entries, not
arbitrary skew/distortion. Use pixels in the same units and coordinate
convention as `K`; do not undistort/normalize twice. `refine=True` runs the
module's internal beta refinement; set `False` for a direct deterministic
baseline or when gradients through refinement are not needed.

Failure modes include fewer than four matches, mismatched point/pixel counts,
non-broadcastable leading batches, degenerate/coplanar point configurations,
nonfinite coordinates, and a singular camera geometry. For reliable tests,
use six or more non-coplanar points with positive camera depth and verify
reprojection error, rather than checking only that an `SE3` object returned.
The estimated pose convention is the transform used by PyPose's reprojection
functions; when composing with another transform, verify direction with a
known synthetic projection.

## ICP

Construct `ICP(init=None, stepper=None)` and call:

```python
pose = icp(source, target, ord=2, dim=-1, init=None)
```

`source` and `target` are `(...,N,3)` point clouds. `init` must be an `SE3`
LieTensor and a call-level value overrides the constructor. ICP initializes its
working source with the initial pose, repeatedly finds nearest target neighbors,
solves the correspondence transform with SVD, updates, and stops through the
stepper. It returns a source-to-target `SE3` estimate.

The default stepper allows up to 200 iterations. Use a bounded explicit
`ReduceToBason(steps=..., patience=..., decreasing=..., tol=...)` in tests and
call `reset()` before reuse. ICP is local: an incorrect initial pose, sparse or
ambiguous correspondences, symmetric/repeated structures, collinear/coplanar
points, outliers, or scale mismatch can cause a plausible but wrong local
minimum. An SVD rigid transform also has no ability to recover scale.

Validate both transform and residual:

```python
registered = pose.unsqueeze(-2) @ source
residual = (registered - matched_or_target).norm(dim=-1).mean()
```

For unequal source/target sizes, nearest-neighbor matching still operates, but
do not compare pointwise arrays without using the correspondences. Check the
stepper loss trend and stop reason; a fixed iteration cap is not evidence of
convergence.

## GeodesicLoss

`GeodesicLoss(reduction='mean')` compares only the rotation parts of two
compatible LieTensors. It accepts `reduction='none'`, `'mean'`, or `'sum'` and
raises for other values. The effective error is the norm of the logarithm of
`input.rotation() * target.rotation().Inv()` (or the equivalent rotation
geodesic for matrix representations). `none` returns one loss per batch item;
`mean`/`sum` return scalars. Inputs must both be LieTensors with compatible
rotation types/shapes; this is a rotation loss, not translation or trajectory
metric.
