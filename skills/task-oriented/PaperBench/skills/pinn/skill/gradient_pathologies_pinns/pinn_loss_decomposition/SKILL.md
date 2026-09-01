---
name: pinn_loss_decomposition
description: Compute separated Helmholtz PINN residual and boundary losses so gradient imbalance can be diagnosed and corrected.
---

# PINN Loss Decomposition

Use this skill when recovery needs separate PDE residual and boundary/data-fit loss terms. Do not collapse losses before gradient-statistic annealing.

## Inputs

- A trainable model with coordinate predictions.
- Interior collocation points and forcing values.
- Boundary points and exact boundary values.
- Helmholtz parameters and current lambda values.

## Outputs

- Residual loss.
- Boundary loss.
- Weighted total loss.
- Per-parameter gradients for residual and boundary losses when a compatible reduced model is used.

## Workflow

1. Predict the solution on interior and boundary samples.
2. Compute the Helmholtz residual or a reduced residual proxy for the selected model family.
3. Compute mean-squared residual and boundary errors separately.
4. Combine them with current lambda weights only after logging the individual terms.

## Validation

Run `python scripts/losses.py --self-test` or the skill tests.
