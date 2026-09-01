---
name: diffused_score_training
description: Build and validate reduced denoising score-training traces for single-observation simulation-based inference posteriors.
---

# Diffused Score Training

Use this skill when a recovery or implementation needs the F-NPSE training contract for single-observation posterior scores. Do not use it to claim full neural score-network training unless a real neural model, simulator dataset, and optimizer loop are actually run.

## Inputs

- Simulator pairs `(theta, x)` or reduced analytic Gaussian parameters.
- A noise level or reduced diffusion setting.
- Initial trainable surrogate parameters.
- Learning rate and seed.

## Outputs

- Score targets for diffused or analytic conditional posterior samples.
- A training trace with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- Booleans distinguishing reduced surrogate training from full score-network training.

## Workflow

1. Convert the SBI task to a standard-normal-prior parameterization when possible.
2. For an analytic Gaussian reduced run, compute the posterior mean and variance for one observation.
3. Fit a small affine score surrogate `a * theta + b * x + c` to the exact score by one or more gradient steps.
4. Save the loss and parameter-change trace for recovery validation.
5. Keep the trace honest: mark reduced training as reduced and keep full-model flags false.

## Validation

Run `python tests/test_diffused_score_training.py` or validate the whole skill with the Distiller `validate_skill_tree.py --run-tests` command.

## Limitations

This skill provides deterministic reduced-training utilities. It does not implement the paper's full residual MLP score network or 400-level training loop.
