# Commands and Hydra configurations

These are package-level command templates. Replace angle-bracket values with
paths or names supplied by the caller. The bundled checker is deliberately
non-executing; the four entry points below compose Hydra and can run simulation,
metrics, aggregation, or a web server.

## Configuration layout

The simulation entry points use the `default_simulation` config from the
simulation config group. Its defaults select common settings and leave
`observation`, `ego_controller`, and `planner` for composition. The simulation
config search path also exposes experiment files. The repository's standard
experiment names are:

- `open_loop_boxes`;
- `closed_loop_nonreactive_agents`;
- `closed_loop_reactive_agents`;
- `validation_challenge` and the remote variants.

The corresponding experiment file selects the observation, ego controller,
planner, simulation metrics, and metric aggregator. Always inspect the final
composed config when replacing one of those groups.

The common defaults use `group=${oc.env:NUPLAN_EXP_ROOT}/exp` and
`output_dir=${group}/${experiment}`. For reproducible development, override
`group` or `output_dir` explicitly rather than relying on a timestamped
`experiment_uid`. `NUPLAN_DATA_ROOT` supplies dataset lookup and
`NUPLAN_EXP_ROOT` supplies the default output parent; neither variable causes
this skill to download data.

## Non-executing preflight

Run the checker from the installed skill directory (or provide its path):

```bash
python <simulation-skill>/scripts/check_simulation_config.py \
  --config-root <simulation-config-root> \
  --experiment open_loop_boxes \
  --mode simulation \
  --override worker=sequential \
  --override scenario_filter.limit_total_scenarios=1 \
  --override exit_on_failure=true
```

It checks the supplied config root, the requested default/custom config name,
the local experiment name, and `key=value` override shape. It never imports
Hydra, resolves interpolations, instantiates `_target_` objects, creates output
directories, accesses data, opens a port, or launches any nuPlan process. A
successful check proves only local naming and syntax—not data, map, dependency,
backend, or planner readiness.

Useful checks can be made with `--config-name default_simulation.yaml` (or
`--config default_simulation.yaml`) and `--mode metrics`, `--mode aggregate`,
or `--mode nuboard` for the other config groups. Quote list-valued overrides
in the shell, for example `selected_simulation_metrics='[ego_jerk_statistics]'`.

## `run_simulation`

`run_simulation.py` composes `default_simulation`, builds scenarios, planners,
observations, controllers, callbacks, and one `SimulationRunner` per
scenario/planner pair, then calls the runner executor. It asserts that
`simulation_log_main_path` is null: a fresh simulation cannot simultaneously
be a metric-only run.

```bash
python -m nuplan.planning.script.run_simulation \
  +simulation=open_loop_boxes \
  scenario_filter.limit_total_scenarios=1 \
  worker=sequential \
  number_of_gpus_allocated_per_simulation=0 \
  number_of_cpus_allocated_per_simulation=1 \
  exit_on_failure=true \
  run_metric=false \
  group=<experiment-parent>
```

For closed loop, use `+simulation=closed_loop_nonreactive_agents` or
`+simulation=closed_loop_reactive_agents`; preserve the experiment's complete
observation/controller/planner trio. During planner development, prefer one
scenario, a sequential worker, an explicit output identity, and
`exit_on_failure=true`. Set `run_metric=true` only when the selected metric
engine is ready and its required scenario data are available.

With the standard simulation log callback and `serialization_type=pickle` or
`msgpack`, logs are written for later metric-only evaluation and nuBoard
scenario rendering. The default callback is configured by
`simulation_log_callback`; do not use unsupported serialization types.

## `run_metric`

`run_metric.py` uses the same simulation config composition but does not run a
planner or advance a simulation. It requires a non-null
`simulation_log_main_path`, loads serialized `SimulationLog` objects, builds a
metric engine per scenario type, and runs one `MetricRunner` per log. It writes
per-scenario temporary metric files which a main callback integrates into
parquet.

```bash
python -m nuplan.planning.script.run_metric \
  +simulation=open_loop_boxes \
  simulation_log_main_path=<simulation-output-root> \
  worker=sequential \
  exit_on_failure=true \
  group=<metric-output-parent>
```

The log root must contain compatible `.pkl.xz` or `.msgpack.xz` logs under the
planner/scenario hierarchy. Changing the planner does not change a stored log;
run a new simulation when planner behavior changes.

## `run_metric_aggregator`

`run_metric_aggregator.py` does not rerun simulation or metrics. It optionally
integrates scenario `.pickle.temp` files into `<output>/metrics`, loads metric
parquet files, applies the configured weighted-average aggregators, and writes
aggregated parquet files under `<output>/aggregator_metric` (or the configured
path). `challenges` filters which aggregator/path names are used.

```bash
python -m nuplan.planning.script.run_metric_aggregator \
  output_dir=<experiment-output-root> \
  scenario_metric_paths='[<experiment-output-root>/metrics]' \
  metric_aggregator='[open_loop_boxes_weighted_average]' \
  challenges='[open_loop_boxes]'
```

Use `metric_aggregator='[default_weighted_average]'` and `challenges=[]` for a
non-challenge-specific aggregate. If no compatible parquet files are found,
the callback warns and does not produce a meaningful aggregate. Aggregation
cannot repair missing logs, incomplete metrics, or mixed scenario sets.

## `run_nuboard`

`run_nuboard.py` composes `default_nuboard`, validates the supplied
`simulation_path`, builds the scenario builder, constructs `NuBoard`, and starts
a Bokeh server. It does not compute metrics. `simulation_path` is a list of
`.nuboard` descriptor files or directories containing them; a directory uses
the newest matching descriptor.

```bash
python -m nuplan.planning.script.run_nuboard \
  simulation_path='[<experiment-output-root>/nuboard_<timestamp>.nuboard]' \
  port_number=5006
```

The descriptor records the metric, aggregator, and optional simulation-log
roots plus folder names. Keep all referenced sibling paths in place. A valid
metric parquet is enough for Overview/Histograms, but the Scenarios view also
needs serialized simulation logs. `scenario_rendering_frame_rate_cap_hz` must
be between 1 and 60; choose a lower value for high-latency remote viewing.

## Override safety

A Hydra override has the form `key=value`; group selection commonly uses
`+simulation=name`, and nested values use
`scenario_filter.limit_total_scenarios=1`. The checker accepts these forms but
does not prove that a key exists or that a value has the expected type. Review
list syntax, interpolation, `_target_` changes, output paths, worker mode, and
backend requirements before a large or distributed run. Do not use an
unreviewed override to instantiate an untrusted class.
