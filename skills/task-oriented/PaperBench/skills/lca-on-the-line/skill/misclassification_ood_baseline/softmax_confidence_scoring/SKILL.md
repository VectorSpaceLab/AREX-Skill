---
name: softmax_confidence_scoring
description: Compute maximum softmax probability detector scores from logits or probabilities for misclassification and OOD detection.
---

# Maximum Softmax Probability Scoring

Use this skill when a recovery or evaluation task needs the Hendrycks-Gimpel baseline score: the predicted class probability from a classifier softmax distribution. Do not use it as a calibration method or as evidence that a probability equals true confidence.

## Inputs
- A JSON list of numeric vectors, either logits or already-normalized probability vectors.
- Optional mode: `logits`, `probabilities`, or `auto`.

## Outputs
- One record per example with `predicted_class` and `msp`.
- Optional aggregate summary with mean MSP.

## Workflow
1. Validate that every row is non-empty and finite.
2. Convert logits with a max-subtracted stable softmax.
3. In `auto` mode, accept rows as probabilities only when non-negative and summing to one within tolerance.
4. Return the argmax class and its probability.
5. Pass these MSP values to a detection metric skill rather than thresholding by hand unless a threshold is explicitly requested.

## Validation
Run `python tests/test_msp.py` or validate the full skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not train classifiers, load image datasets, or estimate calibrated uncertainty. It only implements the paper baseline scoring primitive.
