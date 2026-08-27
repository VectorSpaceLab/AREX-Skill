# Migration and Validation

Use this reference when updating old OpenAI Gym code or proving that a custom Gymnasium environment follows the modern API.

## Old Gym to Gymnasium Checklist

| Old pattern | Modern Gymnasium pattern | Why it matters |
| --- | --- | --- |
| `import gym` | `import gymnasium as gym` | Gymnasium is a separate maintained package. |
| `obs = env.reset()` | `obs, info = env.reset()` | Reset now returns initial info. |
| `env.seed(42)` | `obs, info = env.reset(seed=42)` | Seeds are applied at episode reset. |
| `obs, reward, done, info = env.step(action)` | `obs, reward, terminated, truncated, info = env.step(action)` | Natural endings and time/external cutoffs are separate. |
| `while not done:` | `while not (terminated or truncated):` | Either signal ends the episode. |
| `env.render(mode="human")` | `gym.make(env_id, render_mode="human")`; then `env.render()` | Render mode is fixed at creation. |
| `info.get("TimeLimit.truncated")` | use the `truncated` return value | Time limits are no longer hidden in `info`. |
| `target = reward + (1 - done) * gamma * value` | bootstrap on `not terminated`; handle `truncated` separately | Truncation can still have future value. |

## Training Loop Migration

Old style:

```python
import gym

env = gym.make("CartPole-v1")
env.seed(123)
obs = env.reset()
done = False
while not done:
    action = env.action_space.sample()
    obs, reward, done, info = env.step(action)
```

Modern style:

```python
import gymnasium as gym

env = gym.make("CartPole-v1")
obs, info = env.reset(seed=123)
terminated = truncated = False
while not (terminated or truncated):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
env.close()
```

For quick migration of loop control only:

```python
done = terminated or truncated
```

For RL algorithms, keep the distinction:

```python
if terminated:
    next_value = 0.0
elif truncated:
    next_value = value_function(next_obs)
else:
    next_value = value_function(next_obs)
```

A time limit truncation is not the same as task failure. Treating all `done` values as terminal can bias value targets.

## Step API Compatibility Utilities

Gymnasium provides conversion helpers in `gymnasium.utils.step_api_compatibility`:

```python
from gymnasium.utils.step_api_compatibility import (
    convert_to_done_step_api,
    convert_to_terminated_truncated_step_api,
    step_api_compatibility,
)

obs, reward, terminated, truncated, info = convert_to_terminated_truncated_step_api(
    old_step_returns,
    is_vector_env=False,
)

obs, reward, done, info = convert_to_done_step_api(
    modern_step_returns,
    is_vector_env=False,
)
```

Notes:

- Old single-env `done` returns may encode time-limit truncation in `info["TimeLimit.truncated"]`.
- Conversion to modern API removes `TimeLimit.truncated` from `info` and returns separate booleans.
- Vector conversion has additional info layout cases; route vector loop details to `../vectorization/SKILL.md`.
- These helpers are useful for adapters and tests, but new custom environments should implement the modern 5-return API directly.

## Validation with `check_env`

Signature:

```python
from gymnasium.utils.env_checker import check_env

check_env(env, warn=None, skip_render_check=False, skip_close_check=False)
```

What it checks:

- `env` inherits from `gymnasium.Env`, not old `gym.Env`.
- `action_space` and `observation_space` exist and are valid spaces.
- Reset signature accepts `seed` and `options` and returns `(obs, info)`.
- Reset seeding is deterministic for the same seed and different for different seeds where expected.
- Step returns valid observation, numeric reward, boolean `terminated` and `truncated`, and dict `info`.
- Step determinism holds for the same seed and action when the environment claims determinism.
- Render modes match metadata unless `skip_render_check=True`.
- Closing a made environment is safe, unless `skip_close_check=True`.

Common invocation:

```python
raw_env = MyEnv()
check_env(raw_env, skip_render_check=True)
```

Use `skip_render_check=True` for headless CI or when render dependencies are optional. Use `skip_close_check=True` only when close behavior is unavailable in the current backend; document why.

## Passive Checker from `gym.make`

`gym.make` normally wraps custom envs with `PassiveEnvChecker` unless `disable_env_checker=True` is set in registration or make-time arguments. This wrapper checks the first reset, step, and render calls and emits warnings/errors for API mismatches.

Default wrapper behavior from `gym.make`:

```text
TimeLimit<OrderEnforcing<PassiveEnvChecker<RawEnv>>>
```

Actual wrappers depend on `max_episode_steps`, `order_enforce`, `disable_env_checker`, render mode, and additional wrapper specs. Use wrapper details and recording/transform catalogs from `../wrappers-recording/SKILL.md`.

Do not use `disable_env_checker=True` until the raw env passes `check_env` or you have a clear performance reason in production training.

## Validation Triage

When `check_env` fails, triage in this order:

1. Is the class a `gymnasium.Env` subclass rather than old `gym.Env`?
2. Are `action_space` and `observation_space` defined before reset/step calls?
3. Does `reset` accept `seed` and `options` and call `super().reset(seed=seed)`?
4. Does `reset` return exactly `(obs, info)` with `info` as a dict?
5. Does `step` return exactly five values with separate boolean `terminated` and `truncated`?
6. Are all observations inside `observation_space`, including dtype and shape?
7. Are rewards numeric and finite?
8. Does `render_mode` appear in `metadata["render_modes"]`, and does `render()` return the mode-specific type?
9. Is `close()` idempotent and resource-safe?

## Reproducibility Checks

A deterministic reset smoke test:

```python
env = MyEnv()
obs1, info1 = env.reset(seed=123)
obs2, info2 = env.reset(seed=123)
assert env.observation_space.contains(obs1)
assert env.observation_space.contains(obs2)
```

If observations differ for identical seeds, check for:

- Missing `super().reset(seed=seed)`.
- Randomness from global `np.random` instead of `self.np_random`.
- Sampling from spaces with independent RNGs that were not seeded intentionally.
- Mutable observations returned by reference and later modified.

For reproducible random actions, also seed the action space:

```python
env.action_space.seed(123)
```

## Registration Validation

After registration:

```python
spec = gym.spec("demo/GridWorld-v0")
assert spec.id == "demo/GridWorld-v0"

env = gym.make("demo/GridWorld-v0", max_episode_steps=25)
assert env.spec is not None
print(env.spec.max_episode_steps)
env.close()
```

Validate:

- The ID follows `namespace/name-vN` unless you intentionally omit the optional namespace or version.
- You do not mix versioned and unversioned registrations for the same namespace/name.
- Make-time kwargs are accepted by the env constructor.
- `max_episode_steps` creates or overrides `TimeLimit` behavior.
- `disable_env_checker`, if used, is justified.
- `gym.pprint_registry(disable_print=True)` includes your ID when registry visibility matters.

## Native Verification Candidates

For integrated repo-skill verification, useful source-backed candidates include:

- Core env and wrapper semantics from Gymnasium's core tests.
- Registration and make behavior for `TimeLimit`, `OrderEnforcing`, `PassiveEnvChecker`, specs, and version errors.
- Env checker tests for reset signatures, seed determinism, return shapes, and step validation.
- Step API compatibility tests for old/new conversion semantics.

Keep these as verification evidence only. Do not make runtime skill content depend on the original test paths.
