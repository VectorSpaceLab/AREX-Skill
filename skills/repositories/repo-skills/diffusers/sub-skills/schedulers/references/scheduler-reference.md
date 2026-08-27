# Scheduler Reference

This reference covers Diffusers scheduler selection, swapping, timestep/sigma configuration, manual stepping, and scheduler config serialization. It is self-contained for scheduler-focused inference and tests and assumes Diffusers and Torch are already installed.

## Core APIs

Common imports:

```python
from diffusers import DDIMScheduler, DDPMScheduler, DPMSolverMultistepScheduler, EulerDiscreteScheduler
from diffusers.schedulers import AysSchedules
```

Factories and serialization:

- `SchedulerMixin.from_pretrained(model_or_dir, subfolder="scheduler", **kwargs)` loads a scheduler config from a pipeline repository or local pipeline directory.
- `ConfigMixin.from_config(config, **kwargs)` builds a scheduler from an existing config and applies explicit overrides.
- `scheduler.save_pretrained(save_directory)` writes only the scheduler config; use pipeline save APIs for full pipeline packaging.
- `scheduler.compatibles` can list compatible scheduler classes, but compatibility does not mean every field has the same semantics.

Representative constructor defaults in the inspected Diffusers version:

- `DDPMScheduler(..., prediction_type="epsilon", timestep_spacing="leading", rescale_betas_zero_snr=False)`
- `EulerDiscreteScheduler(..., prediction_type="epsilon", timestep_spacing="linspace", use_karras_sigmas=False, use_exponential_sigmas=False, use_beta_sigmas=False, final_sigmas_type="zero")`

Representative `step` behavior:

- `DDIMScheduler.step(..., eta=0.0, use_clipped_model_output=False, generator=None, variance_noise=None, return_dict=True)`
- `DDPMScheduler.step(..., generator=None, return_dict=True)`
- `DPMSolverMultistepScheduler.step(..., generator=None, variance_noise=None, return_dict=True)`
- `EulerDiscreteScheduler.step(..., s_churn=0.0, s_tmin=0.0, s_tmax=float("inf"), s_noise=1.0, generator=None, return_dict=True)`

Most scheduler `step` calls return an object with `.prev_sample`; several also expose `.pred_original_sample`.

## Choose a scheduler

| User intent | Scheduler pattern | Notes |
|---|---|---|
| Fast general inference | `DPMSolverMultistepScheduler.from_config(..., algorithm_type="sde-dpmsolver++", solver_order=2, use_karras_sigmas=True)` | Good DPM++ 2M SDE Karras-style option when the model family is compatible. |
| Euler or A1111 Euler parity | `EulerDiscreteScheduler` or `EulerAncestralDiscreteScheduler` | Call `scale_model_input` in manual loops; Euler supports custom timesteps and sigmas. |
| Deterministic DDIM loop | `DDIMScheduler` | Use `eta=0.0` for deterministic DDIM-style manual stepping. |
| DDPM tests/noise addition | `DDPMScheduler` | Common for `add_noise`, DDPM parity, and custom descending timesteps. |
| Low-step brightness extremes | scheduler override with `rescale_betas_zero_snr=True`, `timestep_spacing="trailing"`, and compatible `prediction_type` | Do not enable blindly on epsilon-trained checkpoints. |
| Flow matching, LCM, TCD, video, or distilled checkpoints | Model-specific scheduler from the checkpoint docs/config | Do not replace with DDIM/Euler/DPM just because the API accepts the config. |

A1111/k-diffusion mapping patterns:

- DPM++ 2M → `DPMSolverMultistepScheduler`
- DPM++ 2M Karras → `DPMSolverMultistepScheduler(use_karras_sigmas=True)`
- DPM++ 2M SDE Karras → `DPMSolverMultistepScheduler(algorithm_type="sde-dpmsolver++", use_karras_sigmas=True)`
- Euler → `EulerDiscreteScheduler`
- Euler a → `EulerAncestralDiscreteScheduler`
- Heun → `HeunDiscreteScheduler`
- LMS Karras → `LMSDiscreteScheduler(use_karras_sigmas=True)`

## Swap a pipeline scheduler

Prefer `from_config` for an already loaded pipeline:

```python
from diffusers import EulerDiscreteScheduler

old = pipe.scheduler
pipe.scheduler = EulerDiscreteScheduler.from_config(
    old.config,
    prediction_type=old.config.prediction_type,
    timestep_spacing="trailing",
)
```

Prefer `from_pretrained(..., subfolder="scheduler")` when loading scheduler config from a model repository or local pipeline directory:

```python
from diffusers import DPMSolverMultistepScheduler

scheduler = DPMSolverMultistepScheduler.from_pretrained(
    "model-or-local-pipeline-dir",
    subfolder="scheduler",
)
```

After swapping, inspect the actual result because target scheduler defaults fill missing config fields:

```python
print(type(pipe.scheduler).__name__)
for key in ["prediction_type", "timestep_spacing", "algorithm_type", "solver_order", "use_karras_sigmas"]:
    if hasattr(pipe.scheduler.config, key):
        print(key, getattr(pipe.scheduler.config, key))
pipe.scheduler.set_timesteps(10, device=pipe.device)
print(pipe.scheduler.timesteps[:3], pipe.scheduler.timesteps[-3:])
```

Important behavior from scheduler tests: switching DDIM to Euler can give Euler's default `timestep_spacing="linspace"` unless an explicit override such as `timestep_spacing="trailing"` is passed. Explicit overrides can persist across later compatible swaps because they become part of the config.

## Config fields

Fields commonly preserved across compatible schedulers:

- `num_train_timesteps`, `beta_start`, `beta_end`, `beta_schedule`, `trained_betas`
- `prediction_type`: usually `"epsilon"`, `"sample"`, or `"v_prediction"`; DPM-Solver also supports `"flow_prediction"`
- `timestep_spacing`: `"leading"`, `"linspace"`, or `"trailing"`
- `steps_offset`, `rescale_betas_zero_snr`

Fields to choose deliberately because they are scheduler-specific:

- DPM-Solver: `algorithm_type`, `solver_order`, `solver_type`, `lower_order_final`, `euler_at_final`, `final_sigmas_type`, `use_lu_lambdas`, `use_flow_sigmas`, `flow_shift`
- Sigma schedulers: `use_karras_sigmas`, `use_exponential_sigmas`, `use_beta_sigmas`, `sigma_min`, `sigma_max`, `final_sigmas_type`, `timestep_type`
- DDPM: `variance_type`
- DDIM: `set_alpha_to_one`, `eta` passed to `step`

Do not copy every config key blindly. `from_config` can warn about ignored unexpected keys or initialize missing keys from target-class defaults.

## Timesteps and spacing

Always initialize inference timesteps before manual stepping:

```python
scheduler.set_timesteps(num_inference_steps=20, device=device)
for timestep in scheduler.timesteps:
    model_input = scheduler.scale_model_input(sample, timestep)
    model_output = model(model_input, timestep).sample
    sample = scheduler.step(model_output, timestep, sample).prev_sample
```

Spacing meanings:

- `leading`: evenly spaced integer steps from the training schedule; default for DDIM/DDPM.
- `linspace`: includes endpoints and divides the schedule linearly where supported; default for several sigma/DPM schedulers.
- `trailing`: starts from the end of the training schedule; useful for low-step inference and zero-SNR workflows.

Constraints to remember:

- `DDIMScheduler.set_timesteps(num_inference_steps)` raises if inference steps exceed `num_train_timesteps`.
- `DPMSolverMultistepScheduler.set_timesteps` requires exactly one source among generated steps, custom `timesteps`, or supported custom `sigmas` paths.
- `DDPMScheduler` custom timesteps must be descending and less than `num_train_timesteps`.

## Custom timesteps

Use custom timesteps only with schedulers and pipelines that support them. Safe pattern for Euler or DPM-Solver:

```python
scheduler.set_timesteps(10)
custom_timesteps = scheduler.timesteps.tolist()

scheduler = type(scheduler).from_config(scheduler.config, use_karras_sigmas=False)
scheduler.set_timesteps(num_inference_steps=None, timesteps=custom_timesteps)
```

DPM-Solver and Euler restrictions include:

- Do not pass both `num_inference_steps` and `timesteps`.
- Do not use custom `timesteps` with `use_karras_sigmas=True`; related sigma/lambda conversion options can also be incompatible.
- For Euler continuous `timestep_type` with `prediction_type="v_prediction"`, custom timesteps are not supported.

DDPM restrictions include:

- Custom timesteps must be descending.
- Each timestep must be inside the training schedule.
- Pass either `num_inference_steps` or `timesteps`, not both.

## Custom sigmas and AYS schedules

Custom `sigmas` are supported by select sigma-based schedulers and only by pipelines that forward a `sigmas` argument. Euler tests validate resetting a scheduler from its generated sigmas:

```python
scheduler.set_timesteps(10)
custom_sigmas = scheduler.sigmas.tolist()

scheduler = EulerDiscreteScheduler.from_config(scheduler.config)
scheduler.set_timesteps(num_inference_steps=None, sigmas=custom_sigmas)
```

Sigma conversion flags are mutually exclusive: enable at most one of `use_karras_sigmas`, `use_exponential_sigmas`, or `use_beta_sigmas`. `use_beta_sigmas=True` requires SciPy.

`AysSchedules` exposes named timestep/sigma schedules such as `StableDiffusionTimesteps`, `StableDiffusionSigmas`, `StableDiffusionXLTimesteps`, `StableDiffusionXLSigmas`, and `StableDiffusionVideoSigmas`. Use a schedule only with the model family and scheduler type it was designed for, and pass only one schedule axis (`timesteps` or `sigmas`) at a time.

## Prediction type and zero-SNR

`prediction_type` is a checkpoint compatibility setting, not a quality knob:

- `epsilon`: model predicts diffusion noise.
- `sample`: model predicts the sample directly where supported.
- `v_prediction`: model predicts velocity; use for velocity-trained checkpoints.
- `flow_prediction`: DPM-Solver option for flow-style model families.

A wrong `prediction_type` may produce finite tensors and still ruin visual output. For zero-SNR workflows, use a model trained for the matching target, commonly `v_prediction`, and combine:

```python
pipe.scheduler = type(pipe.scheduler).from_config(
    pipe.scheduler.config,
    prediction_type="v_prediction",
    rescale_betas_zero_snr=True,
    timestep_spacing="trailing",
)
image = pipe(prompt, guidance_rescale=0.7).images[0]
```

If the checkpoint's training target is unknown, inspect model docs/config or ask before changing this field.

## Manual step validation

Tiny deterministic smoke pattern:

```python
import torch
from diffusers import EulerDiscreteScheduler

scheduler = EulerDiscreteScheduler(num_train_timesteps=20, prediction_type="epsilon")
scheduler.set_timesteps(4)
sample = torch.linspace(-1, 1, 16, dtype=torch.float32).reshape(1, 1, 4, 4)
model_output = torch.zeros_like(sample)

for timestep in scheduler.timesteps:
    model_input = scheduler.scale_model_input(sample, timestep)
    assert model_input.shape == sample.shape
    sample = scheduler.step(model_output, timestep, sample).prev_sample
    assert torch.isfinite(sample).all()
```

Check these invariants:

- `scheduler.num_inference_steps is not None` after `set_timesteps`.
- `len(scheduler.timesteps)` matches requested steps or custom schedule length.
- For sigma schedulers, `scheduler.sigmas` exists and is finite.
- `prev_sample.shape == sample.shape` and values are finite.
- Manual-loop sample, model output, timesteps, and scheduler internals are on compatible devices/dtypes.

## Save/load scheduler configs

Round-trip scheduler-only configs independently:

```python
import tempfile
from diffusers import DPMSolverMultistepScheduler

scheduler = DPMSolverMultistepScheduler(num_train_timesteps=100, solver_order=2)
scheduler.set_timesteps(5)

with tempfile.TemporaryDirectory() as tmpdir:
    scheduler.save_pretrained(tmpdir)
    loaded = DPMSolverMultistepScheduler.from_pretrained(tmpdir)
    loaded.set_timesteps(5)
    assert loaded.config.solver_order == scheduler.config.solver_order
```

When validating a config copied from another scheduler class, compare class name, critical config fields, generated timesteps/sigmas, and one tiny `step` output rather than assuming JSON equivalence is semantic equivalence.
