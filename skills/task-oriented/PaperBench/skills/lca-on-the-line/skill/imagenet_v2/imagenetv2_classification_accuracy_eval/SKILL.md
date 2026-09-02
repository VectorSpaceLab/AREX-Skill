---
name: imagenetv2_classification_accuracy_eval
description: Compute ImageNetV2-style top-k accuracy and drops from sampled candidate records with labels and ranked predictions.
---

# ImageNetV2 Classification Accuracy Evaluation

Use this skill when sampled ImageNetV2-style records need top-1/top-5 metrics or an accuracy drop relative to an original validation metric.

## Inputs
- Sample JSON with records containing `label` and ranked `predictions`.
- Optional original accuracy baseline.

## Outputs
- `top1`, `top5`, sample count, and optional drop.

## Workflow
1. Load sampled records.
2. Count whether the true label is ranked first for top-1.
3. Count whether the true label appears in the first five predictions for top-5.
4. Compute drops as `original_accuracy - new_accuracy`.

## Validation
Run `python scripts/evaluate_accuracy.py tests/fixtures/sample.json --original-top1 0.75 --output /tmp/metrics.json`.

## Limitations
This skill consumes precomputed predictions; it does not run a vision model.
