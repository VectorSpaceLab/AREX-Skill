# Configuration guide

## Building the environment configuration

The direct constructor accepts `scenarios` and `agent_interfaces` as required
arguments. A minimal CPU configuration is:

```python
from smarts.core.agent_interface import AgentInterface, AgentType
from smarts.env.configs.hiway_env_configs import (
    HiWayEnvV1Configuration, ScenarioOrder,
)
from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1

interface = AgentInterface.from_type(
    AgentType.Laner, max_episode_steps=200
)
env = HiWayEnvV1(
    scenarios=["built-scenario"],
    agent_interfaces={"ego": interface},
    scenarios_order=ScenarioOrder.sequential,
    headless=True,
    fixed_timestep_sec=0.1,
    seed=42,
)
```

`HiWayEnvV1Configuration` is a dataclass with these live fields:

| Field | Default/meaning |
|---|---|
| `scenarios` | required list of generated scenario directories |
| `agent_interfaces` | required id-to-`AgentInterface` mapping |
| `sim_name` | `None`; useful to distinguish visualization streams |
| `scenarios_order` | `ScenarioOrder.scrambled` (`default` aliases it) |
| `headless` | `False`; use `True` for non-rendered checks |
| `visdom` | `False`; deprecated optional integration |
| `fixed_timestep_sec` | `0.1` seconds |
| `sumo_options` | fresh `SumoOptions` dataclass |
| `seed` | `42` |
| `observation_options` | `ObservationOptions.multi_agent` |
| `action_options` | `ActionOptions.multi_agent` |
| `environment_return_mode` | `EnvReturnMode.per_agent` |

The separate `EnvironmentConfiguration` is simply
`EnvironmentConfiguration(id: str)`. Registry/Hydra-style applications can
combine that `id` with the HiWay fields, but direct construction does not need
an id. `gym.make("smarts.env:hiway-v1", ...)` uses the registered id and
requires the SMARTS Gymnasium registration module to have been imported.

## Scenario iteration and seeding

`ScenarioOrder.sequential` has value 0 and `scrambled` has value 1. The default
is scrambled. SMARTS expands scenario variations discovered in generated
traffic data and advances the iterator at reset. Provide stable list ordering,
a stable seed, and deterministic policy actions when comparing runs. The
`seed` constructor argument seeds SMARTS; `reset(seed=...)` also initializes
the Gymnasium RNG and re-applies the SMARTS seed after reset.

`fixed_timestep_sec` controls the simulation step duration for core providers.
Keep it positive and consistent across experiments. Changing it changes
controller integration, timing observations, and the interpretation of direct
angular velocity actions.

## Interface sensors and dimensions

`AgentInterface` defaults to `accelerometer=True` and `lane_positions=True`,
while most optional perception sensors are false. The common controls are:

```python
from smarts.core.agent_interface import (
    AgentInterface, NeighborhoodVehicles, OGM, RGB, Signals, Waypoints,
)
from smarts.core.controllers import ActionSpaceType

interface = AgentInterface(
    waypoint_paths=Waypoints(lookahead=40),
    neighborhood_vehicle_states=NeighborhoodVehicles(radius=50),
    occupancy_grid_map=OGM(width=64, height=64, resolution=100 / 64),
    top_down_rgb=RGB(width=128, height=128, resolution=100 / 128),
    signals=Signals(lookahead=120),
    action=ActionSpaceType.Continuous,
    max_episode_steps=500,
)
```

`True` resolves to the default dataclass; `False` disables the sensor. RGB,
occupancy, drivable-area, occlusion, and custom-render paths need the optional
camera-observation/rendering dependencies. They also require a compatible
software display/offscreen setup in many deployments. Do not turn them on in a
headless core smoke solely because the package itself imports successfully.

`occlusion_map` additionally requires an occupancy grid with matching width
and height. `custom_renders` must use valid shader/dependency objects and is
not a basic policy interface. If only low-dimensional driving features are
needed, leave image fields false for much better step performance.

## Done criteria

```python
from smarts.core.agent_interface import (
    AgentInterface, AgentsAliveDoneCriteria, DoneCriteria,
    EventConfiguration, InterestDoneCriteria,
)

interface = AgentInterface(
    action=ActionSpaceType.Lane,
    max_episode_steps=200,
    event_configuration=EventConfiguration(
        not_moving_time=30, not_moving_distance=1
    ),
    done_criteria=DoneCriteria(
        collision=True,
        off_road=True,
        off_route=True,
        not_moving=True,
        interest=InterestDoneCriteria(
            actors_filter=("pedestrian.*",), strict=False
        ),
    ),
)
```

The default `DoneCriteria` marks collision, off-road, and off-route as done;
shoulder, wrong-way, not-moving, interest, and agent-alive criteria are opt-in.
A done agent is removed from the active dictionaries and can contribute to the
`__all__` count. Use `AgentsAliveDoneCriteria` only when the multi-agent
lifecycle has been specified carefully; it can end an agent based on total ego
or total actor counts and named agent lists.

## Vehicles and controller selection

`vehicle_class` is the current interface field for the vehicle definition;
`vehicle_type` is retained only for deprecated compatibility. The interface
action selects the controller and the chassis path:

- continuous: direct throttle/brake/steering clipping;
- actuator dynamic: throttle/brake plus integrated steering-rate state;
- lane/lane-with-speed: waypoint-based lane-following controller, requiring a
  vehicle near a lane and an Ackermann-capable chassis;
- target/relative target/multi-target pose: motion planner;
- trajectory/MPC: trajectory tracking controller;
- trajectory-with-time: interpolation controller;
- direct: direct kinematic or chassis control.

A lane controller can fail with an out-of-lane error when a controlled vehicle
is not near a known lane. A lane policy also needs waypoint paths in its
interface. Use a direct or trajectory interface only when the action arrays,
headings, speeds, and timestep are intentionally supplied by the policy.

## SUMO and optional provider settings

`SumoOptions` has the live fields:

```text
num_external_clients=0, auto_start=True, headless=True, port=None
```

These settings matter only when the selected scenario supports SUMO traffic.
They do not install or start SUMO. A port conflict, missing executable, or
external TraCI service is an optional-integration failure; route it to
`cli-integrations` rather than weakening a CPU-only environment smoke.
