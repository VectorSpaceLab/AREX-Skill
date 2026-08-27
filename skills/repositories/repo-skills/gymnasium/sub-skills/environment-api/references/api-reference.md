# Environment API Reference

This reference covers Gymnasium's single-environment lifecycle and registry surface.

## Imports and Creation

```python
import gymnasium as gym

env = gym.make("CartPole-v1", render_mode=None)
```

Key public signatures verified for Gymnasium 1.3.0:

- `gymnasium.make(id, max_episode_steps=None, disable_env_checker=None, **kwargs)` returns an `Env` and applies default wrappers from the registered spec.
- `gymnasium.register(id, entry_point=None, reward_threshold=None, nondeterministic=False, max_episode_steps=None, order_enforce=True, disable_env_checker=False, additional_wrappers=(), vector_entry_point=None, kwargs=None)` adds an `EnvSpec` to the registry.
- `gymnasium.make_vec(id, num_envs=1, vectorization_mode=None, vector_kwargs=None, wrappers=None, **kwargs)` is vector-specific; route lifecycle details to `../vectorization/SKILL.md`.
- `Env.reset(*, seed=None, options=None)` returns `(observation, info)`.
- `Env.step(action)` returns `(observation, reward, terminated, truncated, info)`.

## The Modern Env Loop

```python
import gymnasium as gym

env = gym.make("CartPole-v1")
try:
    observation, info = env.reset(seed=123)
    episode_return = 0.0
    terminated = truncated = False

    while not (terminated or truncated):
        action = env.action_space.sample()
        observation, reward, terminated, truncated, info = env.step(action)
        episode_return += float(reward)
finally:
    env.close()
```

Semantics:

- `observation` must be an element of `env.observation_space`.
- `action` should be an element of `env.action_space`; use `env.action_space.sample()` only for random policies or smoke tests.
- `reward` must be an `int`, `float`, NumPy integer, or NumPy floating scalar.
- `terminated=True` means the task reached a natural terminal state such as success or failure.
- `truncated=True` means an external limit stopped the episode, often a time limit.
- `info` is a Python `dict` for diagnostics and auxiliary data.
- End an episode when `terminated or truncated`; for value bootstrapping, usually bootstrap across `truncated` but not across `terminated`.

## Env Attributes

Every usable environment should expose:

- `action_space`: a Gymnasium `Space` describing valid actions.
- `observation_space`: a Gymnasium `Space` describing valid observations.
- `metadata`: a dictionary such as `{"render_modes": ["human", "rgb_array"], "render_fps": 30}`.
- `render_mode`: the fixed render mode chosen at construction, usually passed through `gym.make(..., render_mode="human")` or `render_mode="rgb_array"`.
- `np_random`: the environment's NumPy random generator, initialized by `super().reset(seed=seed)`.
- `np_random_seed`: the current seed, or `-1` if the RNG was set directly and the seed is unknown.
- `spec`: an `EnvSpec` when the environment was made through the registry.
- `unwrapped`: the base environment beneath wrappers.

Use `../spaces-data/SKILL.md` for space design, sampling, flattening, and dtype/shape details.

## Reset, Seeding, and Reproducibility

For users of an existing environment:

```python
obs, info = env.reset(seed=42)
env.action_space.seed(42)
```

For custom env authors, call `super().reset(seed=seed)` before using `self.np_random`. This initializes both `self.np_random` and `self.np_random_seed`. Passing `seed=None` after a seeded reset keeps advancing the existing generator rather than resetting it to a fixed value.

Do not use old `env.seed(...)`; official support for that pattern was dropped. Use `env.reset(seed=<desired seed>)`.

## Rendering and Closing

Render mode is selected when the environment is created:

```python
human_env = gym.make("CartPole-v1", render_mode="human")
array_env = gym.make("CartPole-v1", render_mode="rgb_array")

human_env.reset()
human_env.render()  # Uses the creation-time mode.
human_env.close()
```

Rules:

- Do not call `env.render(mode="human")`; the mode belongs in `gym.make` or the custom env constructor.
- `render_mode="human"` conventionally returns `None` from `render()`.
- `render_mode="rgb_array"` should return a NumPy array with dtype `uint8`, shape `(height, width, 3)`.
- A mode ending in `_list`, such as `rgb_array_list`, is handled through collection wrappers when the base mode exists.
- `close()` should be safe to call more than once; release windows, file handles, simulators, and subprocess resources.

Use `../wrappers-recording/SKILL.md` for recording videos, `RecordVideo`, `RenderCollection`, `HumanRendering`, and optional media dependencies.

## Registration, Specs, and Default Wrappers

Register custom environments with IDs of the form `namespace/name-vN`, with `namespace/` optional and `-vN` optional:

```python
gym.register(
    id="demo/GridWorld-v0",
    entry_point=GridWorldEnv,
    max_episode_steps=100,
)

env = gym.make("demo/GridWorld-v0", size=7)
spec = gym.spec("demo/GridWorld-v0")
```

Important `EnvSpec` fields include:

- `id`, `namespace`, `name`, `version` parsed from the environment ID.
- `entry_point`, either a callable class/function or a string like `"package.module:EnvClass"`.
- `kwargs`, default constructor arguments merged with `gym.make(..., **kwargs)`.
- `max_episode_steps`, used by `TimeLimit` unless overridden or disabled with `max_episode_steps=-1` at make time.
- `order_enforce`, controlling whether `OrderEnforcing` is applied.
- `disable_env_checker`, controlling whether `PassiveEnvChecker` is skipped.
- `additional_wrappers`, extra wrapper specs applied during `make`.
- `vector_entry_point`, used by vector creation; route details to `../vectorization/SKILL.md`.

`gym.make(...)` wrapper order from the registration code is:

1. Create the raw environment from `entry_point` and kwargs.
2. Set a minimal spec on `env.unwrapped`.
3. Apply `PassiveEnvChecker` unless disabled.
4. Apply `OrderEnforcing` if the spec requests it.
5. Apply `TimeLimit` if a positive spec or make-time `max_episode_steps` is set.
6. Apply registered `additional_wrappers`.
7. Apply render helper wrappers when needed for `human` or `_list` modes.

`gym.pprint_registry(disable_print=True)` returns a formatted registry listing. `gym.registry.keys()` gives raw registered IDs.

## Version and Namespace Rules

- Registering both a versioned and unversioned environment with the same namespace/name is rejected.
- Looking up an old version can raise `DeprecatedEnv` and suggest the latest registered version.
- Looking up an unknown version can raise `VersionNotFound` with available versions.
- Looking up an unknown name raises `NameNotFound`, often with a spelling suggestion.
- Malformed IDs raise an error; stick to `Namespace/Name-v0` or `Name-v0` patterns.
- `gym.envs.registration.namespace("my_namespace")` can scope multiple registrations.

## When to Disable Default Behavior

Use these switches intentionally:

```python
# Skip checker wrapper for hot training after validation.
env = gym.make("demo/GridWorld-v0", disable_env_checker=True)

# Disable TimeLimit even if the spec has max_episode_steps.
env = gym.make("demo/GridWorld-v0", max_episode_steps=-1)

# Override spec time limit for a run.
env = gym.make("demo/GridWorld-v0", max_episode_steps=25)
```

Do not disable `PassiveEnvChecker` or `OrderEnforcing` to hide a broken environment. Validate first with `check_env` and a direct custom-env smoke test.
