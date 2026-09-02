---
name: induction_head_detector
description: Detect induction-head copying behavior on repeated token sequences with explicit mechanism checks.
---

# Induction Head Detector

Use this skill when testing whether an attention pattern or simplified circuit implements the induction-head algorithm `[a][b] ... [a] -> [b]`. It is especially useful for Transformer Circuits style recovery experiments on repeated random-token sequences. Do not count positions with no previous occurrence as induction successes.

## Inputs

- A token sequence as strings or ids.
- Optional policy for selecting the earlier matching source; the default is the most recent previous occurrence.
- Optional expected next tokens or labels.

## Outputs

- Applicable positions where a previous occurrence and successor token exist.
- Predicted next tokens copied from the earlier successor.
- Accuracy on applicable positions.
- Mechanism checks: previous-token shift, same-token matching, OV copying assumption, and repeated-token prediction.

## Workflow

1. Iterate over destination positions except the final position.
2. Find earlier source positions whose token equals the destination token and that have a successor.
3. Select the most recent matching source.
4. Predict the token after that source.
5. Compare with the actual next token and summarize accuracy.

## Validation

Run the included tests or the Paper2Skills skill-tree validator with `--run-tests`.

## Limitations

This skill validates the behavioral core of induction heads. For a trained model, pair it with QK/K-composition and OV-copying evidence from the relevant matrices.
