---
name: ewc_penalty
description: Compute Elastic Weight Consolidation's Fisher-weighted quadratic penalty, gradient, and additive multi-task quadratic terms.
---

# EWC Penalty

Use this skill when training a new task after estimating previous-task Fisher importance. It implements the paper equation `lambda / 2 * sum(F_i * (theta_i - theta_star_i)^2)` and the matching gradient.

## Inputs

- Current parameters `theta`.
- Previous optimum `theta_star`.
- Diagonal Fisher vector `fisher`.
- EWC multiplier `lambda_value`.

## Outputs

- Scalar EWC penalty.
- Gradient contribution to add to the new-task gradient.
- Optional summed penalty over multiple previous anchors.

## Workflow

1. Validate matching vector dimensions and nonnegative Fisher entries.
2. Compute parameter deltas from the old optimum.
3. Apply the paper's `lambda / 2` penalty scaling.
4. Add the gradient `lambda * fisher * delta` to the task-B gradient.
5. Sum penalties for multiple previous tasks when needed.

## Validation

Run:

```bash
python tests/test_ewc_penalty.py
```

## Limitations

This skill computes the consolidation term only. It must be combined with a task-specific loss in a training harness.
