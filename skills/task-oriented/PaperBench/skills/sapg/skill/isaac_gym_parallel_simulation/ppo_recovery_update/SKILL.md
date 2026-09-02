---
name: ppo_recovery_update
description: Run a deterministic PPO style clipped scalar update over batched rollout evidence for recovery validation.
---

# PPO Recovery Update

Use this skill when an Isaac Gym recovery needs proof that batched rollout data fed a real trainable update. The skill implements a tiny deterministic PPO-style clipped surrogate over scalar log-probability shifts. Do not use it as a full RL algorithm or as evidence of the paper's full robotics scores.

## Inputs
- Old log probabilities, advantages, scalar policy parameter, clip epsilon, learning rate.
- Optional finite-difference epsilon.

## Outputs
- Loss before and after, parameter before and after, and optimizer-state-change evidence.

## Workflow
1. Compute clipped surrogate loss over the batch.
2. Estimate the scalar gradient by finite differences.
3. Apply one gradient-descent update.
4. Report whether the parameter and loss changed.

## Validation
Run `python tests/test_ppo_update.py` or validate this skill tree with tests enabled.

## Limitations
This is a reduced scalar update for mechanism recovery. It is not a replacement for Isaac Gym's full PPO implementation.
