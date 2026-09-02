---
name: tecoa_text_contrastive_objective
description: Compute TeCoA image-to-text contrastive logits, loss, margins, and accuracy for robustness recovery.
---

# TeCoA Text Contrastive Objective

Use this skill when image and text embeddings must be scored according to the TeCoA objective. It implements the paper's cross-modal supervision contract: adversarial visual features should align with the correct text embeddings under normalized cosine logits.

Do not use this skill to generate adversarial perturbations or update model parameters. It is a deterministic scoring module consumed by attack and recovery harnesses.

## Inputs

- `image_embeddings`: numeric matrix with shape `[batch, dim]`.
- `text_embeddings`: numeric matrix with shape `[classes, dim]`.
- `labels`: integer target text index for each image row.
- `temperature`: positive scalar, default `0.07`.

## Outputs

- `logits`: cosine logits divided by temperature.
- `loss`: mean image-to-text cross-entropy.
- `accuracy`: top-1 image-to-text accuracy.
- `margins`: correct logit minus best wrong logit for each row.
- `mean_margin`: average margin.

## Workflow

1. Validate matrix dimensions, non-zero vectors, label range, and temperature.
2. L2-normalize image and text embeddings row-wise.
3. Compute image-to-text logits.
4. Compute cross-entropy, top-1 accuracy, and margins.
5. Return JSON-serializable metrics so recovery can compare clean, adversarial, and adapted states.

## Validation

Run the tests in `tests/test_contrastive_objective.py` or the Distiller skill-tree validator with `--run-tests`.

## Limitations

This skill uses Python standard-library math for portability. It is intended for deterministic reduced/proxy checks and numeric cross-checks, not high-throughput CLIP training.
