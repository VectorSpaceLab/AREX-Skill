---
name: bounded_pruning_recovery
description: Run a bounded soft-mode recovery experiment for EL2N/GraNd data pruning with executable mechanism evidence.
---

# Bounded Pruning Recovery

Use this skill when full CIFAR/ResNet retraining is infeasible but soft-mode recovery allows a declared reduced/proxy experiment. The experiment must still run the core paper mechanism: compute early EL2N scores from model probabilities, retain high-score examples, prune low-score examples, and execute a real optimizer step.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated `early_example_scoring` and `score_based_subset_selection` skill directories.
- Output recovery directory.

## Outputs
- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- Generated skill invocation records suitable for the Distiller gate.

## Workflow
1. Build a deterministic small supervised classification dataset inside the attempt.
2. Train a tiny standard-library softmax classifier for bounded steps.
3. Compute class probabilities and invoke the scoring skill to produce EL2N scores.
4. Invoke the selection skill to retain the high-score half.
5. Measure selected-minus-pruned mean EL2N gap.
6. Run and log an optimizer step with before/after loss and parameters.
7. Save mechanism checks distinguishing proxy execution from full CIFAR/ResNet execution.

## Validation
Run the recovery harness, then run Distiller's recovery validator:

```bash
python recovery/run_recovery.py
python <distiller>/recover-paper/scripts/validate_recovery_experiment.py <attempt_dir> --output <attempt_dir>/recovery/experiment_validation.json
```

## Limitations
- This is not a full paper reproduction unless CIFAR/ResNet data and training are explicitly used.
- Full-runtime flags must remain false for standard-library proxy runs.
