---
name: tecoa_adversarial_feature_attack
description: Generate bounded text-conditioned adversarial feature perturbations for reduced TeCoA robustness recovery.
---

# TeCoA Adversarial Feature Attack

Use this skill when a recovery experiment needs a bounded adversarial perturbation that attacks image-text contrastive matching. It is a feature-level reduced proxy for the paper's image-space PGD when full CLIP gradients are unavailable.

Do not use this skill as evidence of full image-space robustness unless the caller provides a real differentiable image encoder and records that stronger runtime separately. In soft-mode recovery, mark its outputs as feature-level proxy evidence.

## Inputs

- `image_embeddings`: clean image feature matrix.
- `text_embeddings`: text feature matrix.
- `labels`: target text indices.
- `epsilon`: Linf perturbation bound.
- `step_size`: finite-difference attack step scale.
- `steps`: positive number of projected attack steps.

## Outputs

- `adversarial_embeddings`: perturbed features.
- `delta`: perturbation matrix.
- `loss_trace`: loss after each attack step.
- `bound_checks`: maximum absolute perturbation and whether the Linf bound passed.

## Workflow

1. Validate non-negative epsilon, positive step size, and positive steps.
2. Copy clean image embeddings so the caller's inputs are not mutated.
3. Estimate a finite-difference gradient of the TeCoA contrastive loss with respect to each feature coordinate.
4. Ascend in the sign direction, project to the Linf epsilon ball, and repeat.
5. Return a trace and bound checks for recovery validation.

## Validation

Run `tests/test_feature_attack.py` or validate this skill with the Distiller module skill validator and `--run-tests`.

## Limitations

This implementation is intentionally tiny and deterministic. It exercises the TeCoA adversarial mechanism without requiring torch, CLIP, ImageNet, or GPU access.
