---
name: ppo_recovery_evaluation
description: Validate reduced PPO recovery results for target consistency, source-boundary compliance, numeric metrics, and mechanism-faithful proxy evidence.
---

# PPO Recovery Evaluation

## When To Use

Use this skill after a PPO recovery harness has produced a result and trace. It is especially useful in soft mode, where a reduced proxy may be acceptable only if it exercises PPO's clipped-ratio mechanism.

Do not use it to replace the Distiller recovery experiment validator; use it as a PPO-specific cross-check.

## Inputs

- `module_plan.json` with `fast_recovery_target`.
- `recovery_result.json` or equivalent result object.
- `source_manifest.json` or equivalent source list.
- Optional generated-skill invocation log.

## Outputs

JSON with `ok`, `errors`, `warnings`, target-match status, metric summary, and source-boundary status.

## Workflow

1. Compare recovery `paper_target` against `module_plan.fast_recovery_target`.
2. Confirm all metrics are numeric.
3. Confirm required mechanism checks are true for proxy recovery.
4. Confirm source manifest does not include the original repository path.
5. Confirm generated core skills were invoked or cross-checked.
6. Return actionable errors if any requirement fails.

## Validation

Run:

```bash
python tests/test_recovery_evaluation.py
python scripts/evaluate_recovery.py --module-plan path/to/module_plan.json --recovery-result path/to/recovery_result.json --source-manifest path/to/source_manifest.json
```

## Limitations

This skill checks artifact consistency and mechanism evidence. It does not independently rerun training.
