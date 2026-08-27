---
name: core-api
description: "Use the DPM-Solver PyTorch and JAX single-file APIs directly:
  noise schedules, model wrappers, solver settings, inversion/noising helpers,
  and tiny validation checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core API

Use this sub-skill when a user wants to copy DPM-Solver into custom diffusion
code, wrap their own model, choose solver settings, debug API calls, or run a
small backend smoke test without executing the repository's large examples.

## When To Read

Read this sub-skill for tasks that mention:

- `NoiseScheduleVP`, `model_wrapper`, `DPM_Solver`, `sample`, `inverse`, or
  `add_noise`.
- Discrete beta schedules, `alphas_cumprod`, continuous VP SDE schedules, or
  log-SNR time steps.
- `algorithm_type="dpmsolver"` versus `"dpmsolver++"`, JAX `predict_x0`,
  solver order, `skip_type`, `method`, `denoise_to_zero`, or dynamic
  thresholding.
- A custom PyTorch or JAX diffusion model that should sample in 10-25 function
  evaluations.

## Workflow

1. Choose the backend file:
   - PyTorch: copy [`../../scripts/dpm_solver_pytorch.py`](../../scripts/dpm_solver_pytorch.py).
   - JAX: copy [`../../scripts/dpm_solver_jax.py`](../../scripts/dpm_solver_jax.py).
2. Read [`references/api-reference.md`](references/api-reference.md) for exact
   signatures, backend differences, and minimal integration skeletons.
3. Read [`../../references/solver-choice-guide.md`](../../references/solver-choice-guide.md)
   before recommending order/method/step settings.
4. Use [`references/noise-schedules-and-wrappers.md`](references/noise-schedules-and-wrappers.md)
   when converting a model's training-time labels or parameterization to the
   continuous-time noise prediction interface.
5. Run one bundled smoke script before deeper debugging:
   - [`scripts/minimal_torch_sample.py`](scripts/minimal_torch_sample.py)
   - [`scripts/minimal_jax_sample.py`](scripts/minimal_jax_sample.py)
6. If the user needs DDPM, ScoreSDE, or Stable Diffusion commands, route to the
   corresponding sibling sub-skill instead of expanding this page.

## Recommended Direct PyTorch Skeleton

```python
import torch
from dpm_solver_pytorch import NoiseScheduleVP, model_wrapper, DPM_Solver

# `model(x, t_input, **kwargs)` must return the model's prediction.
noise_schedule = NoiseScheduleVP(schedule="discrete", betas=betas)
model_fn = model_wrapper(
    model,
    noise_schedule,
    model_type="noise",
    guidance_type="uncond",
    model_kwargs=model_kwargs,
)
solver = DPM_Solver(model_fn, noise_schedule, algorithm_type="dpmsolver++")
sample = solver.sample(
    x_T,
    steps=20,
    order=2,
    skip_type="time_uniform",
    method="multistep",
)
```

## Recommended Direct JAX Skeleton

```python
import jax.numpy as jnp
from dpm_solver_jax import NoiseScheduleVP, model_wrapper, DPM_Solver

noise_schedule = NoiseScheduleVP(schedule="linear", continuous_beta_0=0.1, continuous_beta_1=20.0)
model_fn = model_wrapper(model, noise_schedule, model_type="noise", guidance_type="uncond")
solver = DPM_Solver(model_fn, noise_schedule, predict_x0=False)
sample = solver.sample(x_T, steps=20, order=3, skip_type="time_uniform", method="singlestep")
```

## Common Decisions

- Use `schedule="discrete"` with `betas` or `alphas_cumprod` when adapting a
  DDPM-style model trained on integer time labels.
- Use `schedule="linear"` for continuous VP SDE / ScoreSDE-like integration.
- In PyTorch, `algorithm_type="dpmsolver++"` is the DPM-Solver++ path; in JAX,
  use `predict_x0=True` for the comparable data-prediction solver path.
- Use order 2 for large guidance scales and order 3 for unconditional or lightly
  guided sampling.
- Use `return_intermediate=True` only in PyTorch and only for non-adaptive
  methods.
- Use PyTorch `inverse` and `add_noise` for inversion/editing workflows; the
  root JAX file does not expose equivalent public helpers.

## Troubleshooting

Read [`references/troubleshooting.md`](references/troubleshooting.md) for API
misuse, tensor shape, dynamic thresholding, JAX classifier-free guidance, and
schedule conversion failures. Read the root
[`../../references/troubleshooting.md`](../../references/troubleshooting.md)
for install/backend/checkpoint issues shared with examples.

## Boundaries

- Do not run the original repository examples from this sub-skill.
- Do not promise sample quality without a known-good high-step baseline and a
  matching noise schedule.
- Do not recommend JAX `model_type="score"`, classifier-free guidance, or
  `thresholding=True` in the unpatched root JAX file without warning about the
  verified compatibility caveats.
- Do not apply dynamic thresholding to latent-space Stable Diffusion latents.
