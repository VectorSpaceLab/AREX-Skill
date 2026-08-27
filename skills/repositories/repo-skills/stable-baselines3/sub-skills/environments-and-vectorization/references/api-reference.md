# Environment API Reference

This reference captures the SB3 environment helpers most often needed when creating or debugging custom envs and vectorized env stacks.

## Env Checker

```python
from stable_baselines3.common.env_checker import check_env

check_env(env, warn=True, skip_render_check=True) -> None
```

Parameters:

- `env`: a `gymnasium.Env` instance.
- `warn`: when true, emit SB3 compatibility warnings in addition to hard API assertions.
- `skip_render_check`: when true, do not call render during checking.

Checks include env inheritance, `observation_space`/`action_space` existence, `reset(seed=0)` support, `reset()`/`step()` return arity, observation shape/dtype/bounds/keys, reward and done types, render metadata when enabled, goal-env reward vectorization, and NaN/Inf probing through `VecCheckNan(DummyVecEnv([lambda: env]))` when supported.

## `make_vec_env`

```python
from stable_baselines3.common.env_util import make_vec_env

make_vec_env(
    env_id,
    n_envs=1,
    seed=None,
    start_index=0,
    monitor_dir=None,
    wrapper_class=None,
    env_kwargs=None,
    vec_env_cls=None,
    vec_env_kwargs=None,
    monitor_kwargs=None,
    wrapper_kwargs=None,
)
```

Key behavior:

- `env_id` can be a Gymnasium id string, env class, or callable returning an env.
- `vec_env_cls=None` means `DummyVecEnv`.
- `monitor_dir=None` still applies `Monitor` but does not write Monitor CSV files.
- `wrapper_class` is applied after `Monitor` to each sub-env.
- `seed` is applied to action spaces immediately and to env resets on the next `vec_env.reset()`.

## `Monitor`

```python
from stable_baselines3.common.monitor import Monitor

Monitor(
    env,
    filename=None,
    allow_early_resets=True,
    reset_keywords=(),
    info_keywords=(),
    override_existing=True,
)
```

The wrapped env still uses Gymnasium returns:

- `reset(**kwargs) -> (obs, info)`.
- `step(action) -> (obs, reward, terminated, truncated, info)`.

At episode end, `Monitor` adds `info["episode"] = {"r": return, "l": length, "t": elapsed_seconds, ...}` and optionally logs rows to `filename`.

## VecEnv Constructors

```python
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

DummyVecEnv(env_fns)
SubprocVecEnv(env_fns, start_method=None)
```

- `env_fns` is a list of zero-argument callables, each returning a fresh Gymnasium env instance.
- `DummyVecEnv` executes in-process and rejects factories that return the same env instance multiple times.
- `SubprocVecEnv` executes envs in child processes; `start_method` must be supported by Python multiprocessing on the host.

## VecEnv Methods And Returns

```python
obs = vec_env.reset()
obs, rewards, dones, infos = vec_env.step(actions)
vec_env.seed(seed)
vec_env.set_options(options)
vec_env.get_attr("name", indices=None)
vec_env.set_attr("name", value, indices=None)
vec_env.env_method("method_name", *args, indices=None, **kwargs)
```

Notes:

- `actions` must have a leading dimension of `num_envs`.
- `obs`, `rewards`, and `dones` are batched; `infos` is a list of dicts.
- `seed()` and `set_options()` affect the next reset only.
- Use `env_method()` or setter methods for wrapped env attributes rather than reaching through wrappers directly.

## Vector Wrappers

```python
from stable_baselines3.common.vec_env import VecCheckNan, VecFrameStack, VecNormalize

VecCheckNan(venv, raise_exception=False, warn_once=True, check_inf=True)
VecFrameStack(venv, n_stack, channels_order=None)
VecNormalize(
    venv,
    training=True,
    norm_obs=True,
    norm_reward=True,
    clip_obs=10.0,
    clip_reward=10.0,
    gamma=0.99,
    epsilon=1e-8,
    norm_obs_keys=None,
)
```

`VecNormalize` supports `Box` observations and one-level `Dict` observations whose normalized keys are `Box` spaces. For image-like observations, normalization changes exposed observation bounds/dtype to normalized float ranges; coordinate policy preprocessing accordingly.

