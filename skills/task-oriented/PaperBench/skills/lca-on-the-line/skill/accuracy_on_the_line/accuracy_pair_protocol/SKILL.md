---
name: accuracy_pair_protocol
description: Validate paired ID/OOD accuracy records before fitting accuracy-on-the-line calibration experiments.
---

# Accuracy Pair Protocol

Use this skill when a recovery or benchmark script needs to build the paired in-distribution and out-of-distribution accuracy panel used by Accuracy on the Line. Do not use it to fit the line or decide whether the proxy passes; it only owns record validation and deterministic ordering.

## Inputs

- A JSON list of objects with `model_id`, `id_accuracy`, and `ood_accuracy`.
- Optional metadata fields such as architecture, training duration, or shift name.

## Outputs

- A JSON object containing validated `records`, `count`, `id_range`, `ood_range`, and `provenance`.
- Validation errors for missing fields, duplicate model ids, nonnumeric accuracies, or values outside `[0, 1]`.

## Workflow

1. Parse records from JSON or receive them as Python dictionaries.
2. Require one paired ID and OOD accuracy for every model id.
3. Enforce numeric ranges and unique model ids.
4. Sort records by `model_id` so downstream line fitting is reproducible.
5. Preserve optional metadata without adding predictions or pass/fail decisions.

## Validation

Run `python scripts/accuracy_pairs.py --input tests/fixtures/valid_pairs.json` or validate the tree with the Distiller `validate_skill_tree.py --run-tests` command.

## Limitations

This skill does not download datasets, train models, fit the calibration line, or evaluate a recovery target. Synthetic records must be labeled by the caller as proxy evidence.
