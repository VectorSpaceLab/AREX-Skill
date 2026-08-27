# Solver Choice Guide

Use this reference when choosing DPM-Solver/DPM-Solver++ settings for a user
workflow. It distills the repository README, root solver docstrings, and example
scripts into operational rules.

## Core Decision Axes

| Axis | Main choices | Practical guidance |
| --- | --- | --- |
| Algorithm | PyTorch `algorithm_type="dpmsolver"` or `"dpmsolver++"`; JAX `predict_x0=False` or `True` | `dpmsolver++`/`predict_x0=True` is usually preferred for guided sampling and latent diffusion adapters. Try both for unconditional custom models if quality is uncertain. |
| Step method | `multistep`, `singlestep`, `singlestep_fixed`, `adaptive` | `multistep` is the common stable choice for guided and Stable Diffusion workflows. `singlestep` is useful for DPM-Solver-fast style exploration. `adaptive` ignores the fixed `steps` count and uses tolerance parameters. |
| Order | 1, 2, 3 | Order 1 is equivalent to DDIM-like first-order behavior. Use order 2 for guided sampling with high guidance scales. Use order 3 for unconditional or lightly guided sampling. |
| Steps/NFE | 10, 15, 20, 25, 50 | 10 is a fast low-cost check, 15-20 often gives strong quality, 25 is common for Stable Diffusion examples, and 50 is a convergence-oriented reference. |
| Skip type | `time_uniform`, `logSNR`, `time_quadratic` | Use `time_uniform` for high-resolution image or latent Stable Diffusion workflows. Use `logSNR` for low-resolution examples such as CIFAR-10. `time_quadratic` follows DDIM-style spacing and is a comparison option. |
| Final denoise | PyTorch `denoise_to_zero=True`; JAX `denoise=True` | May improve low-resolution FID at the cost of one extra function evaluation. Usually not recommended for high-resolution or latency-sensitive use. |
| Thresholding | PyTorch `correcting_x0_fn="dynamic_thresholding"`; JAX `thresholding=True` | Intended for pixel-space guided sampling with large guidance scales. Do not use for latent-space Stable Diffusion. See JAX caveats before recommending JAX thresholding. |

## Recommended Defaults By Workflow

### Unconditional or lightly guided custom diffusion model

Start with a quality-oriented multistep configuration:

```python
solver = DPM_Solver(model_fn, noise_schedule, algorithm_type="dpmsolver++")
sample = solver.sample(
    x_T,
    steps=20,
    order=3,
    skip_type="time_uniform",
    method="multistep",
)
```

Also compare `algorithm_type="dpmsolver"` when the model is not strongly guided
or when matching an older DPM-Solver baseline. If the user needs a very fast
screen, reduce `steps` to 10 or 15 and inspect sample quality before increasing.

### Guided sampling with a large guidance scale

Use the second-order DPM-Solver++ multistep family:

```python
solver = DPM_Solver(model_fn, noise_schedule, algorithm_type="dpmsolver++")
sample = solver.sample(
    x_T,
    steps=20,
    order=2,
    skip_type="time_uniform",
    method="multistep",
)
```

For pixel-space diffusion models with high guidance, add dynamic thresholding:

```python
solver = DPM_Solver(
    model_fn,
    noise_schedule,
    algorithm_type="dpmsolver++",
    correcting_x0_fn="dynamic_thresholding",
)
```

Do not apply dynamic thresholding to latent-space Stable Diffusion latents; the
latent `x0` is not bounded like pixel data.

### CIFAR-10 / low-resolution ScoreSDE or DDPM examples

The repository examples use `logSNR` spacing and small NFE values such as 10:

```text
steps=10
skip_type="logSNR"
method="singlestep"
order=3
```

Enable final denoising only when the metric target benefits from it and the
extra NFE is acceptable.

### Stable Diffusion latent sampling

Use DPM-Solver++ with multistep order 2 and about 20-25 steps:

```text
--dpm_solver --ddim_steps 25
```

If adapting the bundled sampler adapter directly, keep `skip_type="time_uniform"`,
`method="multistep"`, `order=2`, and `lower_order_final=True` as the default
family unless the user is intentionally benchmarking scheduler settings.

## Before Blaming The Solver

The README emphasizes a practical baseline: run a high-step DDIM or equivalent
reference first. DPM-Solver accelerates convergence toward the same diffusion
ODE target, but it cannot fix a poorly trained model, wrong noise schedule,
incorrect model parameterization, bad conditioning, missing EMA weights, or
broken checkpoint loading.

## Time Bounds

- `t_start` defaults to the schedule's terminal time (`T`, normally 1.0).
- For discrete-time schedules, `t_end` defaults to `1 / total_N`, such as
  `0.001` for a 1000-step training schedule.
- For continuous-time VP SDEs, use `t_end`/`eps` near `1e-3` for small step
  counts and consider `1e-4` only for larger step counts.
- Never set either time bound to zero; the implementations assert or become
  numerically unstable near singular log-SNR values.

## Comparing Settings Safely

Use small tensors or a tiny batch first. Recommended search dimensions:

1. `dpmsolver` versus `dpmsolver++`.
2. `multistep` versus `singlestep`.
3. `order=2` versus `order=3`.
4. `steps` in `[10, 15, 20, 25, 50]`.
5. `time_uniform` versus `logSNR` if moving between high- and low-resolution
   workflows.
6. Dynamic thresholding only for pixel-space guided models.

Record seed, schedule, model parameterization (`noise`, `x_start`, `v`, or
`score`), guidance type, and checkpoint/EMA choice for every comparison.
