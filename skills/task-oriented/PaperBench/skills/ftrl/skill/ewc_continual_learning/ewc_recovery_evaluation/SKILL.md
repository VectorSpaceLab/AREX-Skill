---
name: ewc_recovery_evaluation
description: Run a bounded EWC retention recovery comparison and emit validator-compatible result, trace, and mechanism-check artifacts.
---

# EWC Recovery Evaluation

Use this skill to execute a reduced or full sequential-training comparison for Elastic Weight Consolidation. It should be used after task protocol, Fisher importance, and EWC penalty skills are available.

## Inputs

- Protocol JSON with task order and datasets.
- Generated skill root containing `ewc_task_protocol`, `ewc_fisher_importance`, and `ewc_penalty`.
- Module-plan target metadata.
- Output paths for recovery artifacts.

## Outputs

- `recovery_result.json` with numeric retention metrics and mechanism checks.
- `training_trace.json` with before/after loss and parameter values.
- Skill invocation evidence proving generated modules were used.

## Workflow

1. Fit task A and snapshot parameters.
2. Estimate a diagonal Fisher from task-A gradients.
3. Train task B with plain SGD and with EWC.
4. Compare task-A retention and Fisher-weighted drift.
5. Save command-produced recovery artifacts.

## Validation

Run:

```bash
python tests/test_recovery_evaluation.py
```

## Limitations

The bundled harness is a reduced synthetic proxy. It does not claim full permuted-MNIST or Atari reproduction.
