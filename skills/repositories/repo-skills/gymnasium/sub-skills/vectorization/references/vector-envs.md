# Vector Environment Lifecycle

Gymnasium vector environments run `num_envs` independent sub-environments behind a single `VectorEnv` API. They are useful for batched evaluation and training, but the loop shape is different from a single `Env` loop.

## Constructors

### `gymnasium.make_vec`

```python
import gymnasium as gym

envs = gym.make_vec(
    "CartPole-v1",
    num_envs=8,
    vectorization_mode="sync",  # "sync", "async", "vector_entry_point", or None
    vector_kwargs={"autoreset_mode": gym.vector.AutoresetMode.NEXT_STEP},
)
```

Use `make_vec` when the environment is registered. Important arguments:

- `id`: a registered environment ID or `EnvSpec`.
- `num_envs`: number of sub-environments.
- `vectorization_mode`: `None` first uses a registered `vector_entry_point` when available, otherwise falls back to sync; explicit values are `"sync"`, `"async"`, or `"vector_entry_point"`.
- `vector_kwargs`: forwarded to the vectorizer constructor, such as `copy`, `observation_mode`, `autoreset_mode`, or `shared_memory` for async.
- `wrappers`: single-environment wrapper callables applied to each base env before sync/async vectorization; not valid for `"vector_entry_point"` mode.
- `**kwargs`: forwarded to each base environment constructor, such as `render_mode` or env-specific options.

Prefer explicit `vectorization_mode="sync"` when debugging. Use `"async"` only after the factories, wrappers, and spaces work in sync mode.

### `SyncVectorEnv`

```python
import gymnasium as gym
from gymnasium.vector import SyncVectorEnv

def make_cartpole(gravity=None):
    kwargs = {} if gravity is None else {"sutton_barto_reward": True}
    return gym.make("CartPole-v1", **kwargs)

envs = SyncVectorEnv([lambda: make_cartpole(), lambda: make_cartpole()])
```

`SyncVectorEnv(env_fns, copy=True, observation_mode="same", autoreset_mode=AutoresetMode.NEXT_STEP)` runs sub-environments serially in the current process. Use it for cheap environments, deterministic debugging, environments that cannot be pickled, and custom factories that close over local objects.

### `AsyncVectorEnv`

```python
import gymnasium as gym
from gymnasium.vector import AsyncVectorEnv

def make_env():
    return gym.make("CartPole-v1")

envs = AsyncVectorEnv([make_env for _ in range(4)], shared_memory=True)
```

`AsyncVectorEnv(env_fns, shared_memory=True, copy=True, context=None, daemon=True, worker=None, observation_mode="same", autoreset_mode=AutoresetMode.NEXT_STEP)` runs workers in subprocesses. Use it when environment stepping is expensive enough to offset process and serialization overhead. Factories must be process-safe and importable/picklable in the selected multiprocessing context.

## Batched Spaces and Outputs

Every vector env exposes both single and batched spaces:

| Attribute | Meaning | Example for `CartPole-v1`, `num_envs=3` |
| --- | --- | --- |
| `single_action_space` | action for one sub-env | `Discrete(2)` |
| `action_space` | action batch passed to `step` | `MultiDiscrete([2, 2, 2])` |
| `single_observation_space` | observation for one sub-env | `Box(shape=(4,))` |
| `observation_space` | observation batch returned by `reset`/`step` | `Box(shape=(3, 4))` |

A step returns five batched values:

```python
observations, rewards, terminations, truncations, infos = envs.step(actions)
```

- `observations` is valid for `envs.observation_space`.
- `rewards`, `terminations`, and `truncations` are arrays of shape `(envs.num_envs,)`.
- `infos` is a dictionary of arrays keyed by info names, with companion boolean masks named `_{key}` when only some sub-envs supplied that key.
- `done_mask = terminations | truncations` replaces a scalar `done` check.

Correct loop skeleton:

```python
observations, infos = envs.reset(seed=123)
for update in range(num_updates):
    actions = policy(observations)  # must match envs.action_space
    observations, rewards, terminations, truncations, infos = envs.step(actions)
    done_mask = terminations | truncations
```

For random or exploratory actions, sample from `envs.action_space`, not `envs.single_action_space`.

## Seeds, Partial Reset, and Attributes

`reset(seed=integer)` expands the integer into per-env seeds `[seed, seed + 1, ...]` in Gymnasium's built-in sync/async vectorizers. You may also pass a list of seeds with length `num_envs`.

For `AutoresetMode.DISABLED`, reset only the finished sub-envs with a boolean mask:

```python
mask = terminations | truncations
if mask.any():
    observations, infos = envs.reset(options={"reset_mask": mask})
```

`SyncVectorEnv` and `AsyncVectorEnv` provide attribute helpers:

```python
values = envs.get_attr("np_random_seed")
envs.set_attr("some_attribute", [value0, value1])
results = envs.call("some_method", arg)
```

For async envs, avoid issuing another async call while one is pending; close after exceptions to clean up workers.

## Autoreset Modes

Gymnasium records the active mode in `envs.metadata["autoreset_mode"]` as `gymnasium.vector.AutoresetMode`.

| Mode | What happens | Training-loop implication |
| --- | --- | --- |
| `NEXT_STEP` | A finished sub-env is reset on the next `step`; the terminal step returns the final observation, then the following step returns the reset observation with zero reward and false masks for that sub-env. | Default and easiest for many rollout buffers; use the terminal masks from the step where they occur. |
| `SAME_STEP` | A finished sub-env is reset immediately inside the terminal `step`; the returned observation is the reset observation. | Read `infos["final_obs"]` and `infos["final_info"]` with masks such as `infos["_final_obs"]` when terminal observations matter. |
| `DISABLED` | Gymnasium does not autoreset finished sub-envs. | You must call `reset(options={"reset_mask": done_mask})` before stepping finished sub-envs again. |

Do not assume every wrapper or external vector implementation supports every autoreset mode. Some vector observation/stateful wrappers assert or document a subset.

## Choosing Sync, Async, or Vector Entry Point

- Use `sync` for debugging, cheap environments, custom closures, deterministic stack traces, or environments with non-picklable state.
- Use `async` for expensive CPU-bound environments with picklable factories and compatible observations.
- Use `vector_entry_point` only when the registered environment supplies a custom vector implementation. It may be faster, but it does not accept `wrappers` or `vector_kwargs` through `make_vec`.
- If an environment has no single-env `entry_point`, sync/async vectorization cannot create it; if it has no `vector_entry_point`, explicit `vector_entry_point` mode cannot create it.

## Rendering and Closing

Vector `render()` returns a tuple of frames or `None`, depending on sub-env render modes and vector implementation. For video, use vector recording wrappers and create environments with compatible image rendering such as `render_mode="rgb_array"`.

Always close in `finally` blocks:

```python
envs = gym.make_vec("CartPole-v1", num_envs=2, vectorization_mode="sync")
try:
    observations, infos = envs.reset()
    observations, rewards, terminations, truncations, infos = envs.step(envs.action_space.sample())
finally:
    envs.close()
```
