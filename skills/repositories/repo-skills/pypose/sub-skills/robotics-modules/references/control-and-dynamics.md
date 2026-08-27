# Dynamics, LQR, and MPC

## Discrete-time dynamics

### LTI

`LTI(A, B, C, D, c1=None, c2=None)` represents

```text
x[k+1] = A x[k] + B u[k] + c1
y[k]   = C x[k] + D u[k] + c2
```

Use state/input/observation features in the last dimension:
`x (..., n)`, `u (..., q)`, `y (..., m)`, `A (..., n, n)`, `B (..., n, q)`,
`C (..., m, n)`, and `D (..., m, q)`. Leading batch dimensions may broadcast
when the matrix-vector products are valid. Optional constants have shapes
`(...,n)` and `(...,m)`. Matrices are registered buffers, so `.to(device)` moves
them with the module; construct them with the intended dtype/device first.

`System.forward` returns `(next_state, observation)` and advances `systime`
through a hook. `reset(t=0)` sets the time and returns `self`. The `observation`
corresponds to the state/input passed to that call, while the returned first
item is the next state. Keep this timing distinction when building a training
trajectory.

### LTV and NLS

`LTV` is an LTI shell intended for matrix values selected as a function of the
clock. A common subclass stores `A[...,T,n,n]` and returns
`self._A[..., self._t % T, :, :]`; call `reset` and select a known time when
replaying. `set_refpoint(..., t=...)` sets a reference time but does not itself
run a transition.

`NLS()` requires `state_transition` and `observation`. They receive the current
state, input, and time. `set_refpoint` calls both at the selected point and uses
PyTorch Jacobians to expose an equivalent affine local LTI model:
`A=df/dx`, `B=df/du`, `C=dg/dx`, `D=dg/du`, with offsets `c1`, `c2`. This is the
bridge used by EKF and iterative LQR/MPC. Functions should return consistent
`(..., feature)` tensors and avoid in-place mutation or random noise.

## LQR

Construct `LQR(system, Q, p, T)`. The quadratic stage vector is the concatenated
`tau=[x,u]`, so with state dimension `n` and control dimension `q`:

```text
Q: (..., T, n+q, n+q)  # or (..., n+q, n+q), tiled over T
p: (..., T, n+q)        # or (..., n+q), tiled over T
x_init: (B,n)
```

`Q` must be square, `Q` and `p` must share dtype/device, and their batch/time
shapes must agree. The forward contract is:

```python
x, u, cost = lqr(x_init, dt=1, u_traj=None,
                  u_lower=None, u_upper=None, du=None)
```

with `x (B,T+1,n)`, `u (B,T,q)`, and `cost (B,)`. `u_traj` supplies a nominal
control trajectory for iterative/nonlinear use; omitted values are zeros. The
optional bounds and `du` constrain the forward controls. `dt` is used to choose
reference times during backward recursion.

LQR runs a rollout before its backward recursion. For nonlinear `NLS`, it calls
`system.set_refpoint` at each horizon state/input and reads local `A/B`, so the
model must have correct Jacobians and the state/input trajectory must preserve
features. For `LTI`, the same matrices are reused. The `Quu` control block is
Cholesky factored; an indefinite or singular control cost/dynamics combination
raises or produces invalid gains. Make `Q` positive definite in the control
block for a stable baseline.

The first control is not returned alone: consume `u[...,0,:]` when implementing
a receding-horizon loop. If repeatedly solving with a mutable model, reset its
clock or use an explicit reference time policy.

## MPC

Construct `MPC(system, Q, p, T, stepper=None)`. Its forward argument order is
intentionally different from LQR:

```python
x, u, cost = mpc(dt, x_init, u_init=None,
                 u_lower=None, u_upper=None, du=None)
```

MPC performs iterative LQR for a nonlinear system. `u_init` is the current
nominal trajectory and should be `(B,T,q)` (or the exact batch shape expected by
LQR). It returns the same `(B,T+1,n)`, `(B,T,q)`, `(B,)` layout. It uses
`ReduceToBason(steps=10)` by default and decrements the configured max steps by
one internally; a supplied stepper is mutated and must implement the stepper
interface. Set an explicit `ReduceToBason(steps=1 or 2, patience=..., tol=...)`
for deterministic tests and inspect final cost. `MPC.forward` runs its iterative
search under `torch.no_grad()` and then makes a final differentiable LQR call
using the best nominal controls.

A stepper's lifecycle is:

```python
stepper.reset()
while stepper.continual():
    ...
    stepper.step(loss)
```

Always reset before reuse. A custom stepper must stop even if loss is NaN or
unchanged; otherwise a caller can hang. Check that the final `cost` is finite
and compare it with the initial nominal cost when possible.

## Horizon and shape checklist

- Decide whether `T` means the number of controls/stages (`u` has `T`) or the
  number of state samples (`x` has `T+1`). PyPose LQR/MPC use the former.
- Build `Q`/`p` with the concatenated feature ordering `[state, control]`; do
  not pass separate state/control costs without assembling them.
- Batch all `Q`, `p`, `x_init`, and model matrices consistently. The LQR forward
  implementation requires `x_init.ndim == 2` at its final solve.
- Keep `dt` in the same time units as the dynamics. For continuous-time models
  discretized externally, document that discretization; PyPose's `LTI` is
  already a discrete-time step.
- Use identical `dtype` and `device`; constructor assertions reject mismatches.

## Composition recipes

**Linear finite-horizon control:** create `LTI`, tile costs if needed, call
`LQR(x_init)`, and apply `u[...,0,:]` to the real plant before re-solving.

**Nonlinear receding horizon:** create pure `NLS`, provide a positive-definite
control cost and a nominal `u_init`, construct an explicit stepper, call
`MPC(dt, x_init, u_init)`, apply only the first control, then update/re-solve.

**Estimator + controller:** filter the observation into `x_est`, hand the
estimate to LQR/MPC, and keep the estimator's `Q/R` uncertainty separate from
the controller's stage cost `Q/p`. Do not accidentally pass a covariance as a
controller cost.
