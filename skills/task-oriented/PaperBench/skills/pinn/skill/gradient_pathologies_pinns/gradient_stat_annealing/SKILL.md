---
name: gradient_stat_annealing
description: Update PINN data-loss weights from residual and data-fit gradient statistics using the paper's moving-average annealing rule.
---

# Gradient Statistic Annealing

Use this skill when a composite PINN loss keeps residual and data-fit losses separate and needs the paper's adaptive lambda update. Do not use it when only aggregate loss gradients are available.

## Inputs

- Residual-gradient magnitudes or a residual-gradient vector.
- One or more data-fit gradient vectors.
- Current lambda values.
- Smoothing coefficient `alpha` and numerical `epsilon`.

## Outputs

- Updated lambdas.
- Instantaneous lambda estimates.
- Residual max-gradient statistic and data mean-gradient statistics.
- Balance ratios for recovery mechanism checks.

## Workflow

1. Compute `max(abs(grad L_r))`.
2. Compute `mean(abs(grad L_i))` for each data-fit loss.
3. Compute `lambda_hat_i = max_grad_r / (mean_grad_i + epsilon)`.
4. Apply `lambda_i = (1 - alpha) * lambda_i + alpha * lambda_hat_i`.
5. Log all values in the training trace.

## Validation

Run `python scripts/annealing.py --self-test` or the generated skill tests.
