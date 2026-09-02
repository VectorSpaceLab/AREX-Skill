---
name: recovery_evaluation
description: Evaluate Tent recovery artifacts for numeric metrics, source-boundary compliance, and mechanism-faithful proxy evidence.
---

# Recovery Evaluation and Mechanism Checks

Use this skill after running a Tent recovery experiment. It is appropriate for full CIFAR/ImageNet recovery and for soft-mode reduced recovery. Do not accept a proxy solely because an accuracy value is high; the trace must show target-only entropy adaptation, changed modulation parameters, and executable evidence.

## Inputs

- `recovery_result.json` with paper target, metrics, commands, and mechanism checks.
- `training_trace.json` with losses and parameter values before and after adaptation.
- `source_manifest.json` and generated skill invocation logs.
- `module_plan.json` fast recovery target.

## Outputs

- A validation report with `ok`, metric gaps, mechanism failures, and recommended decision.
- Human-readable feedback for analysis artifacts.

## Workflow

1. Verify source manifests do not include original repository paths.
2. Confirm recovery target metadata matches the module plan target.
3. Check that at least one numeric metric is present.
4. For proxy runs, require mechanism checks for target-only adaptation, entropy loss, normalization-affine update, and optimizer execution.
5. Compare `loss_before` and `loss_after`, plus `params_before` and `params_after`.
6. Recommend `accept` only when executable evidence and mechanism checks pass.

## Validation

Run `python scripts/evaluate_recovery.py --self-test`. The self-test checks a valid proxy trace and an invalid unchanged-parameter trace.

## Limitations

This evaluator complements, but does not replace, Distiller's recovery experiment validator. Always run both in final recovery.


## Refinement Cycle 4
An unchanged-parameter ablation produced a refine decision; proxy acceptance must require parameter or optimizer-state change, not metric text alone.
