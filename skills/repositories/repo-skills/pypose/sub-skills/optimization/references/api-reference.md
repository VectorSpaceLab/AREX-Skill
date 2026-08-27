# Optimization API reference

This reference targets the verified PyPose 0.9.5 surface. Check the installed
package version and backend before relying on optional sparse APIs.

## Optimizers

```text
LM(model, solver=None, strategy=None, kernel=None, corrector=None,
   weight=None, reject=16, min=1e-6, max=1e32, vectorize=True, sparse=False)
GN(model, solver=None, kernel=None, corrector=None, weight=None,
   vectorize=True)
```

`LM` is also exported as `pypose.optim.LevenbergMarquardt`, and `GN` as
`pypose.optim.GaussNewton`. Both accept an `nn.Module`; the module parameters
are the optimization state. `LM.step(input, target=None, weight=None)` and
`GN.step(input, target=None, weight=None)` return the post-step loss. The
`weight` passed to `step` takes precedence over the constructor's `weight`.

Defaults and behavior:

- `LM` defaults to `Cholesky()` and `TrustRegion()`. It clamps the Hessian
  diagonal to `[min, max]`, and rejects up to `reject` unsuccessful updates.
- `GN` defaults to `PINV()` and has no damping strategy or sparse flag.
- `kernel` and `corrector` can be one object or a list. A list has length one
  or the number of residual outputs; `None` entries are treated as trivial.
- `vectorize` is forwarded to `modjac` for dense optimization.
- `sparse=True` activates the optional backend during `LM` construction and
  requires CUDA plus BAE; see [sparse-optimization.md](sparse-optimization.md).

## Linear solvers

```text
PINV(atol=None, rtol=None, hermitian=False)
LSTSQ(rcond=None, driver=None)
Cholesky(upper=False)
CG(maxiter=None, tol=1e-5)
PCG(maxiter=None, tol=1e-5)  # optional BAE backend
```

Each solver is called as `solver(A, b)` and returns a step/solution. `PINV`
uses a Moore-Penrose pseudoinverse; `LSTSQ` uses `torch.linalg.lstsq` and is
usually faster and more stable than `PINV`; `Cholesky` requires a real
symmetric or complex Hermitian positive-definite matrix. `CG` expects a
symmetric positive-definite matrix and accepts dense or compatible COO, CSR,
BSR, or related sparse layouts. `PCG` is BAE-provided and is the intended
sparse LM solver.

For `LSTSQ`, CPU drivers include `gels`, `gelsy`, `gelsd`, and `gelss`; CUDA
supports `gels` under the PyTorch contract and assumes full rank. Do not select
Cholesky or CG for an indefinite or singular normal equation without first
repairing the model, weighting, damping, or conditioning.

## Damping strategies

```text
Constant(damping=1e-6)
Adaptive(damping=1e-6, high=0.5, low=1e-3, up=2., down=.5,
         min=1e-6, max=1e16)
TrustRegion(radius=1e6, high=.5, low=1e-3, up=2., down=.5,
            factor=.5, min=1e-6, max=1e16)
```

`Constant` leaves the damping unchanged. `Adaptive` increases it after a
poor step and decreases it after a very successful step, bounded by `min` and
`max`. `TrustRegion` stores an inverse-radius damping and adjusts the radius
and shrink factor from the step quality. Strategy values are per-optimizer
parameter-group state; inspect `optimizer.param_groups[0]` when diagnosing a
stalled run.

## Kernels and correctors

Kernels map the nonnegative squared residual block norm to a robust cost:

```text
Huber(delta=1.0)
PseudoHuber(delta=1.0)
Cauchy(delta=1.0)
SoftLOne(delta=1.0)
Arctan(delta=1.0)
Tolerant(a=1.0, b=-1.0)
Scale(delta=1.0)
```

`Huber(delta=1.0)` is the standard sharp robust choice; `PseudoHuber` is
smooth; `Cauchy` suppresses large outliers strongly. All kernel inputs must be
nonnegative. `FastTriggs(kernel)` applies the stable square-root first-order
correction to residual and Jacobian. `Triggs(kernel)` includes second-order
kernel information and can be unstable when the kernel Hessian is negative;
prefer `FastTriggs` for the normal case.

## Scheduling and Jacobians

```text
StopOnPlateau(optimizer, steps, patience=5, decreasing=1e-3,
              verbose=False)
modjac(model, input=None, create_graph=False, strict=False,
       vectorize=False, strategy='reverse-mode', flatten=False)
psjac(func)  # alias of parallel_for_sparse_jacobian(func)
```

A scheduler loop is:

```python
while scheduler.continual():
    loss = optimizer.step(input, target)
    scheduler.step(loss)
```

Call `scheduler.optimize(input, target=None, weight=None)` for the built-in
loop. Use `continual()` with parentheses; the deprecated boolean attribute is
intentionally rejected. `steps` is the maximum number of optimizer steps,
while `patience` counts steps whose reduction is less than `decreasing`.

`modjac` differentiates module outputs with respect to module parameters. Its
return is nested according to output and parameter structure unless
`flatten=True`; `flatten=True` concatenates outputs into rows and parameters
into columns. `strategy='forward-mode'` requires `vectorize=True`. `strict=True`
raises for an input-independent output; `strict=False` returns the mathematically
correct zero Jacobian in that case. `psjac` only adds sparse-tracing metadata
and preserves normal function behavior when called normally.

## Residuals, targets, and weights

For output `f(theta, input)` and target `y`, PyPose minimizes residual
`R = f - y`; with no target it minimizes `f`. A tuple/list of outputs requires
a matching tuple/list of targets (or `None` targets). Inputs may be one tensor,
a tuple/list, or a dictionary (the latter is expanded as keyword arguments).
The final output dimension is the residual block dimension. Preserve it even
for a scalar block: use `(..., 1)` rather than `(...,)` when sample structure
matters.

A dense weight is a square positive-definite matrix or a list of such matrices
matching residual outputs. It must broadcast with the residual's batch/block
layout. Sparse LM currently requires `weight=None` both at construction and at
`step`.
