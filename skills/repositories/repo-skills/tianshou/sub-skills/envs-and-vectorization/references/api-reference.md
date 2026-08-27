# API Reference: Environments and Vectorization

## Public Imports

```python
from tianshou.env import (
    ContinuousToDiscrete,
    DummyVectorEnv,
    MultiDiscreteToDiscrete,
    PettingZooEnv,
    RayVectorEnv,
    ShmemVectorEnv,
    SubprocVectorEnv,
    TruncatedAsTerminated,
    VectorEnvNormObs,
)
from tianshou.utils.space_info import SpaceInfo
```

## Vector Env Constructors

| Class | Constructor | Use When | Notes |
| --- | --- | --- | --- |
| `DummyVectorEnv` | `DummyVectorEnv(env_fns, wait_num=None, timeout=None)` | First validation, debugging, deterministic smoke checks, cheap envs | Runs envs sequentially in the main process. |
| `SubprocVectorEnv` | `SubprocVectorEnv(env_fns, wait_num=None, timeout=None, share_memory=False, context=None)` | CPU-heavy env stepping or isolation from main process | `context` may be `"fork"`, `"spawn"`, or `None`; factories must survive multiprocessing serialization. |
| `ShmemVectorEnv` | `ShmemVectorEnv(env_fns, wait_num=None, timeout=None)` | Subprocess stepping with shared observation buffers | API matches `SubprocVectorEnv`; best for fixed-shape array/dict/tuple observations with supported NumPy dtypes. |
| `RayVectorEnv` | `RayVectorEnv(env_fns, wait_num=None, timeout=None)` | Distributed env workers through Ray | Requires separately installed `ray`; initializes Ray if needed. |

All vector env constructors take a sequence of zero-argument callables. Each callable must create and return a fresh Gymnasium-compatible env or `PettingZooEnv` instance.

## BaseVectorEnv Behavior

- `len(envs)` and `envs.env_num` report the number of factories.
- `envs.reset(env_id=None, **kwargs)` returns `(obs, infos)`, where `infos` is a NumPy array of per-env info dictionaries.
- `envs.step(action, id=None)` returns `(obs, rew, terminated, truncated, info)` as NumPy arrays.
- When `wait_num` or `timeout` enables async mode, step ids must correspond to ready environments; returned `info` entries include `env_id`.
- `envs.seed(seed)` seeds action spaces and calls env-level `seed` when available, otherwise resets with `seed=...`; an int expands to `seed + i` per env.
- `envs.get_env_attr(name, id=None)` and `envs.set_env_attr(name, value, id=None)` access underlying env attributes through workers.
- `envs.action_space`, `envs.observation_space`, and other Gym reserved attributes are proxied as lists from workers.
- `envs.close()` should be called exactly once when finished; methods assert if called after close.

## Worker Notes

| Worker | Used By | Key Behavior |
| --- | --- | --- |
| `DummyEnvWorker` | `DummyVectorEnv` | Instantiates the env in-process; easiest to inspect with breakpoints and direct exceptions. |
| `SubprocEnvWorker` | `SubprocVectorEnv`, `ShmemVectorEnv` | Uses multiprocessing pipes plus cloudpickle-wrapped factories; can use shared buffers when `share_memory=True`. |
| `RayEnvWorker` | `RayVectorEnv` | Runs env calls through Ray actors; requires the external Ray package and Ray runtime readiness. |

`SubprocEnvWorker` can serialize many closures through cloudpickle, but `spawn` still requires import-safe code and top-level definitions. `ShmemVectorEnv` creates a dummy env up front to inspect observation space and allocate buffers.

## Wrappers

| Wrapper | Input Action Space | Output Action Space | Purpose |
| --- | --- | --- | --- |
| `ContinuousToDiscrete(env, action_per_dim)` | `gymnasium.spaces.Box` | `MultiDiscrete` | Discretize each continuous action dimension. |
| `MultiDiscreteToDiscrete(env)` | `gymnasium.spaces.MultiDiscrete` | `Discrete` | Flatten multidiscrete branches into one discrete index. |
| `TruncatedAsTerminated(env)` | Any Gymnasium env | Same as wrapped env | Treat `truncated` as terminal by returning `terminated = terminated or truncated`. |
| `VectorEnvNormObs(envs, update_obs_rms=True)` | Vector env or EnvPool-like env | Same vector interface | Normalize observations with `RunningMeanStd`; supports copying stats to evaluation envs. |

## PettingZooEnv

`PettingZooEnv(env)` wraps a PettingZoo AEC env whose agents share identical observation spaces and identical action spaces. If spaces differ, pad them with SuperSuit before wrapping.

Reset and step observations are dictionaries:

- `obs`: the active agent observation.
- `agent_id`: the active PettingZoo agent id.
- `mask`: legal-action booleans when the source observation has `action_mask`, or all-true for discrete spaces without a mask.

`step(action)` returns `(obs, rewards, terminated, truncated, info)`, where `rewards` is a list aligned to `possible_agents`.

## SpaceInfo

`SpaceInfo.from_env(env)` and `SpaceInfo.from_spaces(action_space, observation_space)` summarize supported `Box` and `Discrete` spaces:

- `action_info.action_shape`, `min_action`, `max_action`, and `action_dim`.
- `observation_info.obs_shape` and `obs_dim`.

Unsupported spaces raise `ValueError`; inspect or wrap `Dict`, `Tuple`, `MultiDiscrete`, and custom spaces explicitly before using `SpaceInfo`.
