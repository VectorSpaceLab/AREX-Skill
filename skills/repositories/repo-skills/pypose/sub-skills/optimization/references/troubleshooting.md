# Optimization troubleshooting

Use the smallest reproducible model and record PyPose, PyTorch, device, dtype,
solver, strategy, initial loss, final loss, and exception text. Do not conflate
backend readiness, model shape, and numerical conditioning failures.

## Imports and versions

```python
import torch, pypose as pp
print(pp.__version__)
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available())
```

Dense optimization needs the normal PyPose/PyTorch installation. Sparse LM
additionally needs CUDA and a compatible BAE install; `pypose.optim.solver.PCG`
may be a lazy optional-backend symbol. Run
`scripts/sparse_lm_smoke.py --check-only` for an explicit sparse readiness
answer. BAE's Warp initialization warnings are informational unless followed
by an import or execution exception.

## Model, input, and target

**Symptoms:** `TypeError`, missing argument, a target subtraction shape error,
or an unexpected tuple/list.

- A tensor input is passed as one positional argument.
- A tuple/list input is expanded positionally.
- A dict input is expanded as keyword arguments.
- `input=()` is required for a no-input model.
- A tuple/list model output needs matching target structure, or `target=None`.
- Targets must be broadcast-compatible with their corresponding outputs.

Add a preflight call outside the optimizer:

```python
with torch.no_grad():
    output = model(input)  # mirror PyPose's input structure
print(type(output), getattr(output, "shape", None))
```

Keep each residual's final dimension as its block dimension. Scalar samples
should generally be `(..., 1)`. A flattened global vector turns all samples
into one residual block and changes robust-kernel behavior.

## Shape and parameter failures

**Symptom:** `Jacobian and parameter sequences must have the same length`,
`no trainable parameters`, update split errors, or padded LieTensor columns.

- Check that every optimized variable is a registered `nn.Parameter`/
  `pp.Parameter` and that at least one has `requires_grad=True`.
- Do not include frozen parameters in custom Jacobian concatenation.
- For LieTensor parameters, use manifold coordinates; PyPose's dense flattening
  handles the manifold/embedding distinction.
- Verify all batched factors have matching leading dimensions and residual block
  dimensions.
- Call `modjac(model, input, flatten=False)` and print nested shapes before
  switching to `flatten=True`.

**Symptom:** `modjac` returns disconnected zeros or raises in strict mode.

A parameter may not influence the output, or an input path is detached. Use
`strict=False` to inspect mathematically zero derivatives, but repair an
accidental `.detach()`, wrong parameter reference, or unused module member.
`forward-mode` requires `vectorize=True` and can have different performance
characteristics from the default reverse mode.

## Numerical failures

**Symptom:** NaN Jacobian, NaN loss, or Inf parameter.

1. Evaluate model output and residual before the optimizer; use
   `torch.isfinite` on input, target, output, and residual.
2. Check division by depth/scale, Lie group logarithm domains, invalid rotations,
   and target units.
3. Use a smaller perturbation and a deterministic seed.
4. Preserve residual block dimensions and avoid accidental global reductions.
5. Disable robustification temporarily to isolate the base residual.

**Symptom:** Cholesky failure or CG/PCG breakdown.

Cholesky, CG, and PCG require SPD systems. Check Jacobian rank, positive-
definite weights, graph anchoring/connectivity, and finite damping. Use
`LSTSQ`/`PINV` for a dense diagnostic; use larger positive LM damping for a
poorly conditioned initial state. Do not treat a solver switch as proof that
the original system was valid.

**Symptom:** LM loss rises or repeatedly rejects.

Inspect `optimizer.reject_count`, `optimizer.last`, `optimizer.loss`, and
`optimizer.param_groups[0]`. Check residual sign (`output - target`), target
alignment, initialization, weight scale, and robust corrector. Start with
`Constant(damping=...)`; then tune `Adaptive` or `TrustRegion`. Keep rejection
enabled while diagnosing and never accept a failed step just to make progress.

**Symptom:** robust result is unstable or outliers dominate.

Ensure the kernel receives nonnegative squared block norms and `delta` is
positive. Keep the residual block dimension visible. Use `FastTriggs(kernel)`
explicitly; full `Triggs` can be unstable when the kernel's second derivative
is negative. `FastTriggs` needs gradient-enabled kernel differentiation and is
not compatible with `torch.inference_mode()`; normal `torch.no_grad()` use is
supported.

## Weights and multiple residuals

**Symptom:** matrix shape errors or an unexpected objective scale.

Check that a dense weight is square, positive definite, same dtype/device, and
broadcastable to the residual block layout. For multiple outputs, provide one
weight per output in a list. A per-step `weight` overrides the constructor
weight. Sparse LM does not support weights; route weighted problems to dense
LM/GN or reformulate deliberately as one unweighted residual.

## Scheduler failures

Call `scheduler.step(loss)` after `optimizer.step`, because the scheduler
expects `optimizer.loss` to exist. Use `scheduler.continual()` with
parentheses. It stops at the maximum `steps`, after the configured plateau
patience, or after an LM rejection. Set `verbose=True` while diagnosing loss
and relative-decrease behavior. `decreasing` is an absolute reduction
threshold in the implementation despite the scheduler's historical wording.

## Sparse-specific failures

**Missing backend / CPU:** CUDA is required for BAE sparse LM; there is no CPU
substitute. Run the explicit check. If the task can be solved densely, use
`LM(..., sparse=False)` and a dense solver, but report that sparse execution was
not verified.

**`weight` assertion:** sparse `LM.step` requires `weight is None`, including a
weight passed through a scheduler. The source PGO example sets information
weights to `None` for this reason.

**Multiple residual warning:** sparse mode uses only the first residual tensor.
Do not assume the second output contributes to the objective.

**`psjac` errors:** every decorated function must be row-local and have
matching leading batch dimensions. Remove batch means/reductions and global
state. `psjac` is tracing metadata, not a vmap permission for cross-row code.

**CUDA OOM:** distinguish missing backend from allocation failure by checking
that imports and the tiny smoke pass first. Select a free device, clear stale
allocations, reduce factors and `maxiter`, avoid retained graphs, and scale up
incrementally. The full BA dataset is not a readiness test.

**Sparse numerical failure:** verify an anchored graph, finite factor outputs,
correct long CUDA indices, positive damping, SPD normal equations, and a
reasonable `PCG(tol, maxiter)`. A disconnected graph or unconstrained global
transform can make the system singular even when every factor is finite.

## Evidence and escalation

Use `tests/optim/test_optimizer.py`, `test_solver.py`, `test_scheduler.py`,
`test_jacobian.py`, and `test_sparse_lm.py` as focused behavior references.
The bundled dense and sparse smokes are intentionally smaller and deterministic.
If a native test requires a dataset, plotting, a busy GPU, or network access,
record it as unrun rather than weakening a runtime claim.
