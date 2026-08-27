# Sparse LM with BAE and CUDA

PyPose's `LM(..., sparse=True)` uses an optional BAE backend to trace sparse
Jacobians, construct sparse normal equations, and solve them with BAE's
`PCG`. It is intended for large factor graphs such as bundle adjustment and
pose-graph optimization, not as a CPU version of dense LM.

## Backend contract

The verified preparation used:

- PyPose `0.9.5`.
- PyTorch `2.13.0+cu130` with CUDA available.
- `bae==0.2.1`, built with `USE_CUDSS=0` for the selected PCG path.
- `warp-lang==1.8.1`, whose matrix type API matches the BAE 0.2.1 wrappers.
- An NVIDIA CUDA device with enough free memory.

Treat BAE, Warp, PyTorch, and CUDA compatibility as a set, not independent versions.
When building BAE from its public source release, install the verified Warp
version and use a CUDA-enabled build environment; a generic latest `warp-lang`
upgrade can remove APIs expected by BAE 0.2.1. A representative command is:

```bash
python -m pip install --force-reinstall --no-deps warp-lang==1.8.1
python -m pip install --no-build-isolation "git+https://github.com/pypose/bae.git@0.2.1"
```

Set the public `CUDA_HOME` environment variable when the CUDA toolkit is not
found automatically. If compilation needs CUDA headers/libraries from the
PyTorch wheel, expose those directories through the compiler's normal include
and library search variables; do not treat a successful BAE import as proof
until the tiny CUDA smoke passes. A
successful Python import is not enough: resolve `pypose.optim.solver.PCG`,
construct it, allocate a CUDA tensor, and run the tiny bundled smoke before a
large graph. BAE may initialize Warp and print sparse beta/invariant warnings;
those are not automatically failures. A missing `bae`, unresolved `PCG`, no
CUDA device, or incompatible CUDA runtime is a readiness failure.

Run the diagnostic from any directory:

From the `pypose` skill directory, run:

```bash
python sub-skills/optimization/scripts/sparse_lm_smoke.py --check-only
```

The helper can also be invoked by absolute path from any working directory.

Without `--check-only`, missing prerequisites produce a clear successful skip
so a dense-only machine can still run the general skill checks. The explicit
readiness check returns nonzero for an unavailable backend.

## Sparse model construction

Mark optimized parameters with `sjac=True`:

```python
class PoseGraph(nn.Module):
    def __init__(self, nodes):
        super().__init__()
        self.nodes = pp.Parameter(nodes, sjac=True)

    @psjac
    def edge_error(node1, node2, relative):
        return (relative.Inv() @ node1.Inv() @ node2).Log().tensor()

    def forward(self, edges, relative):
        nodes = self.nodes
        return self.edge_error(nodes[edges[:, 0]], nodes[edges[:, 1]], relative)
```

`psjac` is the alias of `parallel_for_sparse_jacobian`. It only marks a
function for sparse tracing and does not change ordinary function behavior.
The decorated function must be batch-row local: output row `i` may depend on
matching input row `i`, but not on a reduction or a different row. Valid
examples are independent BA reprojection factors and PGO edges. Invalid
examples include a batch mean, a global normalization, sorting across rows,
or any output depending on all samples.

Then use a sparse solver and explicit strategy:

```python
optimizer = pp.optim.LM(
    graph,
    solver=pp.optim.solver.PCG(tol=1e-4, maxiter=250),
    strategy=pp.optim.strategy.TrustRegion(up=2.0, down=0.5**4),
    reject=30,
    sparse=True,
)
```

Sparse LM's current restrictions are strict:

- only one residual tensor is supported. A tuple/list causes a warning and
  only the first residual is used;
- `weight` must be `None`, both when constructing `LM` and when calling `step`;
- the backend requires CUDA; there is no CPU substitute;
- parameters intended for sparse tracing need `sjac=True`;
- `PCG` requires a symmetric positive-definite system and enough iterations;
- factor functions decorated with `psjac` must preserve independent batch rows.

The full BA and PGO sources also use index tensors and anchored/fixed states.
Keep index tensors integer and on the same CUDA device as the model. An anchor
such as a fixed root pose must not be registered as an optimizable parameter.

## Tiny smoke before a real graph

Use the bundled `sparse_lm_smoke.py` first. It creates a tiny CUDA identity
model with `sjac=True`, checks the `psjac` alias by executing a row-local
function, uses `PCG` and `Constant`, and asserts a loss decrease. It does not
fetch BAL/G2O data, plot, or write dataset artifacts.

For a real graph, start with a tiny subset and verify:

1. the initial residual is finite and has shape `(number_of_factors, block_dim)`;
2. each factor only indexes the parameters it should touch;
3. the anchored/frozen parameters are not updated;
4. `PCG` reduces the linear residual within `maxiter`;
5. LM loss decreases and the update stays finite;
6. only then scale factor count, parameter count, and iteration budget.

## CUDA and OOM recovery

A CUDA OOM is distinct from missing BAE. Capture the exception text and report
whether allocation failed during backend import, sparse Jacobian assembly,
normal-equation construction, or PCG. Recovery order:

1. clear stale CUDA allocations and run one process on an explicitly selected
   free GPU;
2. reduce the factor/parameter fixture and `maxiter`, and run the tiny smoke;
3. avoid retaining loss/Jacobian graphs (`torch.no_grad()` is already used by
   `LM.step`); do not turn on `create_graph` for sparse diagnostics;
4. use smaller batches or graph partitions only if that preserves factor
   locality and the intended objective;
5. if the graph is genuinely small/dense, switch to dense LM with `Cholesky`
   or `LSTSQ` rather than forcing sparse mode.

Do not claim sparse verification from a CPU `CG` run. A CPU dense test can
validate the residual math, but BAE/CUDA sparse semantics require the CUDA
smoke and selected native sparse tests.

## Numerical and shape failures

- **Missing BAE/PCG**: run `--check-only`; install a compatible BAE build and
  verify its CUDA/PyTorch linkage. Do not catch this as a model bug.
- **CUDA unavailable**: select a free compatible device or route to dense mode;
  do not silently set `sparse=False` while claiming sparse execution.
- **Unsupported weight**: remove `weight` in sparse mode or use dense LM for
  weighted residuals. PGO's native example explicitly sets its information
  weight to `None` for this reason.
- **Multiple residuals**: combine them into one carefully shaped residual only
  if that preserves the objective, or route to dense mode; sparse LM otherwise
  uses only the first output.
- **`psjac` tracing error**: remove reductions/global cross-row operations,
  verify each argument has the intended leading batch dimension, and mark
  sparse parameters with `sjac=True`.
- **Index/device error**: use CUDA `torch.long` index tensors and move inputs,
  model, targets, and relative measurements to the same device/dtype.
- **NaN/Inf**: check camera depth, logarithm/group domains, residual division,
  target alignment, and initial state before tracing. A NaN Jacobian is not a
  solver tolerance issue.
- **PCG stagnation or non-SPD**: inspect damping, diagonal clamp, finite
  Jacobian blocks, anchoring, and graph connectivity. Increase `maxiter` or
  adjust `tol` only after the matrix is known SPD.
- **Loss rejection**: use `Constant` for a controlled smoke, then tune
  `TrustRegion`/`Adaptive`; inspect `reject_count` and parameter rollback.

## Evidence boundary

`tests/optim/test_sparse_lm.py` verifies `psjac` export, a tiny sparse identity
convergence case, and an anchored chain PGO case. `examples/module/ba`,
`examples/module/pgo`, and `examples/module/reprojpgo` establish factor and
scheduler patterns but include dataset, plotting, or runtime assumptions.
`pypose/autograd/function.py`, `pypose/optim/optimizer.py`, and
`pypose/optim/solver.py` define the implementation restrictions. The runtime
skill intentionally does not import or read those source files.
