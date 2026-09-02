---
name: speed_ratio_replay_diagnostics
description: Compute speed-ratio and replay-overwrite diagnostics for massively parallel off-policy Q-learning configurations.
---

# Speed Ratio Replay Diagnostics

Use this skill when configuring or reviewing PQL under high actor throughput. It estimates whether replay is overwritten too quickly and whether actor, policy, or value learners are imbalanced. It is not a replacement for benchmark training curves, but it provides mechanism evidence for recovery and ablation runs.

## Inputs

- `num_envs`: positive integer parallel environment count.
- `rollout_steps`: positive integer actor steps per collection tick.
- `replay_capacity`: positive integer transition capacity.
- `actor_rate`, `policy_rate`, `value_rate`: positive relative rates.

## Outputs

- `transitions_per_tick`.
- `replay_refresh_ticks`.
- `actor_to_value_ratio` and `policy_to_value_ratio`.
- Warning labels for overwrite pressure and update imbalance.

## Workflow

1. Compute incoming transition volume from environments and rollout steps.
2. Estimate how many collection ticks refresh the replay buffer.
3. Normalize actor and policy rates by value-learning rate.
4. Flag high overwrite pressure when replay refresh is very small.
5. Flag learner imbalance when policy or actor rates dominate value updates.

## Validation

Run:

```bash
python scripts/diagnostics.py --num-envs 10000 --rollout-steps 1 --replay-capacity 1000000 --actor-rate 10000 --policy-rate 1 --value-rate 100
python tests/test_diagnostics.py
```

## Limitations

The thresholds are diagnostic heuristics. Real tuning still requires task-level evaluation returns and wall-clock measurements.
