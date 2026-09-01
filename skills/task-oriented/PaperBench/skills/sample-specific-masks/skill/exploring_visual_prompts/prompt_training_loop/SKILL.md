---
name: prompt_training_loop
description: Optimize only universal visual prompt parameters while frozen model components remain unchanged.
---

# Frozen-Model Prompt Training Loop

Use this skill when a recovery or implementation must demonstrate the paper's central adaptation mechanism: the model is frozen and only a shared visual prompt is optimized with cross-entropy. It is not for fine-tuning, linear probing, or per-image adversarial perturbation.

## Inputs
- A frozen model or differentiable proxy that maps prompted examples to logits.
- Prompt parameters initialized once for the task.
- Training examples and labels.
- Learning-rate and step-count settings.

## Outputs
- Updated prompt parameters.
- A trace containing loss before and after optimization.
- Invariant checks showing frozen weights did not change.

## Workflow
1. Evaluate the unprompted or initial-prompt loss.
2. Compute cross-entropy gradients with respect to prompt parameters only.
3. Apply SGD or a recorded optimizer update to the prompt.
4. Re-evaluate loss and task metric.
5. Record `params_before`, `params_after`, `loss_before`, `loss_after`, and frozen-parameter checks.

## Validation
A tiny logistic proxy test verifies that one or more prompt updates reduce loss and leave frozen weights unchanged.

## Limitations
The helper script is intentionally scalar and lightweight for deterministic validation. Real CLIP recovery can replace the gradient provider while preserving the same contracts.
