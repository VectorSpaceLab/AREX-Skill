---
name: rnd_bonus_model
description: Compute Random Network Distillation novelty bonuses from frozen deterministic target features and trainable predictor mean-squared error.
---

# RND Bonus Model

Use this skill when implementing the core Random Network Distillation exploration bonus. It applies when observations have already been normalized and the experiment needs intrinsic rewards from predictor error against a fixed random target. Do not use this for forward-dynamics prediction; RND predicts a deterministic function of the current observation.

## Inputs
- Normalized observation vectors.
- A deterministic target feature map or target parameters that remain frozen.
- Predictor parameters and a learning rate.

## Outputs
- Per-sample squared prediction errors for intrinsic reward.
- Mean predictor loss.
- Updated predictor parameters after gradient descent.
- Checksums or copied parameters proving the target stayed fixed.

## Workflow
1. Build a seeded random target map and a separately initialized predictor.
2. Compute target features and predictor features for the same normalized observations.
3. Compute MSE and update only predictor parameters.
4. Use the detached per-sample errors as intrinsic rewards.
5. Log target-parameter equality before and after training when recovery uses this skill.

## Validation
Run `python scripts/rnd_model.py --self-test`. The test trains a tiny linear predictor, verifies loss decreases, and verifies target parameters remain unchanged.

## Limitations
The included script is a deterministic linear RND implementation for reduced recovery and regression tests. Larger neural policies may replace the linear predictor while preserving the frozen-target and MSE contracts.
