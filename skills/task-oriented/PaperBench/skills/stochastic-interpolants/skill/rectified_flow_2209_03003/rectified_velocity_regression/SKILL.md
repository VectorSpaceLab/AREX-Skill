---
name: rectified_velocity_regression
description: Fit and audit a small rectified-flow velocity model with least-squares regression and optimizer evidence.
---

# Rectified Velocity Regression

Use this skill when rectified-flow records must be converted into a trained velocity field or when recovery must prove that an optimizer step happened. Do not use it to construct interpolation records.

## Inputs
- Records with `xt`, `t`, and `target_velocity`.
- Affine parameters `w_x`, `w_t`, and `b` per dimension.
- A learning rate and optional step count.

## Outputs
- Loss before and after training.
- Parameter values before and after training.
- Optimizer-change evidence and gradients.

## Workflow
1. Evaluate `v(x,t) = w_x * x + w_t * t + b` per dimension.
2. Compute mean squared error against `target_velocity`.
3. Compute analytic gradients and update parameters with SGD.
4. Report loss reduction and parameter changes.

## Validation
Run `python tests/test_velocity.py` or validate with `--run-tests`.

## Limitations
This deterministic affine model is intended for bounded recovery and unit tests; it is not a replacement for the paper's full neural image model.
