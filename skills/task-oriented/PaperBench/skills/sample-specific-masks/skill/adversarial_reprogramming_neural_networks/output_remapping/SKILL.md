---
name: output_remapping
description: Aggregate frozen target model outputs into adversarial task labels using one-to-one or many-to-one mappings.
---

# Target-to-Adversarial Label Remapping

Use this skill when a recovery must implement the paper's `h_g` mapping from original target-model classes to attacker-task classes. It is appropriate for logits or probabilities. Do not use it as a learned classifier head; the mapping is fixed during program optimization.

## Inputs
- `scores`: original target-model logits or probabilities.
- `mapping`: dictionary from adversarial labels to lists of original class indices.
- `reducer`: `sum` or `mean` for many-to-one aggregation.

## Outputs
- Aggregated adversarial-task scores.
- Deterministic predicted adversarial label.
- Mapping validation metadata.

## Workflow
Validate that mapped labels are in range, aggregate each label group, then choose the label with maximum aggregate score using lexical label order for ties.

## Validation
Run `python tests/test_output_remapping.py`.

## Limitations
This skill does not choose semantic ImageNet labels; it implements and validates a supplied mapping.
