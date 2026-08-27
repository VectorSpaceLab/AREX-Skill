# Wrappers and RL data utilities

This reference distills PARL's environment-wrapper and data-buffer behavior into operating guidance. It is self-contained and intentionally avoids relying on source examples at runtime.

## Public import surfaces

Common utility imports:

```python
from parl.env import CompatWrapper, ActionMappingWrapper, VectorEnv
from parl.env.atari_wrappers import wrap_deepmind, MonitorEnv, get_wrapper_by_cls
from parl.env.mujoco_wrappers import wrap_rms, get_ob_rms
from parl.env.multiagent_env import MAenv
from parl.utils import ReplayMemory
```

Runtime-checked constructor signatures:

| Object | Signature | Main use |
| --- | --- | --- |
| `CompatWrapper` | `CompatWrapper(env)` | Adapt Gym >=0.26 `reset`/`step` to old PARL-style returns. |
| `ActionMappingWrapper` | `ActionMappingWrapper(env)` | Map model actions in `[-1, 1]` to a continuous `Box` action range. |
| `VectorEnv` | `VectorEnv(envs)` | Step a list of synchronous env instances and auto-reset finished envs. |
| `ReplayMemory` | `ReplayMemory(max_size, obs_dim, act_dim)` | Fixed-capacity off-policy/offline replay buffer for flat observations. |

## Gym compatibility: `CompatWrapper`

PARL examples generally expect old Gym semantics:

```python
obs = env.reset()
next_obs, reward, done, info = env.step(action)
env.seed(seed)
```

Gym >=0.26 changed this to `reset() -> (obs, info)`, `step() -> (obs, reward, terminated, truncated, info)`, and reset-time seeding. `CompatWrapper` hides that change for PARL-style code:

```python
import gym
from parl.env import CompatWrapper

env = CompatWrapper(gym.make("CartPole-v1"))
env.seed(123)
obs = env.reset()
next_obs, reward, done, info = env.step(env.action_space.sample())
```

Important details:

- `CompatWrapper.reset` returns only `obs`, not `(obs, info)`.
- `CompatWrapper.step` returns only four values and ignores Gym's separate `truncated` return; it also forces `done=True` when `_max_episode_steps` is reached.
- `CompatWrapper.seed(seed)` stores the seed for the next reset on Gym >=0.26, but delegates to `env.seed(seed)` on older Gym.
- `is_gym_version_ge(version)` compares the installed `gym.__version__`. It does not understand Gymnasium objects directly; if using Gymnasium, provide a compatible shim or recheck behavior explicitly.

## Continuous action mapping: `ActionMappingWrapper`

Continuous-control examples often make a policy output actions in `[-1, 1]`. `ActionMappingWrapper` maps that model output to the environment's true `Box` action interval:

```python
from parl.env import CompatWrapper, ActionMappingWrapper

env = CompatWrapper(gym.make("Pendulum-v1"))
env = ActionMappingWrapper(env)
# agent.predict(obs) should now produce values in [-1, 1]
obs, reward, done, info = env.step(model_output_action)
```

Mapping formula:

```text
mapped = low + (model_output - (-1.0)) * ((high - low) / 2.0)
mapped = clip(mapped, low, high)
```

Contracts and caveats:

- The wrapped env must expose `action_space.low` and `action_space.high` like `gym.spaces.Box`.
- PARL stores `low_bound = action_space.low[0]` and `high_bound = action_space.high[0]`; the wrapper assumes a uniform scalar range across action dimensions. For per-dimension ranges, verify the current behavior before relying on it.
- Input actions are asserted to be within `[-1.001, 1.001]`. Clip or squash model outputs before calling `step`.
- The wrapper preserves `_max_episode_steps` when the underlying env exposes it.

## Synchronous vector environments: `VectorEnv`

`VectorEnv` is a lightweight synchronous wrapper around a Python list of envs:

```python
from parl.env import VectorEnv

vector_env = VectorEnv([make_env(seed=i) for i in range(num_envs)])
obs_batch = vector_env.reset()
next_obs_batch, reward_batch, done_batch, info_batch = vector_env.step(actions)
```

Behavior:

- `reset()` returns a Python list, one observation per env.
- `step(actions)` calls each env with `actions[env_id]` and returns four Python lists.
- If an env returns `done=True`, `VectorEnv` immediately calls that env's `reset()` and places the reset observation in `obs_batch` while preserving `done=True` in `done_batch`.
- There is no asynchronous process management, shared memory, timeout handling, or batching conversion. Convert returned lists to arrays in caller code when the agent expects arrays.
- Ensure `len(actions) == len(envs)`; the class does not perform a friendly length check before indexing.

## Atari wrappers: `wrap_deepmind`

`wrap_deepmind(env, dim=84, framestack=True, obs_format="NHWC", test=False, test_episodes=3)` applies a DeepMind-style Atari stack:

1. `CompatWrapper`
2. `MonitorEnv` for episode reward/length information
3. no-op reset
4. max-and-skip when the env id includes `NoFrameskip`
5. episodic-life behavior
6. fire-on-reset when the action meanings include `FIRE`
7. grayscale resize to `dim x dim`
8. clipped rewards
9. optional 4-frame stack in `NHWC` or `NCHW`
10. optional test wrapper that exposes evaluation rewards

Use it only for Atari-like environments that provide ALE lives, action meanings, image observations, and the optional OpenCV/Gym dependency stack. Do not use it for CartPole, MuJoCo, ordinary Box-control tasks, or arbitrary image environments without rechecking every assumption.

Useful helpers:

- `MonitorEnv.get_episode_rewards()`, `get_episode_lengths()`, `get_total_steps()`, and `next_episode_results()` expose episode statistics.
- `get_wrapper_by_cls(env, MonitorEnv)` walks a wrapper chain to fetch a nested wrapper instance.
- `FrameStack(..., obs_format="NCHW")` is used by PARL Atari A2C/IMPALA-style examples when the model expects channel-first images.

## MuJoCo/continuous-control RMS wrappers: `wrap_rms`

`wrap_rms(env, gamma, test=False, ob_rms=None)` applies continuous-control wrappers for single-agent MuJoCo-style tasks:

1. `CompatWrapper`
2. `TimeLimitMaskEnv`, which sets `info["bad_transition"] = True` when an episode ends exactly at the time limit
3. `MonitorEnv`, which adds `info["episode"]` with raw reward, length, and elapsed time at episode end
4. `VecNormalizeEnv`, which tracks running observation and/or return statistics

Training pattern:

```python
env = wrap_rms(env, gamma=0.99)
```

Evaluation pattern using training observation statistics:

```python
train_ob_rms = get_ob_rms(train_env)
eval_env = wrap_rms(eval_env, gamma=None, test=True, ob_rms=train_ob_rms)
```

Caveats:

- This wrapper expects continuous observations with `ob.ndim` and a one-dimensional `observation_space.shape`.
- `test=True` disables return normalization and sets the observation normalizer into evaluation mode.
- The underlying env must expose Gym-compatible `_max_episode_steps` and `_elapsed_steps` for the time-limit marker to be meaningful.
- MuJoCo itself is an optional dependency and is not part of PARL's default minimum utility stack.

## Multi-agent environment wrappers

Modern MPE wrapper:

```python
from parl.env.multiagent_env import MAenv

env = MAenv("simple_spread", continuous_actions=False)
obs_n = env.reset()
next_obs_n, reward_n, done_n, info_n = env.step(action_n)
```

Supported scenario names:

- `simple`
- `simple_adversary`
- `simple_crypto`
- `simple_push`
- `simple_speaker_listener`
- `simple_spread`
- `simple_tag`
- `simple_world_comm`

Behavior:

- The wrapper converts PettingZoo parallel-env dictionaries to PARL-style lists ordered by `agents_name`.
- `observation_space`, `action_space`, `obs_shape_n`, and `act_shape_n` are lists aligned to the agent order.
- For discrete actions, each input action is interpreted as logits/probabilities and converted with `argmax`.
- For continuous actions, each input action must be in `[-1, 1]` and is mapped to the PettingZoo action space range per agent.

Dependency status:

- The modern wrapper requires PettingZoo MPE plus a compatible Gym release.
- The legacy `parl.env.multiagent_simple_env.MAenv` uses OpenAI's old multiagent-particle-envs package and is deprecated in favor of `parl.env.multiagent_env.MAenv`.

## Replay memory: `ReplayMemory`

Basic usage:

```python
from parl.utils import ReplayMemory

rpm = ReplayMemory(max_size=100000, obs_dim=obs_dim, act_dim=action_dim)
rpm.append(obs, action, reward, next_obs, terminal)
obs_b, act_b, reward_b, next_obs_b, terminal_b = rpm.sample_batch(batch_size)
```

Storage layout:

| Field | Discrete action (`act_dim == 0`) | Continuous action (`act_dim > 0`) |
| --- | --- | --- |
| `obs` | `(max_size, obs_dim)`, `float32` | `(max_size, obs_dim)`, `float32` |
| `action` | `(max_size,)`, `int32` | `(max_size, act_dim)`, `float32` |
| `reward` | `(max_size,)`, `float32` | same |
| `terminal` | `(max_size,)`, `bool` | same |
| `next_obs` | `(max_size, obs_dim)`, `float32` | `(max_size, obs_dim)`, `float32` |

Operational notes:

- The built-in buffer is a circular fixed-capacity buffer. After `max_size` appends, `_curr_pos` wraps and older samples are overwritten.
- `size()` and `len(rpm)` return the current filled size, not the capacity.
- `sample_batch(batch_size)` samples indices uniformly with replacement from the currently filled portion.
- `make_index(batch_size)` and `sample_batch_by_index(batch_idx)` are useful when several learners need the same sample indices.
- `save(pathname)` and `load(pathname)` use NumPy `.npz` files and write/read local files. Use explicit output paths and close over expected capacity when loading.
- `load_from_d4rl(dataset)` expects a dict with `observations`, `next_observations`, `actions`, `rewards`, and `terminals`; it directly adopts the dataset arrays and asserts that the dataset size fits `max_size`.
- Although the constructor docstring mentions list/tuple dimensions, the implementation allocates arrays as `(max_size, obs_dim)` and `(max_size, act_dim)`. Treat `obs_dim` and continuous `act_dim` as flat integer dimensions unless you have verified a patched implementation.

## Small NumPy RL helpers

PARL also exposes small helpers that are often used near replay/rollout code:

```python
from parl.utils import calc_discount_sum_rewards, calc_gae, np_softmax, np_cross_entropy
```

- `calc_discount_sum_rewards(rewards, gamma)` returns reverse discounted sums using `scipy.signal.lfilter`.
- `calc_gae(rewards, values, next_value, gamma, lam)` computes generalized advantage estimates using temporal differences and the same discounted-sum helper.
- `np_softmax(logits)` and `np_cross_entropy(probs, labels)` are simple NumPy helpers. `np_softmax` does not subtract the max logit, so apply a stable softmax yourself if logits may be large.
