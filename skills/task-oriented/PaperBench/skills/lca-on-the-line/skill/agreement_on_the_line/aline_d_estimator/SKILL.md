---
name: aline_d_estimator
description: Solve the ALine-D pairwise linear system to predict OOD accuracies from ID accuracy and unlabeled agreement statistics.
---

# ALine-D Estimator

Use this skill after agreement statistics and an agreement-line slope are available. It implements the paper's ALine-D estimator rather than a simple plug-in baseline.

## Inputs

- Statistics JSON from `agreement_statistics`.
- Fit JSON from `agreement_line_fit`.

## Outputs

- Predicted OOD accuracy per model.
- ALine-S baseline predictions.
- Equation count and residual diagnostics.

## Workflow

1. Build one linear equation for every unordered model pair.
2. Use the fitted agreement slope and pairwise agreement terms from Equation (6).
3. Solve the least-squares system over probit OOD accuracies.
4. Convert predictions back to probability space.

## Validation

Run `python tests/test_aline_d_estimator.py` from this skill directory.

## Limitations

At least three models are required. Rank-deficient synthetic cases may fail because the system cannot identify every model's OOD accuracy.
