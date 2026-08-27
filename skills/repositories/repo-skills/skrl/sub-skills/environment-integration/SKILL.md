---
name: environment-integration
description: "Route skrl environment construction through the correct framework
  wrapper, vectorization and multi-agent boundary, and optional simulator loader
  without inventing unavailable dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Environment integration

Use this sub-skill when a task starts with an environment name, a Gym/Gymnasium/PettingZoo object, `wrap_env`, vectorization, observation/state/action spaces, `env.device`, `num_envs`, or an external simulator. It produces the common environment interface expected by skrl agents and trainers; it does **not** choose algorithms, model classes, trainer configuration, IPPO/MAPPO settings, or install/run a simulator.

## Route first

1. Identify the environment API and whether it is single-agent or multi-agent. Do not infer from the task name alone.
2. Select the framework that will own tensors/arrays and import its wrapper:
   - PyTorch: `from skrl.envs.wrappers.torch import wrap_env`
   - JAX: `from skrl.envs.wrappers.jax import wrap_env`
   - Warp: `from skrl.envs.wrappers.warp import wrap_env`
3. For Gymnasium, Gym, or a supported registered external environment, create the original environment first, then call `wrap_env(original, wrapper=...)`. Prefer an explicit tag while diagnosing; use `"auto"` only when the environment's class hierarchy is known to expose the expected package base class.
4. For PettingZoo parallel environments, use `wrapper="pettingzoo"` and hand the returned multi-agent interface to [multi-agent-and-runner](../multi-agent-and-runner/SKILL.md). Shimmy compatibility environments follow the API they expose: single-agent Gymnasium-compatible objects use `"gymnasium"`; multi-agent compatibility objects use `"pettingzoo"`.
5. For Isaac Lab, ManiSkill, or MuJoCo Playground, read [external-integrations.md](references/external-integrations.md) before writing a launcher. These are prerequisite-heavy reference routes, not CPU smoke routes.

The exact public signature in skrl 2.1.0 is:

```python
wrap_env(env, wrapper="auto", verbose=True)
```

It returns a framework-specific `Wrapper` or `MultiAgentEnvWrapper`; an unknown wrapper tag raises `ValueError`. The accepted tags are `auto`, `gym`, `gymnasium`, `isaaclab`, `isaaclab-single-agent`, `isaaclab-multi-agent`, `mani-skill`, `pettingzoo`, and `playground` in the three public signatures. See the framework caveat for Warp in [standard-environments.md](references/standard-environments.md).

## Minimal single-agent contract

```python
import gymnasium as gym
from skrl.envs.wrappers.torch import wrap_env

env = wrap_env(gym.make("Pendulum-v1"), wrapper="gymnasium")
observation, info = env.reset()
# action must be a framework array/tensor with the flattened batch shape expected by the wrapper
action = ...
observation, reward, terminated, truncated, info = env.step(action)
env.close()
```

The wrapper normalizes `reset()` to `(observation, info)` and `step()` to `(observation, reward, terminated, truncated, info)`. It converts observations, rewards, and flags to the selected framework and forwards `render()` and `close()`. `state()` returns a converted state when the original environment provides a state/state space; otherwise it returns `None` (and agents should use `observation_space`). Do not expect a bare Gym/Gymnasium object to have skrl's tensor/array outputs or `device`, `num_envs`, and state behavior.

## Inspect before routing downstream

After wrapping, check `env.observation_space`, `env.state_space`, `env.action_space`, `env.device`, `env.num_envs`, and (for multi-agent) `env.agents`, `env.possible_agents`, `env.observation_spaces`, and `env.action_spaces`. Spaces are Gymnasium space objects; the conversion utilities support Box, Discrete, MultiDiscrete, Tuple, and Dict compositions and flatten composite values into a batch-by-feature representation. Unsupported space kinds or values fail during conversion rather than being silently coerced. Use these spaces to configure models, then hand framework details to one of:

- [torch-agent-training](../torch-agent-training/SKILL.md)
- [jax-agent-training](../jax-agent-training/SKILL.md)
- [warp-agent-training](../warp-agent-training/SKILL.md)
- [multi-agent-and-runner](../multi-agent-and-runner/SKILL.md)

For a bounded public CPU check, run [scripts/wrap_gymnasium_smoke.py](scripts/wrap_gymnasium_smoke.py) with `--help` first and then the desired framework. It creates only a Gymnasium Pendulum instance, performs one reset and one step, and closes it; it does not train, download, or import an external simulator. For cross-cutting package, device, or checkpoint failures, also read [../../references/troubleshooting.md](../../references/troubleshooting.md).

## Non-negotiable limits

- Do not use the Gym wrapper tag for a Gymnasium object, or the Gymnasium tag for an old Gym object, merely because both environments are named similarly.
- Do not run the external loader without its simulator installation, task registration, assets, and (often) GPU/runtime process. No external simulator result is implied by this sub-skill.
- Do not route PettingZoo to a single-agent model/trainer: its reset/step values are per-agent dictionaries and its active agent set can change.
- Do not claim CUDA, simulator, real-world, or asset-backed support from a CPU wrapper smoke.
- Always close the original/wrapped environment, including after a failed one-step check.
