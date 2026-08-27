# HighwayEnv action spaces, available actions, and reward info

The action type is selected by `config["action"]["type"]`. Type strings are
case-sensitive:

- `DiscreteMetaAction`
- `ContinuousAction`
- `DiscreteAction`
- `MultiAgentAction`

## `DiscreteMetaAction`

Purpose: high-level lane and speed setpoint changes for controlled vehicles.

Important parameters:

| Key | Meaning |
| --- | --- |
| `longitudinal` | Enable speed changes (`FASTER`, `SLOWER`). Default `True`. |
| `lateral` | Enable lane changes (`LANE_LEFT`, `LANE_RIGHT`). Default `True`. |
| `target_speeds` | Speed setpoints tracked by the underlying MDP vehicle. |

When both axes are enabled, labels are:

```python
{0: "LANE_LEFT", 1: "IDLE", 2: "LANE_RIGHT", 3: "FASTER", 4: "SLOWER"}
```

When only longitudinal actions are enabled, labels are:

```python
{0: "SLOWER", 1: "IDLE", 2: "FASTER"}
```

When only lateral actions are enabled, labels are:

```python
{0: "LANE_LEFT", 1: "IDLE", 2: "LANE_RIGHT"}
```

Do not hard-code label indexes across configs. Read
`env.unwrapped.action_type.actions` or `actions_indexes` after reset.

### Available actions

`env.unwrapped.get_available_actions()` is implemented for `DiscreteMetaAction`.
It always includes `IDLE`; lane changes are omitted at road boundaries or when a
side lane is not reachable; speed changes are omitted at the minimum or maximum
speed index. Taking an unavailable discrete meta-action is treated like `IDLE` by
the controlled vehicle layer, so robust agents should mask unavailable labels.

For `MultiAgentAction`, `get_available_actions()` returns the Cartesian product
of each controlled vehicle's available nested actions. Convert it to a list only
when the product is small.

## `ContinuousAction`

Purpose: low-level acceleration and steering control.

Important parameters:

| Key | Meaning |
| --- | --- |
| `acceleration_range` | Map normalized throttle to acceleration, default `[-5, 5]`. |
| `steering_range` | Map normalized steering to radians, default `[-pi/4, pi/4]`. |
| `speed_range` | Optional min/max reachable speed applied to the vehicle. |
| `longitudinal` | Include acceleration. |
| `lateral` | Include steering. |
| `dynamical` | Use a bicycle-dynamics vehicle class instead of kinematic vehicle. |
| `clip` | Clip input values to `[-1, 1]` before mapping. |

The action space is `Box(-1.0, 1.0, shape=(2,), dtype=float32)` when both axes
are enabled. The action order is `[acceleration, steering]`. If only one axis is
enabled, the shape is `(1,)`; a two-value array is invalid for that config.

## `DiscreteAction`

Purpose: uniform quantization of `ContinuousAction`.

Important parameters are the same as `ContinuousAction`, plus
`actions_per_axis`. The discrete space size is `actions_per_axis ** size`, where
`size` is 2 when both axes are active and 1 when only one axis is active. The
selected integer maps to a point in the Cartesian product of evenly spaced values
from `-1` to `1` for each active axis.

## `MultiAgentAction`

Purpose: one nested action type per controlled vehicle.

Important parameter: `action_config`, a nested single-agent action config. The
action space is a `Tuple` of nested spaces, and `env.step(action)` expects a tuple
matching that space. This is the default pattern for multi-agent intersection
configs.

## Reward and info model

Every standard step returns `(obs, reward, terminated, truncated, info)`. For
most envs, `info` includes:

- `speed`: current ego speed;
- `crashed`: whether the ego vehicle crashed;
- `action`: the action just processed;
- `rewards`: a dict of decomposed reward components when the env implements
  `_rewards()`.

`info["rewards"]` contains component values, not the final weighted scalar. The
scalar `reward` is usually computed by multiplying component names by matching
config weights, summing them, optionally normalizing, and sometimes multiplying
by an on-road component.

Parking does not expose `info["rewards"]` by default; it exposes
`info["is_success"]`. Exit also adds `info["is_success"]`. Intersection adds
`info["agents_rewards"]` and `info["agents_terminated"]` in addition to averaged
multi-objective rewards.

## Reward components by environment family

| Env family | Main components and interpretation |
| --- | --- |
| `highway-v0`, `highway-fast-v0` | `collision_reward`, `right_lane_reward`, `high_speed_reward`, `on_road_reward`. Config weights include `collision_reward=-1`, `right_lane_reward=0.1`, `high_speed_reward=0.4`; scalar reward is normalized when `normalize_reward=True` and multiplied by `on_road_reward`. |
| `merge-v0`, `merge-generic-v0` | `collision_reward`, `right_lane_reward`, `high_speed_reward`, `lane_change_reward`, `merging_speed_reward`. The merging speed component penalizes slow controlled vehicles on the merge lane through its negative config weight. |
| `roundabout-v0` | `collision_reward`, `high_speed_reward`, `lane_change_reward`, `on_road_reward`. High speed is based on target speed index; reward may be normalized and multiplied by `on_road_reward`. |
| `intersection-v0` and variants | `collision_reward`, `high_speed_reward`, `arrived_reward`, `on_road_reward`. Rewards are averaged across controlled vehicles; arrival can override the weighted sum with `arrived_reward`; info includes per-agent reward/termination tuples. |
| `parking-v0` and variants | Goal reward is a negative weighted p-norm between `achieved_goal` and `desired_goal`, plus collision penalty. Config keys include `reward_weights`, `success_goal_reward`, and `collision_reward`. Success is `compute_reward(...) > -success_goal_reward`. |
| `exit-v0` | `collision_reward`, `goal_reward`, `high_speed_reward`, `right_lane_reward`; success is reaching the exit lane/target lane and is also reported as `info["is_success"]`. |
| `two-way-v0` | `high_speed_reward` and `left_lane_reward`; the default config also has a `collision_reward` key, but decomposed rewards only include speed and left-lane terms. |
| `u-turn-v0` | `collision_reward`, `left_lane_reward`, `high_speed_reward`, `on_road_reward`; reward can be normalized and multiplied by `on_road_reward`. |
| `racetrack-v0` | `lane_centering_reward`, `action_reward`, `collision_reward`, `on_road_reward`; `action_reward` is the norm of the continuous action and is usually weighted negatively. |
| `lane-keeping-v0` | Scalar reward is `1 - (lateral_offset / lane_width) ** 2`; this env's custom step returns an empty `info` dict. |

## Goal observations for parking

`parking-v0` uses `KinematicsGoal` by default. The observation dict has:

- `observation`: current scaled state;
- `achieved_goal`: current scaled goal state;
- `desired_goal`: target scaled goal state.

The default features are `x`, `y`, `vx`, `vy`, `cos_h`, `sin_h`; default scales
are `[100, 100, 5, 5, 1, 1]`. Parking computes success from the same goal-state
comparison even if the agent-facing observation is changed to `LidarObservation`
or `GrayscaleObservation`.

## Minimal inspection pattern

```python
obs, info = env.reset(seed=0)
print(env.observation_space)
print(env.action_space)

try:
    print(env.unwrapped.get_available_actions())
except NotImplementedError:
    print("available-action mask is not implemented for this action type")

action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
print(reward, info.keys())
print(info.get("rewards"), info.get("is_success"))
```
