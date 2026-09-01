---
name: agreement_statistics
description: Compute ID accuracy, pairwise ID/OOD agreement, and clipped probit statistics for agreement-on-the-line experiments.
---

# Agreement Statistics

Use this skill after a prediction table has been validated. It preserves the paper's estimator boundary by computing OOD agreement from predictions only and never using OOD labels.

## Inputs

- Normalized prediction table from `prediction_table_contracts`.
- Optional clipping epsilon for probit transforms.

## Outputs

- Per-model ID accuracies.
- Pairwise ID and OOD agreement fractions.
- Probit-transformed accuracies and agreements.

## Workflow

1. Compute ID accuracy from ID labels and ID predictions.
2. Compute unordered pairwise agreement on ID predictions.
3. Compute unordered pairwise agreement on OOD predictions.
4. Clip probabilities before inverse-normal transformation.

## Validation

Run `python tests/test_agreement_statistics.py` from this skill directory.

## Limitations

This skill does not fit the agreement line or solve ALine-D.
