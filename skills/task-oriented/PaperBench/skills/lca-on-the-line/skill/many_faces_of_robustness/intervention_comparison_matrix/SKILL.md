---
name: intervention_comparison_matrix
description: Compare robustness interventions across clean and shifted metrics using direction-aware evidence signs.
---

# Intervention Comparison Matrix

Use this skill to summarize robustness interventions in the style of the paper's tables: each method is compared against a baseline on clean and shifted metrics, and improvements are interpreted according to whether the metric is error or accuracy.

## Inputs
- A list of metric rows with an `intervention` name and dataset metric values.
- The baseline intervention name.
- Metric direction: lower-is-better for error, higher-is-better for accuracy.

## Outputs
- Direction-aware deltas for each intervention and dataset.
- Evidence signs showing improvement, regression, or tie.
- The best shifted intervention when the target dataset is supplied.

## Workflow
1. Locate the baseline row.
2. For every intervention, compute signed improvements for available datasets.
3. Mark missing values as unavailable rather than zero.
4. Report the strongest intervention for the chosen shifted metric and whether the clean/shift gap narrows.

## Validation
Run `python tests/test_matrix.py` or the Distiller tree validator.

## Limitations
This skill analyzes metric tables; it does not judge whether the datasets themselves are representative.
