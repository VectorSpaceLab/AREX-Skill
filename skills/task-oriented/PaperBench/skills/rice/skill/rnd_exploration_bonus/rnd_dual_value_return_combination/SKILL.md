---
name: rnd_dual_value_return_combination
description: Compute separate extrinsic and intrinsic return streams for Random Network Distillation dual-value-head policy optimization.
---

# RND Dual Value Return Combination

Use this skill when implementing the RND paper's combination of episodic extrinsic rewards and potentially non-episodic intrinsic rewards. It is appropriate for PPO-style recovery harnesses or tests that need to verify return boundaries. Do not collapse the streams before return computation when the intrinsic stream is non-episodic.

## Inputs
- Extrinsic reward sequence and done flags.
- Intrinsic reward sequence.
- `gamma_E` and `gamma_I`.
- A flag selecting non-episodic intrinsic returns.

## Outputs
- Extrinsic returns for the extrinsic value head.
- Intrinsic returns for the intrinsic value head.
- Combined value target equal to the elementwise sum.

## Workflow
1. Compute extrinsic discounted returns while resetting at episode boundaries.
2. Compute intrinsic returns with either non-episodic continuation or episodic reset, as configured.
3. Keep the two return targets separate for value-head losses.
4. Sum the two value estimates only when forming the combined value target.

## Validation
Run `python scripts/dual_returns.py --self-test`. The test checks that a done flag resets extrinsic returns but does not reset non-episodic intrinsic returns.

## Limitations
This skill does not implement the PPO clipped objective. It defines the return/value-head contract that a PPO implementation should consume.
