---
name: reinforcement-learning
description: "Operate ML-From-Scratch DeepQNetwork CartPole workflows, model
  builders, replay memory, epsilon decay, and Gym compatibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# reinforcement-learning

Use this sub-skill when the task is specifically about ML-From-Scratch's `DeepQNetwork` workflow: CartPole setup, Gym compatibility, model-builder callbacks, replay memory, epsilon-greedy behavior, `train`, or `play`/render behavior.

## Route first

- For the DQN lifecycle, use [`references/workflows.md`](references/workflows.md).
- For Gym/NumPy compatibility, reset/step API drift, render/display failures, and state/action shape errors, use [`references/troubleshooting.md`](references/troubleshooting.md).
- For a bounded non-rendering smoke check, run [`scripts/run_dqn_smoke.py`](scripts/run_dqn_smoke.py).
- For layer, optimizer, loss, and `NeuralNetwork` internals, route to [`../deep-learning/SKILL.md`](../deep-learning/SKILL.md).
- For package-wide install/dependency context, see [`../../references/package-overview.md`](../../references/package-overview.md) and [`../../references/troubleshooting.md`](../../references/troubleshooting.md).

## Operating scope

Supported package surface:

- `DeepQNetwork(env_name='CartPole-v1', epsilon=1, gamma=0.9, decay_rate=0.005, min_epsilon=0.1)`
- `dqn.set_model(model_builder)` where the callback accepts `n_inputs` and `n_outputs`
- `dqn.train(n_epochs=500, batch_size=32)` for educational training loops
- `dqn.play(n_epochs)` only when rendering/display support is intentionally available

Do not present this repository as a full RL framework. It is an educational DQN implementation with a small replay buffer, no target network, no vectorized environments, and version-sensitive Gym assumptions.

## Default stance

Start with a one-epoch, no-render smoke before longer training. Prefer `gym==0.25.x` with NumPy `<2` for compatibility. If the user is on newer Gym APIs, normalize `reset` to an observation and `step` to `(obs, reward, done, info)` before calling `DeepQNetwork.train`.
