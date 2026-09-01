---
name: c2st_metric_evaluation
description: Compute a deterministic classifier two-sample accuracy proxy for comparing posterior sample distributions.
---

# C2ST Metric Evaluation

Use this skill when a recovery experiment must compare reference posterior samples and approximate posterior samples with a C2ST-style distributional metric. The score is an accuracy where 0.5 indicates indistinguishable distributions.

## Inputs
- Sample JSON containing `reference_samples` and `approximate_samples`.
- Optional threshold and seed.

## Outputs
- Metric JSON with `c2st_accuracy`, mean-distance diagnostics, and pass/fail flag.

## Workflow
1. Validate non-empty sample matrices with equal dimensions.
2. Z-score both groups using reference-sample statistics.
3. Build a deterministic linear-threshold classifier from the difference of group means.
4. Report balanced classification accuracy and whether it is near the reference target.

## Validation
Run the included tests or validate the tree with `validate_skill_tree.py --run-tests`.

## Limitations
This script is a lightweight deterministic proxy for bounded recovery; the paper used an MLP classifier with cross-validation for full benchmark results.
