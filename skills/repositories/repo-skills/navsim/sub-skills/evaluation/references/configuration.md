# Evaluation configuration

NAVSIM evaluation uses Hydra composition. Override config *keys*, not Python
constructor arguments, and keep the resolved config with the output CSV.
`python -m navsim.planning.script.<runner>` is the package-safe form of the
public runners.

## Important defaults

The common evaluation composition supplies:

- a required `train_test_split` and its scene filter;
- `worker=ray_distributed_no_torch` by default;
- `proposal_sampling.num_poses=40` and `proposal_sampling.interval_length=0.1`;
- `traffic_agents=non_reactive` for one-stage selection;
- `gpu=true`, `verbose=false`, and a two-hour distributed timeout;
- dataset paths from `OPENSCENE_DATA_ROOT`, map paths from
  `NUPLAN_MAPS_ROOT`, and cache/experiment paths from `NAVSIM_EXP_ROOT`.

The default PDM scorer config uses weights `5, 5, 2, 2, 2` for EP, TTC, LK,
HC, and EC. Its key thresholds are documented in
[metrics-reference](metrics-reference.md).

## Split and path overrides

Use one split consistently across caching, scoring, and submission validation:

```text
train_test_split=navtest
metric_cache_path=$NAVSIM_EXP_ROOT/metric_cache
```

For two-stage evaluation, override all relevant synthetic roots rather than
assuming a default:

```text
train_test_split=navhard_two_stage
metric_cache_path=$NAVSIM_EXP_ROOT/navhard_two_stage/metric_cache
synthetic_sensor_path=$OPENSCENE_DATA_ROOT/navhard_two_stage/sensor_blobs
synthetic_scenes_path=$OPENSCENE_DATA_ROOT/navhard_two_stage/synthetic_scene_pickles
```

`navsim_log_path` and `original_sensor_path` normally derive from the selected
split's data split. If they are overridden, verify that the scene filter and
cache were built over the same token universe. Do not point a two-stage split
at a standard log-only cache.

## Agent and scorer overrides

Baseline or custom agent selection:

```text
agent=constant_velocity_agent
agent=human_agent
agent=ego_status_mlp_agent agent.checkpoint_path=$CHECKPOINT
agent=transfuser_agent agent.checkpoint_path=$CHECKPOINT
```

For learned agents, sensor roots and checkpoint format are agent contracts;
route model details to the agents/training skills. Keep the scorer and simulator
proposal sampling coupled. If changing the interval or number of poses, apply
both nested overrides and rebuild the cache:

```text
proposal_sampling.num_poses=40
proposal_sampling.interval_length=0.1
scorer.proposal_sampling.num_poses=40
scorer.proposal_sampling.interval_length=0.1
simulator.proposal_sampling.num_poses=40
simulator.proposal_sampling.interval_length=0.1
```

In the standard composition, scorer and simulator reference the common
`proposal_sampling`, so changing the common key is preferred. The explicit
form is useful for diagnosing a custom composition. A mismatch must stop with
the scorer/simulator assertion; do not bypass it.

## Worker choices

Select a worker according to the data-backed workload and debugging need:

```text
worker=sequential
worker=single_machine_thread_pool
worker=ray_distributed_no_torch
```

For a thread pool, optionally set `worker.max_workers=N` and
`worker.use_process_pool=false`. Use sequential execution for a small,
repeatable diagnostic, not as an assumption that full evaluation is cheap. The
metric cache runner refuses Ray's built-in distributed mode for this job; do
not set `worker.use_distributed=true` for caching.

## Scorer threshold overrides

Use the nested scorer config names exactly:

```text
scorer.config.progress_weight=5.0
scorer.config.ttc_weight=5.0
scorer.config.lane_keeping_weight=2.0
scorer.config.history_comfort_weight=2.0
scorer.config.two_frame_extended_comfort_weight=2.0
scorer.config.lane_keeping_deviation_limit=0.5
scorer.config.lane_keeping_horizon_window=2.0
scorer.config.future_collision_horizon_window=1.0
scorer.config.human_penalty_filter=true
```

Changing weights or thresholds defines a different metric protocol. Include all
non-default overrides in the run record and do not compare it to a default
leaderboard score without recalculation.

## Output and verbosity

`experiment_name` is required by the evaluation output composition. `output_dir`
may be supplied for an explicit destination; otherwise it is derived under the
experiment root with a timestamp. `verbose=true` prints the final rows but does
not replace inspecting the CSV. Keep Hydra's resolved config and the CSV
co-located.

## Safe override workflow

1. Start from the exact runner for the desired stage.
2. Add only split, cache/data roots, agent/submission, worker, policy, and
   experiment/output overrides needed for the run.
3. Render or inspect the final values with the bundled inspector or Hydra's
   help/config mode before allowing data access.
4. Confirm cache/split/sampling consistency and policy semantics.
5. Run once, preserve logs/CSV, and stop on warnings described in
   [troubleshooting](troubleshooting.md).
