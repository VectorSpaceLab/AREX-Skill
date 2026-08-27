# Environment API Troubleshooting

Use this guide to diagnose `make`, `reset`, `step`, registration, render, and checker failures.

## `reset` Returns Only an Observation

Symptom:

```text
The result returned by `env.reset()` was not a tuple of the form `(obs, info)`
```

Fix:

```python
def reset(self, *, seed=None, options=None):
    super().reset(seed=seed)
    observation = self._get_obs()
    info = self._get_info()
    return observation, info
```

Also update callers:

```python
obs, info = env.reset(seed=123)
```

## Missing `super().reset(seed=seed)`

Symptoms:

- `check_env` says the RNG was not generated when a seed was passed.
- Same seed does not reproduce observations.
- Different seeds do not change observations.

Fix:

```python
def reset(self, *, seed=None, options=None):
    super().reset(seed=seed)
    self._state = self.np_random.integers(...)
    return obs, info
```

Avoid global `np.random` for environment randomness unless you intentionally manage and document a separate RNG.

## Old `done` Step API

Symptom:

```text
Core environment is written in old step API which returns one bool instead of two.
```

Fix new envs directly:

```python
terminated = reached_goal or failed_task
truncated = hit_external_limit
return obs, reward, terminated, truncated, info
```

For compatibility adapters only, use `gymnasium.utils.step_api_compatibility.convert_to_terminated_truncated_step_api(...)`.

## Confusing `terminated` and `truncated`

Use `terminated=True` when the MDP task naturally ends: goal reached, agent failed, game over, unsafe state, or terminal absorbing state.

Use `truncated=True` when an outside limit stops the episode: time limit, step budget, wall-clock cutoff, evaluator cutoff, or dataset boundary.

Loop control often uses:

```python
done = terminated or truncated
```

Value bootstrapping usually uses `terminated`, not `done`:

```python
bootstrap_mask = 0.0 if terminated else 1.0
```

If a time limit ends the episode, the value function may still need to estimate future value.

## Step Called Before Reset

Symptom:

- `OrderEnforcing` raises an error when `env.step(...)` is called before `env.reset()`.

Fix:

```python
env = gym.make("CartPole-v1")
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
```

Do not disable `OrderEnforcing` to hide this. Reset at the beginning of each episode and after `terminated or truncated`.

## Render Mode Passed to `render()`

Old pattern:

```python
env.render(mode="human")
```

Modern pattern:

```python
env = gym.make("CartPole-v1", render_mode="human")
env.reset()
env.render()
```

If a custom env supports rendering, store the constructor argument as `self.render_mode` and declare supported modes in `metadata["render_modes"]`.

## Render Checker Warnings

Common warnings and fixes:

- No `metadata["render_modes"]`: add `metadata = {"render_modes": [...], "render_fps": 30}`.
- `render_mode` not in metadata: validate in `__init__` or add the supported mode.
- `human` returns a frame: return `None` for human display.
- `rgb_array` returns the wrong type: return a `np.ndarray` with dtype `uint8`, three axes, and last dimension `3`.
- `ansi` or `ascii` returns non-string data: return `str`.
- Alternative render modes fail in `check_env`: instantiate through `gym.make` with a valid `spec`, or use `skip_render_check=True` in headless contexts and test rendering separately.

For recording and render wrappers, route to `../wrappers-recording/SKILL.md`.

## Close Warnings

Symptom:

- `check_env` warns that calling `env.close()` on a closed environment raised an exception.

Fix:

```python
def close(self):
    if self.window is not None:
        self.window.close()
        self.window = None
```

Make `close()` idempotent. Guard every resource release with a state check.

## Observation or Action Not in Space

Symptoms:

- `The first element returned by env.reset() is not within the observation space.`
- `The obs returned by step() is not within the observation space.`
- Warnings about dtype, shape, tuple/dict keys, or scalar types.

Fixes:

- Match `Box` dtype exactly, e.g. return `np.array(..., dtype=np.float32)` for `spaces.Box(..., dtype=np.float32)`.
- Match `Dict` keys exactly; no missing or extra keys.
- Match `Tuple` length exactly.
- Clip or otherwise constrain observations to declared bounds.
- Validate manually with `env.observation_space.contains(obs)` and `env.action_space.contains(action)`.

Use `../spaces-data/SKILL.md` for detailed dtype, shape, and flattening diagnostics.

## Invalid Env ID or Registry Errors

Valid ID shape:

```text
namespace/name-vN
```

Examples:

- `CartPole-v1`
- `demo/GridWorld-v0`
- `MyEnv` if intentionally unversioned

Common errors:

- `NameNotFound`: environment name is unknown; inspect `gym.registry.keys()` or `gym.pprint_registry()` and check spelling.
- `NamespaceNotFound`: namespace is unknown; check the prefix before `/` or import/register the package first.
- `VersionNotFound`: requested version does not exist; use an available version.
- `DeprecatedEnv`: an older version was requested; switch to the suggested latest version if compatible.
- `RegistrationError` for versioned/unversioned conflicts: do not register both `demo/MyEnv` and `demo/MyEnv-v0`.
- Malformed ID: remove unsupported punctuation or smart quotes and follow the ID pattern.

If an ID uses module syntax like `module:Env-v0`, ensure importing that module performs registration.

## Registration Conflicts During Repeated Script Runs

Symptom:

- Warning about overriding an environment already in the registry.

For smoke scripts, either tolerate the warning, check before registering, or delete only your own demo ID. For library code, avoid repeated side-effect registrations in import paths unless that is the package's intended plugin behavior.

Safer local script pattern:

```python
if "demo/GridWorld-v0" not in gym.registry:
    gym.register(id="demo/GridWorld-v0", entry_point=GridWorldEnv)
```

## `gym.make` Constructor Keyword Error

Symptom:

```text
got an unexpected keyword argument 'render_mode'
```

Fix custom env constructor:

```python
def __init__(self, render_mode=None, size=5):
    self.render_mode = render_mode
```

If a make-time kwarg such as `size=10` fails, add it to `__init__` or remove it from `gym.make(...)`.

## Old OpenAI Gym Class Incompatibility

Symptom:

```text
Gym is incompatible with Gymnasium, please update the environment class to `gymnasium.Env`.
```

Fix:

```python
import gymnasium as gym

class MyEnv(gym.Env):
    ...
```

If you must load old Gym environments, use compatibility packages such as Shimmy and keep the adapter boundary explicit.

## Default Wrapper Confusion

When `gym.make` returns a chain like:

```text
<TimeLimit<OrderEnforcing<PassiveEnvChecker<MyEnv<demo/MyEnv-v0>>>>>
```

Interpretation:

- `PassiveEnvChecker` validates first interactions.
- `OrderEnforcing` requires reset before step/render where appropriate.
- `TimeLimit` emits `truncated=True` after `max_episode_steps`.

Use `env.unwrapped` for the raw custom environment and `env.spec` for spec metadata. For wrapper authoring and catalogs, route to `../wrappers-recording/SKILL.md`.

## Built-in Env or Extra Missing

This sub-skill covers the API surface, not optional environment family installation. If `gym.make("ALE/..." )`, Box2D, MuJoCo, Toy Text, Classic Control rendering, or media/video extras fail, route to `../builtin-envs/SKILL.md` and `../wrappers-recording/SKILL.md` as appropriate.

Known dependency boundary: `gymnasium.utils.save_video` requires `moviepy` through `gymnasium[other]` in a base install.
