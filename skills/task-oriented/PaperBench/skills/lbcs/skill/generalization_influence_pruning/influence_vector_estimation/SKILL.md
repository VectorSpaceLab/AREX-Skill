---
name: influence_vector_estimation
description: Estimate per-example parameter influence vectors for dataset pruning using gradients and damped inverse-Hessian approximations.
---

# Influence Vector Estimation

Use this skill when a recovery or implementation needs the paper mechanism that approximates the parameter change caused by removing each training example without retraining. Do not use it as an independent scalar importance ranker; its output is meant to be aggregated vectorially by a pruning optimizer.

## Inputs

- Feature matrix, labels, and model parameters for a small differentiable classifier, or explicit per-example gradients and a Hessian/curvature matrix.
- Positive damping value for numerical stability.
- Approximation scope, such as last linear layer, recorded in metadata.

## Outputs

- JSON with one influence vector per example.
- Metadata containing damping, vector dimension, sample count, finite-value checks, and sign convention.

## Workflow

1. Compute per-example gradients for the selected parameter block.
2. Build or accept a curvature matrix and add `damping * I`.
3. Solve the damped linear system for every example.
4. Return removal influence vectors using a consistent sign convention.
5. Validate shapes and non-finite values before passing vectors downstream.

## Validation

Run `python scripts/influence_estimator.py --demo` and `python tests/test_influence_estimator.py` from this skill directory.

## Limitations

This skill provides a scalable approximation. It does not claim full leave-one-out retraining equivalence, and full CIFAR-scale recovery requires the actual model/data runtime.
