---
name: reverse_denoising_step
description: Convert predicted DDPM epsilon values into reverse-process means and deterministic or stochastic denoising samples.
---

# Reverse Denoising Step

Use this skill when a DDPM recovery needs to apply the paper's epsilon-parameterized reverse Gaussian transition. It converts `epsilon_theta(x_t,t)` into `mu_theta(x_t,t)` and optionally adds reverse Gaussian noise. Do not use it to train the epsilon model or to compute image metrics.

## Inputs
- Schedule dictionary with `betas`, `alphas`, `alpha_bars`, and optionally `posterior_variances`.
- Current noisy scalar/list `x_t`.
- Predicted epsilon scalar/list matching `x_t`.
- One-based timestep `t`.
- Optional reverse noise `z` and variance mode.

## Outputs
- Reverse mean value(s) from the DDPM equation.
- Reverse sample value(s), equal to the mean when `z` is zero or omitted.
- Coefficients used for auditability.

## Workflow
1. Build or load a schedule from the diffusion schedule skill.
2. Call `reverse_mean(schedule, x_t, predicted_epsilon, t)`.
3. Call `reverse_sample(...)` with explicit zero noise for deterministic recovery checks.
4. Record the output in mechanism checks when validating proxy recovery.

## Validation
Run `python tests/test_reverse_step.py` or the Distiller skill-tree validator with `--run-tests`.

## Limitations
The helper validates the reverse mean equation and single-step sampling. It does not claim to reproduce long-chain image generation quality in a bounded recovery run.
