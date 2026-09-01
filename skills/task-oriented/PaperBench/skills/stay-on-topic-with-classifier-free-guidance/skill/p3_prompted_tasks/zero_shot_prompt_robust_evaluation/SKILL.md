---
name: zero_shot_prompt_robust_evaluation
description: Compute held-out prompted-task accuracy and prompt wording consistency for T0/P3-style recovery experiments.
---

# Zero-Shot and Prompt-Robust Evaluation

Use this skill after a model or proxy predictor has produced predictions for held-out prompted examples. It measures correctness and robustness across alternative templates for the same raw item.

## Inputs
- Prediction records with `example_id`, `template_id`, `prediction`, and `target`.

## Outputs
- Overall accuracy, per-template accuracy, and same-example prompt consistency.

## Workflow
1. Compare canonical prediction and target strings for exact-match accuracy.
2. Group records by template id for per-prompt diagnostics.
3. Group records by example id and measure whether all prompt variants produce the same prediction.
4. Return JSON-serializable metrics and counts.

## Validation
Run included deterministic metric tests.

## Limitations
This skill does not generate predictions; it only evaluates records already produced by an experiment.
