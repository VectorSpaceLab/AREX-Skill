---
name: recovery_evaluation_harness
description: Run and evaluate a bounded agreement-on-the-line proxy recovery with source-boundary and mechanism checks.
---

# Recovery Evaluation Harness

Use this skill to turn generated ALine-D predictions into executable recovery evidence. It chains the generated input, statistics, line-fit, and estimator skills and computes MAE only after the estimator has produced predictions.

## Inputs

- Raw prediction-table JSON with hidden OOD labels for evaluation.
- Generated skills root.
- Work directory for intermediate artifacts.

## Outputs

- Evaluation JSON with MAE percent, per-model errors, and mechanism checks.
- Intermediate validated table, statistics, line fit, and ALine-D estimate artifacts.

## Workflow

1. Validate the prediction table and separate OOD labels.
2. Compute agreement statistics without OOD labels.
3. Fit the agreement line.
4. Solve ALine-D.
5. Compute true OOD accuracies and MAE using hidden labels only after prediction.
6. Serialize mechanism checks for recovery validation.

## Validation

Run `python tests/test_recovery_evaluation_harness.py` from this skill directory.

## Limitations

This skill evaluates proxy or reduced recovery evidence; it does not download full benchmark model testbeds.
