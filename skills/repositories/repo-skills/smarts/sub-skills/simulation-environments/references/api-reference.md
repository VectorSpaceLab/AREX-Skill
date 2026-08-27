# Simulation API reference

This reference distills the installed SMARTS 2.0.1 API used by this route. The
public import names below are the stable operating surface; inspect the live
package with `scripts/inspect_interfaces.py` when an environment has a
 different SMARTS release.

## Imports and signatures

```python
from smarts.core.agent import Agent
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.core.controllers import ActionSpaceType
from smarts.env.configs.base_config import EnvironmentConfiguration
from smarts.env.configs.hiway_env_configs import (
    EnvReturnMode, HiWayEnvV1Configuration, ScenarioOrder, SumoOptions,
)
from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1
from smarts.env.gymnasium.wrappers.parallel_env import ParallelEnv
from smarts.env.gymnasium.wrappers.single_agent import SingleAgent
```

Verified signatures:

```text
AgentInterface(
    debug=False, event_configuration=<factory>, done_criteria=<factory>,
    max_episode_steps=None, neighborhood_vehicle_states=False,
    waypoint_paths=False, road_waypoints=False, drivable_area_grid_map=False,
    occupancy_grid_map=False, top_down_rgb=False, lidar_point_cloud=False,
    action=None, vehicle_type='', vehicle_class='generic_sedan',
    accelerometer=True, lane_positions=True, signals=False,
    occlusion_map=False, custom_renders=()
) -> None

AgentInterface.from_type(requested_type: AgentType, **kwargs) -> AgentInterface

HiWayEnvV1(
    scenarios, agent_interfaces, sim_name=None,
    scenarios_order=ScenarioOrder.scrambled, headless=False, visdom=False,
    fixed_timestep_sec=0.1, seed=42, sumo_options=SumoOptions(),
    visualization_client_builder=<default builder>,
    observation_options=ObservationOptions.multi_agent,
    action_options=ActionOptions.multi_agent,
    environment_return_mode=EnvReturnMode.per_agent, render_mode=None
)

EnvironmentConfiguration(id: str) -> None

HiWayEnvV1Configuration(
    scenarios, agent_interfaces, sim_name=None,
    scenarios_order=ScenarioOrder.scrambled, headless=False, visdom=False,
    fixed_timestep_sec=0.1, sumo_options=<factory>, seed=42,
    observation_options=ObservationOptions.multi_agent,
    action_options=ActionOptions.multi_agent,
    environment_return_mode=EnvReturnMode.per_agent
) -> None
```

`HiWayEnvV1Configuration` is the environment-argument dataclass. The separate
`EnvironmentConfiguration` contains only a Gymnasium registration `id`; a
configuration used by a registry-driven application may inherit both.

## Agent and interface

`Agent` is an abstract policy with `act(self, obs, **configs)`. Use
`Agent.from_function(callable)` for a small policy. `AgentInterface.from_type`
creates a fresh interface and then applies keyword overrides, so this is safe:

```python
interface = AgentInterface.from_type(
    AgentType.Standard,
    max_episode_steps=500,
    lidar_point_cloud=True,
)
```

The verified `AgentType` members are:

| Type | Preset action | Main observation intent |
|---|---|---|
| `Buddha` | `Empty` | no observation/action work |
| `Full` | `Continuous` | all standard sensors, including image/lidar options |
| `Standard` | `ActuatorDynamic` | waypoints and neighborhood vehicles |
| `Laner` | `Lane` | waypoint paths and discrete lane commands |
| `Loner` | `Continuous` | waypoint paths, no neighborhood requirement |
| `Tagger` | `Continuous` | waypoints and neighborhood vehicles |
| `StandardWithAbsoluteSteering` | `Continuous` | waypoints and neighborhood vehicles |
| `LanerWithSpeed` | `LaneWithContinuousSpeed` | waypoints and target speed/lane delta |
| `Tracker` | `Trajectory` | waypoint paths and trajectory tracking |
| `Boid` | `MultiTargetPose` | multiple-vehicle pose control |
| `MPCTracker` | `MPC` | waypoint paths and MPC trajectory tracking |
| `TrajectoryInterpolator` | `TrajectoryWithTime` | time-indexed trajectory interpolation |
| `Direct` | `Direct` | neighborhood/signals and direct kinematic control |

The preset table describes defaults, not a restriction: `from_type(...,
waypoint_paths=True)` or `interface.replace(...)` can extend an interface.
Sensor booleans resolve to default dataclasses in `__post_init__`. A custom
`RGB`, `OGM`, `Waypoints`, `NeighborhoodVehicles`, `Signals`, or `Lidar`
instance carries dimensions/radius/lookahead into the observation pipeline.
`vehicle_class` is the current vehicle-class field; the older `vehicle_type`
field is deprecated.

`requires_rendering` is true when an interface requests top-down RGB, an
occupancy/drivable grid, or custom renders. Do not enable those in a CPU-only
smoke unless the camera/rendering optional stack is installed.

## Action enum

The verified `ActionSpaceType` members are:

```text
Continuous=0, Lane=1, ActuatorDynamic=2,
LaneWithContinuousSpeed=3, TargetPose=4, Trajectory=5,
MultiTargetPose=6, MPC=7, TrajectoryWithTime=8, Direct=9,
Empty=10, RelativeTargetPose=11
```

See `action-observation-reward.md` for exact formatted Gymnasium spaces and
controller input shapes. Use `env.action_space[agent_id]` as the final source
of truth because action formatting options alter what the policy must return.

## Environment properties and lifecycle

After construction, useful properties include `agent_ids` (all configured
ids), `agent_interfaces`, `action_space`, `observation_space`, `seed`,
`scenario_log`, and `smarts`. The last two expose simulator state for logging;
do not mutate the underlying simulator through `smarts` while using the
Gymnasium interface.

- `reset(*, seed=None, options=None)` returns `(obs, info)`.
- `step(action)` returns five values; the exact types depend on
  `environment_return_mode`.
- `render()` is only meaningful for `render_mode="rgb_array"` and requires
  the renderer path.
- `close()` destroys simulator resources and is idempotent for normal use.

Reset options accepted by the HiWay implementation include `scenario` (an
explicit scenario object accepted by SMARTS internals) and `start_time`.
Ordinary callers should select from `scenarios` and let the scenario iterator
advance unless they have a specific reset-time use case.

## `ParallelEnv` surface

```text
ParallelEnv(env_constructors, auto_reset, seed=42)
```

Each constructor must be a callable that accepts `seed=` and returns a
Gymnasium environment. `batch_size`, `observation_space`, `action_space`, and
`seed()` are available. `reset()` returns two sequences; `step(actions)`
returns five sequences; `close(terminate=False)` shuts down worker processes.
Every child must have equal action and observation spaces. Worker seeds are
`seed + index`.

`SingleAgent(env)` is only valid when exactly one agent interface is configured.
It unwraps the agent's dict values into standard scalar Gymnasium reset/step
returns and replaces the wrapper's spaces with that one agent's spaces.
