---
name: multi_label_mapping
description: Construct and apply BAR multi-label mappings that average groups of source-model probabilities into target-label probabilities.
---

# Multi-label Mapping

Use this skill when a source classifier has a different label space from the target task and BAR-style adversarial reprogramming needs a deterministic mapping from source labels to target labels.

Do not use it when the source model already exposes the target label space directly.

## Inputs

- Source confidence rows or logits for each sample.
- Integer target labels.
- Number of source labels assigned to each target label.
- Optional frequency-based construction mode.

## Outputs

- Mapping `{target_label: [source_label_indices]}`.
- Mapped target probabilities computed by averaging source probabilities in each group.

## Workflow

1. Normalize each source output row if it is not already a probability vector.
2. For fixed mappings, validate non-empty non-overlapping source groups.
3. For frequency mapping, rank source labels by class-conditioned mean confidence and greedily assign unused labels to target classes.
4. Compute each target probability as the average of its mapped source probabilities.
5. Renormalize mapped probabilities before focal or cross-entropy loss if required.

## Validation

Run `python tests/test_multi_label_mapping.py` or `validate_skill_tree.py --run-tests`.

## Limitations

The paper used ImageNet-scale label spaces. This skill provides the reusable mapping logic and deterministic reduced-test behavior; it does not provide a pretrained source classifier.
