---
name: jsrl_recovery_evaluation
description: Evaluate Jump-Start Reinforcement Learning recovery evidence with mechanism checks for guide roll-in, curriculum handoff, value update, and proxy metric validity.
---

# JSRL Recovery Evaluation

## When To Use

Use this skill after a JSRL experiment has run and produced trajectories, training traces, and metrics. It is especially useful in soft-mode reduced recovery, where final scores alone are not enough to prove mechanism faithfulness.

## Inputs

- Module plan target containing dataset, metric, and paper value.
- Recovery metrics for JSRL, vanilla exploration, and optional random switching.
- Trajectory summaries with controller labels.
- Training trace with loss and parameter changes.
- Source-boundary and generated-skill invocation evidence.

## Outputs

- Primary metric such as `success_rate_gain`.
- Mechanism checks for guide use, exploration handoff, curriculum decrease, value update, random ablation, and source-boundary safety.
- Feedback flags for analysis.

## Workflow

1. Confirm recovery metadata matches the module-plan target.
2. Compute JSRL success-rate gain over vanilla exploration.
3. Verify at least one trajectory contains both guide and exploration controllers.
4. Verify curriculum guide steps decrease or the random ablation samples a schedule.
5. Verify the value-update trace changed trainable parameters.
6. Mark reduced recovery explicitly and never label a Q-table proxy as full D4RL/IQL/QT-Opt training.

## Validation

Run:

```bash
python scripts/evaluate_recovery.py --demo
python -m pytest tests
```

The demo emits a compact metric/mechanism bundle.

## Limitations

This skill evaluates evidence; it does not run the environment itself. Recovery harnesses should invoke it after executing the rollout and update skills.
