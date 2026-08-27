---
name: deep-reinforcement-learning-with-pytorch
description: "Route and use the repository's PyTorch reinforcement-learning
  examples across tabular control, DQN, on-policy actor-critic, and off-policy
  continuous control."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Deep Reinforcement Learning with PyTorch

This repo is a collection of single-file reinforcement-learning examples, not an installable Python package. Use this root skill as the router for the algorithm family that matches the user's request.

## Read first
- `references/dependency-and-compatibility.md` for Gym, Torch, env-ID, and optional-extra notes.
- `references/troubleshooting.md` for repo-wide failure patterns.
- `references/plotting.md` for the `.npy` curve format used by the plotting helper.
- `scripts/rl_env_compat_report.py` for a quick non-training env / backend probe.
- `scripts/plot_training_curves.py` for the bundled result-plotting helper.

## Route map

| User intent | Go here | Why |
| --- | --- | --- |
| Q-learning, Sarsa, toy GridWorld, terminal-state bookkeeping | `sub-skills/tabular-control/SKILL.md` | Small tabular examples with deterministic update rules. |
| DQN, replay buffers, target networks, MountainCar reward shaping, TensorBoard logs | `sub-skills/value-based-discrete-control/SKILL.md` | Char01 DQN family on discrete Gym control. |
| REINFORCE, policy gradients, actor-critic, A2C, PPO, saved on-policy pickles | `sub-skills/on-policy-actor-critic/SKILL.md` | Char02 / Char03 / Char04 / Char07 on-policy workflows. |
| DDPG, SAC, TD3, continuous actions, checkpoint playback, BipedalWalker compatibility | `sub-skills/off-policy-continuous-control/SKILL.md` | Char05 / Char09 / Char10 continuous-control workflows. |
| Plot `.npy` learning curves or compare runs | `scripts/plot_training_curves.py` | Shared support workflow, not a training family. |
| Check Gym, CUDA, Box2D, and legacy env IDs before choosing a route | `scripts/rl_env_compat_report.py` | Fast inspection helper for classic-control and continuous-control support. |

## How to use this skill

1. Identify the algorithm family first.
2. Read the matching sub-skill before touching the original training scripts.
3. Use the root compatibility helper when the question is about env IDs, optional extras, or device availability.
4. Use the root plotting helper when the question is about `.npy` curves rather than algorithm behavior.
5. Do not launch the repository's full default training loops unless the user explicitly asks for training and provides a budget.

## Compatibility snapshot

- The repository uses legacy Gym-style APIs and legacy env names in its source scripts.
- Modern substitutes verified in the inspection environment are Pendulum-v1 and BipedalWalker-v3.
- CUDA is optional, not required. If Torch sees a GPU, the continuous-control scripts may use it automatically.
- TensorFlow appears in the historical requirements file but no discovered source file imports it.
- Char08 ACER is docs-only in this checkout; there is no runnable ACER sub-skill.

## When in doubt

- If the task mentions CartPole, MountainCar, or reward shaping, start with DQN or on-policy classic-control troubleshooting rather than the continuous-control route.
- If the task mentions Pendulum or BipedalWalker, use the continuous-control route and check the compatibility helper for the modern env ID.
- If the task is only about plotting run curves or sanity-checking the environment, stay at the root support layer.
- Keep runtime links inside this generated skill tree; do not depend on the original checkout remaining present.
