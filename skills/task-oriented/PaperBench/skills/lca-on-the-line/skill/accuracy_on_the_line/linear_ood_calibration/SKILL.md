---
name: linear_ood_calibration
description: Fit and inspect linear calibration between in-distribution and out-of-distribution accuracies.
---

# Linear OOD Calibration

Use this skill after paired accuracy records have been validated. It implements the paper mechanism that OOD accuracy often lies on a line as ID accuracy varies across model variants.

## Inputs

- Validated records containing `model_id`, `id_accuracy`, and `ood_accuracy`.
- Optional residual threshold for interpreting fit quality.

## Outputs

- Least-squares slope and intercept mapping ID accuracy to OOD accuracy.
- Pearson correlation, mean absolute residual, and per-model predictions/residuals.
- A deterministic JSON summary suitable for recovery logs.

## Workflow

1. Extract paired ID/OOD arrays in deterministic record order.
2. Fit ordinary least squares with OOD accuracy as the dependent variable.
3. Compute Pearson correlation and residuals.
4. Return numeric evidence without deciding whether a soft-mode proxy is acceptable.
5. Use residuals to inspect weak-shift or outlier behavior.

## Validation

Run `python scripts/fit_accuracy_line.py --input <validated_records.json>` or run the included tests through `validate_skill_tree.py --run-tests`.

## Limitations

This skill does not validate input records, choose the dataset, or claim full paper reproduction. It assumes records already obey the pair protocol.
