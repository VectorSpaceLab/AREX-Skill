---
name: diffusion_noise_objective
description: Compute SR3-style conditional diffusion corruption, noise-prediction loss, and a deterministic scalar optimizer update.
---

# Diffusion Noise Objective

Use this skill when implementing or checking SR3 training logic. It owns timestep corruption, predicted-noise loss, and reduced scalar update math. Do not use it as a sampler.

## Inputs
- A pair with `condition` and `target`.
- A timestep value and beta/noise schedule value.
- A scalar denoiser parameter for reduced recovery.

## Outputs
- Noisy target, true noise, predicted noise, MSE loss, and updated parameter.

## Workflow
1. Compute a deterministic proxy noise value from the target and timestep.
2. Mix clean target and noise according to beta.
3. Predict noise from condition, noisy value, timestep, and the trainable scalar parameter.
4. Compute squared error and update the scalar parameter with gradient descent.
5. Record `params_before`, `params_after`, `loss_before`, and `loss_after` for validators.

## Validation
Run `python tests/test_noise_objective.py` or validate the skill tree with `--run-tests`.

## Limitations
The scalar parameter is a bounded proxy for a neural denoiser; it validates objective mechanics, not full model capacity.
