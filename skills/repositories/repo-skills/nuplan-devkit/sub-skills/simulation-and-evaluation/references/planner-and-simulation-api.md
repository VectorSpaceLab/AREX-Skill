# Planner and simulation API

This reference is the operating contract for the versioned nuPlan simulation
stack. Import paths are package paths; the implementation is not required to
remain available once the skill has been loaded.

## `AbstractPlanner` contract

The planner interface is:

```python
from nuplan.planning.simulation.planner.abstract_planner import (
    AbstractPlanner, PlannerInitialization, PlannerInput,
)
from nuplan.planning.simulation.trajectory.abstract_trajectory import (
    AbstractTrajectory,
)

class MyPlanner(AbstractPlanner):
    def name(self) -> str: ...
    def initialize(self, initialization: PlannerInitialization) -> None: ...
    def observation_type(self) -> Type[Observation]: ...
    def compute_planner_trajectory(
        self, current_input: PlannerInput
    ) -> AbstractTrajectory: ...
```

`PlannerInitialization` is a frozen record containing:

- `route_roadblock_ids: List[str]`: route roadblocks from the scenario;
- `mission_goal: StateSE2`: the scenario mission goal;
- `map_api: AbstractMap`: the map API for the scenario.

`PlannerInput` is a frozen record containing:

- `iteration: SimulationIteration`: the current index and `TimePoint`;
- `history: SimulationHistoryBuffer`: the rolling ego/observation history;
- `traffic_light_data: Optional[List[TrafficLightStatusData]]`.

### Lifecycle and failure behavior

For each scenario, `SimulationRunner` calls callbacks, then
`Simulation.initialize()`. Initialization resets the setup, preloads the
history buffer, initializes observations, appends the current ego state, and
returns `PlannerInitialization`. The runner calls `planner.initialize()` once
for that scenario. It then repeats until the time controller reaches the end:

1. build one `PlannerInput` from the current iteration and history;
2. call `compute_trajectory()` (not the abstract method directly);
3. propagate the trajectory through the ego controller and observation;
4. append the new state and observation to history.

At the end, callbacks run and `generate_planner_report()` returns recorded
`compute_trajectory()` runtimes. The wrapper records runtime on both success
and exception, then re-raises the original exception. `requires_scenario=True`
is for oracle planners whose constructor receives a scenario; it is not valid
for a normal submission planner.

Reset planner-owned mutable state between scenarios. Do not assume one planner
instance is safe to reuse without resetting it.

## Observation and trajectory compatibility

`observation_type()` must return exactly the class returned by the configured
observation's `observation_type()`. `validate_planner_setup()` compares the two
classes for equality and raises `ValueError` on mismatch; it does not perform a
conversion.

`AbstractTrajectory` exposes `start_time`, `end_time`, `duration`,
`get_state_at_time()`, `get_state_at_times()`, `get_sampled_trajectory()`, and
`is_in_range()`. The standard `InterpolatedTrajectory` requires at least two
non-empty states, all instances of the same `InterpolatableState` class. State
time values must be usable as a strictly time-ordered interpolation axis.
Queries outside the inclusive `[start_time, end_time]` range assert.

The first state should represent the current ego state and the trajectory must
cover the next simulation timestamp. If the controller step is `dt`, ensure
`end_time >= current_time + dt`; a longer horizon is safer for tracking
controllers. Use `TimePoint` microseconds consistently, avoid duplicate or
non-monotonic timestamps, and return finite, physically compatible state
values. Never return `None`, a raw array, a one-state list, or a state type the
controller cannot query.

A useful isolated contract check is:

1. initialize a planner with a minimal `PlannerInitialization` fixture;
2. call `compute_trajectory()` with a fixture `PlannerInput`;
3. assert an `AbstractTrajectory` with at least two samples and the expected
   start time;
4. assert `is_in_range(next_iteration.time_point)`;
5. query the next time and check state type, finite pose, velocity, and heading.

## Built-in planner facts

- `SimplePlanner(horizon_seconds, sampling_time, acceleration,
  max_velocity=5.0, steering_angle=0.0)` uses `DetectionsTracks`, starts from
  the current ego state, and propagates a kinematic bicycle model. Its sample
  count is `int(horizon_seconds / sampling_time)` future steps, so positive
  values and a horizon covering the simulation step are required.
- `IDMPlanner(target_velocity, min_gap_to_lead_agent, headway_time, accel_max,
  decel_max, planned_trajectory_samples, planned_trajectory_sample_interval,
  occupancy_map_radius)` uses `DetectionsTracks`. Initialization stores the map
  and resolves route roadblocks; it requires a usable route (at least a
  starting and target roadblock in the common case). It builds a lane path and
  applies an IDM longitudinal policy using the occupancy map.
- `MLPlanner(model)` uses `DetectionsTracks`. Initialization starts the model
  loader. The model's future trajectory sampling controls horizon, interval,
  and output count; relative model poses are transformed to absolute ego states
  and wrapped in `InterpolatedTrajectory`. Model/checkpoint construction is
  outside this sub-skill, but malformed output is still a planner failure.

## Observation/controller interfaces

A custom observation implements `observation_type()`, `reset()`,
`initialize()`, `get_observation()`, and
`update_observation(iteration, next_iteration, history)`. A custom ego
controller implements `get_state()`, `reset()`, and
`update_state(current_iteration, next_iteration, ego_state, trajectory)`.

- `LogPlaybackController` advances recorded ego states by scenario iteration;
  it is appropriate for open-loop replay and does not consume planner output
  to move the ego.
- `PerfectTrackingController` queries the trajectory exactly at
  `next_iteration.time_point`; out-of-range trajectories fail, and a speed of
  50 m/s or greater raises a safety error.
- `TwoStageController` tracks the trajectory with an `AbstractTracker`, then
  propagates the resulting command through an `AbstractMotionModel`.
- `TracksObservation` replays `DetectionsTracks` from the scenario.
- `IDMAgents` also exposes `DetectionsTracks`, but propagates other agents with
  an IDM policy and may retain selected open-loop detections.

`simulation_history_buffer_duration` must be at least the scenario database
interval. The default is 2 seconds and the implementation adds one database
interval when sizing the rolling buffer.

## Supported combinations

| Evaluation | Observation | Ego controller | Typical experiment |
|---|---|---|---|
| Open-loop boxes | `box_observation` / `DetectionsTracks` | `log_play_back_controller` | `open_loop_boxes` |
| Closed-loop, non-reactive agents | `box_observation` / `DetectionsTracks` | `two_stage_controller` | `closed_loop_nonreactive_agents` |
| Closed-loop, reactive agents | `idm_agents_observation` / `DetectionsTracks` | `two_stage_controller` | `closed_loop_reactive_agents` |

The table is a complete setup choice, not just a planner suggestion. Changing
only the planner can leave an incompatible observation, controller, or metric
set. A mismatch must be fixed in Hydra composition before execution.
