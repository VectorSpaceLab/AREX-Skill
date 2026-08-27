---
name: simulation-environments
description: "Operate built-in HighwayEnv Gymnasium environments, registration,
  reset-step loops, rendering, vectorization, finite-MDP helpers, and
  multi-agent wrappers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Simulation environments

Use this sub-skill when you need to instantiate and operate built-in HighwayEnv Gymnasium environments safely. It covers environment ID selection, registration, `gym.make`, `reset`/`step`/`render` lifecycles, bounded random rollouts, vectorized environments, `RecordVideo`, finite-MDP helper methods, and multi-agent wrapper semantics.

## Route to this sub-skill for

- Choosing a built-in HighwayEnv environment ID or version.
- Fixing Gymnasium registration/name lookup problems.
- Writing short, safe reset/step loops that handle `terminated` and `truncated` correctly.
- Updating runtime config through `gym.make(..., config=...)`, `env.unwrapped.config`, or `reset(options={"config": ...})`.
- Rendering `rgb_array` frames, recording short videos, or avoiding display windows.
- Vectorizing HighwayEnv environments or creating them in spawned subprocesses.
- Understanding `env.unwrapped.to_finite_mdp()`, `simplify()`, `change_vehicles()`, `set_preferred_lane()`, and `set_route_at_intersection()`.
- Using `intersection-multi-agent-*` environments and `MultiAgentWrapper` return semantics.

## Route elsewhere

- Observation, action, reward, space-shape, and `info["rewards"]` details: read `../observations-actions-rewards/SKILL.md`.
- Road networks, lanes, vehicles, dynamics classes, and custom environment implementation: read `../road-vehicle-dynamics/SKILL.md`.
- RL training loops, Stable-Baselines3 integration, long evaluations, and benchmark reporting: read `../training-and-evaluation/SKILL.md`.

## References and scripts

- Read [references/environment-workflows.md](references/environment-workflows.md) when selecting environment IDs/versions, registering HighwayEnv, applying config updates, or using finite-MDP and environment-copy helpers.
- Read [references/gymnasium-api.md](references/gymnasium-api.md) when writing production reset/step/close code, handling Gymnasium return values, seeding, spaces, `info`, and safe episode loops.
- Read [references/rendering-vectorization-multi-agent.md](references/rendering-vectorization-multi-agent.md) when rendering frames, recording videos, vectorizing environments, spawning subprocess workers, or using multi-agent variants.
- Read [references/troubleshooting.md](references/troubleshooting.md) when `gym.make` cannot find an env, rendering fails or returns `None`, vector/multiprocessing fails, helper methods raise optional-dependency errors, or episodes run unexpectedly long.
- Run [scripts/smoke_env_rollout.py](scripts/smoke_env_rollout.py) to verify that an installed HighwayEnv environment can be registered, made, reset, stepped with sampled actions, optionally rendered as `rgb_array`, and summarized as JSON.

## Minimal operating pattern

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)  # harmless when already registered

env = gym.make("highway-v0", config={"duration": 5, "vehicles_count": 10})
try:
    obs, info = env.reset(seed=0)
    terminated = truncated = False
    while not (terminated or truncated):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
finally:
    env.close()
```

Prefer explicit step caps for smoke checks and automation. Some scenarios can run for many decision steps, and `lane-keeping-v0` relies on Gymnasium's registration time limit rather than an internal `duration` termination.
