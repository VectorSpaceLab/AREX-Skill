# Gymnasium API for HighwayEnv

Use this reference when writing code that resets, steps, seeds, inspects, or closes HighwayEnv environments through the Gymnasium API.

## Imports and registration

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)
```

Importing `highway_env` registers built-in IDs for the current process. Explicit registration is safe and makes the dependency visible in scripts.

## `gym.make` signatures that HighwayEnv supports

Common construction:

```python
env = gym.make("highway-v0")
```

Construction with config:

```python
env = gym.make(
    "highway-v0",
    config={"duration": 5, "vehicles_count": 10},
)
```

Construction with pixel rendering:

```python
env = gym.make(
    "highway-v0",
    render_mode="rgb_array",
    config={"screen_width": 320, "screen_height": 160},
)
```

Construction with a human window:

```python
env = gym.make(
    "highway-v0",
    render_mode="human",
    config={"real_time_rendering": True},
)
```

Most built-in driving environments accept `render_mode` directly. If an environment constructor rejects `render_mode`, make it without rendering for automation or choose a scenario with standard `AbstractEnv(config, render_mode)` construction.

## Reset semantics

Gymnasium reset returns `(obs, info)`:

```python
obs, info = env.reset(seed=0)
```

HighwayEnv also accepts config updates through reset options:

```python
obs, info = env.reset(
    seed=0,
    options={"config": {"duration": 3, "vehicles_count": 6}},
)
```

During reset, HighwayEnv:

- applies `options["config"]` if provided;
- updates render metadata and video FPS;
- rebuilds observation and action spaces;
- resets simulation time and step counters;
- recreates the road, vehicles, and controlled vehicles;
- returns a first observation and an `info` dict.

If a config update changes observation/action types, always reset before reading `observation_space`, `action_space`, or stepping.

## Step semantics

Gymnasium step returns five values:

```python
obs, reward, terminated, truncated, info = env.step(action)
```

- `terminated`: task terminal condition, such as a crash, off-road terminal, arrival, or success condition.
- `truncated`: time limit or configured duration reached. Gymnasium wrappers may add truncation even when the unwrapped environment returns `False`.
- `reward`: usually a scalar float. Multi-agent wrapper variants can return a tuple of per-agent rewards.
- `info`: includes common keys such as `speed`, `crashed`, and `action` for many scenarios; environments with reward decompositions include `info["rewards"]`. Multi-agent intersection variants add `agents_rewards` and `agents_terminated`.

HighwayEnv advances low-level physics multiple times per decision step. The number of simulated frames per action is approximately:

```python
frames_per_action = env.unwrapped.config["simulation_frequency"] // env.unwrapped.config["policy_frequency"]
```

## Safe bounded loop patterns

### One episode with an explicit step cap

```python
obs, info = env.reset(seed=0)
for step_index in range(50):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        break
```

### Multiple episodes without an infinite loop

```python
obs, info = env.reset(seed=0)
episodes_finished = 0
for step_index in range(200):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        episodes_finished += 1
        obs, info = env.reset()
```

Avoid `while True` in smoke tests or automation unless an external timeout is guaranteed.

## Action and observation spaces

Use spaces rather than hard-coded action values when writing generic helpers:

```python
print(env.observation_space)
print(env.action_space)
action = env.action_space.sample()
assert env.observation_space.contains(obs)
```

Common action-space shapes differ by scenario:

- Discrete road tasks use a Gymnasium `Discrete` space, so sampled actions are integers.
- Parking, racetrack, and lane keeping use continuous `Box`-like actions, so sampled actions are numeric arrays.
- Multi-agent configurations use tuple-style observations/actions; the wrapper variants also return per-agent reward/termination tuples.

For detailed observation/action/reward configuration, route to the observations-actions-rewards sub-skill.

## Config inspection

Read the active config from the unwrapped environment:

```python
cfg = env.unwrapped.config
print(cfg["duration"], cfg["simulation_frequency"], cfg["policy_frequency"])
```

Mutate only when you can reset immediately afterward:

```python
env.unwrapped.config.update({"duration": 4, "vehicles_count": 5})
obs, info = env.reset(seed=12)
```

Use `reset(options={"config": ...})` when changing config at episode boundaries in a cleaner, localized way.

## Available action labels

Some discrete meta-action environments expose action labels through the unwrapped action type:

```python
indexes = getattr(env.unwrapped.action_type, "actions_indexes", {})
idle = indexes.get("IDLE")
if idle is not None:
    obs, reward, terminated, truncated, info = env.step(idle)
```

Use `env.unwrapped.get_available_actions()` to ask the current action type for context-dependent available action indices:

```python
available = env.unwrapped.get_available_actions()
```

Not every action type has the same labels or availability semantics.

## Seeding notes

Use `env.reset(seed=seed)` to seed the environment RNG. For reproducible sampled smoke actions, seed the action space too:

```python
seed = 123
obs, info = env.reset(seed=seed)
env.action_space.seed(seed)
```

Repeated `reset(seed=same_seed)` can reproduce scenario initialization; repeated `action_space.sample()` also needs action-space seeding if the random action sequence matters.

## Closing and cleanup

Always close environments that render or may allocate viewer resources:

```python
env = gym.make("highway-v0", render_mode="rgb_array")
try:
    obs, info = env.reset(seed=0)
    frame = env.render()
finally:
    env.close()
```

This is especially important when using `RecordVideo`, human windows, multiprocessing, or vector environments.

## Smoke helper

The bundled `scripts/smoke_env_rollout.py` runs this API pattern from the command line and prints a JSON summary. Use it before longer workflows to verify that registration, construction, reset, stepping, and optional RGB rendering work in the active Python environment.
