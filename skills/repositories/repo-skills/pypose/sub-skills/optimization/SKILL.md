---
name: optimization
description: "Use PyPose's dense or sparse Gauss-Newton and Levenberg-Marquardt
  workflows for nonlinear least squares, including residual contracts,
  Jacobians, linear solvers, damping strategies, robust kernels, stopping, and
  BAE/CUDA sparse LM diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyPose optimization

Use this skill when a task is a nonlinear least-squares problem whose learnable
state is held by a `torch.nn.Module` (including `pp.Parameter` LieTensor
parameters), and the desired operation is a dense `GN`/`LM` step or a structured
sparse `LM` solve. It covers model residuals, targets, weights, Jacobians,
linear solvers, damping, robustification, and stopping. The bundled scripts use
an installed PyPose package and do not read a PyPose checkout.

Do **not** use this skill for primitive LieTensor group/algebra operations
(route those to `lie-tensor`), EKF/UKF/PF/LQR/MPC or other module-specific
control/filter workflows (route to `robotics-modules`), or projections,
splines, point-cloud geometry, and trajectory metrics (route to
`geometry-evaluation`).

## Choose a path

- Choose **dense** for ordinary-size or dense-Jacobian problems, multiple
  residual tensors, non-`None` weights, robust kernels/correctors, CPU, or when
  a dense solver is adequate.
- Choose **sparse LM** only when the Jacobian is genuinely structured and large,
  every sparse constraint below is satisfied, and a CUDA installation of the
  optional BAE backend is available. Sparse mode is a CUDA/BAE capability, not
  a CPU fallback.
- Start with `GN` when a plain least-squares linearization is sufficient and
  there is no need for LM damping/rejection. Start with `LM` for ill-conditioned
  or poorly initialized problems, robust damping, or sparse optimization.

Read the relevant reference before implementation:

- [API reference](references/api-reference.md) for signatures and shape rules.
- [Dense workflows](references/dense-workflows.md) for model construction and
  GN/LM/scheduler recipes.
- [Solver, kernel, and strategy reference](references/solver-kernel-strategy-reference.md)
  for numerical choices.
- [Sparse optimization](references/sparse-optimization.md) for `sjac`, `psjac`,
  BAE, and the sparse restrictions.
- [Troubleshooting](references/troubleshooting.md) for diagnosis and recovery.

Runnable checks (from any working directory, with PyPose installed):

From the `pypose` skill directory, use the bundled helpers:

```bash
python sub-skills/optimization/scripts/dense_lm_smoke.py --help
python sub-skills/optimization/scripts/dense_lm_smoke.py
python sub-skills/optimization/scripts/sparse_lm_smoke.py --help
python sub-skills/optimization/scripts/sparse_lm_smoke.py       # skips clearly if CUDA/BAE is absent
python sub-skills/optimization/scripts/sparse_lm_smoke.py --check-only
```

The same files can be invoked by absolute path from any working directory.

The sparse helper's default missing-backend behavior is an informative,
successful skip. `--check-only` is the explicit readiness gate and returns a
nonzero status when CUDA or BAE is unavailable.

## Core residual contract

1. Put all variables to optimize in `nn.Parameter` or `pp.Parameter` members of
   an `nn.Module`. A `pp.Parameter` can carry `sjac=True` for sparse tracing;
   that flag is only relevant to sparse LM.
2. Make `forward(input)` accept the actual input structure: one tensor, a tuple
   or list, or a dictionary. PyPose calls tuples/lists positionally and
   dictionaries by keyword. Use `input=()` for a no-input model.
3. Return either one tensor/LieTensor or a tuple/list of residual outputs. With
   `target=None`, PyPose minimizes the model output; otherwise each output is
   residualized as `output - target`. Targets must have the corresponding
   structure and be broadcast-compatible.
4. Preserve the final dimension as the residual block dimension. For scalar
   sample residuals use shape `(..., 1)`, not a flattened global vector; this
   preserves per-sample Jacobian and robust-kernel structure. A reprojection
   residual commonly has shape `(..., 2)`.
5. Use a positive-definite square weight with the same residual ownership only
   in dense mode. A weight may be one matrix or a list matching the residual
   tuple; it must be broadcastable according to the residual block dimensions.
   A `weight` passed to `step` overrides the constructor weight.
6. Run finite-value and shape checks before choosing a solver. The Jacobian
   columns must correspond to trainable parameter update coordinates. For
   LieTensor parameters, PyPose's optimizer uses manifold coordinates rather
   than padded embedding coordinates.

Conceptually, the optimizer linearizes `R(theta)`, applies an optional weight
and robust corrector, solves for an update `D`, and adds `D` to the parameters.
`GN` uses a least-squares/pseudoinverse-style linear solve. `LM` forms damped
normal equations, clamps their diagonal to `[min, max]`, adapts damping through
a strategy, and can reject unsuccessful steps.

## Dense recipe

```python
import torch
from torch import nn
import pypose as pp
from pypose.optim import LM                 # or GN
from pypose.optim.solver import Cholesky   # or LSTSQ/PINV/CG as appropriate
from pypose.optim.strategy import Constant
from pypose.optim.scheduler import StopOnPlateau

class Residual(nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = nn.Parameter(torch.tensor(0.2))
        self.bias = nn.Parameter(torch.tensor(-1.0))

    def forward(self, x):
        return self.scale * x + self.bias

model = Residual()
optimizer = LM(model, solver=Cholesky(), strategy=Constant(damping=1e-4))
scheduler = StopOnPlateau(optimizer, steps=25, patience=4,
                           decreasing=1e-8)
while scheduler.continual():
    loss = optimizer.step(x, target=y)
    scheduler.step(loss)
```

Use `optimizer.step(input, target=None, weight=None)` for one iteration and
`scheduler.optimize(input, target=None, weight=None)` for the scheduler-owned
loop. Record the initial loss and stop on a finite, decreasing loss rather than
assuming a fixed iteration count. `GN` has no damping strategy or sparse mode;
its default solver is `PINV`. `LM` defaults to `Cholesky` and
`TrustRegion`, with up to 16 rejected steps. Use `Constant` for a fixed
smoke/known scale, `Adaptive` for quality-based damping changes, or
`TrustRegion` for radius-based control.

For multiple residuals, pass a robust kernel such as `Huber` and a
`corrector` as either one object (reused for every residual) or a list of
length one or the number of residuals.
If a kernel is provided without a corrector, PyPose constructs automatic
`FastTriggs` correction. Prefer an explicit `FastTriggs(kernel)` for a stable
first-order robust solve, especially for kernels with a potentially
indefinite second derivative.

`modjac` is useful for inspection and custom dense workflows. Call it against
the module and the same input structure used by the model; use
`flatten=True` only when a single global Jacobian is really intended. The
optimizer internally obtains unflattened Jacobians and retains residual-block
structure.

## Sparse LM recipe

Sparse mode is a separate path:

```python
from pypose.autograd.function import psjac
from pypose.optim import LM
from pypose.optim.solver import PCG
from pypose.optim.strategy import Constant

class FactorModel(nn.Module):
    def __init__(self, state):
        super().__init__()
        self.state = pp.Parameter(state, sjac=True)

    @psjac
    def factor(values):
        return values                 # one independent block per batch row

    def forward(self, indices):
        return self.factor(self.state[indices])

optimizer = LM(FactorModel(state), solver=PCG(maxiter=250, tol=1e-4),
               strategy=Constant(damping=1e-6), sparse=True)
```

A `psjac` function must be row-local: each output batch row may depend only on
matching input batch rows. Do not decorate batch reductions, global statistics,
or functions that mix rows. Mark sparse-traced parameters with `sjac=True`.
Use `PCG` for the sparse symmetric positive-definite normal equations and keep
factor output blocks small.

Before running sparse LM, check all of the following:

- CUDA is available and the selected tensors/model are on CUDA.
- `bae==0.2.1` (or a separately verified compatible BAE release) is installed;
  `pypose.optim.solver.PCG` resolves to the backend implementation.
- The problem has one residual tensor. If the model returns multiple residuals,
  sparse mode warns and uses only the first one.
- `weight` is `None`; sparse weighting is currently unsupported.
- The residual/Jacobian is structurally sparse and factorwise `psjac` semantics
  are valid.
- The normal equations are suitable for CG/PCG and the requested memory fits
  the GPU.

The full BA, PGO, and reprojection-PGO examples are evidence for this pattern,
not runtime dependencies: they assume datasets, plotting, file output, and
CUDA. Use the bundled sparse identity smoke for a tiny readiness/convergence
check before attempting a real graph.

## Verification and recovery checklist

- Confirm `pypose.__version__`, PyTorch version/device, and finite input/target
  values before a run.
- Log the loss before the first step, every returned loss, reject count (LM),
  damping/radius strategy state, and the final parameter error.
- If the loss rises, let LM reject/retry while damping grows; if repeated
  rejection reaches `reject`, inspect residual signs, target alignment,
  initialization, and solver conditioning rather than disabling rejection.
- For a robust objective, verify the residual's last dimension and non-negative
  squared inputs to the kernel. Use explicit corrector selection when automatic
  correction is unstable.
- For sparse failures, first run `sparse_lm_smoke.py --check-only`, then reduce
  the fixture/problem size and test `PCG` independently. Distinguish missing
  BAE/CUDA from CUDA OOM, unsupported sparse kernels, and an actual numerical
  breakdown.

Evidence basis: the installed PyPose 0.9.5 API and backend probes, `pypose/optim`,
`pypose/autograd`, and `pypose/sparse`; `README.md`; `docs/source/optim.rst` and
`docs/source/autograd.rst`; the BA, PGO, and reprojection-PGO examples; and the
optimizer, solver, scheduler, Jacobian, and sparse-LM tests. These sources are
provenance for the instructions, not files required at runtime.
