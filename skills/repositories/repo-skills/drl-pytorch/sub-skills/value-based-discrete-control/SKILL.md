---
name: value-based-discrete-control
description: "Use DRL-Pytorch tabular Q-learning and non-Atari discrete-action
  value-based algorithms: Q-learning, DQN/DDQN/Dueling DQN, prioritized replay
  DQN/DDQN, C51, and NoisyNet DQN."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Value-Based Discrete Control

Use this sub-skill when a task asks for DRL-Pytorch's non-Atari, discrete-action value-based workflows:

- tabular Q-learning on CliffWalking;
- DQN, Double DQN, Dueling DQN, and Dueling Double DQN on CartPole or LunarLander;
- prioritized replay DQN/DDQN, preferring the modern LightPrior implementation unless the user specifically asks for sum-tree PER;
- categorical/distributional DQN (C51);
- NoisyNet DQN exploration.

Route elsewhere for Atari NoFrameskip DQN, EnvPool/Actor-Sharer-Learner, PPO, DDPG, TD3, SAC, continuous-action control, MuJoCo, or BipedalWalker workflows.

## Operating references

1. Start with [algorithm workflows](references/algorithm-workflows.md) for algorithm choice, EnvIdex mapping, safe commands, checkpoint naming, play mode, TensorBoard, and optional Box2D caveats.
2. Use [API and CLI reference](references/api-and-cli-reference.md) for distilled classes, functions, flags, local import names, and per-directory caveats.
3. Use [troubleshooting](references/troubleshooting.md) when CUDA defaults, Box2D, working directories, checkpoint names, TensorBoard, Gym/Gymnasium version drift, shapes, or stochastic training cause failures.
4. Run [scripts/smoke_value_based.py](scripts/smoke_value_based.py) for a no-training diagnostic against a user-supplied DRL-Pytorch checkout.

## Fast decision table

| User request | Use this workflow | Key choice |
|---|---|---|
| "Q-learning" or "CliffWalking" | Tabular Q-learning | No CLI flags; use the QLearningAgent API or bundled smoke. |
| "DQN/DDQN/Dueling" on CartPole or LunarLander | DQN family | `--Duel` and `--Double` select vanilla/Dueling/Double variants. |
| "prioritized replay" or "PER" | Prioritized DQN/DDQN | Prefer LightPrior Gymnasium 0.2x; use sum-tree only when requested. |
| "C51" or "distributional DQN" | Categorical DQN | `--DQL` toggles Double Q-learning inside C51. |
| "NoisyNet exploration" | NoisyNet DQN | No epsilon flag; exploration comes from NoisyLinear layers. |
| "Atari Pong/Enduro/NoFrameskip" | Not this sub-skill | Route to the Atari/ASL workflow. |
