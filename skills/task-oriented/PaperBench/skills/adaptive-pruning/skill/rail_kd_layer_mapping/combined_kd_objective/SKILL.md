---
name: combined_kd_objective
description: Combine supervised, output distillation, and RAIL intermediate losses with validated RAIL-KD lambda weights.
---

# Combined KD Objective

Use this skill when constructing a RAIL-KD training or proxy recovery objective. It preserves the paper's equation (4): the student minimizes a weighted sum of supervised task loss, output-logit knowledge distillation loss, and the randomized intermediate representation loss. Do not use this skill as a replacement for computing the RAIL representation loss itself.

## Inputs

- `ce_loss`: finite scalar for supervised cross-entropy/task loss.
- `kd_loss`: finite scalar for output prediction distillation.
- `rail_loss`: finite scalar from RAIL-KDl or RAIL-KDc.
- `lambdas`: three non-negative weights `(lambda1, lambda2, lambda3)` that sum to one.

## Outputs

- Total scalar objective.
- Weighted contribution dictionary for audit logs.
- Validation status or an exception for invalid inputs.

## Workflow

1. Validate that all loss components are finite numeric scalars.
2. Validate that all lambda weights are non-negative and sum to one within tolerance.
3. Compute the total weighted objective.
4. Return component contributions so recovery can report what the optimizer minimized.

## Validation

Run:

```bash
python scripts/kd_objective.py --ce 0.4 --kd 0.3 --rail 0.2 --lambdas 0.2 0.3 0.5
python -m pytest tests
```

## Limitations

This skill computes scalar composition only. Production training code still needs a differentiable implementation for framework tensors, but the same validation and contribution reporting should be preserved.
