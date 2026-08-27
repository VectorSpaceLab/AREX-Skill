---
name: observations-actions-rewards
description: "Configure HighwayEnv observations, actions, rewards, and info outputs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Observations, actions, and rewards for HighwayEnv

Use this sub-skill when a task is about selecting or debugging HighwayEnv
observation spaces, action spaces, reward component interpretation, goal-style
parking observations, `info` outputs, or safe config validation.

## Read this first

- Read [references/configuration-reference.md](references/configuration-reference.md)
  when creating or modifying a `config={...}` dictionary, updating config at
  reset time, validating nested config shape, or choosing complete snippets.
- Read [references/observations.md](references/observations.md) when selecting
  between `Kinematics`, `OccupancyGrid`, `TimeToCollision`, `LidarObservation`,
  `KinematicsGoal`, image, tuple, attributes, exit, or multi-agent observations.
- Read [references/actions-rewards.md](references/actions-rewards.md) when
  choosing `DiscreteMetaAction`, `ContinuousAction`, `DiscreteAction`, or
  `MultiAgentAction`; mapping discrete labels; using `get_available_actions()`;
  or explaining scalar rewards, `info["rewards"]`, and `info["is_success"]`.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an
  observation/action config fails, an action has the wrong shape or unavailable
  label, `info` is missing a key, or a space shape is surprising.
- Run [scripts/inspect_spaces.py](scripts/inspect_spaces.py) for a safe one-step
  JSON inspection of an env id plus optional JSON config before giving an agent a
  final space/reward interpretation.

## Boundaries and routing

This sub-skill owns observation/action/reward configuration and interpretation.
Route these adjacent tasks elsewhere:

- Environment creation, reset/step loops, vectorization, render modes, video
  wrappers, and display/headless issues: use
  [simulation-environments](../simulation-environments/SKILL.md), and for
  training video workflows use
  [training-and-evaluation](../training-and-evaluation/SKILL.md).
- Custom roads, lanes, vehicles, new environment classes, and road geometry that
  changes what observations see: use
  [road-vehicle-dynamics](../road-vehicle-dynamics/SKILL.md).
- RL algorithm choice, Stable-Baselines3/Torch setup, long training loops,
  evaluation budgets, and benchmark reporting: use
  [training-and-evaluation](../training-and-evaluation/SKILL.md).
