---
name: deberta_sift_finetuning
description: Run deterministic SiFT style normalized perturbation and optimizer traces for DeBERTa reduced recovery evidence.
---

# DeBERTa SiFT Fine-Tuning

Use this skill when a recovery needs to demonstrate the paper's scale-invariant fine-tuning idea without mutating a shared environment or requiring deep learning libraries. The helper normalizes vectors, applies bounded perturbations, and performs a real scalar optimizer update that can be logged in `training_trace.json`.

## Inputs

- Numeric feature vector or scalar features for a candidate.
- Trainable parameters.
- Gold target or desired margin.
- Perturbation scale and learning rate.

## Outputs

- Normalized feature vector.
- Perturbed feature vector.
- Loss before and after the update.
- `params_before` and `params_after` suitable for Distiller reduced-recovery validation.

## Workflow

1. Normalize the feature vector with `scripts/sift_finetuning.py`.
2. Apply a deterministic perturbation to the normalized vector.
3. Compute logistic classification loss.
4. Update trainable parameters by gradient descent.
5. Record whether the optimizer state or parameters changed.

## Validation

Run the skill-tree validator with tests. The tests verify stable normalization, bounded perturbation, numeric loss, and parameter changes after one optimizer step.

## Limitations

This skill is a reduced SiFT mechanism probe. It is not full adversarial training of a DeBERTa model and must be marked as reduced recovery when used without the real model stack.
