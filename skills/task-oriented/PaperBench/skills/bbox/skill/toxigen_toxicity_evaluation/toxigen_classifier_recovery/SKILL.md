---
name: toxigen_classifier_recovery
description: Run a bounded ToxiGen-style classifier update and report validator-compatible before-after loss, AUC, and parameter evidence.
---

# ToxiGen Classifier Recovery

Use this skill when a recovery experiment needs to demonstrate the paper's classifier-improvement mechanism without full HateBERT or RoBERTa fine-tuning. It trains a tiny logistic classifier over deterministic text features and emits before/after metrics.

Do not use this skill to claim full paper Table 4 reproduction. A result from this skill is a reduced proxy unless it is replaced by a real model fine-tuning stack.

## Inputs

- Generated or curated examples with `text` and `label`.
- Optional group and generation method metadata.
- Learning rate and update-step count.

## Outputs

- `loss_before`, `loss_after`, `auc_before`, `auc_after`.
- `params_before`, `params_after`, and `optimizer_state_changed`.
- Per-example probabilities before and after the update.

## Workflow

1. Extract deterministic features from each text: bias/toxicity cue count, benign cue count, identity cue count, and normalized length.
2. Initialize logistic weights and bias to zero unless supplied.
3. Compute binary cross-entropy and pairwise AUC.
4. Run bounded gradient-descent updates.
5. Recompute metrics and emit a trace with parameter-change evidence.

## Validation

Run:

```bash
python scripts/classifier_recovery.py --self-test
python tests/test_classifier_recovery.py
```

The tests verify that parameters change and that loss does not increase on a simple fixture.

## Limitations

This skill is intentionally small and deterministic. It is useful for mechanism-faithful soft recovery, edge-case tests, and harness validation, not for reporting deployed toxicity classifier performance.
