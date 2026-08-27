# Environment workflows

This reference is for choosing and instantiating built-in HighwayEnv scenarios. It assumes HighwayEnv and Gymnasium are installed in the active Python environment.

## Registration and `gym.make`

HighwayEnv registers its Gymnasium environments when the `highway_env` package is imported. Calling `gym.register_envs(highway_env)` is also safe and mirrors Gymnasium's explicit plugin registration pattern.

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)  # idempotent for current HighwayEnv releases

env = gym.make("highway-v0")
```

For subprocess workers started with `spawn` or `forkserver`, the child process may not inherit the parent's import side effect. Use Gymnasium's module syntax or import inside the worker factory:

```python
env = gym.make("highway_env:highway-v0")
```

Use exact registered IDs. Gymnasium environment IDs are case-sensitive; the historical parking action-repeat variant is registered as `parking-ActionRepeat-v0`.

## Built-in environment catalog

Prefer the newest connected-lane versions for new experiments where they exist. Older versions are useful for reproducing legacy results.

| Family | Registered IDs | Main use | Default action style | Version guidance |
|---|---|---|---|---|
| Highway | `highway-v0`, `highway-fast-v0` | Multilane highway driving with traffic | Discrete meta actions | `highway-fast-v0` is a faster, shorter, lower-traffic variant for quick RL/debug loops. |
| Merge | `merge-v0`, `merge-v1`, `merge-generic-v0`, `merge-generic-v1` | Enter or negotiate merge traffic | Discrete meta actions | Use `merge-v1` or `merge-generic-v1` for connected-lane neighbour search. |
| Roundabout | `roundabout-v0`, `roundabout-v1`, `roundabout-generic-v0`, `roundabout-generic-v1` | Navigate a roundabout | Discrete meta actions | Use `roundabout-v1` or `roundabout-generic-v1` for connected-lane neighbour search. |
| Parking | `parking-v0`, `parking-ActionRepeat-v0`, `parking-parked-v0` | Goal-conditioned parking | Continuous action | `parking-ActionRepeat-v0` lowers policy frequency and episode duration; `parking-parked-v0` adds parked obstacles. |
| Intersection | `intersection-v0`, `intersection-v1`, `intersection-v2` | Cross unsignalized intersections | Discrete for `v0`/`v2`; continuous for `v1` | Use `intersection-v2` for connected-lane neighbour search unless you specifically need the continuous-action `v1`. |
| Multi-agent intersection | `intersection-multi-agent-v0`, `intersection-multi-agent-v1`, `intersection-multi-agent-v2` | Two controlled vehicles crossing an intersection | Tuple-style multi-agent discrete actions | Use `intersection-multi-agent-v2` for connected-lane neighbour search and the registered multi-agent wrapper. |
| Racetrack | `racetrack-v0`, `racetrack-v1`, `racetrack-large-v0`, `racetrack-large-v1`, `racetrack-oval-v0`, `racetrack-oval-v1` | Continuous lane-following around tracks | Continuous action | Use `v1`/`large-v1`/`oval-v1` for connected-lane neighbour search. |
| Lane keeping | `lane-keeping-v0` | Pure lateral bicycle-dynamics lane following | Continuous action | Gymnasium registration applies a 200-step time limit; the unwrapped env does not internally terminate/truncate. |
| Two way | `two-way-v0` | Overtake while managing oncoming traffic risk | Discrete meta actions | No connected-lane variant is registered. |
| Exit | `exit-v0`, `exit-v1` | Reach a highway exit ramp | Discrete meta actions | Use `exit-v1` for connected-lane neighbour search. |
| U-turn | `u-turn-v0`, `u-turn-v1` | Overtake blocking vehicles through a U-turn | Discrete meta actions | Use `u-turn-v1` for connected-lane neighbour search. |

Connected-lane variants set `neighbour_vehicles_connected_lanes=True` in `env.unwrapped.config` and propagate it to `env.unwrapped.road.neighbour_vehicles_connected_lanes` after reset. Legacy versions keep same-segment neighbour lookup for reproducibility.

## Environment config workflows

HighwayEnv environments are configured by a mutable `env.unwrapped.config` dictionary. At a high level, this config controls observation type, action type, simulation frequency, policy frequency, traffic density/counts, duration, rewards, and rendering size. Detailed observation/action/reward fields are owned by the observations-actions-rewards sub-skill; custom road and vehicle internals are owned by the road-vehicle-dynamics sub-skill.

### Configure at construction

Use this for reproducible scripts where config is known up front:

```python
env = gym.make(
    "highway-v0",
    config={
        "duration": 10,
        "lanes_count": 3,
        "vehicles_count": 20,
        "policy_frequency": 2,
    },
)
```

The constructor builds initial spaces and an initial scene. You should still call `reset(seed=...)` before collecting data.

### Configure an existing environment at reset

Use reset options when a script needs to change scenario parameters between episodes:

```python
env = gym.make("highway-v0")
obs, info = env.reset(
    seed=123,
    options={"config": {"duration": 5, "vehicles_count": 8}},
)
```

During `reset`, HighwayEnv applies `options["config"]`, updates render metadata, rebuilds observation/action spaces, resets time counters, recreates the scene, propagates connected-lane neighbour settings to the road, and returns the first `(obs, info)`.

### Update `env.unwrapped.config` directly

Direct mutation is acceptable for interactive work, but reset before relying on it:

```python
env = gym.make("roundabout-v1")
env.unwrapped.config.update({"duration": 6, "screen_width": 640, "screen_height": 480})
obs, info = env.reset(seed=7)
```

If you change observation or action config, reset is required because spaces and controlled vehicle classes are rebuilt around those settings.

## AbstractEnv lifecycle essentials

All built-in driving scenarios derive from a common environment lifecycle, with a few scenario-specific overrides.

1. Construction loads `default_config()`, applies `config`, defines spaces, and creates an initial scene.
2. `reset(seed=None, options=None)` optionally applies `options["config"]`, resets `time`, `steps`, and `done`, recreates road/vehicles, redefines spaces, and returns `(obs, info)`.
3. `step(action)` advances one policy decision. Internally, it simulates `simulation_frequency // policy_frequency` lower-level physics frames, then returns `(obs, reward, terminated, truncated, info)`.
4. `terminated` means a task terminal condition occurred, such as crash, off-road terminal, or arrival. `truncated` means the environment duration or Gymnasium time limit stopped the episode.
5. `render()` returns a frame only for `render_mode="rgb_array"`; it returns `None` for `human` mode.
6. `close()` closes any viewer and should be called in `finally` blocks.

## Safe one-episode rollout

```python
import gymnasium as gym
import highway_env

gym.register_envs(highway_env)

env = gym.make("merge-v1", config={"duration": 5, "vehicles_count": 8})
try:
    obs, info = env.reset(seed=0)
    for step_index in range(20):  # explicit cap for automation
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
finally:
    env.close()
```

Use `env.action_space.sample()` for generic smoke tests. Hard-coded integer actions are only valid for discrete action spaces; continuous and multi-agent environments expect different action structures.

## Helpful unwrapped environment methods

Call these on `env.unwrapped` after at least one reset. They return copies or helper objects and are mostly useful for planning, diagnostics, or counterfactual simulations rather than ordinary Gymnasium training loops.

```python
env = gym.make("highway-v0", config={"duration": 5})
obs, info = env.reset(seed=0)
base = env.unwrapped

nearby_only = base.simplify()
idm_copy = base.change_vehicles("highway_env.vehicle.behavior.IDMVehicle")
lane_copy = base.set_preferred_lane(0)
route_copy = base.set_route_at_intersection("o1")
```

- `simplify()` deep-copies the current env and keeps the ego vehicle plus nearby vehicles within the perception distance.
- `change_vehicles(vehicle_class_path)` deep-copies the env and converts non-ego vehicles to the requested behavior class path.
- `set_preferred_lane(preferred_lane)` deep-copies the env and changes IDM vehicles' planned lane preference when their routes support lane indices.
- `set_route_at_intersection(_to)` deep-copies the env and asks IDM vehicles to choose a route at the next intersection toward a destination label such as `"o1"`.
- `set_vehicle_field`, `call_vehicle_method`, and `randomize_behavior` are additional copy-returning helpers for counterfactual vehicle behavior changes.

## `to_finite_mdp()` caveats

`env.unwrapped.to_finite_mdp()` converts a suitable discrete road-driving state into a finite time-to-collision MDP. It is not a general Gymnasium wrapper.

```python
env = gym.make("highway-v0")
obs, info = env.reset(seed=0)
mdp = env.unwrapped.to_finite_mdp()
```

Use it only when all of these are true:

- The environment has discrete actions with `env.action_space.n`.
- The controlled vehicle exposes speed-index/target-speed state used by discrete meta actions.
- The optional `finite_mdp` Python package is available.
- A TTC approximation is acceptable for planning; other vehicles are assumed to keep constant speed and lane for the approximation.

For continuous-control scenarios such as parking, racetrack, and lane keeping, use the normal Gymnasium API instead.
