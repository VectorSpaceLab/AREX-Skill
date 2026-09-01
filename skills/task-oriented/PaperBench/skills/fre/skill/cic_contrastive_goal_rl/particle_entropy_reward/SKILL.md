---
name: particle_entropy_reward
description: Estimate CIC intrinsic reward using k-nearest-neighbor particle entropy over learned transition embeddings.
---

# Particle Entropy Reward

Use this skill when a CIC-style recovery or implementation needs the entropy-based intrinsic reward over state-transition embeddings. Do not use this skill to compute the contrastive loss or downstream task reward.

## Inputs

- `embeddings`: two-dimensional transition embedding matrix.
- `k`: number of nearest neighbors to average, clamped to `batch_size - 1`.
- `epsilon`: positive distance stabilizer before logarithms.

## Outputs

- `rewards`: per-transition intrinsic reward values based on average log nearest-neighbor distances.
- `diagnostics`: min, max, mean reward, effective `k`, and neighbor distances.

## Workflow

1. Validate a batch of at least two embedding vectors.
2. Compute pairwise Euclidean distances.
3. Exclude self-distances from neighbor lists.
4. Select the nearest `k` neighbors for each point.
5. Average `log(distance + epsilon)` as the intrinsic reward.
6. Use reward diagnostics to verify finite, diverse exploration signal.

## Validation

Run:

```bash
python scripts/entropy_reward.py --demo
python tests/test_entropy_reward.py
```

## Limitations

This skill implements the reward estimator only. It does not interact with an RL environment or train a policy.
