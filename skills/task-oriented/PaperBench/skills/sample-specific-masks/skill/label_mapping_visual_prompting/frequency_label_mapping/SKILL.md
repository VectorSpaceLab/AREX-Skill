---
name: frequency_label_mapping
description: Build deterministic one-to-one target-to-source label mappings from source prediction frequencies.
---

# Frequency Label Mapping

Use this skill when a visual prompting pipeline must map target classes to source classes using top-1 source prediction frequencies. It implements the FLM lower-level mapping used before prompt training and inside ILM-VP.

## Inputs
- Predictions or logits grouped by target label.
- Ordered target labels and source labels.

## Outputs
- Target-to-source mapping.
- Frequency/count table.
- Audit entries for tie-breaking, duplicate exclusion, and fallbacks.

## Workflow
1. Convert logits to top-1 source labels when needed.
2. Count source labels for each target class.
3. In target-label order, choose the most frequent unused source label.
4. Break ties by supplied source-label order.
5. If no unused source labels remain, emit a duplicate warning.

## Validation
Run `python tests/test_frequency_label_mapping.py` or `validate_skill_tree.py --run-tests`.

## Limitations
FLM optimizes mapping frequency, not semantic quality. Use mapping diagnostics to explain whether selected labels are interpretable.
