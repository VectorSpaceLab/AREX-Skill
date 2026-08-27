# State estimation and model composition

## Build a model with a stable call contract

A filter needs a model whose transition and observation functions are callable
without injecting random noise during Jacobian/sigma-point evaluation. Define an
`NLS` subclass like this:

```python
class SensorModel(pp.module.NLS):
    def state_transition(self, state, input, t=None):
        # state: (..., n), input: (..., q), return (..., n)
        return f(state, input, t)

    def observation(self, state, input, t=None):
        # return (..., m)
        return h(state, input, t)
```

`NLS.forward` stores `self.state` and `self.input`, evaluates both functions at
`self.systime`, and returns `(next_state, observation)`. The registered forward
hook increments the time after the call. Thus a model initialized with
`model.reset(t0)` uses `t0` for the first `forward`; it does not use `t0+1`.
`reset()` is essential before a second replay. For explicit linearization, use
`model.set_refpoint(state=x, input=u, t=t)` and only then read `model.A`/`B`/
`C`/`D`/`c1`/`c2`. A refpoint without a prior model call must provide all needed
state and input values.

For `LTI`, pass `A`, `B`, `C`, and `D` with final matrix axes. The model computes

```text
x_next = A @ x + B @ u + c1
observation = C @ x + D @ u + c2
```

using PyPose's batched matrix-vector operations. For `LTV`, stack time matrices
and override the matrix properties (normally selecting `[..., self._t, :, :]`)
or use a subclass that generates matrices from `self._t`. A custom LTV should
keep its time convention explicit and reset its clock before replay.

## One-step EKF contract

Use:

```python
estimator = pp.module.EKF(model, Q=Q_default, R=R_default)
x_next, P_next = estimator(x, y, u, P, Q=None, R=None, t=None)
```

The constructor buffers are optional, but the call must receive `Q` and `R` if
they were not configured at construction. Per-call values override buffers.
`x` and `u` are the previous estimate/current input, while `y` is the current
measurement. The implementation linearizes at `(x,u,t)`, predicts `xm` using
`state_transition(x,u,t)`, forms the innovation against `observation(x,u,t)`,
and returns the posterior state/covariance.

Use square covariance shapes:

```text
x       (..., n)
y       (..., m)
u       (..., q)
P, Q    (..., n, n)
R       (..., m, m)
output  (..., n), (..., n, n)
```

`P`, `Q`, and `R` should be symmetric positive semidefinite/definite in the
intended noise model. A zero or poorly conditioned innovation covariance can
make the pseudoinverse produce unstable gains; inspect `torch.linalg.eigvalsh`
or add physically justified diagonal noise rather than masking the failure.
After every update, check `P` is finite and approximately symmetric. If a
strictly symmetric covariance is required downstream, symmetrize a copy at the
boundary, not the model's hidden state without recording it.

A minimal deterministic data loop is:

```python
for k in range(T - 1):
    truth[k + 1], measurement[k] = model(truth[k], control[k])
    estimate[k + 1], covariance[k + 1] = estimator(
        estimate[k], measurement[k], control[k], covariance[k])
```

Noise belongs in `truth`/`measurement` generation. Do not put random noise in
`state_transition` or `observation` when the same model is linearized, because
the finite/autograd derivatives then include unrelated noise.

## UKF contract

`UKF(model, Q, R, msqrt=None)` follows the same call layout with optional `k`:

```python
x_next, P_next = ukf(x, y, u, P, Q=None, R=None, t=None, k=None)
```

The default square-root function is `torch.linalg.cholesky`. It constructs
`2*n+1` sigma points along the last state axis and uses `k=3-n` when omitted.
Use a custom `msqrt` only when its output is a compatible square-root matrix for
`(..., n, n)` covariance. `P` must have matching last two dimensions; non-PSD
or singular inputs can fail in Cholesky before the measurement update. For
small numerical asymmetries, validate/symmetrize the covariance before calling,
and treat a large diagonal jitter as a modeling decision.

The filter first propagates sigma points through `state_transition`, computes a
prior mean/covariance with `Q`, then generates observation sigma points and
updates with `R`. Keep nonlinear periodic or manifold-valued state components
within the representation expected by the model; this module uses ordinary
Euclidean weighted means and is not a replacement for a manifold-aware filter.

## PF contract

`PF(model, Q, R, particles=1000)` uses the same call shape:

```python
x_next, P_next = pf(x, y, u, P, Q=None, R=None, t=None)
```

At each call it samples `particles` states from `MultivariateNormal(x, n*P)`,
propagates them through the model, computes measurement likelihood under `R`,
resamples using normalized weights, and returns their mean and covariance plus
`Q`. It is stochastic even with the same input unless the caller controls
`torch`'s RNG. Use enough particles for a multimodal posterior and record the
seed/count in experiments. A singular `P` or `R`, negative variance, or an
incompatible batch covariance fails in the distribution constructors.

The current implementation's particle axis is leading to the sampled state
before model broadcasting; test batch shapes explicitly when using batched
models. Prefer a small particle count only for smoke checks, not accuracy.

## Choosing and composing estimators

- **EKF:** efficient and differentiable through local Jacobians when the model
  is smooth and the posterior is near one mode.
- **UKF:** avoids explicit Jacobians and captures some local nonlinearity, but
  still assumes a Euclidean sigma-point representation and a valid square root.
- **PF:** handles non-Gaussian/multimodal uncertainty but is stochastic and more
  expensive; its estimate is a Monte Carlo sample summary.

All three share the same model and covariance dimensions, so one can compare
them on a common deterministic trajectory. Do not share a mutable model clock
between parallel estimators without resetting or using independent model
instances. `set_refpoint` is called by EKF/UKF/PF before propagation, but the PF
also calls `model(xp, u)` internally, advancing the model hook once per filter
step; use explicit `t` for time-varying models and check whether this clock
advance matches your intended timeline.

## Hard checks for estimation code

1. Create `Q`, `R`, and initial `P` with `torch.eye` in the same dtype/device as
   the state.
2. Assert `P.shape[-2:] == (n,n)` and `R.shape[-2:] == (m,m)` before calling.
3. Check filter outputs are finite and `max(abs(P-P.mT))` is small.
4. On a seeded fixture, compare initial and final state error; do not assert
   every random trajectory improves monotonically.
5. For time-varying models, record `reset(t=...)`, the `t` passed to each call,
   and the model's `systime` after calls.
6. If a call fails, reduce to unbatched `(...=empty)` shapes, then add batch and
   time axes one at a time; never silently squeeze the feature dimension.
