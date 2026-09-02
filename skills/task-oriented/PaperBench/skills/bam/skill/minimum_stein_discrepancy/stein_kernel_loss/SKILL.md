---
name: stein_kernel_loss
description: Compute one-dimensional kernel Stein and diffusion kernel Stein losses for unnormalized model recovery experiments.
---

# Stein Kernel Loss

Use this skill when a task needs to evaluate an empirical KSD or scalar diffusion KSD objective for a one-dimensional unnormalized model. It is appropriate for bounded recovery experiments, diagnostics, and cross-checks of minimum Stein discrepancy estimators. Do not use it as a general multidimensional matrix-kernel implementation.

## Inputs

- `samples`: at least two numeric observations.
- `theta`: model parameter used by the score and diffusion functions.
- `score_fn(x, theta)`: derivative of the log unnormalized density with respect to `x`.
- `bandwidth`: positive Gaussian-kernel bandwidth.
- Optional `diffusion_fn(x, theta)` and `diffusion_derivative_fn(x, theta)` for scalar DKSD.

## Outputs

- Pairwise scalar Stein-kernel values.
- U-statistic loss over all ordered distinct pairs.
- Diagnostics containing pair count and finite-value status.

## Workflow

1. Define the model score without using normalizing constants.
2. Choose identity diffusion for vanilla KSD or a scalar diffusion and derivative for DKSD.
3. Call `u_statistic_loss` from `scripts/stein_loss.py` for a candidate parameter.
4. Repeat over candidate parameters or pass the objective to an optimizer skill.
5. Save diagnostics when the value is used as recovery evidence.

## Validation

Run `python -m pytest tests` or validate through the Distiller skill-tree validator with `--run-tests`.

## Limitations

This skill implements the scalar one-dimensional special case used for fast recovery. It intentionally does not implement the full matrix-valued RKHS formula or Riemannian geometry from the paper.
