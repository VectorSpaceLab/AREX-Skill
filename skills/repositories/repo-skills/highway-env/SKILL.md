---
name: highway-env
description: "Use Farama HighwayEnv for Gymnasium autonomous-driving
  environments, simulation configuration, road/vehicle dynamics, and bounded RL
  rollouts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# HighwayEnv repo skill

Use this repo skill when a task involves `highway-env` / HighwayEnv autonomous-driving simulation environments: creating Gymnasium envs, choosing scenario IDs, configuring observations/actions/rewards, rendering or recording rollouts, building custom road/vehicle scenarios, or preparing safe reinforcement-learning smoke tests.

HighwayEnv is a Python package named `highway-env` with import package `highway_env`. It registers Gymnasium environments for highway, merge, roundabout, parking, intersection, racetrack, lane-keeping, two-way, exit, and U-turn driving tasks.

## Fast start

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)  # idempotent and useful for tools/linters

env = gym.make("highway-v0", config={"duration": 5, "vehicles_count": 10})
try:
    obs, info = env.reset(seed=0)
    terminated = truncated = False
    while not (terminated or truncated):
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
finally:
    env.close()
```

If the package or environment lookup is suspect, run [scripts/check_highway_env_install.py](scripts/check_highway_env_install.py). It imports the package, lists registered HighwayEnv IDs, makes a selected env, runs a bounded sampled-action rollout, and can optionally check `rgb_array` rendering.

## Route map

- Read [sub-skills/simulation-environments/SKILL.md](sub-skills/simulation-environments/SKILL.md) for built-in environment IDs, `gym.make`, registration, reset/step/close loops, config update timing, render modes, vectorization, multi-agent wrappers, and finite-MDP helpers.
- Read [sub-skills/observations-actions-rewards/SKILL.md](sub-skills/observations-actions-rewards/SKILL.md) for `config={...}` dictionaries that change observation spaces, action spaces, reward components, goal observations, `info` fields, or action availability.
- Read [sub-skills/road-vehicle-dynamics/SKILL.md](sub-skills/road-vehicle-dynamics/SKILL.md) for `RoadNetwork`, lanes, roads, vehicles, controllers, behaviour models, obstacles/landmarks, connected-lane neighbour detection, and custom environment classes.
- Read [sub-skills/training-and-evaluation/SKILL.md](sub-skills/training-and-evaluation/SKILL.md) for bounded random-policy rollouts, Stable-Baselines3/Torch/rl-agents optional integration, vectorized training skeletons, policy evaluation, videos, and long-run safety limits.

## Root references

- Read [references/installation-and-smoke.md](references/installation-and-smoke.md) when installing, verifying imports, selecting a smoke-check command, or separating package dependencies from optional RL dependencies.
- Read [references/environment-catalog.md](references/environment-catalog.md) when choosing a built-in environment family, version suffix, action style, or common configuration knobs.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, registration, headless rendering, optional dependency, config, and long-run failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) to check the source version, commit, tag, evidence baseline, and refresh triggers for this generated skill.
- `references/repo-routing-metadata.json` contains managed router placement metadata for DisCo's repo-skill library.

## Operating guardrails

- Import `highway_env` before `gym.make("highway-v0")`; direct Gymnasium lookup can fail if environments were not registered in the current process.
- Use current Gymnasium signatures: `obs, info = env.reset(...)` and `obs, reward, terminated, truncated, info = env.step(action)`.
- Use bounded loops in automation. Do not copy examples with `while True` unless an external runner imposes a hard timeout.
- Use `render_mode="rgb_array"` for headless frame capture. Use `render_mode="human"` only for local interactive viewing.
- Treat Stable-Baselines3, Torch, rl-agents, old baselines/HER stacks, display servers, and Colab helpers as optional project dependencies, not as dependencies installed by `highway-env`.
- Do not depend on the original repository checkout for runtime work. The bundled references and scripts in this skill are the reusable operating context.
