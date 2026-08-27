---
name: training-and-algorithms
description: "Choose and train Stable-Baselines3 algorithms, instantiate
  A2C/PPO/DQN/SAC/TD3/DDPG, handle action-space compatibility, and run short CPU
  smoke training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Algorithms

Use this sub-skill when an agent needs to select an SB3 algorithm, construct a model, call `learn()`, tune basic rollout/replay parameters, or run a short safe training smoke test.

## Route by Need

- For algorithm choice and action-space compatibility, read [Algorithm Selection](references/algorithm-selection.md).
- For constructor-to-`learn()` workflows, short training snippets, `train_freq`, `gradient_steps`, gSDE, and action noise, read [Training Workflows](references/training-workflows.md).
- For verified public exports, policy aliases, constructor parameters, and `learn()` notes, read [API Reference](references/api-reference.md).
- For common training failures and warning diagnosis, read [Troubleshooting](references/troubleshooting.md).
- For a minimal CPU smoke command, run [`scripts/train_smoke.py`](scripts/train_smoke.py) with `--help` first.

## Boundaries

- Custom environment validation, `check_env()`, wrappers, `make_vec_env()`, and render-mode setup belong in `environments-and-vectorization`.
- Evaluation callbacks, saving/loading, model persistence, and deployment-style prediction loops belong in `evaluation-and-persistence`.
- Deep custom policy classes, feature extractors, network architecture design, and `policy_kwargs` internals belong in `policies-and-customization`.
