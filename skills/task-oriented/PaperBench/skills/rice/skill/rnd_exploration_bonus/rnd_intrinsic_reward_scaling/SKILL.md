---
name: rnd_intrinsic_reward_scaling
description: Scale Random Network Distillation intrinsic rewards with running discounted-return statistics for stable exploration bonuses.
---

# RND Intrinsic Reward Scaling

Use this skill when raw RND prediction errors need to become an intrinsic reward stream for policy optimization. It preserves raw errors for diagnostics while dividing rewards by a running estimate of intrinsic-return standard deviation. Do not use it to change the predictor loss itself.

## Inputs
- Raw RND prediction-error sequence.
- Intrinsic discount factor, usually `gamma_I`.
- Optional running return statistics.

## Outputs
- Scaled intrinsic rewards.
- Discounted intrinsic returns.
- Updated running scale statistics.

## Workflow
1. Convert raw errors into discounted intrinsic returns.
2. Update running mean/variance over those returns.
3. Divide each raw error by `sqrt(var + eps)`.
4. Keep both raw and scaled values in recovery logs.

## Validation
Run `python scripts/reward_scaling.py --self-test`. The validation checks finite outputs, discounted-return ordering, and positive scaling behavior.

## Limitations
This skill does not compute policy gradients or PPO advantages. It only implements the RND reward-scale contract from the paper.
