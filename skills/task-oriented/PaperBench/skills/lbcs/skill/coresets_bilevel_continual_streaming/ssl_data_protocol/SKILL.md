---
name: ssl_data_protocol
description: Construct deterministic semi-supervised splits with labeled, validation, unlabeled, pseudo-label, and per-example weight fields for SSL recovery experiments.
---

# Semi-supervised Data Protocol

Use this skill when a recovery or experiment needs the data contract from Ren, Yeh, and Schwing 2020: labeled training examples, unlabeled training examples, validation examples, pseudo-labels, and one persistent non-negative weight per unlabeled example.

Do not use this skill to evaluate final test accuracy or to tune model parameters directly. Its output is a protocol object consumed by influence-weight and recovery modules.

## Inputs
- Labeled examples with feature vectors and labels.
- Validation examples with feature vectors and labels.
- Unlabeled examples with feature vectors and stable ids.
- Optional model parameters used to create pseudo-labels.

## Outputs
- JSON-compatible dictionaries with `labeled`, `validation`, and `unlabeled` lists.
- Each unlabeled item has `id`, `x`, `pseudo_label`, and `weight` fields.
- A `weight_state` dictionary keyed by unlabeled id.

## Workflow
1. Validate that all three splits are non-empty and ids are unique across unlabeled examples.
2. Generate deterministic pseudo-labels from a linear score when model parameters are supplied; otherwise use a sign-threshold policy.
3. Initialize every unlabeled weight to the requested non-negative value.
4. Return the split object without embedding downstream final metrics or control markers.

## Validation
Run `python tests/test_protocol.py` or validate through `validate_skill_tree.py --run-tests`.

## Limitations
This skill intentionally creates tiny deterministic splits for mechanism checks. Full benchmark data loading belongs in a separate dataset-specific adapter.
