---
name: coherence_recovery_evaluation
description: Evaluate coherence boosting recovery metrics and source-boundary mechanism checks for proxy experiments.
---

# Coherence Recovery Evaluation

Use this skill after predictions have been produced by coherence boosting skills. It computes baseline and boosted metrics and records mechanism checks for reduced/proxy recovery.

## Inputs
- Labels, baseline predictions, boosted predictions, selected alpha, and invocation metadata.
- A list of source paths used during recovery.

## Outputs
- Accuracy metrics and `accuracy_gain_over_full_context`.
- Mechanism checks for full/short separation, alpha selection, no finetuning, and source-boundary compliance.

## Workflow
1. Compute exact accuracy for baseline and boosted predictions.
2. Compute the gain over the full-context baseline.
3. Verify no source path contains the original repository path marker.
4. Emit booleans suitable for `recovery_result.json`.

## Validation
Run `tests/test_recovery_evaluation.py`.

## Limitations
This skill validates the recovery evidence; it does not claim full paper-scale reproduction unless the runtime evidence supports it.
