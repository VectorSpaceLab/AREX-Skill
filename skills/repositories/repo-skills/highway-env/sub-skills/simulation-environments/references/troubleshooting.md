# Troubleshooting simulation environments

Use this guide when HighwayEnv registration, reset/step loops, rendering, vectorization, multiprocessing, or helper methods fail.

## `gym.make` cannot find an environment

Typical symptoms:

- `NameNotFound`
- `Environment ... doesn't exist`
- The env works in the parent process but not in a spawned worker

Fixes:

1. Import and register HighwayEnv before `gym.make`:

   ```python
   import gymnasium as gym
   import highway_env

   gym.register_envs(highway_env)
   env = gym.make("highway-v0")
   ```

2. Use the exact registered ID including version suffix, for example `highway-v0`, not `highway`.
3. In spawned/forkserver workers, use module-qualified IDs such as `highway_env:highway-v0` or import/register inside the worker factory.
4. Check case-sensitive historical IDs. The action-repeat parking variant is `parking-ActionRepeat-v0`.
5. If import itself fails, install the `highway-env` package into the active Python environment before running the script.

## Gymnasium warns that an environment is out of date

Some legacy IDs are kept for reproducibility. For new work, prefer connected-lane variants:

- `exit-v1` over `exit-v0`
- `merge-v1` over `merge-v0`
- `merge-generic-v1` over `merge-generic-v0`
- `roundabout-v1` over `roundabout-v0`
- `roundabout-generic-v1` over `roundabout-generic-v0`
- `racetrack-v1`, `racetrack-large-v1`, or `racetrack-oval-v1` over their `v0` counterparts
- `u-turn-v1` over `u-turn-v0`
- `intersection-v2` over `intersection-v0` when discrete actions are acceptable
- `intersection-multi-agent-v2` over older multi-agent variants

Keep older IDs only when reproducing prior results or when a needed variant has no connected-lane replacement, such as continuous `intersection-v1`.

## Config update appears to have no effect

Changing `env.unwrapped.config` does not fully rebuild spaces or the scene until reset.

Use one of these patterns:

```python
env = gym.make("highway-v0", config={"duration": 5, "vehicles_count": 10})
obs, info = env.reset(seed=0)
```

or

```python
env.unwrapped.config.update({"duration": 5, "vehicles_count": 10})
obs, info = env.reset(seed=0)
```

or

```python
obs, info = env.reset(options={"config": {"duration": 5, "vehicles_count": 10}})
```

If you changed observation/action config, reset before reading spaces or calling `step`.

## `render()` returns `None`

`render()` returns a NumPy array only when the environment was created with `render_mode="rgb_array"`.

```python
env = gym.make("highway-v0", render_mode="rgb_array")
obs, info = env.reset(seed=0)
frame = env.render()
```

`render_mode="human"` opens or updates a window and returns `None`. `render_mode=None` performs no rendering and returns `None` with a warning if `render()` is called.

If a specific registered constructor rejects the `render_mode` keyword, create it without that keyword for non-rendered automation. For an RGB smoke check, the bundled smoke helper applies a conservative fallback by setting `env.unwrapped.render_mode` before reset.

## Rendering fails on a headless server

Avoid `render_mode="human"` on headless machines. Use:

```python
env = gym.make("highway-v0", render_mode="rgb_array")
```

Current HighwayEnv derives off-screen rendering from `render_mode`; the old `OFFSCREEN_RENDERING` environment variable is deprecated and ignored. If pygame display errors persist, check that `pygame-ce` is installed and that your code is not forcing `offscreen_rendering=False` or `render_mode="human"`.

## Video is too short, too fast, or misses intermediate motion

Use `RecordVideo` with `render_mode="rgb_array"` and register the wrapper with the unwrapped HighwayEnv instance:

```python
from gymnasium.wrappers import RecordVideo

base_env = gym.make("highway-v0", render_mode="rgb_array", config={"duration": 5})
env = RecordVideo(base_env, video_folder="videos", episode_trigger=lambda episode_id: True)
env.unwrapped.set_record_video_wrapper(env)
```

This lets HighwayEnv capture intermediate physics frames between policy decisions. Also set a short `duration` and a step cap for smoke videos.

## Episode never ends or script hangs

Use both Gymnasium done signals and an external step cap:

```python
for step_index in range(100):
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
    if terminated or truncated:
        break
```

Common causes:

- Ignoring `truncated` and checking only `terminated`.
- Leaving default durations high for smoke tests.
- Using `lane-keeping-v0` unwrapped: it does not internally terminate/truncate; the registered Gymnasium wrapper applies a 200-step limit.
- Running a training example instead of a smoke rollout. Route long training/evaluation to the training-and-evaluation sub-skill.

## Action shape/type errors

Symptoms include `AssertionError`, `ValueError`, or low-level numeric shape errors during `env.step(action)`.

Fixes:

- Use `env.action_space.sample()` in generic smoke code.
- Do not send integer actions to continuous environments such as `parking-v0`, `racetrack-v0`, and `lane-keeping-v0`.
- Do not send continuous arrays to discrete meta-action environments such as `highway-v0`, `merge-v1`, or `roundabout-v1`.
- Multi-agent environments expect tuple-style actions when configured with `MultiAgentAction`.
- Route detailed action config and dimensions to the observations-actions-rewards sub-skill.

## Observation space check fails after reset

If `env.observation_space.contains(obs)` fails:

1. Ensure config was applied before reset or through reset options.
2. Do not mutate observation config after reset without resetting again.
3. For image/grayscale observations, ensure `render_mode`/off-screen rendering and screen dimensions are compatible with the observation config.
4. Route detailed observation-space diagnosis to the observations-actions-rewards sub-skill.

## Vectorized environment errors

Common causes:

- Worker factory forgot to import/register HighwayEnv.
- Per-env configs produce incompatible observation or info structures.
- Custom wrappers add object-valued `info` entries that cannot stack cleanly.
- A zero-action array was used for a tuple or continuous action space with incompatible shape.

Safer patterns:

```python
def make_env():
    import gymnasium as gym
    import highway_env
    gym.register_envs(highway_env)
    return gym.make("highway-v0", config={"duration": 2})
```

or for subprocess-safe module loading:

```python
env = gym.make("highway_env:highway-v0")
```

Use `envs.action_space.sample()` unless the vector action-space structure is known.

## Multi-agent wrapper surprises

`intersection-multi-agent-v1` and `intersection-multi-agent-v2` return tuple rewards and tuple terminations through `MultiAgentWrapper`:

```python
obs, reward, terminated, truncated, info = env.step(action)
# reward may be a tuple, terminated may be a tuple, truncated remains bool-like
```

Choose your done convention explicitly:

```python
any_done = any(terminated) if isinstance(terminated, tuple) else bool(terminated)
all_done = all(terminated) if isinstance(terminated, tuple) else bool(terminated)
```

The unwrapped `info` contains `agents_rewards` and `agents_terminated` for per-agent diagnostics.

## `to_finite_mdp()` fails

Possible causes:

- The optional `finite_mdp` Python package is not installed.
- The environment uses continuous actions and lacks `action_space.n`.
- The current controlled vehicle lacks the discrete speed-index state expected by the TTC approximation.

Use `to_finite_mdp()` only for suitable discrete road-driving tasks after reset:

```python
env = gym.make("highway-v0")
obs, info = env.reset(seed=0)
mdp = env.unwrapped.to_finite_mdp()
```

If a finite-MDP approximation is not essential, use normal Gymnasium rollouts instead.

## Helper methods appear to change nothing

Methods such as `simplify()`, `change_vehicles()`, `set_preferred_lane()`, and `set_route_at_intersection()` return deep-copied environment objects. They do not mutate the original Gymnasium wrapper in place.

```python
copy_env = env.unwrapped.simplify()
```

Use the returned copy for planning/diagnostics, or keep using the original `env` for ordinary Gymnasium rollouts.

## Smoke script returns `ok: false`

Run the bundled smoke helper with a small config first. From this sub-skill directory:

```bash
python scripts/smoke_env_rollout.py \
  --env-id highway-v0 --steps 3 --duration 3 --vehicles-count 5 --seed 0
```

If that fails, inspect the JSON `error_type` and `error` fields. Registration/name errors usually require import/installation fixes; render errors usually require `--render-rgb` instead of `--render-mode human`; action errors usually mean the selected env has a different action-space type than expected.
