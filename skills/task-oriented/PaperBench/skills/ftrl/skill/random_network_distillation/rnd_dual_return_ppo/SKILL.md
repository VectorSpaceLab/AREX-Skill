---
name: rnd_dual_return_ppo
description: Compute separate intrinsic and extrinsic discounted returns for RND-style PPO with dual value heads.
---

# RND Dual Return PPO

Use this skill when combining RND intrinsic rewards with task extrinsic rewards under separate value heads. Do not collapse streams before return calculation when their discount factors or episode-boundary semantics differ.

## Inputs

- Extrinsic rewards, intrinsic rewards, and done flags.
- Extrinsic and intrinsic discount factors.
- Boolean flag indicating whether intrinsic returns are non-episodic.
- Optional extrinsic and intrinsic value estimates.

## Outputs

- Extrinsic discounted returns.
- Intrinsic discounted returns.
- Separate and combined advantages.

## Workflow

1. Compute extrinsic returns with episode termination resets.
2. Compute intrinsic returns with either episodic or non-episodic semantics.
3. Subtract stream-specific value estimates to get stream advantages.
4. Sum stream advantages for policy optimization while training value heads separately.

## Validation

Run `python tests/test_dual_returns.py` from this skill directory.

## Limitations

This skill implements the reward-stream contract, not a full PPO optimizer.
