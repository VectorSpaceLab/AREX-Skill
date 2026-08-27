---
name: dpm-solver
description: "Use DPM-Solver and DPM-Solver++ single-file samplers for diffusion
  ODE sampling, PyTorch/JAX integration, ScoreSDE/DDPM examples, and Stable
  Diffusion acceleration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DPM-Solver

Use this skill when a task asks how to integrate, configure, debug, or adapt the
DPM-Solver / DPM-Solver++ samplers from Cheng Lu et al.'s `dpm-solver` project.
The repository is a source-code distribution rather than a normal PyPI package:
the durable user-facing artifacts are the single-file PyTorch and JAX solver
modules plus example integrations for DDPM/guided-diffusion, ScoreSDE, and
Stable Diffusion.

## Start Here

1. Identify whether the user wants **direct solver API integration**, a
   **PyTorch example workflow**, a **JAX ScoreSDE workflow**, or **Stable
   Diffusion sampling acceleration**.
2. If they need code, prefer the bundled implementation copies in
   [`scripts/dpm_solver_pytorch.py`](scripts/dpm_solver_pytorch.py) and
   [`scripts/dpm_solver_jax.py`](scripts/dpm_solver_jax.py) instead of relying
   on an original checkout.
3. Use [`references/solver-choice-guide.md`](references/solver-choice-guide.md)
   before recommending `algorithm_type`, `order`, `method`, `steps`,
   `skip_type`, thresholding, or denoising settings.
4. Run [`scripts/check_dpm_solver_environment.py`](scripts/check_dpm_solver_environment.py)
   when imports, PyTorch/JAX availability, CUDA visibility, or a tiny numerical
   smoke test are uncertain.
5. Treat full image generation, pretrained checkpoints, FID evaluation, Stable
   Diffusion weights, dataset downloads, and multi-GPU training as opt-in:
   they are network-, credential-, GPU-, memory-, and time-sensitive.
6. Read [`references/repo-provenance.md`](references/repo-provenance.md) before
   refreshing this skill against a newer source snapshot.

## Route By Task

| User task | Read |
| --- | --- |
| Copy DPM-Solver into custom code, wrap a diffusion model, choose noise schedules, inspect API signatures, run tiny smoke tests | [`sub-skills/core-api/SKILL.md`](sub-skills/core-api/SKILL.md) |
| Adapt DDPM, guided-diffusion, ScoreSDE PyTorch sampling commands, configs, checkpoints, or DPM-Solver flags | [`sub-skills/torch-examples/SKILL.md`](sub-skills/torch-examples/SKILL.md) |
| Use the JAX ScoreSDE integration, understand JAX-specific solver differences, `pmap`/device behavior, or JAX caveats | [`sub-skills/jax-examples/SKILL.md`](sub-skills/jax-examples/SKILL.md) |
| Add DPM-Solver to latent Stable Diffusion, plan `txt2img --dpm_solver`, use the sampler adapter, or troubleshoot model-weight/runtime constraints | [`sub-skills/stable-diffusion/SKILL.md`](sub-skills/stable-diffusion/SKILL.md) |

## Key Operating Facts

- Direct use imports `NoiseScheduleVP`, `model_wrapper`, and `DPM_Solver` from
  the PyTorch or JAX module.
- `NoiseScheduleVP(schedule="discrete", betas=...)` or
  `NoiseScheduleVP(schedule="discrete", alphas_cumprod=...)` converts a
  discrete diffusion schedule to continuous time labels in `(0, 1]`.
- `NoiseScheduleVP(schedule="linear", continuous_beta_0=0.1,
  continuous_beta_1=20.)` covers continuous VP SDEs used by ScoreSDE-style
  examples. The bundled JAX module also exposes `schedule="cosine"`; the root
  PyTorch file does not, while the Stable Diffusion nested copy does.
- PyTorch `DPM_Solver(..., algorithm_type="dpmsolver++")` selects data
  prediction internally and is the common default for guided sampling. The JAX
  API uses `predict_x0=True` for the DPM-Solver++-style path.
- `method="multistep"`, `order=2`, `skip_type="time_uniform"`, and roughly
  20-25 steps are the Stable Diffusion / large-guidance default family.
- `method="singlestep"` or `method="multistep"` with order 3 is the common
  exploration path for unconditional or lightly guided sampling.
- `correcting_x0_fn="dynamic_thresholding"` is for pixel-space guided sampling;
  do not use dynamic thresholding for latent-space Stable Diffusion.

## Installation And Import Baseline

There is no root package metadata. For custom code, copy one bundled solver file
into the target project or keep it on `PYTHONPATH` and install only the backend
needed by that file:

```bash
python -m pip install torch        # for dpm_solver_pytorch.py
python -m pip install jax jaxlib   # for dpm_solver_jax.py CPU use
```

Minimal PyTorch import and smoke check:

```bash
python scripts/check_dpm_solver_environment.py --backend torch --smoke
```

Minimal JAX import and smoke check:

```bash
python scripts/check_dpm_solver_environment.py --backend jax --smoke
```

## Root References And Tools

- [`references/solver-choice-guide.md`](references/solver-choice-guide.md):
  practical solver setting choices for unconditional, guided, low-resolution,
  high-resolution, and latent-space workflows.
- [`references/api-summary.md`](references/api-summary.md): compact signatures,
  naming differences, return behavior, and caveats for the PyTorch and JAX
  solver files.
- [`references/troubleshooting.md`](references/troubleshooting.md): install,
  import, backend, numerical, guidance, checkpoint, and optional dependency
  troubleshooting shared across sub-skills.
- [`scripts/check_dpm_solver_environment.py`](scripts/check_dpm_solver_environment.py):
  self-contained import/backend/smoke checker for the bundled solver copies.
- [`scripts/dpm_solver_pytorch.py`](scripts/dpm_solver_pytorch.py) and
  [`scripts/dpm_solver_jax.py`](scripts/dpm_solver_jax.py): source-derived
  bundled implementations future agents can copy into projects.

## Safety And Scope Boundaries

- Do not start model downloads, dataset downloads, FID computation, Stable
  Diffusion generation, notebook execution, or multi-GPU sampling unless the
  user explicitly approves the cost and runtime.
- Do not assume a CUDA, ROCm, MPS, TPU, or JAX accelerator backend is available;
  run a backend probe and use CPU only for tiny API smoke tests unless real
  generation is requested.
- Do not route Hugging Face `diffusers` scheduler API tasks here when the user
  is using the `diffusers` package directly; prefer a Diffusers-specific skill
  for `DPMSolverMultistepScheduler` pipelines.
- Do not tell future agents to run original repository examples. If a workflow
  is useful, use this skill's distilled references and bundled command builders.
- Keep Stable Diffusion safety, license, checkpoint, and gated-weight
  requirements explicit when constructing commands.

## Verification Expectations

Start with the smallest safe checks: import the backend, construct a linear
noise schedule, run a zero-model sample on a tiny tensor, and validate planned
command arguments without loading checkpoints. Full native example parity is
blocked by external checkpoints/datasets and should be recorded as skipped or
opt-in unless the user provides the assets and hardware.
