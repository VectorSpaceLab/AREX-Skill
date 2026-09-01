---
name: pruning_recovery_harness
description: Run a bounded end-to-end proxy recovery for generalization-influence dataset pruning using generated module skills.
---

# Pruning Recovery Harness

Use this skill when the full CIFAR-scale paper experiment is blocked or too expensive and soft-mode recovery permits a declared reduced proxy. The harness must invoke or cross-check the generated influence, pruning, and bound-check skills and produce executable recovery evidence.

## Inputs

- Attempt directory with `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing the other module skills.
- Output paths for recovery logs and result JSON.

## Outputs

- `recovery_result.json`-compatible object with metrics and mechanism checks.
- Training trace with `params_before` and `params_after`.
- Generated data item and skill invocation logs.

## Workflow

1. Build a deterministic tiny binary-classification dataset.
2. Use the influence skill to estimate per-example parameter influences.
3. Use the aggregate pruning skill to remove the largest feasible subset.
4. Train one logistic-regression update on the retained data and log loss/parameter changes.
5. Use the gap-bound skill to validate target metadata, aggregate influence, and observed gap.
6. Write recovery artifacts under the current attempt.

## Validation

Run `python scripts/run_proxy_recovery.py --help` and the recovery experiment validator on the attempt after execution.

## Limitations

The proxy is mechanism-faithful but not a full CIFAR reproduction. It must be labeled `is_proxy: true` and must not claim full model or full dataset execution.
