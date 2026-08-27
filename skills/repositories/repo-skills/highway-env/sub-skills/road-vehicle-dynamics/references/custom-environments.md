# Custom environment implementation guide

This reference explains how to implement a custom HighwayEnv-style environment while keeping road/vehicle dynamics, Gymnasium registration, and reward/termination code separated. For general `gym.make`, reset/step/render usage, use the simulation sub-skill. For detailed observation/action configuration, use the observations/actions/rewards sub-skill.

## Custom environment lifecycle

A custom environment should subclass `highway_env.envs.common.abstract.AbstractEnv`. The base class handles:

1. storing and merging the configuration;
2. creating observation/action type objects from `config["observation"]` and `config["action"]`;
3. calling `_reset()` during `reset()`;
4. copying `config["neighbour_vehicles_connected_lanes"]` onto `self.road` after `_reset()`;
5. simulating several road steps per policy action in `_simulate()`;
6. returning `(obs, reward, terminated, truncated, info)` from `step()`.

The subclass owns the scene, rewards, and episode end conditions.

## Required and common methods

| Method | Required? | Purpose |
|---|---:|---|
| `@classmethod default_config(cls)` | Yes for configurable envs | Start from `super().default_config()` and merge scenario-specific defaults. |
| `_reset(self)` | Yes | Rebuild a fresh road and vehicles. Usually calls `_create_road()` and `_create_vehicles()` or `_make_road()` and `_make_vehicles()`. |
| `_reward(self, action)` | Yes | Return the scalar reward for the last policy action. |
| `_rewards(self, action)` | Optional but recommended | Return a dict of reward components for `info["rewards"]` and easier debugging. |
| `_is_terminated(self)` | Yes | Return true for terminal task outcomes such as crash, success, or off-road terminal. |
| `_is_truncated(self)` | Yes | Return true for time-limit or administrative cutoffs. |
| `_info(self, obs, action=None)` | Optional | Extend base info with task-specific fields such as success flags or per-agent data. |
| `step(self, action)` | Optional | Override only when you need post-step spawning/cleanup or a nonstandard transition wrapper; usually call `super().step(action)` first. |
| `define_spaces(self)` | Rare | Override only when a second observation helper or custom space wiring is needed. |

## Minimal self-contained environment skeleton

```python
import gymnasium as gym
import numpy as np

from highway_env import utils
from highway_env.envs.common.abstract import AbstractEnv
from highway_env.road.lane import LineType, StraightLane
from highway_env.road.road import Road, RoadNetwork
from highway_env.vehicle.kinematics import Vehicle


class TwoSegmentEnv(AbstractEnv):
    @classmethod
    def default_config(cls) -> dict:
        config = super().default_config()
        utils.update_config(
            config,
            {
                "observation": {"type": "Kinematics"},
                "action": {"type": "DiscreteMetaAction"},
                "duration": 20,
                "vehicles_count": 3,
                "collision_reward": -1.0,
                "high_speed_reward": 0.3,
                "reward_speed_range": [15, 30],
                "normalize_reward": True,
                "neighbour_vehicles_connected_lanes": True,
            },
        )
        return config

    def _reset(self) -> None:
        self._create_road()
        self._create_vehicles()

    def _create_road(self) -> None:
        net = RoadNetwork()
        for lane_id in range(2):
            y = lane_id * StraightLane.DEFAULT_WIDTH
            net.add_lane(
                "a",
                "b",
                StraightLane([0, y], [80, y], line_types=(LineType.CONTINUOUS, LineType.STRIPED)),
            )
            net.add_lane(
                "b",
                "c",
                StraightLane([80, y], [160, y], line_types=(LineType.STRIPED, LineType.CONTINUOUS)),
            )
        self.road = Road(
            network=net,
            np_random=self.np_random,
            record_history=self.config["show_trajectories"],
            neighbour_vehicles_connected_lanes=self.config["neighbour_vehicles_connected_lanes"],
        )

    def _create_vehicles(self) -> None:
        ego_lane = ("a", "b", 0)
        lane = self.road.network.get_lane(ego_lane)
        ego = Vehicle.make_on_lane(self.road, ego_lane, longitudinal=20.0, speed=25.0)
        ego = self.action_type.vehicle_class(self.road, ego.position, ego.heading, ego.speed)
        self.vehicle = ego
        self.road.vehicles.append(ego)

        other_type = utils.class_from_path(self.config["other_vehicles_type"])
        for i in range(self.config["vehicles_count"]):
            lane_index = ("a", "b", i % 2)
            other = other_type.make_on_lane(
                self.road,
                lane_index,
                longitudinal=45.0 + 20.0 * i,
                speed=22.0,
            )
            other.randomize_behavior()
            self.road.vehicles.append(other)

    def _rewards(self, action) -> dict[str, float]:
        scaled_speed = utils.lmap(self.vehicle.speed, self.config["reward_speed_range"], [0, 1])
        return {
            "collision_reward": float(self.vehicle.crashed),
            "high_speed_reward": float(np.clip(scaled_speed, 0, 1)),
            "on_road_reward": float(self.vehicle.on_road),
        }

    def _reward(self, action) -> float:
        rewards = self._rewards(action)
        reward = sum(self.config.get(name, 0) * value for name, value in rewards.items())
        if self.config["normalize_reward"]:
            reward = utils.lmap(
                reward,
                [self.config["collision_reward"], self.config["high_speed_reward"]],
                [0, 1],
            )
        return float(reward * rewards["on_road_reward"])

    def _is_terminated(self) -> bool:
        return bool(self.vehicle.crashed)

    def _is_truncated(self) -> bool:
        return self.time >= self.config["duration"]


gym.register(id="two-segment-v0", entry_point=TwoSegmentEnv)
```

After the module defining this class is imported, `gym.make("two-segment-v0")` can create it. If the class lives in an importable package, prefer an entry-point string such as `"my_project.envs:TwoSegmentEnv"` instead of passing the class object directly.

## Scene-construction checklist

### 1. Configuration

- Start with `config = super().default_config()`.
- Merge custom defaults using `utils.update_config(config, {...})` so nested observation/action defaults stay complete.
- Include `duration`, reward weights, traffic counts, road geometry sizes, and `neighbour_vehicles_connected_lanes` when they affect behaviour.
- Keep observation/action details minimal here and route their tuning to `../observations-actions-rewards/SKILL.md`.

### 2. Road creation

- Create a new `RoadNetwork()` every reset unless the geometry is immutable and safely copied.
- Add lanes in deterministic order. The append order defines lane IDs.
- Use `StraightLane`, `SineLane`, and `CircularLane` for most scenarios; use `PolyLane`/`PolyLaneFixedWidth` for sampled custom centerlines.
- Set `line_types`, `speed_limit`, `forbidden`, and `priority` during lane construction.
- Wrap the network in `Road(...)` or `RegulatedRoad(...)`.
- Pass `np_random=self.np_random` so `reset(seed=...)` controls random scene generation.
- Pass `record_history=self.config["show_trajectories"]` if trajectory display may be enabled.
- Pass `neighbour_vehicles_connected_lanes=self.config["neighbour_vehicles_connected_lanes"]` for clarity; the base reset will also synchronize this flag after `_reset()`.

### 3. Vehicle creation

- Use `self.action_type.vehicle_class` for controlled vehicles so the class matches the configured action type.
- Use `utils.class_from_path(self.config["other_vehicles_type"])` for non-controlled traffic when the config exposes behaviour type.
- Place deterministic vehicles with `Vehicle.make_on_lane(...)`, `IDMVehicle.make_on_lane(...)`, or `self.action_type.vehicle_class.make_on_lane(...)`.
- Use `Vehicle.create_random(...)` or `other_type.create_random(...)` only when stochastic spacing is desired.
- Append every controlled and non-controlled vehicle to `self.road.vehicles`.
- Set `self.vehicle = ego` for a single ego vehicle, or fill `self.controlled_vehicles` for multi-agent or multi-ego tasks.
- For route-aware controllers, call `plan_route_to(destination_node)` after vehicle construction.
- Use `enable_lane_change=False` on `IDMVehicle` instances when traffic must stay in lane.

### 4. Objects and goals

- Append `Obstacle` instances to `self.road.objects` for walls, blocked lanes, or solid hazards.
- Append `Landmark` instances for non-solid goals; the vehicle does not crash on contact, while the landmark can register `hit=True`.
- When a goal is tied to a vehicle, attach it as `vehicle.goal` and include it in `self.road.objects`.
- If an object size changes after construction, update `LENGTH`, `WIDTH`, and `diagonal` consistently.

### 5. Rewards and info

- Keep `_reward(action)` scalar. Use `_rewards(action)` to expose named components in `info["rewards"]`.
- Common components are collision, speed, lane preference, on-road status, goal/success, and action penalty.
- Multiply or gate rewards by `on_road_reward` when off-road driving should invalidate other rewards.
- Use `utils.lmap(value, source_range, target_range)` for speed/reward normalization, then clip when needed.
- For success flags, override `_info` and add `info["is_success"]` or per-agent fields.

### 6. Termination and truncation

- `_is_terminated()` should represent task terminal states: crash, success, arrival, all agents complete, or off-road terminal when configured.
- `_is_truncated()` should represent time limits: usually `self.time >= self.config["duration"]`.
- Avoid mixing time limits into `_is_terminated()` unless the task specifically defines timeout as terminal.

### 7. Optional dynamic spawning/cleanup

If vehicles should appear or disappear during an episode, override `step` carefully:

```python
def step(self, action):
    obs, reward, terminated, truncated, info = super().step(action)
    self._clear_finished_vehicles()
    self._maybe_spawn_vehicle()
    return obs, reward, terminated, truncated, info
```

Make spawn functions reject vehicles too close to existing vehicles to avoid immediate collisions unless that is the intended task.

## Registration patterns

### Local class registration

```python
import gymnasium as gym

gym.register(id="my-custom-v0", entry_point=MyCustomEnv)
```

This is convenient in notebooks or scripts, but the module must execute the registration before `gym.make("my-custom-v0")`.

### Importable package registration

```python
gym.register(id="my-custom-v0", entry_point="my_project.envs:MyCustomEnv")
```

This is preferable for reusable projects. Ensure `my_project.envs` imports the class and that the package is installed or otherwise importable.

### Connected-lane variant registration

To preserve reproducibility, register separate IDs when changing neighbour-search semantics:

```python
from highway_env.envs.common.abstract import ConnectedLaneNeighboursMixin

class ConnectedLaneTwoSegmentEnv(ConnectedLaneNeighboursMixin, TwoSegmentEnv):
    pass

gym.register(id="two-segment-v0", entry_point=TwoSegmentEnv)
gym.register(id="two-segment-v1", entry_point=ConnectedLaneTwoSegmentEnv)
```

Use `*-v0` for legacy/same-segment behaviour only if you need compatibility with earlier runs; use a new version ID for connected-lane behaviour.

## Bounded smoke test for a custom environment

After registration, use a short, no-training smoke test:

```python
env = gym.make("two-segment-v0")
try:
    obs, info = env.reset(seed=0)
    for _ in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        if terminated or truncated:
            break
finally:
    env.close()
```

If this fails because of `gym.make`, registration, render mode, or general Gymnasium operation, route to `../simulation-environments/SKILL.md`. If it fails because observation/action spaces do not match the config, route to `../observations-actions-rewards/SKILL.md`.

## Design review checklist before using a custom env for experiments

- Does `reset(seed=...)` produce deterministic scenarios when all stochastic choices use `self.np_random`?
- Are all lane indexes valid after `_create_road()`?
- Are controlled vehicles in both `self.controlled_vehicles` and `self.road.vehicles`?
- Does `self.vehicle` return the intended ego vehicle?
- Are `simulation_frequency` and `policy_frequency` positive, with simulation frequency at least policy frequency?
- Does `road.neighbour_vehicles_connected_lanes` match the intended environment version?
- Do `terminated` and `truncated` reflect distinct task-ending causes?
- Does `info` include enough reward/success debugging fields for downstream agents?
- Is the first validation a bounded smoke test rather than a long training run?
