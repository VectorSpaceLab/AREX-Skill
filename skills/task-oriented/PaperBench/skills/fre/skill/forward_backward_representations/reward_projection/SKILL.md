---
name: reward_projection
description: Project late-specified rewards into backward representation coordinates for immediate FB policy adaptation.
---

# Reward Projection

Use this skill after an FB backward embedding has been learned and a reward is specified later. It should not update the reward-free embeddings or run new task-specific RL.

## Inputs

- Backward embeddings `B` indexed by state or goal.
- Reward observations as `{index, reward}` records or a sparse goal index.

## Outputs

- Task vector `z_R` as the weighted sum or average of backward embeddings.
- Provenance describing which reward entries contributed.

## Workflow

1. Validate that all reward indices exist in `B`.
2. Compute `z_R = sum_g B(g) r(g)` for explicit finite rewards.
3. Preserve multi-goal rewards by summing their weighted backward vectors.
4. Return diagnostics and never mutate `F` or `B`.

## Validation

Run `python scripts/project_reward.py --self-test`. The test checks sparse and composite rewards.

## Limitations

For continuous goals this reduced script expects sampled reward observations rather than integrals over an unknown density.
