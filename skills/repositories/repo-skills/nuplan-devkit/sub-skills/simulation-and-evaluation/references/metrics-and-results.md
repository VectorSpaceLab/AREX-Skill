# Metrics, aggregation, and results

## Metric execution

`MetricsEngine` owns metric builders for a scenario type. It can `add_metric`,
`compute(history, scenario, planner_name)`, and `write_to_files(...)`. During a
fresh simulation, `MetricCallback.on_simulation_end()` computes the metrics
from the completed `SimulationHistory`. In a metric-only run, the same engine
is called by `MetricRunner` from a serialized `SimulationLog`; no planner
inference or controller propagation occurs in that mode.

Metric computation needs the history and scenario context, not just an ego
trajectory. Depending on the selected metric it may require ego states,
planned trajectories, observations/agents, traffic lights, map geometry, and
mission goal. A synthetic history that omits those fields is not evidence that
the metric works.

The simulation metric builder first selects configured low-level and
scenario-specific builders, then constructs high-level metrics from their
`required_metrics`. If `selected_simulation_metrics` is set, only known metric
names are retained. Verify the final metric names after composition: a typo can
remove a requested metric without fixing it at runtime.

Metric exceptions are logged with the metric name and re-raised as a
`RuntimeError` by `MetricsEngine`. Preserve that name and the first traceback.
When callback workers are enabled, `run_runners()` waits for metric callback
futures before reporting final status; a runner report can still be marked
failed when an asynchronous callback fails.

## Common metric families

- **Open loop**: planner/expert displacement (ADE/FDE-style), heading errors,
  and miss-rate statistics sampled at configured horizons and frequencies.
- **Closed loop**: collisions, drivable-area compliance, driving direction,
  progress, time-to-collision, speed-limit compliance, comfort, acceleration,
  jerk, and speed diagnostics.
- **Diagnostics**: mean speed, longitudinal/lateral acceleration, yaw rate,
  and displacement-error variants.

Thresholds, sampling frequency, horizon, units, and score direction are config
values. Do not assume a universal bound or compare scores from different metric
YAML selections.

## Metric file shape

A per-metric parquet row carries identity columns including:

- `log_name`;
- `scenario_name`;
- `scenario_type`;
- `planner_name`;
- `metric_computator`;
- `metric_statistics_name`.

`MetricStatistics` contributes statistic name/unit/type/value fields, optional
microsecond time-series columns, and optional `metric_score` and
`metric_score_unit`. `MetricStatisticsDataFrame.load_parquet()` restores a
metric dataframe and supports filtering by scenario name/type, planner, and
log. Before comparing results, check planner names, scenario keys, metric name,
units, and scenario counts.

## Aggregation semantics

`run_metric_aggregator.py` loads integrated metric parquet files and invokes one
or more configured `WeightedAverageMetricAggregator` objects. For each
planner, the default implementation:

1. joins metric scores by `scenario_name`;
2. applies every configured `multiple_metrics` value as a multiplicative gate;
3. computes the weighted average of remaining available metric scores using
   named weights or the `default` weight (1.0 when unspecified);
4. averages scenario scores within each `scenario_type`;
5. computes the final score weighted by each scenario type's scenario count.

A missing metric row is missing data, not a perfect score. A metric listed in
`multiple_metrics` is a gate/multiplier, not also a weighted-sum term. A
challenge-specific aggregator selects files whose paths contain its challenge
name. Check that all required metrics cover the same planner/scenario set and
that the selected aggregator matches the evaluation protocol.

The aggregator exposes `aggregated_metric_dataframe`, `final_metric_score`, and
`parquet_file`; `read_parquet()` reloads an output. If no usable metric files
are found, the callback warns instead of creating a meaningful score.

## Result layout

A normal output root may contain:

```text
<output>/
  nuboard_<timestamp>.nuboard
  runner_report.parquet
  simulation_log/
    <planner>/<scenario_type>/<log>/<scenario>/<scenario>.pkl.xz
    # or .msgpack.xz
  metrics/<metric-statistics-name>.parquet
  aggregator_metric/<aggregator-file>.parquet
  summary/<summary>.pdf
  code/hydra/                 # when Hydra config logging is enabled
```

The exact contents depend on callbacks and settings. Per-scenario metrics are
initially saved as `.pickle.temp` files and integrated by `MetricFileCallback`.
`SimulationLogCallback` serializes a `SimulationLog` containing scenario,
planner, and history using compressed pickle or msgpack. Use a new output
identity after a failed run if callbacks may have mixed temporary and final
files.

`runner_report.parquet` records success/error status, start/end times, scenario,
planner, log, and planner runtime report. Inspect `succeeded` and
`error_message`; an existing output directory alone is not a pass. The `.nuboard`
descriptor is a serialized `NuBoardFile` handoff, not a metric result. It
contains roots and folder names for the dashboard and is invalid if referenced
folders have moved or been deleted.

## nuBoard views and comparison gate

nuBoard discovers the descriptor's metric parquet, aggregator parquet, and
optional simulation logs. The dashboard provides:

- **Overview**: aggregate scores by planner and scenario type;
- **Histograms**: metric/statistic distributions;
- **Scenarios**: selected logs, map/object rendering, time series, and scores.

Scenario rendering is unavailable without serialized logs even if metrics and
overview are valid. Before comparing two planners, verify the same metric set,
scenario types, scenario names/counts, log population, score unit, and
aggregator weights/gates. A partial join can look numerically valid while
changing the denominator.
