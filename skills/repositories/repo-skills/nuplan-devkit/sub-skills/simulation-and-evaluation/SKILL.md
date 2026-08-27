---
name: simulation-and-evaluation
description: "Implement or run nuPlan planners, assemble open or closed loop
  simulations, compute and aggregate metrics, inspect serialized results, or
  launch nuBoard."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Simulation and evaluation

Use this skill for planner implementation and inference, simulation assembly,
metric computation or scoring, result inspection, and nuBoard. Keep training,
feature preprocessing, and checkpoint production in `training-and-preprocessing`;
keep database/map layout in `data-and-maps`; keep remote submission protocol in
`submission-and-cli`.

## Route the request first

Classify the request before changing code:

- **Planner**: implement a class satisfying the planner contract or choose a
  configured baseline.
- **Simulation**: run an open-loop replay or a closed-loop controller and
  observation setup.
- **Metrics**: compute metrics during simulation or rerun them from serialized
  simulation logs.
- **Aggregation**: combine metric parquet files into scenario, scenario-type,
  and final planner scores.
- **Inspection**: inspect parquet/log outputs or launch nuBoard.

Read the relevant reference before acting:

- [Planner and simulation API](references/planner-and-simulation-api.md)
- [Commands and Hydra configurations](references/commands-and-configs.md)
- [Metrics, aggregation, and results](references/metrics-and-results.md)
- [Troubleshooting](references/troubleshooting.md)

Run the non-executing validator before a new or complex Hydra invocation:

```bash
python <simulation-skill>/scripts/check_simulation_config.py \
  --config-root <simulation-config-root> \
  --experiment open_loop_boxes \
  --mode simulation \
  --override worker=sequential \
  --override scenario_filter.limit_total_scenarios=1
```

The validator only checks local config paths and override shape; it never
starts Hydra, simulation, metric computation, a server, or a download.

## Planner contract

A custom planner must expose `name()`, `initialize(PlannerInitialization)`,
`observation_type()`, and `compute_planner_trajectory(PlannerInput)`. Return an
`AbstractTrajectory`, normally an `InterpolatedTrajectory`, from
`compute_planner_trajectory`; the public `compute_trajectory()` wrapper records
runtime and re-raises failures. Initialization supplies route roadblock IDs,
the mission goal, and map API. Each input supplies the current iteration,
rolling history, and optional traffic-light data.

The trajectory must contain at least two time-ordered compatible states and
cover the next simulation iteration. Every controller queries the trajectory
at that next timestamp; an `InterpolatedTrajectory` rejects out-of-range
queries. Ensure the planning horizon is long enough for the scenario time
step, and use consistent microsecond timestamps. Do not return `None`, a raw
array, or a trajectory whose state type does not match the controller.

Planner observation type must exactly match the configured observation type.
For a normal planner, initialize once per scenario and do not retain mutable
state across scenarios without resetting it. `SimplePlanner` produces a
straight, constant-acceleration trajectory with a velocity cap. `IDMPlanner`
needs a map-backed route with usable roadblocks and follows a BFS path plus an
IDM longitudinal policy. `MLPlanner` consumes a compatible model wrapper and
turns the model's future relative poses into an interpolated trajectory; model
training and feature construction are out of scope here.

## Assemble and run safely

Choose the complete trio, not just a planner:

| Goal | Observation | Ego controller | Typical experiment |
|---|---|---|---|
| Open-loop boxes | `box_observation` | `log_play_back_controller` | `open_loop_boxes` |
| Closed-loop, non-reactive agents | `box_observation` | `two_stage_controller` | `closed_loop_nonreactive_agents` |
| Closed-loop, reactive agents | `idm_agents_observation` | `two_stage_controller` | `closed_loop_reactive_agents` |

A simulation runner initializes the planner, repeatedly obtains a
`PlannerInput`, calls the planner, invokes callbacks, and propagates the
trajectory through the ego controller and observation engine until the step
time controller reaches the end. `run_metric=true` attaches a metric engine
at simulation end. Enable simulation-log serialization when a later
metric-only run or nuBoard scenario rendering is required.

Prefer a one-scenario, sequential dry run while developing a planner. Set an
explicit output directory or experiment name, limit scenarios, and set
`exit_on_failure=true` when you need the first failure to be visible. Do not
silently switch a closed-loop request to open-loop: the controller and
observation change the evaluated behavior.

## Evaluate and inspect

Simulation produces runner reports, a `.nuboard` descriptor, optional
serialized simulation logs, metric files, and aggregated files. Metric-only
execution requires `simulation_log_main_path`; a fresh simulation must leave it
unset. Aggregation reads integrated metric parquet files and writes weighted
average parquet output. nuBoard consumes the `.nuboard` descriptor and shows
Overview, Histograms, and Scenarios; pass the descriptor or its containing
experiment directory explicitly.

When a run fails, first identify the layer from the error: Hydra/config,
scenario/data, planner/trajectory, controller/observation, metric engine,
aggregation, or nuBoard. Preserve the first traceback and runner report.
Use [Troubleshooting](references/troubleshooting.md) rather than masking a
planner or metric failure with `exit_on_failure=false`.

## Completion checks

Before calling the task complete, confirm:

1. The planner observation type and returned trajectory horizon match the
   configured observation/controller and simulation time step.
2. The chosen Hydra experiment overrides the intended observation, controller,
   planner, metrics, worker, scenario filter, and output path.
3. The output contains the expected logs/metric parquet/aggregator parquet (or
   the request explicitly did not require them).
4. Metric and aggregate scores are not being compared across mismatched
   scenario types, planners, or incomplete metric sets.
5. nuBoard receives a valid `.nuboard` file and all referenced sibling folders
   remain available.
