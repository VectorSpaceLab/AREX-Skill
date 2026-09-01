---
name: flan_heldout_instruction_evaluator
description: Evaluate held-out direct and CoT instruction examples, compute accuracy delta, and emit FLAN recovery mechanism checks.
---

# FLAN Held-Out Instruction Evaluator

Use this skill after an instruction-finetuning run to measure held-out generalization.

## Inputs

- Held-out examples and predictions before/after finetuning.
- Mixture audit, training trace, and target metadata.

## Outputs

- Accuracy before/after/delta and mechanism checks.

## Workflow

1. Check held-out ids are absent from training ids.
2. Compute exact-match accuracy before and after.
3. Emit mechanism checks for CoT, optimizer, and target matching.

## Validation

Run `python tests/test_evaluator.py`.

## Limitations

Supports deterministic proxy metrics, not full benchmark evaluation.
