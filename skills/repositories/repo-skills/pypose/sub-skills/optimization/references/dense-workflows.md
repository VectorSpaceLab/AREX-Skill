# Dense nonlinear least-squares workflows

Dense mode is the default PyPose optimization path. It works on CPU or CUDA,
handles one or multiple residual outputs, dense weights, robust kernels and
correctors, and ordinary or LieTensor parameters.

## 1. Define a residual model

Keep all variables being optimized as module parameters. The module's
`forward` must expose a residual tensor or a tuple/list of residual tensors.
Inputs can be a tensor, positional tuple/list, or keyword dictionary. Targets
are optional; `target=None` means the output itself is the residual.

```python
class LineResidual(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.slope = torch.nn.Parameter(torch.tensor(0.0))
        self.intercept = torch.nn.Parameter(torch.tensor(0.0))

    def forward(self, x):
        # (..., 1) keeps one scalar residual block per sample.
        return (self.slope * x + self.intercept).unsqueeze(-1)

x = torch.linspace(-1, 1, 32)
y = (2.5 * x - 0.7).unsqueeze(-1)
```

Do not flatten the sample dimension into one scalar residual when using a
robust kernel. The last dimension is the block dimension whose squared norm is
passed to a kernel. For vector residuals, use `(..., D)`; for scalar residuals
where sample structure matters, use `(..., 1)`.

A module can return multiple residuals:

```python
class Coupled(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.x = torch.nn.Parameter(torch.tensor(0.0))
    def forward(self, data, anchor):
        return (self.x * data, self.x - anchor)

# input=(data, anchor), target=None; or give two matching targets.
```

When multiple outputs are returned, kernels, correctors, and weights may be a
single object reused for every output or lists whose length is one or the
number of outputs. Heterogeneous residuals should use explicit lists and
weights with matching block sizes.

## 2. Choose GN or LM

Use GN for a well-initialized, well-conditioned least-squares problem:

```python
optimizer = pp.optim.GN(model, solver=pp.optim.solver.LSTSQ(),
                         vectorize=True)
```

GN defaults to `PINV`; `LSTSQ` is generally preferred for a dense linear
system. `GN.step(input, target=None, weight=None)` computes a Jacobian,
linearizes the residual, solves for the update, and applies it once.

Use LM when a trust region or damping is useful:

```python
optimizer = pp.optim.LM(
    model,
    solver=pp.optim.solver.Cholesky(),
    strategy=pp.optim.strategy.TrustRegion(radius=1e6),
    reject=16,
    min=1e-6,
    max=1e32,
    vectorize=True,
)
```

LM forms damped normal equations and retries a step while the loss fails to
decrease. `reject` bounds retries. `min` and `max` clamp the normal-equation
diagonal, which prevents zero or excessively large diagonal entries from
immediately destabilizing the solver. A high rejection count is a diagnostic,
not a reason to silently accept an uphill update.

## 3. Weight residual blocks

For dense mode, pass a square positive-definite weight whose block shape
matches the residual. For one residual `R` with final dimension `D`, an identity
weight is often enough:

```python
weight = torch.eye(D, dtype=R.dtype, device=R.device)
optimizer = pp.optim.LM(model, weight=weight)
# A per-step weight overrides constructor weight:
loss = optimizer.step(input, target, weight=weight)
```

For multiple outputs use `weight=[weight_for_first, weight_for_second]`. The
source implementation supports broadcastable weight layouts from block-only
to batch-specific matrices. Verify the weight is positive definite and on the
same device/dtype before calling `step`. Do not pass a weight in sparse mode.

## 4. Robust kernels and correctors

A kernel changes the cost as a function of each residual block's squared norm:

```python
from pypose.optim.kernel import Huber
from pypose.optim.corrector import FastTriggs

kernel = Huber(delta=1.0)
optimizer = pp.optim.LM(model, kernel=kernel,
                        corrector=FastTriggs(kernel))
```

If `corrector` is omitted while `kernel` is present, PyPose automatically
constructs `FastTriggs` correction. An explicit corrector documents the
intention and makes a heterogeneous multi-residual configuration easier to
review. `FastTriggs` rescales each residual/Jacobian using the first derivative
of the kernel and is preferred over full `Triggs` for stability. Do not use
negative residual norms or manually apply the kernel to a global flattened
vector.

Use `PseudoHuber` when a smooth transition is desired and `Cauchy` when large
outliers should be strongly downweighted. Every kernel threshold must be
positive; `Huber` and the other kernel calls assert nonnegative inputs.

## 5. Stop deterministically

```python
from pypose.optim.scheduler import StopOnPlateau

scheduler = StopOnPlateau(optimizer, steps=30, patience=5,
                          decreasing=1e-6, verbose=False)
while scheduler.continual():
    loss = optimizer.step(input, target)
    scheduler.step(loss)
```

`steps` is a hard maximum. `patience` stops after the configured number of
steps without a reduction greater than `decreasing`; an LM rejected step also
stops the scheduler. `scheduler.optimize(input, target=None, weight=None)` is
equivalent to the explicit loop. Do not write `while scheduler.continual:`;
the deprecated boolean form raises a runtime error.

## 6. Inspect Jacobians with `modjac`

```python
J = pp.optim.functional.modjac(model, input=x,
                               vectorize=True, flatten=False)
```

With multiple parameters or outputs, `J` is nested. Use `flatten=True` for a
single 2-D matrix when you explicitly need rows of output and columns of
parameter coordinates. `strict=True` turns disconnected outputs into an
error; `strict=False` produces zero derivatives. Reverse mode is the default;
forward mode can help when outputs greatly outnumber inputs but requires
vectorization. `create_graph=True` is needed only when differentiating through
the Jacobian itself and increases memory use.

Before a solve, check:

```python
with torch.no_grad():
    residual = model(x) - y
assert residual.shape[-1] == 1 or residual.shape[-1] == expected_block_dim
assert torch.isfinite(residual).all()
J = pp.optim.functional.modjac(model, x, vectorize=True)
```

A singular or NaN Jacobian indicates a model/input issue, a disconnected
parameter, a bad LieTensor representation, or a conditioning problem. See
[troubleshooting.md](troubleshooting.md).

## 7. LieTensor parameters

Use `pp.Parameter` for manifold state and return a residual in a tangent/vector
representation appropriate to the problem (for example, a `.Log()` tensor).
PyPose's optimizer flattening uses the manifold dimension for updates rather
than the LieTensor embedding dimension. Keep batch dimensions intact and do
not manually pad Jacobian columns. Primitive `Exp`, `Log`, composition, and
coordinate choices belong to `lie-tensor`; this section only describes their
optimizer boundary.

## Evidence workflows

- `examples/module/reprojpgo/reprojpgo.py` demonstrates dense LM with
  `Huber`, `FastTriggs`, `Cholesky`, `TrustRegion`, and `StopOnPlateau` on a
  reprojection residual. Its dataset/visualization loop is reference-only.
- `tests/optim/test_optimizer.py` covers LieGroup parameters, weights,
  multiple residuals, robust kernels, strategies, frozen parameters and
  manifold-sized updates.
- `tests/optim/test_scheduler.py` covers both explicit and `optimize` loops.
- `scripts/dense_lm_smoke.py` is the safe tiny executable equivalent of this
  workflow.
