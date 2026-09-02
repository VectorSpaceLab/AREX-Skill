---
name: diffusion_noise_schedule
description: Build and validate Gaussian diffusion beta schedules and posterior coefficients for guided diffusion recovery experiments.
---

# Diffusion Noise Schedule

Use this skill when a recovery or implementation needs a small but faithful Gaussian diffusion schedule for `Diffusion Models Beat GANs on Image Synthesis`. Do not use it to claim full ImageNet sampling by itself; it only covers the noising schedule and posterior coefficient contract.

## Inputs

- `schedule`: `linear` or `cosine`.
- `steps`: positive integer timestep count.
- Optional `max_beta` for cosine clipping.

## Outputs

- `betas`: bounded beta values.
- `alphas_cumprod`: monotonically decreasing cumulative products.
- `posterior_variance`, `posterior_mean_coef1`, and `posterior_mean_coef2`.

## Workflow

1. Select the schedule used by the target experiment.
2. Build beta values with the same limiting behavior as the paper's diffusion family.
3. Derive posterior arrays from cumulative alpha products.
4. Validate all values before giving them to a sampler.
5. In reduced recovery, record that this is a reduced schedule and not a checkpoint-level sampling run.

## Validation

Run `python scripts/noise_schedule.py --schedule linear --steps 8 --output /tmp/schedule.json` and run the included tests with the skill validator.

## Limitations

This skill does not implement a neural denoiser, classifier, learned variance head, or FID evaluation. It supplies the deterministic schedule mechanics consumed by other modules.
