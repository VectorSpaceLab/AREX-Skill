---
name: bar_recovery_evaluation
description: Produce validator-ready BAR recovery metrics and mechanism checks for full or declared reduced black-box reprogramming experiments.
---

# BAR Recovery Evaluation

Use this skill at the end of a BAR recovery run to turn predictions, labels, training traces, runtime blockers, and generated-skill invocation evidence into an auditable recovery result.

Do not use it to justify a proxy experiment that did not run masked embedding, multi-label mapping, and a black-box query-only optimization step.

## Inputs

- Predictions and labels.
- Training trace with `params_before`, `params_after`, `loss_before`, and `loss_after`.
- Module-plan fast recovery target.
- Runtime blockers and source-boundary notes.

## Outputs

- Accuracy and loss improvement.
- Mechanism checks for BAR components.
- A recovery-result dictionary compatible with `validate_recovery_experiment.py`.

## Workflow

1. Compute accuracy from predictions and labels.
2. Check that parameters changed when an optimizer step is claimed.
3. Check loss-before/loss-after fields and query count.
4. Mark reduced/proxy booleans explicitly when full medical-data recovery is unavailable.
5. Copy target metadata from `module_plan.json.fast_recovery_target` so the recovery target cannot drift.

## Validation

Run `python tests/test_recovery_evaluation.py` or `validate_skill_tree.py --run-tests`.

## Limitations

This skill evaluates evidence; it does not run BAR training by itself and cannot rescue missing executable command logs.
