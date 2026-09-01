---
name: rnd_normalization_streams
description: Maintain RND observation whitening/clipping and intrinsic reward scaling statistics.
---

# RND Normalization Streams

Use this skill when preparing observations or intrinsic rewards for RND. Do not use it to normalize policy-network observations unless the experiment explicitly chooses that; the paper normalizes predictor/target inputs.

## Inputs

- Numeric observation batches.
- Intrinsic reward or intrinsic-return batches.
- Epsilon and clip bounds.

## Outputs

- Running mean, variance, and count.
- Whitened and clipped observations.
- Reward values scaled by running return standard deviation.

## Workflow

1. Initialize running statistics from early random-agent or synthetic preflight observations.
2. Update statistics with each new batch using a numerically stable batch merge.
3. Normalize observations with `(x - mean) / std` and clip to `[-5, 5]` by default.
4. Scale intrinsic rewards by reward/return standard deviation with epsilon protection.

## Validation

Run `python tests/test_normalization.py` from this skill directory.

## Limitations

This skill provides deterministic numeric helpers, not a distributed RL statistics service.
