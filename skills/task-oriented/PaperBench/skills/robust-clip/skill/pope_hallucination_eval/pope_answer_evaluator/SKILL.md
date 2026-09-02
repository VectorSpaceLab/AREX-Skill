---
name: pope_answer_evaluator
description: Normalize POPE yes/no answers and compute object hallucination classification metrics.
---

# POPE Answer Evaluator

Use this skill after an LVLM or deterministic answer source has answered POPE polling questions. It converts raw answer text into binary yes/no predictions and computes the paper's standard metrics.

Do not use this skill to generate POPE questions or choose absent objects. It assumes labels already come from a POPE question file.

## Inputs

- Ordered answer records with an `answer` string.
- Ordered label/question records with `label` equal to `yes` or `no`.
- Optional output path for metrics JSON.

## Outputs

- Normalized predictions.
- TP, FP, TN, FN.
- Accuracy, precision, recall, F1 score, and yes ratio.
- Per-example records for auditing answer normalization.

## Workflow

1. Pair answer and label records by order.
2. Keep only the first sentence-like segment of each raw answer.
3. Strip commas and split words.
4. Mark the prediction as `no` if the first segment contains `no`, `No`, or `not`; otherwise mark it as `yes`.
5. Convert labels to binary values and compute confusion counts.
6. Compute metrics with safe zero-division handling.
7. Save the metrics and normalized prediction log.

## Validation

Run:

```bash
python scripts/pope_answer_evaluator.py --self-test
python tests/test_answer_evaluator.py
```

The tests cover sentence-form answers, negation, confusion counts, F1, and yes ratio.

## Limitations

This is repository-compatible normalization and may classify unusual answers conservatively as `yes` unless explicit negation is present. If a project needs stricter invalid-answer handling, record that policy separately.