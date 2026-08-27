# PyPose robotics module API reference

This is a compact operating reference distilled from `pypose/module/*.py`,
`docs/source/modules.rst`, and the module tests. Unless stated otherwise,
features are in the last dimension, matrices in the last two dimensions, and
leading dimensions are batch dimensions that must broadcast.

## Public constructors

| Module | Verified constructor | Main call | Return |
|---|---|---|---|
| `System` | `System()` | subclass-specific `model(state, input)` | `(next_state, observation)` |
| `LTI` | `LTI(A, B, C, D, c1=None, c2=None)` | `system(state, input)` | `(next_state, observation)` |
| `LTV` | `LTV(A=None, B=None, C=None, D=None, c1=None, c2=None)` | subclass/property-selected matrices, then `system(state, input)` | `(next_state, observation)` |
| `NLS` | `NLS()` | subclass implementing `state_transition` and `observation`, then `model(state, input)` | `(next_state, observation)` |
| `EKF` | `EKF(model, Q=None, R=None)` | `ekf(x, y, u, P, Q=None, R=None, t=None)` | `(posterior_x, posterior_P)` |
| `UKF` | `UKF(model, Q=None, R=None, msqrt=None)` | `ukf(x, y, u, P, Q=None, R=None, t=None, k=None)` | `(posterior_x, posterior_P)` |
| `PF` | `PF(model, Q=None, R=None, particles=1000)` | `pf(x, y, u, P, Q=None, R=None, t=None)` | `(posterior_x, posterior_P)` |
| `LQR` | `LQR(system, Q, p, T)` | `lqr(x_init, dt=1, u_traj=None, u_lower=None, u_upper=None, du=None)` | `(x, u, cost)` |
| `MPC` | `MPC(system, Q, p, T, stepper=None)` | `mpc(dt, x_init, u_init=None, u_lower=None, u_upper=None, du=None)` | `(x, u, cost)` |
| `IMUPreintegrator` | `IMUPreintegrator(pos=torch.zeros(3), rot=identity_SO3(), vel=torch.zeros(3), gravity=9.81007, gyro_cov=(3.2e-3)**2, acc_cov=(8e-2)**2, prop_cov=True, reset=False)` | `integrator(dt, gyro, acc, rot=None, gyro_cov=None, acc_cov=None, init_state=None)` | dict with `pos`, `rot`, `vel`, optional `cov` |
| `EPnP` | `EPnP(intrinsics=None, refine=True)` | `epnp(points, pixels, intrinsics=None)` | `SE3` LieTensor pose |
| `ICP` | `ICP(init=None, stepper=None)` | `icp(source, target, ord=2, dim=-1, init=None)` | `SE3` LieTensor pose |
| `GeodesicLoss` | `GeodesicLoss(reduction='mean')` | `loss(input, target)` | scalar or batch tensor |

The explicitly verified signatures requested for construction are:
`EKF(model,Q=None,R=None)`, `UKF(model,Q=None,R=None,msqrt=None)`,
`PF(model,Q=None,R=None,particles=1000)`, `LQR(system,Q,p,T)`,
`MPC(system,Q,p,T,stepper=None)`, the `IMUPreintegrator` defaults above,
`EPnP(intrinsics=None,refine=True)`, and `ICP(init=None,stepper=None)`.

## Dynamics contracts

### `System`, `LTI`, `LTV`, `NLS`

- `System.forward(state, input)` converts state/input to at least 1D, calls
  `state_transition`, then `observation`, and advances the integer system clock
  through a forward hook. `reset(t=0)` sets the clock and returns the module;
  `systime` reads/sets it.
- `LTI` implements `x_next = A x + B u + c1` and `y = C x + D u + c2`.
  State/input are row-vector features, so use `(..., n_state)`,
  `(..., n_input)` and matrices `(..., n_state, n_state)`,
  `(..., n_state, n_input)`, `(..., n_obs, n_state)`,
  `(..., n_obs, n_input)`. `c1` and `c2` are optional `(..., feature)` terms.
- `LTV` inherits LTI. Supply stacked matrices or override properties to select a
  time slice using `self._t`; `set_refpoint(..., t=...)` sets the clock for a
  chosen linearization/reference time.
- `NLS` subclasses must implement `state_transition(state, input, t)` and
  `observation(state, input, t)`. A call uses the current time before advancing
  the hook. `set_refpoint` stores the selected state/input/time and enables
  automatic Jacobian properties `A`, `B`, `C`, `D`; affine offsets `c1`, `c2`
  make the local model equivalent to LTI around the selected point.
- `runsys(system, T, x_traj, u_traj)` normalizes vectors to `[B,T,N]` with
  `toBTN`; it fills states through `T-1` transitions. Use explicit trajectory
  shapes rather than assuming a one-dimensional input is a time sequence.

### Filter call shape

Given state dimension `n`, observation dimension `m`, and batch `B`:
`x: (..., n)`, `y: (..., m)`, `u: (..., input_dim)`, `P: (..., n, n)`,
`Q: (..., n, n)`, and `R: (..., m, m)`. A filter returns `x_next: (..., n)`
and `P_next: (..., n, n)`. Matrices can be unbatched or broadcast batchwise,
but do not pass a feature vector as a covariance. `Q` and `R` passed to a
forward call override constructor buffers; omitting both requires the matching
constructor uncertainty to have been set.

- EKF linearizes the model at `(x,u,t)`, predicts through the transition,
  applies the measurement residual, and uses a pseudoinverse for the innovation
  covariance.
- UKF uses a Cholesky-like `msqrt` (default `torch.linalg.cholesky`) and sigma
  points. `k=None` uses `3 - n`; provide a scalar `k` only when deliberately
  changing the weights. `P` must be square and suitable for the selected square
  root.
- PF draws `particles` samples from `MultivariateNormal(x, n*P)`, propagates
  them, computes normalized measurement likelihood under `R`, resamples, and
  returns the sample mean and covariance plus `Q`. It is stochastic; seed it
  when comparing runs. `particles` is an integer count, not a tensor shape.

## Control contracts

- `Q` describes the joint `[x, u]` vector, so if `n_state=n` and
  `n_control=c`, `Q` is `(..., T, n+c, n+c)` and `p` is `(..., T, n+c)`. A
  time-invariant `Q: (..., n+c, n+c)` or `p: (..., n+c)` is tiled across `T`.
  The implementation requires matching dtype/device, a square `Q`, and the
  final feature dimensions to agree.
- LQR requires `x_init: (batch, n_state)` in its forward recursion and returns
  `x: (batch, T+1, n_state)`, `u: (batch, T, n_control)`, and `cost: (batch,)`.
  `dt` is used when selecting reference times for time-varying/nonlinear
  linearization. Bounds and `du` are optional control clamps/change limits.
- MPC has the same costs and trajectory outputs. Its forward argument order is
  `(dt, x_init, u_init=None, ...)`, unlike LQR's `(x_init, dt=1, ...)`. The
  default `ReduceToBason(steps=10)` is reduced by one internally because the
  final call is retained for gradients; custom steppers must expose
  `reset()`, `continual()`, and `step(loss)`.

## Geometric and loss contracts

- `IMUPreintegrator` accepts `dt`, `gyro`, and `acc` with shapes `(B,F,3)`,
  `(F,3)`, or `(3)` after normalization, and returns per-frame state with batch
  and frame dimensions. `cov` is `(B,9,9)` at the final accumulated state and
  is ordered rotation, velocity, position. See the dedicated reference for
  units, frame, defaults, and reset.
- `EPnP` requires at least four matching points: `points (...,N,3)`,
  `pixels (...,N,2)`, and `intrinsics (...,3,3)`. Constructor intrinsics are
  overridden by a non-`None` call argument. The implemented camera matrix is a
  batched rectified matrix with `fx`, `fy`, `cx`, `cy` in the expected entries;
  arbitrary skew/full intrinsics are not supported by this implementation.
- `ICP` accepts `source` and `target` point clouds `(...,N,3)`, optionally an
  `SE3` constructor or call initialization, and uses nearest neighbors + SVD.
  `init` at the call takes precedence over constructor `init`. The output is the
  source-to-target `SE3` estimate. `ord` and `dim` affect nearest-neighbor
  distance calculation.
- `GeodesicLoss` accepts LieTensors whose rotation parts can be extracted
  (`SO3`, `SE3`, `RxSO3`, `Sim3`, and algebra forms). `reduction` is exactly
  `'none'`, `'mean'`, or `'sum'`; `'none'` preserves the batch loss.
