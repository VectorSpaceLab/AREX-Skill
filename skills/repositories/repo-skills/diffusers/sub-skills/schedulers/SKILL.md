---
name: schedulers
description: "Select, configure, swap, serialize, and troubleshoot Diffusers
  schedulers, timesteps, sigmas, and noise schedules for inference and tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Schedulers

Use this sub-skill when a task mentions Diffusers schedulers, samplers, DDIM, DDPM, Euler, DPM-Solver, DPM++, Karras, AYS, timestep spacing, custom timesteps, custom sigmas, `prediction_type`, `rescale_betas_zero_snr`, `set_timesteps`, `scheduler.step`, or scheduler config round-trips.

## Route first

- Full pipeline loading, prompt execution, model downloads, device maps, and image generation belong to the pipelines/inference skill; return here for scheduler choice and configuration.
- Training loop use of schedulers and model training arguments belong to training recipes; this skill covers inference and scheduler-focused tests.
- Model architecture changes and prediction heads are not scheduler tasks; only set `prediction_type` here when it is known to match the checkpoint.
- Packaging a whole pipeline belongs elsewhere, but this skill owns scheduler-only `from_config`, `from_pretrained`, and `save_pretrained` behavior.

## Default workflow

1. Inspect the current scheduler with `type(pipe.scheduler).__name__`, `dict(pipe.scheduler.config)`, and important fields such as `prediction_type`, `timestep_spacing`, `num_train_timesteps`, and sigma options.
2. Pick the scheduler for the sampling goal: DPM-Solver multistep for fast high-quality inference, Euler/Euler ancestral for Euler-style sampler parity, DDIM for deterministic DDIM loops, DDPM for DDPM/noise-addition parity, or model-specific schedulers for FlowMatch, LCM, TCD, video, or distilled checkpoints.
3. Swap an already loaded pipeline with `NewScheduler.from_config(pipe.scheduler.config, explicit_overrides...)`; load a scheduler config from a model directory or Hub repo with `NewScheduler.from_pretrained(model_id_or_dir, subfolder="scheduler")`.
4. Always pass explicit overrides for behavior the user cares about, especially `prediction_type`, `timestep_spacing`, `rescale_betas_zero_snr`, solver options, and sigma conversion flags.
5. Before manual stepping, call `scheduler.set_timesteps(...)`; in denoising loops call `scheduler.scale_model_input(sample, timestep)` before the model and consume `scheduler.step(...).prev_sample`.
6. Validate a swap with a tiny deterministic CPU tensor, finite-output checks, and a config printout before running full inference.

## Quick choices

- Replace DDIM with Euler while preserving compatible config:

```python
from diffusers import EulerDiscreteScheduler

pipe.scheduler = EulerDiscreteScheduler.from_config(
    pipe.scheduler.config,
    prediction_type=pipe.scheduler.config.prediction_type,
    timestep_spacing="trailing",
)
```

- Use DPM++ 2M SDE Karras-style inference:

```python
from diffusers import DPMSolverMultistepScheduler

pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    algorithm_type="sde-dpmsolver++",
    solver_order=2,
    use_karras_sigmas=True,
)
```

- Use zero terminal SNR only for compatible models, commonly `v_prediction` checkpoints:

```python
pipe.scheduler = type(pipe.scheduler).from_config(
    pipe.scheduler.config,
    prediction_type="v_prediction",
    rescale_betas_zero_snr=True,
    timestep_spacing="trailing",
)
image = pipe(prompt, guidance_rescale=0.7).images[0]
```

## References

- Scheduler API and workflow details: [references/scheduler-reference.md](references/scheduler-reference.md)
- Failure diagnosis and fixes: [references/troubleshooting.md](references/troubleshooting.md)
- Local validation helper: [scripts/scheduler_smoke.py](scripts/scheduler_smoke.py)

## Safe validation

Run the bundled helper after installing Diffusers and Torch:

```bash
python path/to/sub-skills/schedulers/scripts/scheduler_smoke.py --help
python path/to/sub-skills/schedulers/scripts/scheduler_smoke.py
```

Expected signals: common scheduler imports succeed; constructor and step signatures print; short `set_timesteps` schedules are produced; tiny CPU `step` checks return finite tensors; and common misuse checks raise the expected errors.
