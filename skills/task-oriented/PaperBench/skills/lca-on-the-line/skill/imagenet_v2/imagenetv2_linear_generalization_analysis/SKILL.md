---
name: imagenetv2_linear_generalization_analysis
description: Fit and inspect original-vs-new ImageNetV2 accuracy relationships for rank preservation and linear generalization gaps.
---

# ImageNetV2 Linear Generalization Analysis

Use this skill after model accuracies are available on original and new datasets. It captures the paper's observation that accuracies drop while model rankings remain close to linear rather than showing diminishing returns from adaptivity.

## Inputs
- JSON list of model records with `model`, `original_accuracy`, and `new_accuracy`.

## Outputs
- Least-squares slope and intercept.
- Mean accuracy gap.
- Pairwise rank agreement.

## Workflow
1. Load model accuracy pairs.
2. Fit `new_accuracy = slope * original_accuracy + intercept`.
3. Compute average original-minus-new gap.
4. Compute pairwise rank agreement between original and new accuracies.

## Validation
Run `python scripts/linear_fit.py tests/fixtures/model_pairs.json --output /tmp/fit.json`.

## Limitations
This skill summarizes metric pairs; it does not explain image-level causes of the gap.
