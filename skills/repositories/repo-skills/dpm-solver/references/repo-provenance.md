# Repo Provenance

## Source Snapshot

- Repository: `LuChengTHU/dpm-solver`
- Public remote URL: `https://github.com/LuChengTHU/dpm-solver.git`
- Source commit: `52bc3fbcd5de56d60917b826b15d2b69460fc2fa`
- Branch at distillation time: `main`
- Exact tag: none found
- Package/distribution version: none declared; repository is a source-code distribution with single-file solver modules
- Working tree state: dirty only because the generated `skills/` directory and production log were untracked

## Evidence Paths

The skill was distilled from these repository-relative sources:

- `README.md`
- `LICENSE`
- `dpm_solver_pytorch.py`
- `dpm_solver_jax.py`
- `examples/ddpm_and_guided-diffusion/README.md`
- `examples/ddpm_and_guided-diffusion/main.py`
- `examples/ddpm_and_guided-diffusion/sample.sh`
- `examples/ddpm_and_guided-diffusion/configs/*.yml`
- `examples/ddpm_and_guided-diffusion/runners/diffusion.py`
- `examples/score_sde_pytorch/README.md`
- `examples/score_sde_pytorch/requirements.txt`
- `examples/score_sde_pytorch/main.py`
- `examples/score_sde_pytorch/sampling.py`
- `examples/score_sde_pytorch/configs/default_*_configs.py`
- `examples/score_sde_jax/README.md`
- `examples/score_sde_jax/requirements.txt`
- `examples/score_sde_jax/main.py`
- `examples/score_sde_jax/sampling.py`
- `examples/score_sde_jax/configs/default_*_configs.py`
- `examples/stable-diffusion/README.md`
- `examples/stable-diffusion/environment.yaml`
- `examples/stable-diffusion/setup.py`
- `examples/stable-diffusion/scripts/txt2img.py`
- `examples/stable-diffusion/scripts/diffedit_inpaint.ipynb`
- `examples/stable-diffusion/ldm/models/diffusion/dpm_solver/dpm_solver.py`
- `examples/stable-diffusion/ldm/models/diffusion/dpm_solver/sampler.py`

## Live Inspection Summary

A private inspection environment verified these public facts without adding any
machine-specific path to runtime skill instructions:

- `dpm_solver_pytorch.py` imports with PyTorch and exposes `NoiseScheduleVP`,
  `model_wrapper`, `DPM_Solver`, `interpolate_fn`, and `expand_dims`.
- `dpm_solver_jax.py` imports with JAX and exposes `NoiseScheduleVP`,
  `model_wrapper`, `DPM_Solver`, `interpolate_fn`, `expand_dims`, and
  `to_sparse_list`.
- Tiny CPU smoke sampling with a zero-noise model passed for both the PyTorch
  and JAX root solver modules.
- The inspected PyTorch backend reported CUDA visibility on the host, but the
  generated skill only requires CPU smoke checks unless the user explicitly
  requests full model generation.
- The inspected JAX backend was CPU-only. JAX accelerator use is therefore
  documented as an optional, unverified runtime capability.

## Refresh Cues

Refresh this skill when any of the following change in a newer checkout:

- The root solver files change public signatures or add/remove algorithms,
  schedules, model types, guidance modes, or denoising/inversion support.
- The Stable Diffusion adapter changes its expected latent diffusion model
  interface or command-line flags.
- Example requirements update substantially, especially JAX/Flax/TensorFlow,
  PyTorch, CUDA toolkit, or Stable Diffusion dependencies.
- The project adds normal packaging metadata, CLI entry points, tests, or a
  maintained distribution version.
