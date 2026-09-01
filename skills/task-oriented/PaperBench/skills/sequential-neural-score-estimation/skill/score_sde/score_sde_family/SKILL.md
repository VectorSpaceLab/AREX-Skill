---
name: score_sde_family
description: Define VE, VP, and sub-VP SDE contracts plus reverse-time SDE and probability-flow ODE dynamics for score-based generative modeling.
---

# Score SDE Family

Use this skill when an experiment needs the paper's forward SDE perturbation, prior density, reverse-time SDE, or probability-flow ODE semantics. Do not use it to claim full image-generation quality by itself.

## Inputs

- SDE type: `ve`, `vp`, or `subvp`.
- Hyperparameters: `sigma_min`, `sigma_max`, `beta_min`, `beta_max`, `num_steps`.
- State values as scalars or lists and continuous time `t` in `(0, 1]`.
- Optional score function value for reverse dynamics.

## Outputs

- Forward drift and diffusion.
- Marginal mean and standard deviation.
- Prior log-density.
- Reverse drift and diffusion, including probability-flow zero diffusion.

## Workflow

1. Instantiate an SDE with `scripts/sde_family.py`.
2. Use `marginal_prob` to perturb clean data for denoising score matching.
3. Use `reverse_drift_diffusion` with `probability_flow=False` for stochastic reverse SDE checks.
4. Use `probability_flow=True` for deterministic ODE checks and likelihood-style recovery.
5. Record SDE type, time, drift, diffusion, and marginal statistics in recovery logs.

## Validation

Run:

```bash
python tests/test_sde_family.py
python scripts/sde_family.py --sde vp --x 1.0 --t 0.5 --score -0.25
```

## Limitations

This skill implements small deterministic numeric contracts for recovery and testing. Full neural image models, JAX/Flax code, and large checkpoint loading are outside this skill.
