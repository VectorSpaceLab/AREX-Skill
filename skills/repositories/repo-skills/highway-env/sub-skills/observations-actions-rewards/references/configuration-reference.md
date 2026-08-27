# HighwayEnv observation/action configuration reference

HighwayEnv environments use a nested configuration dictionary. The two keys
owned by this sub-skill are usually:

```python
config = {
    "observation": {"type": "Kinematics"},
    "action": {"type": "DiscreteMetaAction"},
}
```

Create an env with the config directly, or change it at reset time:

```python
import gymnasium as gym
import highway_env  # registers HighwayEnv ids

env = gym.make("highway-v0", config=config)
obs, info = env.reset(seed=0)

obs, info = env.reset(options={"config": {
    "observation": {"type": "Kinematics", "vehicles_count": 10},
    "action": {"type": "DiscreteMetaAction", "target_speeds": [20, 25, 30]},
}})
```

After a reset-time config update, HighwayEnv rebuilds `observation_type`,
`action_type`, `observation_space`, and `action_space`. Always inspect the new
spaces before assuming a previous model, policy, or wrapper still matches.

## Safe validation workflow

1. Start from the environment id's default observation/action style when
   possible. For example, `parking-v0` defaults to goal observations and
   continuous actions, while `highway-v0` defaults to kinematics and discrete
   meta-actions.
2. Provide nested dicts for `observation` and `action`, not strings.
3. Reset once and check both `env.observation_space` and `env.action_space`.
4. Sample one action from the space and check whether the returned observation is
   contained by the observation space.
5. Inspect `info` after a step; `info["rewards"]` is present only for envs that
   implement decomposed rewards, while parking exposes `info["is_success"]`.
6. For custom environment subclasses that use `highway_env.utils.update_config`,
   make nested overrides complete. That validator reports paths such as
   `config.observation invalid: missing_keys=...` and
   `config.action must be a mapping, got str`.

The bundled `scripts/inspect_spaces.py` automates steps 2-5 without running a
long rollout.

## Complete config snippets

### Nearby vehicle table for highway/intersection-style tasks

```python
config = {
    "observation": {
        "type": "Kinematics",
        "vehicles_count": 15,
        "features": ["presence", "x", "y", "vx", "vy", "cos_h", "sin_h"],
        "features_range": {
            "x": [-100, 100],
            "y": [-100, 100],
            "vx": [-20, 20],
            "vy": [-20, 20],
        },
        "absolute": False,
        "order": "sorted",
        "normalize": True,
        "clip": True,
    },
    "action": {"type": "DiscreteMetaAction"},
}
```

Expected observation space: `Box(..., shape=(15, 7), dtype=float32)`. The first
row is the ego vehicle; unused rows are zeros and can be detected with the
`presence` feature.

### Occupancy grid for convolutional or spatial policies

```python
config = {
    "observation": {
        "type": "OccupancyGrid",
        "features": ["presence", "x", "y", "vx", "vy", "cos_h", "sin_h"],
        "features_range": {
            "x": [-100, 100],
            "y": [-100, 100],
            "vx": [-20, 20],
            "vy": [-20, 20],
        },
        "grid_size": [[-27.5, 27.5], [-27.5, 27.5]],
        "grid_step": [5, 5],
        "absolute": False,
        "align_to_vehicle_axes": False,
        "as_image": False,
    },
    "action": {"type": "DiscreteMetaAction"},
}
```

Expected observation space: channels first, `Box(..., shape=(7, 11, 11),
dtype=float32)`. Cell counts are `floor((max - min) / step)` per axis.

### Time-to-collision for risk-aware discrete driving

```python
config = {
    "observation": {"type": "TimeToCollision", "horizon": 10},
    "action": {"type": "DiscreteMetaAction"},
}
```

Expected observation shape is usually `(3, 3, horizon * policy_frequency)`: three
ego speed hypotheses, three lanes around the current lane, and time bins.

### Parking goal observation with continuous controls

```python
config = {
    "observation": {
        "type": "KinematicsGoal",
        "features": ["x", "y", "vx", "vy", "cos_h", "sin_h"],
        "scales": [100, 100, 5, 5, 1, 1],
        "normalize": False,
    },
    "action": {"type": "ContinuousAction"},
}
```

Expected observation space is a dict with `observation`, `achieved_goal`, and
`desired_goal`, each length 6. The parking reward and `info["is_success"]` are
computed from this goal representation even when a non-goal observation is used
for the agent.

### One-axis continuous steering control

```python
config = {
    "observation": {
        "type": "OccupancyGrid",
        "features": ["presence", "on_road"],
        "grid_size": [[-18, 18], [-18, 18]],
        "grid_step": [3, 3],
        "align_to_vehicle_axes": True,
    },
    "action": {
        "type": "ContinuousAction",
        "longitudinal": False,
        "lateral": True,
        "dynamical": True,
        "steering_range": [-1.0471975511965976, 1.0471975511965976],
    },
}
```

Expected action space: `Box(-1.0, 1.0, shape=(1,), dtype=float32)`. A two-value
action will not match this space.

### Multi-agent intersection observations/actions

```python
config = {
    "observation": {
        "type": "MultiAgentObservation",
        "observation_config": {
            "type": "Kinematics",
            "vehicles_count": 15,
            "features": ["presence", "x", "y", "vx", "vy", "cos_h", "sin_h"],
            "features_range": {
                "x": [-100, 100],
                "y": [-100, 100],
                "vx": [-20, 20],
                "vy": [-20, 20],
            },
            "absolute": True,
            "observe_intentions": False,
        },
    },
    "action": {
        "type": "MultiAgentAction",
        "action_config": {
            "type": "DiscreteMetaAction",
            "longitudinal": True,
            "lateral": False,
            "target_speeds": [0, 4.5, 9],
        },
    },
    "controlled_vehicles": 2,
}
```

Expected spaces are tuples, one observation/action subspace per controlled
vehicle. Actions passed to `step()` must be tuples matching the action space.
