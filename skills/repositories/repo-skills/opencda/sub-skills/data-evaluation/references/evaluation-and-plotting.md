# Evaluation lifecycle and plotting

## Evaluation manager lifecycle

OpenCDA's documented scenario flow is:

1. Load a scenario YAML configuration with `load_yaml`. That loader returns a
   mapping and adds a timestamp-shaped `current_time` field.
2. Construct a `ScenarioManager` (or `CoScenarioManager` for co-simulation),
   create CAV and platoon managers, and run the simulation loop.
3. Construct `EvaluationManager(cav_world, script_name, current_time)` after
   the scenario has been assembled.
4. Call `evaluate()` after the run. The manager calls modules in this order:
   `planning_eval`, `localization_eval`, `kinematics_eval`, and
   `platooning_eval`.

The manager uses a 0.05 second fixed delta and skips the first 60 collected
simulation samples in its planning plots. That skip is a three-second warm-up
at the 20 Hz simulator tick rate. It is separate from the 10 Hz YAML dumper,
which writes every second simulation step after its own first-60-step warm-up.
If a metric combines both streams, state the sample rate and warm-up rule
explicitly.

The default implementation creates an evaluation directory shaped like:

```text
<evaluation-output-root>/<script-name>_<current-time>/
  log.txt
  <actor-id>_localization_plotting.png
  <actor-id>_kinematics_plotting.png
  <platoon-id>_platoon_plotting.png
```

`lprint` appends text to `log.txt`. Planning evaluation prints route and timing
statistics, plots velocity, IMU, hazards, and planned/real routes, while the
localization, kinematics, and platooning modules save figures and append their
performance text. A missing module or empty queue can therefore fail late in
`evaluate()` rather than at manager construction.

## Planning signals and route distance

`planning_eval` compares the initial global route with the recorded ego dynamic
trace. Route entries are pairs whose first item is a waypoint or transform and
whose second/third items carry route metadata. `calculate_route_dist` sums
successive locations; CARLA waypoints use `waypoint.transform.location`, while
transform-like entries use `entry.location`.

The planning plots use:

- dynamic trace timestamps and speeds;
- IMU accelerometer axes and signed magnitude;
- IMU gyroscope axes and Euclidean magnitude;
- safety status fields `collision`, `offroad`, `stuck`, and `ran_light`;
- real route locations versus the initial planned route.

The source plotting code uses `plt.show`/`show(block=False)` for several plots.
For a headless or batch run, select a non-interactive matplotlib backend (for
example, set `MPLBACKEND=Agg` before importing OpenCDA), save figures explicitly,
and close them after saving. The offline YAML helper does not create plots.

## Debug-helper outputs

The native tests establish the light-weight debug contracts without requiring a
live CARLA server:

- `test/test_drive_profile_plotting.py` passes small numeric lists to
  `draw_sub_plot` and expects a figure-like truthy result.
- `test/test_localization_debug_helper.py` checks that one update populates GNSS,
  filtered, and ground-truth histories, and that `evaluate()` returns a figure
  and text.
- `test/test_planer_debug_helper.py` checks planner history lists and that
  `evaluate()` returns a figure and text.

The planner plotting helper composes velocity, acceleration, TTC, time-gap,
and distance-gap profiles. Those are diagnostic artifacts, not proof of a
successful route or safety claim. Preserve the source data and note the actor
id, time base, and backend when sharing a plot.

## What can be verified offline

With only YAML and standard Python/PyYAML, one can verify frame ordering,
required vehicle fields, tuple construction, horizon lengths, missing-id
truncation, and that a separate output tree is populated. With matplotlib and
synthetic history lists, one can verify figure creation using a non-interactive
backend. One cannot verify CARLA route geometry, actor state, sensor timing,
SUMO co-simulation, detector quality, or manager-level metrics without the
corresponding external runtime and data.

The checked inspection environment imported OpenCDA core managers and common
numeric/plotting dependencies, and `pip check` passed with compatible pins.
No CARLA server, SUMO, ScenarioRunner, torch, or YOLOv5 runtime was verified.
