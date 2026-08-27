# Solver, kernel, and strategy reference

Choose a solver from the matrix below after checking the matrix properties,
layout, device, and expected conditioning.

| Solver | Equation/layout | Good default use | Main failure mode |
|---|---|---|---|
| `PINV` | Dense rectangular/square `A`; pseudoinverse | GN fallback or rank-deficient small system | Slow and memory-heavy |
| `LSTSQ` | Dense least-squares `A`; `torch.linalg.lstsq` | Dense GN with a well-defined least-squares solve | Driver/rank/memory issues |
| `Cholesky` | Dense SPD normal equations | Default dense LM | Indefinite or non-positive-definite `A` |
| `CG` | Dense or compatible sparse SPD operator | Iterative solve, small/batched tests | Non-SPD matrix, poor conditioning, no convergence |
| `PCG` | BAE sparse SPD normal equations | CUDA sparse LM | Missing BAE/CUDA, OOM, backend errors |

## Linear solvers

`PINV(atol=None, rtol=None, hermitian=False)` computes a Moore-Penrose
pseudoinverse. It tolerates rectangular matrices but can be expensive. Use
`LSTSQ(rcond=None, driver=None)` for dense least-squares; CPU drivers are
`gels`, `gelsy`, `gelsd`, and `gelss`, while CUDA's documented driver is `gels`
with a full-rank assumption. If `LSTSQ` returns NaNs, repair the system or
fall back to `PINV` only as a deliberate diagnostic.

`Cholesky(upper=False)` requires a real symmetric or complex Hermitian positive-
definite matrix. LM's damped normal equations are designed to make this
reasonable, but a bad Jacobian, weight, or robust correction can still break
it. Inspect finiteness and eigenvalue/diagonal behavior on a small reproduction
before changing `upper`.

`CG(maxiter=None, tol=1e-5)` expects symmetric positive-definite `A`; it accepts
dense and compatible sparse layouts and an optional preconditioner in its
low-level call. The implementation defaults `maxiter` to `10 * n` when omitted.
`PCG(maxiter=None, tol=1e-5)` has the same public constructor but is resolved
from optional BAE and is intended for sparse CUDA normal equations. Test the
matrix-vector operation and a small iteration limit before launching a large
problem.

## Damping strategies

`Constant(damping=1e-6)` is deterministic and useful for smoke tests or a stable
known scale. `damping` must be positive.

`Adaptive(damping=1e-6, high=0.5, low=1e-3, up=2., down=.5, min=1e-6,
max=1e16)` computes a step-quality ratio from actual and predicted loss
reduction. It decreases damping after a very successful step, leaves it alone
after a successful step, and multiplies it by `up` after a poor step, clamping
to `[min, max]`.

`TrustRegion(radius=1e6, high=.5, low=1e-3, up=2., down=.5, factor=.5,
min=1e-6, max=1e16)` stores damping as the inverse radius. Very successful
steps expand the radius; poor steps shrink it and shrink the down factor by
`factor`. The source examples use `TrustRegion(up=2.0, down=0.5**4)` for
sparse BA/PGO, but this is a tuning choice, not a universal default.

For a stalled solve:

1. Record the strategy state from `optimizer.param_groups[0]`.
2. Start with `Constant` and a conservative positive damping to separate
   strategy behavior from model/solver errors.
3. Increase damping/radius conservatism only after checking residual signs,
   target alignment, finite values, and Jacobian rank.
4. Keep `reject` enabled; an uphill step should be rolled back and retried.

## Robust kernels

The kernel receives the nonnegative squared norm of each residual block, not the
raw signed residual. The common choices are:

- `Huber(delta=1.0)`: quadratic below `delta`, linear in residual magnitude
  above it; sharp and predictable.
- `PseudoHuber(delta=1.0)`: smooth Huber-like transition.
- `Cauchy(delta=1.0)`: logarithmic growth, strong outlier suppression.
- `SoftLOne`, `Arctan`, `Tolerant`, and `Scale`: specialized alternatives;
  validate their parameter constraints from the constructor.

The kernel must be given a positive `delta`; `Tolerant` requires `a > 0` and
`b < 0`; `Scale` requires `0 < delta <= 1`. All inputs must be nonnegative and
finite. A negative or NaN squared norm is a residual/model error.

## Correctors

`FastTriggs(kernel)` rescales `R` and `J` using the square root of the kernel's
first derivative. This is the stable default when a kernel is used. `Triggs`
uses second derivatives and can become unstable for a kernel with a negative
second derivative; use only when that second-order correction is intentional
and validated.

Do not use FastTriggs under `torch.inference_mode()`; the source implementation
raises because it needs gradient-enabled kernel differentiation. `torch.no_grad()`
is compatible with the optimizer's normal use. If a kernel is supplied without
a corrector, `LM`/`GN` construct automatic FastTriggs correction.

## Shape and weighting rules

For residual shape `B*M*N*D`, a weight can be block-only `D*D` or have
broadcast-compatible batch/block prefixes, such as `N*D*D`, `M*N*D*D`, or
`B*M*N*D*D`. A list of weights must match the output residual list. Weights
should be square positive-definite matrices and share dtype/device with the
residual. Sparse mode does not support weights.

The final residual dimension must remain visible. A global flattened scalar
makes the robust kernel operate on one giant block and destroys sample-level
structure. For scalar samples, use `[..., 1]`.

## Scheduler behavior

`StopOnPlateau(optimizer, steps, patience=5, decreasing=1e-3,
verbose=False)` tracks `optimizer.last` and `optimizer.loss`. Call `step(loss)`
after every optimizer step. It stops at `steps`, after `patience` reductions
smaller than `decreasing`, or after LM has a rejected step. Calling
`scheduler.continual` as a boolean is deprecated and raises; call
`scheduler.continual()`.

## Evidence and diagnostics

The implementation contracts come from `pypose/optim/solver.py`,
`strategy.py`, `kernel.py`, `corrector.py`, and `scheduler.py`; native checks
are in `tests/optim/test_solver.py`, `test_optimizer.py`, and
`test_scheduler.py`. The CUDA sparse examples use `PCG(tol=1e-4, maxiter=250)`
and `TrustRegion(up=2.0, down=0.5**4)` as a tested starting point, but their
full datasets and plotting are not part of this runtime skill.
