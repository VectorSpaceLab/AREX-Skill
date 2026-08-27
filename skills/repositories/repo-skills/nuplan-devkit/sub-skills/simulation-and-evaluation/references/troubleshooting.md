# Troubleshooting simulation and evaluation

Keep the first traceback, the exact composed config, runner report, and output
identity. Diagnose the earliest failing layer; do not hide a planner or metric
failure by setting `exit_on_failure=false`.

| Symptom | Layer | Recovery |
|---|---|---|
| Config group not found, mandatory `???`, or rejected override | Hydra composition | Run the bundled checker; verify the config root, experiment name, group syntax, quoting, and rendered config. |
| Missing `NUPLAN_DATA_ROOT`, database/map file, or `No scenarios found to simulate!` | Data/scenario builder | Check dataset and map roots, scenario builder/filter, scenario type, and limit. The simulation skill does not download data. |
| Planner `_target_` cannot import or builder says a scenario is required | Planner construction | Verify the installed package target and constructor. Set `requires_scenario` only for an oracle planner; do not add a scenario argument to a normal planner. |
| Observation type mismatch | Setup validation | Compare `planner.observation_type()` with `setup.observations.observation_type()` exactly. Select a matching observation/controller/experiment trio. |
| Initialization assertion, missing route/map object, or IDM BFS warning | Planner initialization/map | Confirm initialization happened, route roadblocks are usable, the map covers the ego, and the route can reach its target. |
| Empty/one-state trajectory, interpolation out of range, duplicate timestamps, or controller query failure | Trajectory/controller | Return at least two same-type, strictly time-ordered states beginning at the current state and covering `next_iteration.time_point`; use microsecond `TimePoint`s. |
| `Current state of controller cannot be None`, speed safety error, or unstable tracking | Ego controller | Inspect the queried state and horizon. `PerfectTrackingController` rejects speed >= 50 m/s; tracking controllers need a queryable future. |
| `simulation_history_buffer_duration` error | Simulation setup | Set it no lower than the scenario `database_interval`; remember the implementation adds one interval when sizing the buffer. |
| Metric engine reports a named `RuntimeError` | Metric/history | Isolate the named metric, verify required map/agent/traffic-light/history fields, and preserve the original traceback. |
| Metric-only run cannot find logs or cannot decode them | Result layout | Set `simulation_log_main_path` to a real compatible output root containing `.pkl.xz` or `.msgpack.xz` logs. Do not use it for a fresh simulation. |
| No metric parquet or aggregate warning | Callback/integration | Wait for callback completion; check `.pickle.temp` files, `metric_dir`, scenario metric paths, parquet readability, and challenge filtering. |
| NaN, missing columns, or unexpected aggregate score | Aggregation/data join | Compare planner/scenario/log keys and metric sets. Missing rows are not zero/one; verify `multiple_metrics`, weights, and scenario counts. |
| nuBoard rejects a path or tabs are empty | Descriptor/layout | Pass a `.nuboard` file or directory containing one, keep its referenced roots beside the descriptor, and confirm parquet files exist. |
| nuBoard Overview works but Scenarios is empty | Serialization | Re-run with `SimulationLogCallback` and `pickle` or `msgpack`; metric-only output cannot recreate simulation tiles. |
| Port or remote rendering issue | nuBoard runtime | Use a free port and keep `scenario_rendering_frame_rate_cap_hz` in 1–60; lower it for high-latency viewing. |

## Recovery order for a malformed custom planner

When both configuration/data and planner output look broken, separate them:

1. Run the non-executing checker with the exact config root, experiment, config
   name, and overrides. Fix missing local names or invalid syntax first.
2. Compose a one-scenario sequential run with an explicit output identity and
   `exit_on_failure=true`. Confirm scenario discovery and planner
   initialization before interpreting trajectory errors.
3. Run an isolated planner contract fixture: initialize with a mock
   `PlannerInitialization`, call `compute_trajectory()` with a mock input, and
   assert two compatible finite samples, current start time, and next-step
   coverage.
4. If that passes, inspect the actual scenario database interval, controller
   query time, and trajectory horizon. An out-of-range assertion is a
   controller/trajectory issue, not a metric issue.
5. Only after simulation succeeds enable metrics. Isolate the named metric,
   then integrate and aggregate. Do not attribute missing experiment-root data
   to a metric threshold or planner score.

Typical signatures include interpolation assertions, `Current state of
controller cannot be None`, velocity safety errors, `Metric Engine failed
with: ...`, and `No metric files found for aggregation!`. Record which layer
was reached and which artifacts exist.

## Clean reruns and scope boundaries

- Preserve runner reports, tracebacks, and partial logs for diagnosis, but use a
  new output identity for a clean rerun when callback files may be mixed.
- Rerun metrics from intact logs only; a changed planner requires new
  simulation logs.
- Rerun aggregation after verifying integrated parquet files; it cannot create
  missing scenario logs or trajectories.
- Regenerate a descriptor when referenced paths moved; do not edit result
  parquet blindly.
- CUDA, data acquisition, S3, Docker, and remote submission are not silently
  enabled by this skill. Route them to the data/maps or submission workflow.
