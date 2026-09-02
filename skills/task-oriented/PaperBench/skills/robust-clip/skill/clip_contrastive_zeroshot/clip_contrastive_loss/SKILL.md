---
name: clip_contrastive_loss
description: Compute CLIP-style normalized similarity logits and symmetric contrastive loss for image-text batches.
---

# CLIP Contrastive Loss

Use this skill when implementing or checking the CLIP training mechanism on paired image/text embeddings. It is appropriate for full, reduced, or synthetic recovery if the result is clearly labeled.

## Inputs
- Equal-length image and text embedding batches.
- A positive logit scale, corresponding to inverse temperature.

## Outputs
- Scaled cosine-similarity logits.
- Image-to-text and text-to-image cross entropy.
- Average symmetric loss and top-1 retrieval accuracy.

## Workflow
1. Normalize each image and text feature vector.
2. Compute all pairwise dot products and multiply by the logit scale.
3. Use diagonal indices as positives for both image-to-text and text-to-image directions.
4. Average the two cross-entropy losses and report retrieval accuracy.

## Validation
Run `python tests/test_contrastive_loss.py` or the generated skill tree validator.

## Limitations
This skill operates on supplied embeddings. It does not implement the visual or text transformer encoders.
