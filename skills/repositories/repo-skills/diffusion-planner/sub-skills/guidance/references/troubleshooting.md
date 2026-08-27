# Guidance troubleshooting

Use the first failing contract, not the last stack-frame symptom. Capture
`x.shape`, `x.device`, `x.dtype`, `t.shape`, `t.min()/t.max()`, valid-neighbor
count, normalizer statistics, energy finiteness, `energy.requires_grad`, and
the gradient norm on a single deterministic batch before launching a full
simulation.

## Import and environment failures

### `GuidanceWrapper` or `collision` will not import

The collision module imports nuPlan vehicle parameters at module import and the
wrapper imports the collision function. Verify with the selected interpreter:

```bash
/path/to/your/python -c 'import torch; print(torch.__version__, torch.version.cuda); from diffusion_planner.model.guidance.guidance_wrapper import GuidanceWrapper; from diffusion_planner.model.guidance.collision import collision_guidance_fn; print(GuidanceWrapper, collision_guidance_fn)'
```

The verified inspection environment uses `torch 2.0.0+cu118` and nuplan-devkit
`1.2.2`; a different environment must be checked rather than inferred to be
compatible. If nuPlan is missing, fix the environment or run geometry-only
logic in an isolated test that does not claim live-module verification.

### CUDA is unavailable

The guided YAML requests `device: cuda`, and the planner asserts CUDA
availability. Use CPU only for the deterministic helper and unit-level
geometry checks. Do not silently change a guided simulation to CPU and compare
its result to a CUDA run; record the device and checkpoint/runtime versions.

### Simulation starts with a permission/path error

The supplied guidance launcher contains placeholder roots, `sudo`, and a
machine-specific interpreter command. Those are not portable contracts. Replace them with explicit user-controlled environment variables and
an interpreter that can read the project/checkpoint and write the experiment
root. Avoid `sudo`, since it can change Python packages, CUDA visibility, and
file ownership.

## Signature and shape failures

### `unexpected keyword argument 'inputs'` or missing `inputs`

The tutorial shows `my_guidance_fn(x, t, cond, inputs)`, while the live wrapper
calls registered functions with `guidance_fn(x, t, cond, **kwargs)`. Name the
parameter `inputs`, or accept `*args, **kwargs`. Do not assume `cond` contains
observations; it is commonly `None`.

### Rank or feature mismatch

At the sampler boundary, state is `[B, P, (T+1)*4]`. `GuidanceWrapper` reshapes
it to `[B, P, T+1, 4]`, with feature order `[x, y, cos_heading, sin_heading]`
and current state at time index `0`. The collision function's source comment
is misleading; use the live wrapper/decoder layout.

Check these invariants:

```text
x.ndim == 4
x.shape[-1] == 4
P == 1 + inputs-dependent predicted neighbor count
inputs["neighbor_current_mask"].shape == [B, P-1]
inputs["neighbor_agents_past"].shape[:2] == [B, P-1]
```

The built-in collision function reads `neighbor_agents_past[..., -1, 7]` as
width and `[..., -1, 6]` as length. A feature-order mismatch can produce
plausible but unsafe rectangles, not just a clean exception.

### Batch time error: ambiguous boolean value

The source collision gate is `mask_diffusion_time = (t < 0.1 and t >
0.005)`. Python `and` cannot combine multiple batch booleans. With `B > 1`,
this can fail before geometry runs. A project-owned custom implementation
should use `torch.logical_and(t < 0.1, t > 0.005)` and reshape/broadcast the
per-sample mask intentionally. Do not hide this by forcing all production
batches to one sample without recording the limitation.

## Autograd and reward failures

### `element 0 of tensors does not require grad`

The DPM adapter differentiates `energy.sum()` with respect to the sampler
input. Find the first detached operation:

- a `with torch.no_grad()` around the custom reward;
- `.detach()` or `.item()` applied to the only path from `x`;
- reconstruction with `torch.tensor(...)` or NumPy;
- a boolean/indexing branch that selects only constants;
- a valid-pair mask that removes every differentiable element.

Log `energy.requires_grad`, `energy.grad_fn`, and `x.requires_grad` inside a
local test. For a legitimate no-pair case, return a finite graph-connected
zero such as `x[..., 0].sum(dim=(-1, -2)) * 0.0` rather than a Python `0`.

### Reward is finite but gradient is zero

A finite reward is not evidence of useful guidance. Inspect `grad.abs().sum()`
for the ego future positions. The built-in function deliberately detaches
neighbor trajectories and heading components. It also gates position
sensitivity by diffusion time. Check that the test time is inside the intended
`0.005 < t < 0.1` range and that the colliding pair is not masked. Validate the
sign with one separated and one overlapping synthetic rectangle.

### Guidance unexpectedly changes the current state

`GuidanceWrapper` zeros the model correction at `x[:, :, 0]`, and the decoder's
initial-state corrector also restores current states during sampling. A custom
function should normally calculate energy over future slots (`1:`). If it must
use the current state as a reference, do not optimize that slot in place.

## NaNs and non-finite energies

### NaN during heading normalization

`cos/sin` are normalized in the collision path. A zero vector yields a zero
denominator. Check:

```python
heading_norm = torch.linalg.vector_norm(x[..., 2:], dim=-1)
assert torch.isfinite(heading_norm).all()
assert (heading_norm > 1e-6).all()
```

For new guidance code, clamp with an epsilon and decide how invalid headings
should be reported. Do not silently replace a model output with a random
heading.

### NaN from normalizers or dimensions

Check inverse-normalizer `mean`/`std` on the same device and dtype as the
state. A zero/non-finite std, a malformed `args.json`, or a CPU tensor mixed
with CUDA geometry can fail only at the first guided evaluation. Confirm
`neighbor_agents_past` dimensions are finite and positive before creating
rectangles.

### NaN or invalid reduction with no collision pairs

`~neighbor_current_mask` selects valid pairs. If all neighbors are masked, the
source creates empty distance/clip reductions. Handle this case before
calling geometry in a project-owned extension and return a graph-connected
zero energy. Log the valid pair count so a zero collision term is not confused
with a successful avoidance result.

### Wrapper assertion fails

The wrapper asserts `not torch.isnan(energy).any()`, but it does not diagnose
which component produced the NaN. Temporarily evaluate each registered energy
separately, then inspect heading norm, dimensions, distance, clip values, and
normalizer outputs. Keep diagnostic logging out of the performance path after
repair.

## Device and mutation failures

### Expected all tensors on one device

`center_rect_to_points` creates its fixed corner-sign tensor on the dimensions'
device, and the collision code creates ego-size/mask constants on the
prediction device. Ensure custom constants use `x.new_tensor(...)` or
`torch.tensor(..., device=x.device, dtype=x.dtype)`. Do not call `.cpu()` for
geometry inside the sampler.

### Later sampler call sees physical rather than normalized observations

`GuidanceWrapper` replaces its local `kwargs["inputs"]` with the inverse-
normalized dictionary. A custom function must not mutate that dictionary or
its tensors in place. Clone before editing and ensure any reused model input
remains in its expected normalized representation outside the wrapper.

### Model correction has an unexpected shape

The wrapper calls the model with flattened `[B, P, (T+1)*4]` state and
`model_condition`. The built-in DiT returns the same flattened shape. An
identity test model is valid only for the wrapper smoke; a real model must
accept `cross_c`, `route_lanes`, and `neighbor_current_mask` with compatible
batch and agent counts.

## Sampling and behavior failures

### Guidance is never called

Verify that the active Hydra config is `diffusion_planner_guidance`, not the
ordinary planner config where `guidance_fn: null`, and that the target resolves
to `GuidanceWrapper`. Confirm the decoder chose `guidance_type="classifier"`
and that the selected checkpoint's `args_file` builds the same model shape.

### Guidance is too weak or reverses behavior

The sampler uses scale `0.5` and the wrapper sums all registered energies. A
new energy may have a very different magnitude from collision guidance. Log
energy and gradient norms for the same fixed tensor with guidance disabled and
enabled, check the sign by finite-difference movement, and adjust only one
term/scale at a time. Do not infer success from a lower raw energy alone.

### Full simulation fails before useful evidence

Return to the local helper and a single model/sampler batch. Full guided nuPlan
simulation also depends on scenario filters, maps, checkpoint files, Ray
workers, and permissions. Route ordinary launch failures to
[closed-loop-planning](../../closed-loop-planning/SKILL.md) after preserving the
first guidance-specific log and tensor diagnostics.
