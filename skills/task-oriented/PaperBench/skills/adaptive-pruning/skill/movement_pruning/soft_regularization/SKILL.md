---
name: soft_regularization
description: Compute soft movement-pruning sigmoid sparsity penalties and gradients for threshold-mask recovery checks.
---

# Soft Movement Sparsity Regularization

Use this skill when implementing or auditing soft movement pruning. It computes the paper penalty `lambda_mvp * sum(sigmoid(S))` and the corresponding score-gradient contribution.

## Inputs
- `scores`: flat or nested numeric scores.
- `lambda_mvp`: nonnegative regularization strength.
- Optional `threshold` and `lr` for before/after keep-ratio diagnostics.

## Outputs
Penalty value, gradient contribution with the same shape as scores, sigmoid mass, and optional threshold keep-ratio diagnostics.

## Workflow
1. Compute stable sigmoid values.
2. Sum sigmoid scores and multiply by `lambda_mvp`.
3. Compute `lambda_mvp * sigmoid(S) * (1 - sigmoid(S))`.
4. Optionally simulate a regularization-only gradient step to show scores are pushed downward.

## Validation
Run `python tests/test_soft_regularization.py`. Tests check zero-lambda behavior, sigmoid-at-zero values, and non-increasing scores under the penalty update.

## Limitations
This skill supplies only the regularizer component; task loss and score masks must be handled by other skills.
