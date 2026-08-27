# Standard environments and wrappers

## Framework selection

`wrap_env` is framework-specific. Select it before constructing the action:

| Runtime | Import | Converted values | CPU-safe baseline |
| --- | --- | --- | --- |
| PyTorch | `skrl.envs.wrappers.torch.wrap_env` | `torch.Tensor`; `env.device` is a `torch.device` | `skrl[torch]` + Gymnasium |
| JAX | `skrl.envs.wrappers.jax.wrap_env` | JAX arrays; `env.device` is a JAX device | `skrl[jax]` + CPU JAX |
| Warp | `skrl.envs.wrappers.warp.wrap_env` | `warp.array`; `env.device` is a Warp device | `skrl[warp]` + Warp CPU |

The public signature is `wrap_env(env, wrapper="auto", verbose=True)`. The `wrapper` tag is selected lazily for many optional integrations, so importing the standard wrapper does not prove that an external backend is installed. `verbose=False` suppresses wrapper-selection logging while troubleshooting.

## Single-agent decision table

| Original object | Explicit tag | Returned shape/behavior | Notes |
| --- | --- | --- | --- |
| Gymnasium environment | `"gymnasium"` | `Wrapper`; reset and step use the current five-result step API | Preferred route for `gymnasium.make(...)` and `gymnasium.make_vec(...)`. |
| OpenAI Gym environment | `"gym"` | `Wrapper`; converts Gym spaces and supports old and new Gym APIs | Requires the optional `gym` package. The old API path maps `TimeLimit.truncated` into `terminated`/`truncated`. |
| Isaac Lab single-agent env | `"isaaclab"` or `"isaaclab-single-agent"` | Isaac Lab wrapper | Load with the matching framework loader first; see [external-integrations.md](external-integrations.md). |
| ManiSkill env | `"mani-skill"` | ManiSkill wrapper | Register the task by importing ManiSkill before `gym.make`. |
| MuJoCo Playground env | `"playground"` | Playground wrapper | Loader and environment are JAX-oriented even when a Torch/Warp wrapper is selected. |

The same tags are exposed by the Torch and JAX wrapper modules. Warp has a `wrap_env` signature with the same annotation, but its source package provides the Gymnasium, ManiSkill, Playground, and Isaac Lab wrapper implementations; there is no Warp `gym_envs.py` or PettingZoo implementation in this release. Treat Warp `"gym"` and Warp `"pettingzoo"` as unsupported/unverified rather than relying on the annotation. Use Gymnasium for a portable Warp route and route multi-agent Warp requests to a compatibility review.

`"auto"` examines direct and unwrapped base-class names. It recognizes Gymnasium, Gym, PettingZoo, ManiSkill, MuJoCo Playground, and Isaac Lab naming patterns. It is convenient for standard registered classes, but can return an unrecognized class-name list for a custom proxy/wrapper; in that case choose an explicit tag. For Isaac Lab, `"isaaclab"` chooses its multi-agent wrapper when `unwrapped.possible_agents` exists; use the explicit single/multi-agent tag when the class does not expose that marker yet.

## Reset, step, spaces, and device

A single-agent wrapper exposes the common methods:

```python
observation, info = env.reset()
observation, reward, terminated, truncated, info = env.step(action)
state = env.state()             # converted state, or None
space = env.observation_space  # Gymnasium Space
state_space = env.state_space   # Space or None
space = env.action_space
n = env.num_envs                # 1 unless the unwrapped env supplies num_envs
n_agents = env.num_agents       # 1 unless the unwrapped env supplies num_agents
device = env.device
```

The base wrapper forwards attributes to the original and its `.unwrapped` object. If no original `device` exists, the framework configuration chooses its default available device; ordinary Gymnasium Pendulum therefore normally reports CPU on a CPU-only host. `num_envs` defaults to `1`. `state_space` defaults to `None`, and `state()` is allowed to return `None`.

The framework conversion utilities handle:

- `Box`: converted to floating values and flattened to `(batch, features)`;
- `Discrete`: represented as a one-column integer value;
- `MultiDiscrete`: represented with one occupied column per discrete component;
- `Tuple` and `Dict`: recursively converted and concatenated in tuple order or sorted dictionary-key order.

Other space types are not automatically supported by these utilities. If a custom environment uses a space such as `MultiBinary`, a nonstandard object, or values with an unexpected dtype/shape, expect a `ValueError` during reset/step conversion. Change the environment space or add a deliberate, tested adapter; do not silently reshape it in an agent model.

The action supplied to `step` is already a framework tensor/array in the wrapper's flattened batch convention. For a non-vectorized Pendulum environment, a one-environment action is typically shaped `(1, action_features)`; for a vectorized environment, it is `(num_envs, action_features)`. The wrapper unflattens it into the original space, sends NumPy/native values to Gymnasium, then converts the result back.

## Vectorized Gymnasium and Gym

Create the vector environment before wrapping:

```python
import gymnasium as gym
from skrl.envs.wrappers.torch import wrap_env

env0 = gym.make_vec("Pendulum-v1", num_envs=4, vectorization_mode="sync")
env = wrap_env(env0, wrapper="gymnasium")
obs, info = env.reset()
# `env.observation_space` and `env.action_space` describe one environment;
# returned observations/rewards/flags carry the `num_envs` batch.
```

For versions without `make_vec`, use the version's vector factory (for example `gym.vector.make`) and the matching `"gym"` or `"gymnasium"` tag. The wrapper detects `gymnasium.vector.VectorEnv` (and the available experimental vector class), uses `single_observation_space`/`single_action_space`, and reports `num_envs` from the original. Vector environments are autoreset-aware: the wrapper caches the initial reset result and returns the cached observation/info on repeated reset calls until a step updates it. `render()` uses the vector environment's `call("render", ...)` route.

The Gym wrapper has an additional old-API branch for Gym versions below 0.25: it calls `seed()` then `reset()` (observation only), accepts a four-result `step`, and derives truncation from `info["TimeLimit.truncated"]`. Modern Gym and Gymnasium use explicit reset info and separate `terminated`/`truncated`; preserve those flags when writing a trainer or evaluation loop.

## Shimmy and PettingZoo boundary

Shimmy adapts other environment APIs into Gymnasium or PettingZoo. It is not a separate `wrap_env` tag:

- a Shimmy single-agent compatibility environment that behaves as Gymnasium should be wrapped with `"gymnasium"`;
- a Shimmy PettingZoo compatibility environment should be wrapped with `"pettingzoo"` in Torch or JAX;
- the optional Shimmy package, the source simulator (for example Atari/DM Control), and any assets must be installed separately.

The PettingZoo wrapper targets the **Parallel API**. A wrapped multi-agent object returns dictionaries for observations, rewards, termination/truncation flags, and info; exposes `agents`, immutable `possible_agents`, `observation_spaces`, `action_spaces`, and per-agent accessor methods; and provides `state_spaces` (global state repeated per possible agent when only `state_space` exists). AEC-only environments must be converted to a supported parallel/compatibility API first. Continue with [multi-agent-and-runner](../../multi-agent-and-runner/SKILL.md), not a single-agent model route.

## Safe check

Run the bundled smoke without external assets:

```bash
python sub-skills/environment-integration/scripts/wrap_gymnasium_smoke.py --help
python sub-skills/environment-integration/scripts/wrap_gymnasium_smoke.py --framework torch
```

Use `--framework jax` or `--framework warp` only when that extra is installed. The check is one reset, one zero action, one step, and `close`; it is not evidence of training quality, CUDA execution, or external simulator availability.
