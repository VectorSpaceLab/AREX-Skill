---
name: epsilon_objective
description: Compute DDPM epsilon-prediction losses and weighted denoising objective terms for recovery training checks.
---

# Epsilon Objective

Use this skill when a DDPM task needs to score predictions of the Gaussian noise injected by the forward process. It implements the simplified epsilon mean-squared-error objective and a bounded variational-style weighting. Do not use this skill to update model parameters; optimizers belong in a training harness.

## Inputs
- True epsilon values used to create `x_t`.
- Predicted epsilon values from a model or reduced proxy.
- Optional schedule dictionary and one-based timesteps for weighted terms.

## Outputs
- `mse`: mean squared epsilon-prediction error.
- `residuals` and `squared_errors` per example.
- Optional `weighted_mse` and `weights` when schedule/timesteps are supplied.

## Workflow
1. Call `epsilon_loss(true_epsilon, predicted_epsilon)` for the paper's simplified training objective.
2. Call `weighted_epsilon_loss(...)` only when a schedule and timesteps are available.
3. Treat exact epsilon prediction as zero loss and any systematic prediction bias as positive loss.
4. Save the returned dictionary in recovery traces when validating reduced training.

## Validation
Run `python tests/test_epsilon_objective.py` or validate the full skill tree with the Distiller validator and `--run-tests`.

## Limitations
The weighted helper uses a deterministic proxy with `sigma_t^2` equal to posterior variance when positive, otherwise `beta_t`. This is sufficient for mechanism checks but not a full likelihood benchmark.
