---
name: entropy_adaptation_step
description: Run and validate Tent-style entropy minimization updates on unlabeled target batches with trainable modulation parameters.
---

# Entropy-Minimizing Adaptation Step

Use this skill to implement the core Tent update in a recovery harness or small experiment. It is appropriate when the adaptation loss is mean softmax entropy on unlabeled target logits and at least one trainable modulation parameter is updated. Do not use it as a pseudo-labeling method or as evidence if no optimizer state or parameter value changes.

## Inputs

- Target batch features or a model callable producing logits.
- Trainable adaptation parameters, usually normalization affine scale and shift.
- Learning rate and number of steps.
- Optional labels for post-adaptation evaluation only, never for loss computation.

## Outputs

- Entropy before and after adaptation.
- Parameter values before and after adaptation.
- Predictions before and after adaptation.
- Mechanism flags showing entropy loss and optimizer execution.

## Workflow

1. Compute logits and mean softmax entropy on the target batch.
2. Backpropagate or analytically compute the entropy gradient for the trainable parameters.
3. Apply the declared optimizer update.
4. Clear or record gradient state.
5. Recompute logits, entropy, and predictions after the update.
6. Save trace fields `params_before`, `params_after`, `loss_before`, and `loss_after`.

## Validation

Run `python scripts/tent_step.py --self-test`. The deterministic self-test uses a tiny two-class target batch and verifies entropy reduction plus changed scale/bias parameters.

## Limitations

The included script is a standard-library proxy for deterministic recovery when PyTorch or real datasets are unavailable. For full recovery, apply the same objective and trace contract to the actual model runtime.
