# Actions, observations, rewards, and done semantics

## Formatting modes

`HiWayEnvV1` defaults to `ActionOptions.multi_agent` and
`ObservationOptions.multi_agent`.

| Mode | Action input | Observation output | Use |
|---|---|---|---|
| `multi_agent` | Dict containing active ids | Dict containing active ids | normal scheduled multi-agent loop |
| `full` | Dict containing every configured id | Dict containing every configured id | fixed-shape vectorized consumers |
| `unformatted` | raw SMARTS actions | raw `Observation` named tuples | low-level/controller debugging |

In formatted modes, `env.action_space` and `env.observation_space` are
Gymnasium `Dict` spaces keyed by configured agent id. In unformatted mode the
formatters expose `None` spaces and do not constrain/rewrite the values. Do not
pass a raw string to a formatted `Discrete` lane space or a formatted tuple
where a `numpy`/Gymnasium value is expected.

`full` observation mode pads an inactive agent with a sampled-shaped structure
and sets its top-level `active` field to false. Active formatted observations
have `active=true`. `full` action mode requires all configured ids in the
input, so it is not appropriate for a scenario where the caller only has
policy actions for active agents unless it deliberately supplies the required
inactive values. `multi_agent` is the safer default for scheduled agents.

## Verified action mapping

The live `ActionSpaceType` enum is:

```text
Continuous, Lane, ActuatorDynamic, LaneWithContinuousSpeed,
TargetPose, Trajectory, MultiTargetPose, MPC, TrajectoryWithTime,
Direct, Empty, RelativeTargetPose
```

The formatted spaces and the underlying controller shape are:

| Type | Formatted Gymnasium value | Controller interpretation |
|---|---|---|
| `Continuous` | `Box([0,0,-1], [1,1,1], float32)` | `(throttle, brake, steering)`; each clipped to the stated range |
| `ActuatorDynamic` | same 3-value Box | `(throttle, brake, steering_rate)`; steering rate is integrated/clipped |
| `Lane` | `Discrete(4)` | `0=keep_lane`, `1=slow_down`, `2=change_lane_left`, `3=change_lane_right`; formatted to strings |
| `LaneWithContinuousSpeed` | Tuple `(float Box, int8 scalar Box)` | `(target_speed_mps, lane_delta)`; lane delta 0 keeps lane, ±1 requests adjacent lane |
| `TargetPose` | 4-value float Box | `(x, y, heading, time_delta)` |
| `RelativeTargetPose` | 3-value float Box | `(delta_x, delta_y, delta_heading)`; converted to a short absolute target pose |
| `Trajectory` | Tuple of four length-20 float sequences | `(x_coords, y_coords, headings, speeds)` for PD tracking |
| `MPC` | same four-sequence shape | `(x_coords, y_coords, headings, speeds)` for MPC tracking |
| `TrajectoryWithTime` | Tuple of five length-20 sequences | `(times, x_coords, y_coords, headings, speeds)` |
| `MultiTargetPose` | base target-pose formatted space | mapping of vehicle id to target poses at the low-level controller boundary; verify the live space before use |
| `Direct` | 2-value float Box | `(linear_acceleration, angular_velocity)` after initialization; controller also accepts a scalar initial speed in low-level use |
| `Empty` | empty Tuple | no action; `None` is accepted by the low-level controller |

The lane strings are available through `smarts.core.controllers.LaneAction`.
The term `break` in low-level type annotations is a historical spelling; the
public action field is `brake`.

Always debug with:

```python
for agent_id, space in env.action_space.spaces.items():
    candidate = policy.act(observations[agent_id])
    print(agent_id, type(candidate), candidate, space, space.contains(candidate))
```

If the environment was made with `action_options="unformatted"`, this check
is intentionally unavailable; then inspect `AgentInterface.action` and
`Controllers.get_action_shape(...)` and use the raw controller type.

## Observation contract

The raw SMARTS `Observation` is a named tuple containing at least:

- timing: `dt`, `step_count`, `steps_completed`, `elapsed_sim_time`;
- `events`: classified collision, off-road, off-route, goal, max-step, and
  configurable done events;
- `ego_vehicle_state`: id, position, dimensions, heading, speed, steering,
  yaw rate, road/lane ids, mission, velocities, and optional acceleration/jerk;
- `under_this_agent_control` and `distance_travelled`;
- optional `neighborhood_vehicle_states`, `waypoint_paths`, `road_waypoints`,
  `signals`, `lidar_point_cloud`, and image/grid observations;
- `via_data` for nearby and recently hit collectible points.

The default formatted observation is a nested Gymnasium dict. It always
contains the active marker, step count, distance, ego state, mission, and event
features. Interface flags add waypoint paths, neighborhood vehicles, road
waypoints, signals, lidar, and image/grid fields. Formatted arrays are padded
for fixed shapes: waypoint paths use up to four paths and twenty points,
neighbor features are bounded to a fixed set, and upcoming signals use a small
fixed set. Lane and vehicle identifiers can be truncated by the formatter.

Image/grid fields are `uint8` arrays. Top-down RGB is shaped
`(height, width, 3)`. Occupancy/drivable/occlusion maps and custom renders
require the optional camera/rendering stack and can dominate step time. Their
presence in an interface makes `requires_rendering` true; a successful CPU
import does not prove those sensors render correctly. Route image behavior to
`sensors-visualization`.

## Reset and step return shapes

### Default per-agent mode

```python
observations, infos = env.reset(seed=integer)
observations, rewards, terminateds, truncateds, infos = env.step(actions)
```

For `HiWayEnvV1` with `environment_return_mode=EnvReturnMode.per_agent`:

- `observations`: `dict[agent_id, observation]`; in multi-agent mode only
  currently active ids; in full mode every configured id;
- `rewards`: `dict[agent_id, float]` for returned SMARTS rewards;
- `terminateds`: `dict[agent_id, bool]` plus `"__all__"`;
- `truncateds`: same dictionary shape as `terminateds` in this implementation;
- `infos`: per-agent diagnostic mappings, including score, reward, done, and
  the environment observation used for diagnostics.

When full formatted observations are enabled, the implementation supplies
inactive observation entries and uses `np.nan` for the corresponding missing
reward entries. Treat `active` as authoritative rather than training on padded
values.

The `"__all__"` flag becomes true after all configured agent done events have
been registered. An individual agent's done status removes it from subsequent
active dictionaries. A scenario can have no active agents while `"__all__"`
is still false, for example while waiting for a later scheduled mission.

### Environment-return mode

With `environment_return_mode=EnvReturnMode.environment` or the string
`"environment"`, step returns:

```python
observations, reward, terminated, truncated, infos
# reward: float sum of per-agent rewards
# terminated/truncated: bool, both based on __all__
```

The observation remains keyed by agent. Do not feed this mode to a learner
expecting per-agent reward dictionaries without an adapter.

### Single-agent wrapper

`SingleAgent` converts the one-id case to ordinary Gymnasium values:

```python
obs, info = env.reset()
obs, float_reward, bool_terminated, bool_truncated, info = env.step(action)
```

It asserts exactly one configured interface and indexes that id from the
underlying dictionaries.

### Parallel wrapper

`ParallelEnv.reset()` returns `(sequence_of_observations,
sequence_of_infos)`. `ParallelEnv.step()` returns five sequences in the same
order as the base step: observation, reward, terminated, truncated, info. Each
item is one child environment's dictionary result. It does not concatenate
nested spaces into a new tensor.

## Reward and done choices

The default SMARTS reward is distance travelled, emitted when the accumulated
movement since the last non-zero reward exceeds approximately 0.5 m; otherwise
it is zero. Treat that as the environment baseline, not a task-specific score.
`info` and `events` expose diagnostics for collisions, off-route/off-road,
reaching a goal, and configured criteria.

`DoneCriteria` defaults to collision, off-road, and off-route termination. It
can additionally use shoulder, wrong-way, not-moving, interest, and
multi-agent alive criteria. `AgentInterface.max_episode_steps` is per-agent;
set it to a finite value for bounded smoke tests. A caller may also impose an
outer loop bound even when SMARTS does not finish.
