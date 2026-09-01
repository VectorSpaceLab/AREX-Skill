---
name: prediction_table_contracts
description: Validate agreement-on-the-line prediction tables while separating estimator inputs from evaluation-only OOD labels.
---

# Prediction Table Contracts

Use this skill when preparing inputs for agreement-on-the-line or ALine-D recovery experiments. Do not use it for probability-score methods that require softmax confidences rather than class predictions.

## Inputs

- JSON table with `models`, `id_labels`, `id_predictions`, `ood_predictions`, and optional `ood_labels`.
- At least three models are required for ALine-D.

## Outputs

- Normalized JSON table with deterministic model ordering.
- Metadata for model/sample counts and a flag showing OOD labels are evaluation-only.

## Workflow

1. Validate unique model identifiers and consistent prediction lengths.
2. Require every model to have ID and OOD class predictions.
3. Store optional OOD labels under `evaluation_only`.
4. Reject attempts to treat OOD labels as estimator-visible fields.

## Validation

Run `python tests/test_prediction_table_contracts.py` from this skill directory.

## Limitations

This skill validates table structure only; it does not compute agreement statistics or accuracy predictions.
