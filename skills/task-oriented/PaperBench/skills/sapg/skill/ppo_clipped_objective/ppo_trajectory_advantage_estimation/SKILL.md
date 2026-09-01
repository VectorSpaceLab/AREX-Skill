---
name: ppo_trajectory_advantage_estimation
description: Compute bootstrapped returns and generalized advantage estimates for fixed-horizon PPO rollout batches.
---

# PPO Trajectory Advantage Estimation

## When To Use

Use this skill when a PPO recovery or implementation has a fixed-horizon rollout segment and needs advantages and returns before optimizing the surrogate objective.

Do not use it to update policy parameters or evaluate the clipped surrogate directly.

## Inputs

- `rewards`: non-empty numeric reward sequence.
- `value_predictions`: value estimate for each reward timestep.
- `terminal_flags`: booleans or 0/1 markers where true means the transition ended an episode.
- `next_value_prediction`: bootstrap value after the segment.
- `gamma`: discount factor.
- `gae_lambda`: trace parameter.

## Outputs

JSON containing `advantages`, `returns`, `normalized_advantages`, and summary statistics.

## Workflow

1. Validate rollout arrays have equal length.
2. Append the bootstrap value to the value sequence.
3. Iterate backward over the segment.
4. Mask continuation at terminal boundaries.
5. Compute `delta = reward + gamma * next_value * nonterminal - value`.
6. Compute `gae = delta + gamma * lambda * nonterminal * next_gae`.
7. Return `returns = advantages + values` and safely normalized advantages.

## Validation

Run:

```bash
python tests/test_advantage_estimation.py
python scripts/estimate_advantages.py --rewards '[1,1]' --values '[0.5,0.25]' --terminals '[false,true]' --next-value 0 --gamma 0.99 --gae-lambda 0.95
```

## Limitations

The skill assumes rewards and values have already been sampled by a policy. It does not construct environments or perform policy optimization.
