---
name: policies-and-customization
description: "Customize Stable-Baselines3 policies, feature extractors,
  Dict-observation policies, exploration noise, gSDE, and HER replay buffers
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Policies and Customization

Use this sub-skill when an SB3 task involves `policy_kwargs`, policy aliases, custom PyTorch policy modules, `BaseFeaturesExtractor`, `MultiInputPolicy`, action noise, generalized State-Dependent Exploration (gSDE), or `HerReplayBuffer`.

## Routes

- For `net_arch`, `activation_fn`, policy aliases, optimizer kwargs, and policy save/load persistence, read [policy-customization](references/policy-customization.md).
- For custom `BaseFeaturesExtractor`, image preprocessing, `CombinedExtractor`, `MultiInputPolicy`, and Dict observations, read [feature-extractors](references/feature-extractors.md).
- For `NormalActionNoise`, `OrnsteinUhlenbeckActionNoise`, vectorized noise, and gSDE constraints, read [noise-and-exploration](references/noise-and-exploration.md).
- For Hindsight Experience Replay setup, goal-env requirements, and the legacy `HER()` import error, read [her-and-replay-buffers](references/her-and-replay-buffers.md).
- For common failures and fast diagnosis checklists, read [troubleshooting](references/troubleshooting.md).

## Safe Inspection

Run the bundled script to instantiate a tiny model without learning and print the resolved policy, spaces, device, and architecture summary:

```bash
python sub-skills/policies-and-customization/scripts/inspect_policy.py --algorithm PPO --policy MlpPolicy
python sub-skills/policies-and-customization/scripts/inspect_policy.py --algorithm DQN --policy MultiInputPolicy --dict-env
python sub-skills/policies-and-customization/scripts/inspect_policy.py --algorithm SAC --policy MlpPolicy --action-noise normal --use-sde
```

The script uses safe defaults, supports `--help`, and trains only when `--train-steps` is explicitly set above zero.

## Boundaries

- Use the environment/vectorization sibling for environment checker, wrappers, vector env, and `Dict` space validation beyond policy choice.
- Use the training/algorithms sibling for choosing PPO vs DQN vs SAC/TD3/DDPG and algorithm-specific learning schedules.
- Use the evaluation/persistence sibling for evaluation loops and save/load workflows; this sub-skill only notes policy customization persistence and custom-object pitfalls.
