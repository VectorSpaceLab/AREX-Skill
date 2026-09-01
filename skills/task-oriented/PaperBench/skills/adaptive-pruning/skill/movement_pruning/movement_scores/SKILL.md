---
name: movement_scores
description: Update movement-pruning importance scores from weight gradients and diagnose whether weights move away from zero.
---

# Straight-Through Movement Score Updates

Use this skill when a pruning or recovery harness needs the core first-order movement-pruning update. Do not use it as a generic magnitude pruning score; its purpose is to accumulate task fine-tuning movement.

## Inputs
- `weights`: numeric list or nested list.
- `scores`: same shape as weights.
- `gradients`: same shape, representing `dL/dW`.
- `lr_score`: score learning rate.
- Optional `lr_weight` for diagnostics of the associated SGD weight update.

## Outputs
Updated scores and per-parameter diagnostics including `score_delta`, `away_from_zero`, and `movement_label`.

## Workflow
1. Flatten and shape-check weights, scores, and gradients.
2. Compute the straight-through score gradient `grad_s = grad_w * weight`.
3. Apply gradient descent `score_new = score - lr_score * grad_s`.
4. Label weights as moving away from zero when an SGD step would increase absolute value.
5. Return updated scores in the original shape.

## Validation
Run `python tests/test_movement_scores.py`. Tests cover all sign combinations of weight and gradient and confirm scores increase exactly for away-from-zero movement.

## Limitations
This skill does not compute model gradients; callers must supply gradients from their training objective.
