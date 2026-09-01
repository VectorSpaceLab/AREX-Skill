---
name: clip_contrastive_objective
description: Compute CLIP-style normalized image/text similarity and symmetric InfoNCE loss for paired multimodal embeddings.
---

# CLIP Contrastive Objective

Use this skill when implementing or checking the core CLIP training mechanism: paired image/text embeddings, L2 normalization, temperature-scaled cosine logits, and symmetric InfoNCE loss.

## Inputs
- Image embedding matrix and text embedding matrix with equal batch size.
- Positive pairs aligned by row index.
- Positive `logit_scale`.

## Outputs
- Normalized embeddings, logits, symmetric loss, and diagnostics.

## Workflow
1. Reject mismatched batches, empty matrices, zero vectors, or non-positive logit scale.
2. Normalize each row to unit length.
3. Compute `logits = logit_scale * image_norm @ text_norm.T`.
4. Compute cross-entropy for image-to-text and text-to-image directions.
5. Average the two losses and report diagonal separation diagnostics.

## Validation
Run `python tests/test_contrastive_objective.py`.

## Limitations
A tiny batch confirms the mechanism but is not full-scale distributed CLIP pretraining.

## Cycle 3 normalization ablation

Stress checks include unequal embedding magnitudes to confirm L2 normalization makes the contrastive mechanism scale-invariant before logits are computed.
