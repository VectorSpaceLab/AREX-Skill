# Noise Schedules And Model Wrappers

DPM-Solver works by solving a continuous-time diffusion ODE. The main
integration task is therefore to make the user's trained model look like a
continuous-time noise-prediction function.

## Discrete-Time Models

Use this for DDPM, improved-DDPM, guided-diffusion, Stable Diffusion, or any
model trained on a finite sequence of integer diffusion labels.

```python
noise_schedule = NoiseScheduleVP(schedule="discrete", betas=betas)
```

or:

```python
noise_schedule = NoiseScheduleVP(schedule="discrete", alphas_cumprod=alphas_cumprod)
```

Rules:

- `betas` should be a one-dimensional backend tensor/array with length `N`.
- `alphas_cumprod` should be the DDPM-style cumulative product of `1 - beta_n`.
- The schedule maps discrete index `n` to continuous time `(n + 1) / N`.
- Default reverse integration ends at `1 / N`, not at zero.
- When a model exposes both `betas` and `alphas_cumprod`, prefer the value used
  by the model's original sampler.

## Continuous VP SDE Models

Use this for ScoreSDE-style VP/subVP models with linear beta schedules:

```python
noise_schedule = NoiseScheduleVP(
    schedule="linear",
    continuous_beta_0=0.1,
    continuous_beta_1=20.0,
)
```

Set `continuous_beta_0` and `continuous_beta_1` from the SDE object rather than
hardcoding defaults when adapting a trained model.

## Model Wrapper Conversion

The model wrapper handles two conversions:

1. **Time conversion**: for discrete schedules, it maps `t_continuous` in
   `[1/N, 1]` to a model input time near `[0, 1000*(N-1)/N]`.
2. **Prediction conversion**: it turns `noise`, `x_start`, `v`, or supported
   `score` predictions into noise predictions.

Example for a noise-prediction model:

```python
model_fn = model_wrapper(
    model,
    noise_schedule,
    model_type="noise",
    model_kwargs={"y": class_labels},
    guidance_type="uncond",
)
```

Example for classifier-free guidance in PyTorch:

```python
model_fn = model_wrapper(
    lambda x, t, cond: unet.apply_model(x, t, cond),
    noise_schedule,
    model_type="noise",
    guidance_type="classifier-free",
    condition=conditioning,
    unconditional_condition=unconditional_conditioning,
    guidance_scale=7.5,
)
```

## Improved-DDPM / Guided-Diffusion Variance Channels

Some improved-DDPM and guided-diffusion models return six channels: predicted
mean/noise plus variance. DPM-Solver is an ODE sampler and uses only the first
three image/noise channels. The example integration strips variance channels:

```python
out = model(x, t, **model_kwargs)
if out.shape[1] == 2 * x.shape[1]:
    out = out[:, : x.shape[1]]
```

Do this only when the host model's documentation or config confirms that the
extra channels are variance outputs.

## Dynamic Thresholding

Dynamic thresholding corrects predicted `x0` values by clipping each sample to a
percentile-derived bound. Use it only for pixel-space models with large guidance
scales:

```python
solver = DPM_Solver(
    model_fn,
    noise_schedule,
    algorithm_type="dpmsolver++",
    correcting_x0_fn="dynamic_thresholding",
)
```

Do not use dynamic thresholding for latent-space Stable Diffusion, where latent
values are not bounded pixel intensities.

## Inversion And Add-Noise Helpers

The PyTorch root solver exposes helper methods useful for image editing:

- `add_noise(x0, t, noise=None)` creates noisy states at one or many times.
- `inverse(x, steps=..., t_start=..., t_end=...)` integrates from data time
  toward noise time using the same solver controls as sampling.

The JAX root solver does not expose public `add_noise` or `inverse` helpers.
For JAX inversion, either implement equivalent schedule math explicitly or port
the PyTorch helper with a dedicated smoke test.
