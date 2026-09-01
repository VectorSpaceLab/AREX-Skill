---
name: rnd_intrinsic_reward
description: Compute and test Random Network Distillation intrinsic rewards from predictor error against a fixed deterministic target feature map.
---

# RND Intrinsic Reward

Use this skill when implementing or auditing an RND novelty bonus. Do not use it for forward-dynamics curiosity or stochastic target prediction.

## Inputs

- Observation vectors as JSON arrays or Python lists of floats.
- Fixed target parameters and trainable predictor parameters.
- Optional normalized observations from a separate normalizer.

## Outputs

- Per-observation mean squared prediction errors used as intrinsic rewards.
- Distillation loss over a batch.
- Updated predictor parameters when training is requested.

## Workflow

1. Keep target parameters immutable for the whole experiment.
2. Compute target and predictor features from the same observation batch.
3. Use mean squared error across feature dimensions as intrinsic reward.
4. Train only predictor parameters on visited observations.
5. Validate novelty by comparing trained/visited error with held-out rare-state error.

## Validation

Run `python tests/test_rnd_intrinsic_reward.py` from this skill directory.

## Limitations

The included script is a deterministic linear RND proxy for bounded recovery and tests; large Atari recovery still needs a full neural policy/runtime.
