---
name: pairwise_similarity_preservation
description: Compute DDPM-PA pairwise cosine-softmax distributions and adapted-to-source KL preservation loss.
---

# Pairwise Similarity Preservation

Use this skill when implementing the DDPM-PA relative-distance preservation term. It compares the geometry of source and adapted generated samples by converting pairwise cosine similarities into per-anchor probability distributions and minimizing KL divergence.

Do not use this skill to compare images to target training images directly. It preserves relative geometry between source and adapted predictions, while target-detail matching belongs to the high-frequency module.

## Inputs

- Source samples or features shaped as a batch of equally shaped numeric vectors, images, or nested lists.
- Adapted samples or features with identical batch size and compatible flattened dimension.
- Optional numerical epsilon and softmax temperature.

## Outputs

- Per-anchor source distributions over non-self samples.
- Per-anchor adapted distributions over non-self samples.
- Scalar KL preservation loss using `KL(p_adapted || p_source)`.

## Workflow

1. Flatten each batch element and L2-normalize it with epsilon protection.
2. Compute cosine similarities for every ordered anchor/neighbor pair.
3. Exclude self-pairs before softmax.
4. Convert similarities to probability distributions.
5. Sum or average adapted-to-source KL divergence across anchors.
6. Return diagnostics so recovery can prove self-pair exclusion and finite loss.

## Validation

Run:

```bash
python scripts/pairwise_loss.py --smoke
python -m pytest tests
```

The tests check zero loss for identical geometry, positive loss for changed geometry, and no self-index in neighbor lists.

## Limitations

The included implementation is deterministic and standard-library only. For tensor frameworks, keep the same anchor-wise exclusion and KL direction; changing either changes the paper mechanism.
