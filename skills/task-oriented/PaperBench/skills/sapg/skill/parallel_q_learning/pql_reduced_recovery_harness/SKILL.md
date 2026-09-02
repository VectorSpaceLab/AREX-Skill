---
name: pql_reduced_recovery_harness
description: Run a mechanism-faithful reduced Parallel Q-Learning proxy experiment with replay, mixed exploration, and optimizer evidence.
---

# PQL Reduced Recovery Harness

Use this skill when full Isaac Gym reproduction is blocked but soft-mode recovery allows a declared reduced proxy. The run must still exercise PQL's core mechanism: many actors, mixed exploration, replay sampling, separate value and policy updates, and numeric training evidence. Do not use it to claim full benchmark reproduction.

## Inputs

- Paths to generated PQL topology, mixed exploration, and diagnostics skills.
- Actor count, rollout length, replay capacity, learning rates, and random seed.
- Module-plan target metadata for populating recovery results.

## Outputs

- Training trace with `loss_before`, `loss_after`, `params_before`, and `params_after`.
- Mechanism checks for actor coverage, mixed exploration, replay use, and optimizer execution.
- Numeric proxy metrics such as `loss_reduction` and final return estimate.

## Workflow

1. Import the topology, mixed exploration, and diagnostics helpers.
2. Build a scalar-control task where reward is highest near a target action.
3. Use many actors with round-robin mixed exploration to collect replay transitions.
4. Fit a simple critic parameter toward Bellman-style rewards.
5. Update a policy parameter toward the critic-implied target.
6. Record every parameter change and emit recovery-compatible JSON artifacts.

## Validation

Run:

```bash
python scripts/reduced_pql.py --actor-count 32 --rollout-steps 4 --updates 8 --output-dir /tmp/pql_reduced_check
python tests/test_reduced_pql.py
```

## Limitations

The scalar environment is a reduced proxy. It validates PQL mechanism contracts and executable recovery evidence, not the paper's Isaac Gym returns or wall-clock speedups.
