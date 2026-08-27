# Evaluation workflows

This reference adapts the public NAVSIM v2 command patterns to the installed
`navsim` package. Commands below are templates: they are intentionally not
executed by this skill. Run them only after the preflight and data checks pass.
Use a shell with the workspace variables described by the setup route; never
replace a placeholder with a path copied from another machine.

## Preflight and invariants

Before a data-backed run, record these values in the experiment notes:

- `train_test_split`: one exact named split, including whether it is a
  two-stage split such as `navhard_two_stage` or `navtest_two_stage`.
- `OPENSCENE_DATA_ROOT`: contains the selected log annotations and sensor
  blobs. Two-stage evaluation additionally needs the selected synthetic sensor
  and synthetic-scene roots.
- `NUPLAN_MAPS_ROOT`: contains the map database used while constructing the
  metric cache and by reactive IDM traffic.
- `NAVSIM_EXP_ROOT`: owns the metric cache and experiment output directories.
- `metric_cache_path`: the cache generated for the same split and scene filter.
- proposal sampling: default evaluation is 40 poses at 0.1 s (4 s), while
  NAVSIM scene annotations are commonly 2 Hz. The scorer and simulator must be
  instantiated with identical sampling; the agent trajectory must cover the
  requested horizon and have a valid `TrajectorySampling`.

Run the inspector before deciding that a run is ready:

```bash
python scripts/inspect_evaluation_config.py \
  --split navtest \
  --cache-path "$NAVSIM_EXP_ROOT/metric_cache" \
  --proposal-num-poses 40 \
  --proposal-interval 0.1
```

A non-zero exit is a stop condition. Missing roots are not repaired by creating
empty directories: provide the actual data or select a data-free smoke check.

## Metric caching

Metric caching precomputes map-relative PDM inputs, interpolated detections and
traffic-light observations, the PDM closed planner trajectory, and cache
metadata. The cache layout is keyed below the cache root by log, scene type,
and token, with a compressed `metric_cache.pkl` per token plus metadata. A
cache is therefore a data artifact, not just a generic feature cache.

Safe command template:

```bash
python -m navsim.planning.script.run_metric_caching \
  train_test_split=navtest \
  metric_cache_path="$NAVSIM_EXP_ROOT/metric_cache" \
  force_feature_computation=false
```

Set `force_feature_computation=true` only when intentionally rebuilding the
same cache. For two-stage data, use the exact two-stage split and ensure the
synthetic scene roots resolve through the selected configuration. Do not mix a
cache created for `navtest` with `navhard_two_stage`, even if some tokens happen
to overlap. Check the cache metadata and success/failure totals before scoring.

Caching accesses maps and annotations and can be expensive. A successful
process exit is insufficient if the cache reports failures or if its metadata
omits tokens selected by evaluation.

## One-stage scoring

Use one-stage scoring for ordinary log scenes or for a controlled comparison of
traffic policies. The one-stage runner computes a four-second simulation for
each token, runs the configured agent, transforms its local trajectory into the
initial ego frame, simulates the ego with the PDM LQR/bicycle pipeline, then
scores the resulting state arrays.

Template (constant-velocity planning baseline, non-reactive traffic):

```bash
python -m navsim.planning.script.run_pdm_score_one_stage \
  train_test_split=navtest \
  agent=constant_velocity_agent \
  traffic_agents=non_reactive \
  experiment_name=cv_one_stage \
  metric_cache_path="$NAVSIM_EXP_ROOT/metric_cache"
```

For reactive IDM traffic, use `traffic_agents=reactive`; for the debugging-only
constant-velocity traffic implementation, select the corresponding policy
configuration explicitly. Keep the traffic choice in the experiment notes:
changing it changes the simulated environment, not merely logging.

For a learned agent, add its package configuration and checkpoint override,
for example:

```bash
python -m navsim.planning.script.run_pdm_score_one_stage \
  train_test_split=navhard_two_stage \
  agent=transfuser_agent \
  agent.checkpoint_path="$CHECKPOINT" \
  worker=single_machine_thread_pool \
  experiment_name=transfuser_one_stage \
  metric_cache_path="$NAVSIM_EXP_ROOT/navhard_two_stage/metric_cache" \
  synthetic_sensor_path="$OPENSCENE_DATA_ROOT/navhard_two_stage/sensor_blobs" \
  synthetic_scenes_path="$OPENSCENE_DATA_ROOT/navhard_two_stage/synthetic_scene_pickles"
```

The one-stage script infers adjacent original frames for two-frame extended
comfort. It requires close time adjacency (the implementation accepts a gap up
to 0.55 s) and writes a CSV with per-token scores and an
`average_all_frames` row. A failed agent token becomes an invalid result; do not
report the average as accepted while invalid scenarios remain.

## Two-stage EPDMS scoring

The standard two-stage runner evaluates first-stage original scenes and
second-stage synthetic follow-ups. Both stages use reactive traffic in the
public implementation. Follow-up scene mappings are part of the split
configuration; do not recreate them from token names.

Template:

```bash
python -m navsim.planning.script.run_pdm_score \
  train_test_split=navhard_two_stage \
  agent=constant_velocity_agent \
  experiment_name=cv_two_stage \
  metric_cache_path="$NAVSIM_EXP_ROOT/navhard_two_stage/metric_cache" \
  synthetic_sensor_path="$OPENSCENE_DATA_ROOT/navhard_two_stage/sensor_blobs" \
  synthetic_scenes_path="$OPENSCENE_DATA_ROOT/navhard_two_stage/synthetic_scene_pickles"
```

The runner intersects scene-loader tokens with cache tokens. It warns and skips
missing cache tokens and also warns about unused cache tokens. Treat either
warning as a split/cache consistency failure until explained. For each valid
row it records the endpoint in global coordinates, the start point, simulated
ego states, frame type, and token. It then:

1. computes two-frame extended comfort for mapped adjacent frames;
2. assigns second-stage Gaussian relevance weights from endpoint-to-start-point
   squared distance, using sigma squared 0.1 and a normalized fallback when all
   weights underflow;
3. inserts extended comfort into the weighted metric vector and recomputes the
   final row score;
4. computes stage-one, stage-two, and combined summary rows, where mapped stage
   scores are multiplied and then averaged as defined by the aggregator.

The combined CSV should contain rows named
`extended_pdm_score_stage_one`, `extended_pdm_score_stage_two`, and
`extended_pdm_score_combined`. If pseudo-closed-loop aggregation fails, the
runner falls back to unit weights and marks the aggregate invalid; stop rather
than treating that fallback as a valid two-stage result.

## Scoring an existing submission pickle

Use the submission runner only when a locally validated pickle contains one
first-stage and one second-stage prediction mapping. The current runner
rejects multi-seed evaluation and uses reactive traffic for both stages.

```bash
python -m navsim.planning.script.run_pdm_score_from_submission \
  train_test_split=navhard_two_stage \
  submission_file_path="$SUBMISSION_FILE" \
  metric_cache_path="$NAVSIM_EXP_ROOT/navhard_two_stage/metric_cache" \
  output_dir="$NAVSIM_EXP_ROOT/score-from-submission"
```

Verify that the pickle's token universe, split, trajectory sampling, and cache
are aligned before invoking it. This command is local scoring only; it does not
upload or publish the submission.

## Output and stop conditions

Hydra writes experiment output under the configured `output_dir`; evaluation
scripts add a timestamped CSV. Preserve the resolved config beside the CSV.
Accept a result only when all of the following are true:

- cache and scene token sets were intentionally compared;
- simulator and scorer proposal sampling matched;
- no unexplained failed tokens remain;
- expected summary rows exist for the selected stage;
- the CSV score columns are numeric where expected and `valid` agrees with the
  reported successful-scenario count;
- two-stage aggregation did not take its invalid fallback.

A zero-row, warning-only, or partially written CSV is a failed run. Do not
silence cache warnings or overwrite a prior experiment while diagnosing it.
