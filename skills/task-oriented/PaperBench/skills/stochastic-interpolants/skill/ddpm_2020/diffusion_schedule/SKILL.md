---
name: diffusion_schedule
description: Build and validate DDPM forward-process schedules and closed-form noisy samples for reduced recovery experiments.
---

# Diffusion Schedule

Use this skill when a recovery or implementation task needs the fixed Gaussian DDPM forward process from Ho et al. 2020. It is appropriate for constructing beta schedules, alpha products, posterior variances, and direct samples from `q(x_t | x_0)`. Do not use it for learned reverse-process parameters or image-quality evaluation.

## Inputs
- `timesteps`: positive integer number of diffusion steps.
- `beta_start`, `beta_end`: scalars satisfying `0 < beta_start <= beta_end < 1`.
- `x0`: scalar/list clean data values.
- `epsilon`: scalar/list Gaussian noise values matching `x0`.
- `t`: one-based timestep index.

## Outputs
- Schedule dictionary with `betas`, `alphas`, `alpha_bars`, and `posterior_variances`.
- Noisy values computed as `sqrt(alpha_bar_t) * x0 + sqrt(1-alpha_bar_t) * epsilon`.
- Validation flags for monotone signal decay and valid variances.

## Workflow
1. Call `scripts/ddpm_schedule.py build --timesteps T --beta-start B0 --beta-end B1` for schedule JSON.
2. Use `forward_sample(schedule, x0, epsilon, t)` or the CLI `sample` command to construct `x_t` directly.
3. Keep timestep inputs in one-based paper notation; the script handles internal indexing.
4. For deterministic tests or recovery, pass explicit epsilon values rather than random sampling.

## Validation
Run `python tests/test_ddpm_schedule.py` or validate the full skill tree with:

```bash
python <distiller>/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

## Limitations
The schedule helper implements a linear schedule for bounded recovery. It is mechanism-faithful for DDPM equations but not a replacement for full image-scale training hyperparameter search.
