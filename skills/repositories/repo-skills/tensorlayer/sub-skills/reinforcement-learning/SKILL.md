---
name: reinforcement-learning
description: "Routes TensorLayer reinforcement-learning utilities and tutorial workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Reinforcement Learning

Use this sub-skill for TensorLayer reward utilities, action sampling, and RL tutorial guidance. This is the route for RL helper functions and reference tutorials that sit around the core model APIs.

## Typical requests

- Discount episode rewards.
- Sample an action from a probability distribution.
- Inspect DQN or Q-learning tutorial structure.
- Understand what TensorLayer's RL examples require from Gym or related extras.

## Read first

- `references/rl-reference.md` for the utility surface and tutorial notes.
- `references/workflows.md` for tiny reward-discount and action-sampling patterns.
- `references/troubleshooting.md` for Gym, stochasticity, and long-running-example issues.

## Bundled check

- `scripts/smoke_rl.py` verifies deterministic reward discounting and a simple action-selection path.

## Boundaries

Include here:
- `tensorlayer.rein`
- RL reward and action helpers
- RL tutorial guidance and dependency notes

Exclude or route elsewhere:
- core layer/model definitions -> `core-modeling`
- supervised training loops and CLI help -> `training-and-cli`
- preprocessing, TFRecord, and iteration helpers -> `data-and-utilities`
- text, seq2seq, or vision workflows -> `text-and-sequence` / `vision-and-apps`

## Fast path

1. Decide whether the user needs a utility function or a full RL tutorial reference.
2. Keep Gym-based tutorials reference-only unless the user explicitly requests the extra runtime stack.
3. Use the smoke script to verify the reward helpers before opening the longer tutorials.
