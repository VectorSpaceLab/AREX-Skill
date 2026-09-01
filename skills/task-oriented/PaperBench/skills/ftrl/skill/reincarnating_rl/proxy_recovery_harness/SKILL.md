---
name: proxy_recovery_harness
description: Run a reduced executable QDagger recovery experiment with generated-skill invocations, training traces, and mechanism checks.
---

# Proxy Recovery Harness

## When To Use

Use this skill when full Atari-scale reincarnating RL is blocked by runtime, checkpoint, or data availability, and soft-mode reduced recovery is permitted. The harness validates QDagger's mechanism with a deterministic tabular proxy. Do not present its metric as a full Atari result.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing `qdagger_loss` and `weaning_schedule`.
- Optional output directory for recovery artifacts.

## Outputs

- `generated_data_item.json`: proxy replay and teacher-policy data.
- `training_trace.json`: loss, parameter, schedule, and optimizer-step evidence.
- `recovery_result.json`: proxy metric and mechanism checks.
- `generated_skill_invocations.json`: evidence that generated module skills were imported/called.

## Workflow

1. Load the generated QDagger loss and weaning schedule helpers by path.
2. Construct a tiny teacher replay and student replay batch.
3. Compute pre-update loss with positive teacher coefficient.
4. Estimate finite-difference gradients over tabular Q-values and apply one optimizer step.
5. Recompute post-update loss and a later decayed coefficient.
6. Write validator-compatible recovery artifacts.

## Validation

Run:

```bash
python scripts/run_proxy_recovery.py --self-test
python tests/test_proxy_recovery_harness.py
```

## Limitations

The harness is a reduced mechanism-faithful proxy. It proves executable QDagger mechanics but not paper-scale ALE performance.
