# Vectorized Environments And Wrappers

SB3 trains on `VecEnv` objects internally. A vectorized env batches multiple independent env instances so actions, observations, rewards, and done flags include a leading `n_envs` dimension. Even a single Gymnasium env is usually wrapped in a VecEnv by SB3.

## Choosing A VecEnv

Use `stable_baselines3.common.env_util.make_vec_env` for most cases:

```python
from stable_baselines3.common.env_util import make_vec_env

vec_env = make_vec_env("CartPole-v1", n_envs=4, seed=123)
```

Selection guidance:

- `DummyVecEnv`: default from `make_vec_env`; runs envs sequentially in the current process. Prefer it for cheap envs, debugging, notebooks, and envs that are hard to pickle.
- `SubprocVecEnv`: runs each env in a subprocess. Use it for expensive env stepping only after confirming the env factory is picklable and guarded by `if __name__ == "__main__":` for spawn/forkserver platforms.
- Direct constructors: use `DummyVecEnv([make_env_0, make_env_1])` or `SubprocVecEnv([...])` when each env needs distinct construction.

Do not create vectorized envs with lambdas returning the same env instance, such as `DummyVecEnv([lambda: env] * 4)`. Each factory must create a new env object.

## `make_vec_env` Wrapping Order

`make_vec_env` does the following for each sub-env:

1. Creates the env from an env id, class, or callable.
2. Seeds the action space immediately when a seed is provided.
3. Wraps each env in `Monitor`; with `monitor_dir=None`, no file is written but episode info is still provided.
4. Applies `wrapper_class` after `Monitor` when provided.
5. Builds the chosen VecEnv class, defaulting to `DummyVecEnv`.
6. Calls `vec_env.seed(seed)` so seeds are applied at the next `vec_env.reset()`.

Because the custom `wrapper_class` is applied after `Monitor`, be careful with wrappers that change termination behavior or need to observe raw episode endings.

## VecEnv API Is Not Gymnasium API

SB3 VecEnv follows an SB3-specific API close to older Gym vector APIs:

- `obs = vec_env.reset()` returns only observations, not `(obs, info)`.
- Reset info is stored in `vec_env.reset_infos`.
- `obs, rewards, dones, infos = vec_env.step(actions)` returns four values, not Gymnasium's five.
- `dones = terminated or truncated` for each environment.
- `infos[i]["TimeLimit.truncated"] = truncated and not terminated` records timeout-style truncation.
- VecEnv auto-resets an environment when `done[i]` is true.
- The observation returned at `obs[i]` when `done[i]` is true is the first observation of the next episode.
- The final observation of the just-ended episode is stored in `infos[i]["terminal_observation"]`.
- `vec_env.reset()` takes no `seed` or `options`; call `vec_env.seed(seed)` or `vec_env.set_options(options)` before the next reset.

When converting `dones` back to Gymnasium-style booleans for one env index:

```python
terminated = dones[i] and not infos[i].get("TimeLimit.truncated", False)
truncated = dones[i] and infos[i].get("TimeLimit.truncated", False)
```

## Monitor And VecMonitor

`Monitor` wraps a single Gymnasium env and records episode return, length, elapsed time, optional reset keywords, and optional info keywords. `make_vec_env` applies it automatically to each sub-env.

Use Monitor data through:

- `info["episode"]` at episode end.
- `env.get_episode_rewards()`, `get_episode_lengths()`, and `get_episode_times()` on a direct `Monitor` instance.
- Monitor CSV files when `filename` or `monitor_dir` is provided.

Use `VecMonitor` when wrapping a VecEnv that was not created through `make_vec_env` or when you need vector-level episode monitoring.

## Safety And Normalization Wrappers

Common vector wrappers:

- `VecCheckNan(venv, raise_exception=False, warn_once=True, check_inf=True)`: warns or raises when actions, observations, rewards, or dones contain NaN/Inf. Use `raise_exception=True` during debugging.
- `VecNormalize(venv, training=True, norm_obs=True, norm_reward=True, clip_obs=10.0, clip_reward=10.0, gamma=0.99, epsilon=1e-8, norm_obs_keys=None)`: normalizes Box observations and rewards using running statistics.
- `VecFrameStack(venv, n_stack, channels_order=None)`: stacks frames for image-like or temporal observations and propagates `terminal_observation` when available.
- `VecTransposeImage`: handles channel-last image observations for CNN-compatible processing when SB3 detects it.
- `VecExtractDictObs(venv, key)`: extracts a single key from dict observations before algorithms that expect a non-dict observation.

For dict observations with `VecNormalize`, pass `norm_obs_keys` when only some dict keys are Box spaces or when image keys should not be normalized. `VecNormalize` supports `Box` and `Dict` observations; for `Dict`, selected keys must be `Box` spaces.

## Dict And Image Routing

- Use one-level `spaces.Dict` observations for mixed image/vector inputs.
- Use `MultiInputPolicy` for algorithms that consume dict observations.
- Keep image leaves as `np.uint8` in `[0, 255]` unless deliberately using normalized channel-first images with policy-level image normalization disabled.
- Use `VecFrameStack` carefully with dict observations; it can stack selected structures but relies on correct `terminal_observation` propagation.
- If an algorithm or policy expects a flat/vector observation, extract or flatten dict keys before training rather than silently changing env returns.

## SubprocVecEnv Caveats

`SubprocVecEnv` defaults to `forkserver` when available and `spawn` otherwise. These start methods are safer around non-thread-safe libraries but require importable env factories and a main guard:

```python
if __name__ == "__main__":
    vec_env = make_vec_env(MyEnv, n_envs=4, vec_env_cls=SubprocVecEnv)
```

Avoid subprocess vectorization when:

- The env factory closes over unpicklable objects.
- The env depends on notebook-local definitions.
- The env is faster to step than the subprocess IPC overhead.
- Global mutable state is used instead of per-env instance state.

