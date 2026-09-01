---
name: detection_metric_protocol
description: Compute AUROC and AUPR detection metrics with paper-faithful score orientations for softmax confidence baselines.
---

# Threshold-Independent Detection Metrics

Use this skill when evaluating maximum-softmax-probability detectors for misclassification or out-of-distribution examples. It implements the paper convention of reporting AUROC and AUPR rather than choosing a single threshold.

## Inputs
- Binary labels where `1` is the positive detector class.
- Numeric scores where larger means more likely positive.
- Optional metadata naming the protocol, such as `success`, `error`, `in`, or `out`.

## Outputs
- `auroc`, `aupr`, `base_rate`, counts, and sorted ranking diagnostics.

## Workflow
1. Choose score orientation before calling the metric: MSP for success/in-distribution positive, negative MSP for error/out-of-distribution positive.
2. Compute AUROC as pairwise positive-vs-negative ranking probability with half credit for ties.
3. Compute average precision by scanning descending scores and averaging precision at positive ranks.
4. Report the positive base rate so AUPR can be compared to the random baseline.

## Validation
Run `python tests/test_metrics.py` or validate the full skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not infer labels or generate scores. It assumes the caller has already created paper-faithful positive labels and score orientation.
