---
name: pruning_recovery_harness
description: Compose generated pruning modules into an auditable no-retraining recovery experiment with mechanism checks.
---

# Pruning Recovery Harness

Use this skill when validating a recovery of the fast post-training Transformer pruning paper. The harness must call generated Fisher search, rearrangement, and mask tuning skills, then write validator-compatible recovery artifacts. It is appropriate for full BERT/GLUE recovery or a declared soft-mode proxy. Do not use the original paper repository during recovery.

## Inputs

- Attempt directory with `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing the three core module skills.
- Optional synthetic or real calibration data.

## Outputs

- `recovery/recovery_result.json` with numeric metrics and mechanism checks.
- `recovery/logs/generated_skill_invocations.json`.
- Source manifest and command logs.

## Workflow

1. Read the module target and handoff blockers.
2. Select the strongest feasible target and declare proxy status.
3. Import generated skill helpers and run search, rearrangement, and tuning in order.
4. Check budget, mask-cardinality preservation, objective non-increase, tuning improvement, zero pruned entries, and no retraining.
5. Compute mechanism pass rate and save auditable JSON.

## Validation

Run recovery's experiment gate after the harness command.

## Coverage invariant

The invocation log must include every core generated module claimed by the proxy, and missing modules must fail validation rather than be treated as not applicable.
