# Scheduler Troubleshooting

Use this guide when scheduler imports work but denoising fails, scheduler swaps silently change behavior, or outputs degrade after timestep, sigma, or prediction-type edits.

## Import or optional dependency failures

Symptoms:

- `ModuleNotFoundError: No module named 'diffusers'` or `No module named 'torch'`
- `Make sure to install scipy if you want to use beta sigmas.`
- Scheduler class import fails for a scheduler that exists in newer documentation.

Fixes:

- Verify the Python environment imports the same Diffusers version expected by the project.
- Install optional dependencies required by the chosen feature, for example SciPy for `use_beta_sigmas=True`.
- Prefer schedulers present in the installed package; if a doc page is newer than the package, update the package or choose an available compatible scheduler.

Fast check:

```bash
python path/to/sub-skills/schedulers/scripts/scheduler_smoke.py --schedulers EulerDiscreteScheduler DPMSolverMultistepScheduler
```

## Local/offline scheduler config problems

Symptoms:

- `from_pretrained` cannot find `scheduler_config.json`.
- Offline loading tries to contact the Hub.
- A local pipeline directory loads the pipeline but not the scheduler subfolder.

Fixes:

- For pipeline repositories or directories, load scheduler config with `subfolder="scheduler"`.
- Use a local model directory that contains the scheduler config when offline.
- For an already loaded pipeline, avoid file lookup and use `NewScheduler.from_config(pipe.scheduler.config, ...)`.

```python
scheduler = EulerDiscreteScheduler.from_pretrained(local_pipeline_dir, subfolder="scheduler")
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")
```

## `step` called before `set_timesteps`

Symptom:

```text
Number of inference steps is 'None', you need to run 'set_timesteps' after creating the scheduler
```

Cause: the scheduler has training schedule state from `__init__`, but inference-specific timesteps, indices, and sigmas are not initialized.

Fix:

```python
scheduler.set_timesteps(num_inference_steps, device=sample.device)
for timestep in scheduler.timesteps:
    model_input = scheduler.scale_model_input(sample, timestep)
    model_output = model(model_input, timestep).sample
    sample = scheduler.step(model_output, timestep, sample).prev_sample
```

Validate:

```python
assert scheduler.num_inference_steps is not None
assert len(scheduler.timesteps) == num_inference_steps
```

## Wrong `prediction_type`

Symptoms:

- Quality collapses after a scheduler swap although tensor shapes and dtypes are valid.
- Zero-SNR/trailing settings do not fix brightness extremes.
- A tiny smoke test is finite but full images are consistently overexposed, underexposed, or unstable.

Cause: the scheduler interprets model output as noise (`epsilon`), direct sample (`sample`), velocity (`v_prediction`), or flow (`flow_prediction`). This must match how the model was trained.

Fixes:

- Preserve the source config when swapping: `prediction_type=pipe.scheduler.config.prediction_type`.
- Use `v_prediction` only for velocity-trained checkpoints.
- Use `rescale_betas_zero_snr=True` and `timestep_spacing="trailing"` only with a compatible prediction target, commonly `v_prediction`.
- Use DPM-Solver `flow_prediction` only for model families that expect it.

Validation:

```python
print(pipe.scheduler.config.prediction_type)
assert pipe.scheduler.config.prediction_type in {"epsilon", "sample", "v_prediction", "flow_prediction"}
```

If the user asks to “try v-prediction for quality,” ask for or inspect the checkpoint's training target first.

## DDIM to Euler swap changed timestep spacing

Symptom: replacing a DDIM scheduler with Euler changes outputs more than expected or starts from different timestep endpoints.

Cause: `from_config` fills missing fields from the target scheduler defaults. DDIM commonly defaults to `timestep_spacing="leading"`; Euler defaults to `"linspace"` unless explicitly overridden.

Fix:

```python
from diffusers import EulerDiscreteScheduler

pipe.scheduler = EulerDiscreteScheduler.from_config(
    pipe.scheduler.config,
    prediction_type=pipe.scheduler.config.prediction_type,
    timestep_spacing="trailing",  # or the exact spacing required by the task
)
```

Validate:

```python
pipe.scheduler.set_timesteps(10, device=pipe.device)
print(pipe.scheduler.config.timestep_spacing)
print(pipe.scheduler.timesteps)
```

## Custom timesteps mismatch

Common errors:

```text
Can only pass one of `num_inference_steps` or `custom_timesteps`.
Must pass exactly one of `num_inference_steps` or `timesteps`.
Cannot use `timesteps` with `config.use_karras_sigmas = True`.
`custom_timesteps` must be in descending order.
```

Fixes:

- Pass generated steps with `set_timesteps(num_inference_steps=steps)`.
- Pass custom steps with `set_timesteps(num_inference_steps=None, timesteps=custom_timesteps)`.
- Sort or construct custom timesteps in descending order.
- Ensure `max(custom_timesteps) < scheduler.config.num_train_timesteps`.
- Disable incompatible sigma/lambda conversions before custom timestep use.

Safe DPM-Solver pattern:

```python
base = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=False)
base.set_timesteps(10)
custom_timesteps = base.timesteps.tolist()

scheduler = DPMSolverMultistepScheduler.from_config(base.config, use_karras_sigmas=False)
scheduler.set_timesteps(num_inference_steps=None, timesteps=custom_timesteps)
```

Validate:

```python
values = scheduler.timesteps.tolist()
assert all(a >= b for a, b in zip(values, values[1:]))
assert max(values) < scheduler.config.num_train_timesteps
```

## Custom sigmas mismatch

Symptoms:

```text
Only one of `config.use_beta_sigmas`, `config.use_exponential_sigmas`, `config.use_karras_sigmas` can be used.
Make sure to install scipy if you want to use beta sigmas.
```

Other symptoms include a pipeline ignoring `sigmas` or a mismatch between sigma count and expected denoising steps.

Fixes:

- Enable at most one of `use_karras_sigmas`, `use_exponential_sigmas`, or `use_beta_sigmas`.
- Install SciPy before using beta sigmas.
- For Euler custom sigmas, pass `num_inference_steps=None, sigmas=custom_sigmas` and let the scheduler derive timesteps.
- Confirm the selected pipeline forwards `sigmas` before using pipeline-level custom sigmas.
- Do not pass both `timesteps` and `sigmas`.

Validate:

```python
scheduler.set_timesteps(num_inference_steps=None, sigmas=custom_sigmas)
assert hasattr(scheduler, "sigmas")
assert len(scheduler.sigmas) >= len(scheduler.timesteps)
assert torch.isfinite(scheduler.sigmas).all()
```

## Device and dtype mistakes

Symptoms:

- Tensor device mismatch involving timesteps, sigmas, `sample`, or `model_output`.
- CPU smoke checks pass but accelerator runs fail.
- Mixed precision output contains `NaN`/`Inf` after scheduler changes.

Fixes:

- Pass `device=sample.device` to `set_timesteps` where supported.
- Keep `sample`, `model_output`, and model parameters on compatible devices and dtypes.
- Do not manually move scheduler internals unless the scheduler docs require it; some schedulers intentionally keep sigmas on CPU and move values internally.
- Start debugging with `torch.float32` CPU tensors, then reintroduce accelerator and reduced precision.

Validation:

```python
scheduler.set_timesteps(num_inference_steps, device=sample.device)
assert scheduler.timesteps.device == sample.device
assert torch.isfinite(sample).all()
```

## Manual loop omits `scale_model_input`

Symptom: Euler/LMS-style schedulers produce poor or changed results, while DDIM-like schedulers seem unaffected.

Cause: some schedulers require scaling the model input by the current noise level; others return the input unchanged. Calling it is the safe generic pattern.

Fix:

```python
for timestep in scheduler.timesteps:
    model_input = scheduler.scale_model_input(sample, timestep)
    model_output = model(model_input, timestep).sample
    sample = scheduler.step(model_output, timestep, sample).prev_sample
```

## Config copied incorrectly

Symptoms:

- Warnings about ignored unexpected config keys or missing keys initialized from defaults.
- `timestep_spacing`, solver options, or sigma settings differ after a compatible scheduler swap.
- Saved scheduler JSON round-trips but stepping behavior changes after changing classes.

Cause: scheduler configs are compatible at the schedule/config level, not identical across scheduler classes.

Fix:

```python
old = pipe.scheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    old.config,
    prediction_type=old.config.prediction_type,
    timestep_spacing="trailing",
    algorithm_type="sde-dpmsolver++",
    solver_order=2,
    use_karras_sigmas=True,
)
```

Then print actual fields and run a tiny finite-output step check.

## API misuse in scheduler-focused tests

Common test mistakes:

- Expecting exact output equality after changing scheduler class or defaults.
- Calling `step` with an integer timestep when the scheduler's `timesteps` are floats, or vice versa.
- Comparing saved config JSON instead of comparing key config fields plus behavior.
- Forgetting that DPM-Solver multistep schedulers maintain model-output history after `set_timesteps`.

Better assertions:

- Class name and key config fields match the intent.
- Timesteps are the expected length/order.
- `prev_sample` shape matches input and is finite.
- Explicitly chosen overrides survive `save_pretrained`/`from_pretrained` round-trip.

## When to stop and ask

Ask for more context or inspect model metadata before changing scheduler behavior when:

- The checkpoint's trained `prediction_type` is unknown.
- The request maps an external sampler name ambiguously.
- The model may require FlowMatch, LCM, TCD, video, or another model-specific scheduler.
- The user wants custom `timesteps` or `sigmas` for a pipeline/scheduler pair that may not forward those arguments.
