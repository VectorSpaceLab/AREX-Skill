# Metrics, modifiers, and videos

## Metric lifecycle

A scorer returns a `MetricReturn` with a unique name, timestamp list, values,
valid flags, and a time aggregation (`mean`, `median`, `max`, `min`, or `last`).
`MetricReturn.aggregate()` excludes invalid values and returns NaN when no valid
value remains. The evaluator also creates a Polars long dataframe with
`name`, `timestamps_us`, `values`, `valid`, `time_aggregation`, `clipgt_id`,
`rollout_id`, `run_uuid`, and `run_name`.

The registered scorer family covers collision, offroad, minimum distance to
obstacles, open-loop collision, ground-truth progress/deviation, minADE, plan
deviation, image health, and safety. A metric can be absent or invalid when
its data source is absent; do not convert “not computed” into a pass.

## Important configuration

`EvalConfig` controls:

- `enabled` and `allow_aggregation_with_failed_rollouts`;
- `parse_unstructured_debug_info` (disable for untrusted driver images because
  some drivers encode debug data with pickle);
- scorer options for minADE, plan deviation, image, and open-loop collision;
- `aggregation_modifiers.max_dist_to_gt_trajectory` and
  `remove_preengagement_timesteps`;
- `scene_score.enabled`, progress saturation, and the short-ground-truth
  threshold;
- `num_processes`, vector-map parameters, vehicle shrinkage/corner rounding,
  and video settings.

Vehicle shrinkage and corner rounding affect collision polygons and video. A
shrink factor of zero preserves the AABB; a value of one collapses the metric
footprint toward a point. Corner roundness is applied after shrinkage and is
bounded to `[0, 1]`.

## Default aggregation behavior

The processing pipeline adds stable identifiers for each trajectory and then
applies modifiers in sequence. The important defaults are:

1. Drop pre-engagement rows where `eval_relevant` is false.
2. Add combined offroad-or-collision and at-fault collision events.
3. Add `duration_frac_20s` from elapsed timestamp.
4. Remove trajectories with black images.
5. Remove timesteps after the first offroad/collision event.
6. Apply the configured ground-truth-distance cutoff.

Time aggregation happens first, then clips are averaged, then rollouts are
averaged for the run. Standard deviation is over rollouts. The text report
prints the selected aggregation function beside each metric, so compare both
value and aggregation method.

Common interpretations:

- `collision_any`, `collision_front`, `collision_lateral`, `collision_rear`,
  and `offroad` are event-like values; zero means no detected event in the
  retained rows.
- `collision_at_fault` combines front/lateral collision events. Rear-end
  collision is kept separately and is not automatically at fault.
- `dist_to_gt_trajectory` is a deviation distance; lower is better and its
  default event handling can truncate later rows.
- `progress`, `progress_rel_to_total`, and `duration_frac_20s` are endpoint or
  completion-style values; inspect `last` semantics and retained timestamps.
- `avg_dist_between_incidents` and its at-fault variant are kilometers per
  incident. A zero incident denominator can yield a non-finite value.
- `offroad` may be filled with zero during aggregation when no offroad column
  exists. The report records that warning; it is not map-backed verification.

## Scene score summary

When scene scoring is enabled, `results-summary.json` includes per-rollout
`status`, `passed`, `score`, `failure_reason`, and score metrics. The score uses
clipped progress relative to the configured saturation threshold, with a full
score override for sufficiently short ground-truth clips. At-fault collision
and offroad must be zero for a pass. Failed rollouts can be appended with a
failure reason even when they have no metric rows.

A long clip must retain its full `gt_dist_traveled_m` even if metric rows are
removed after a deviation event; otherwise a short-clip override can be applied
incorrectly. If required score metrics are absent, enabled scene scoring should
fail fast. Disable scene scoring only when an unscored result is intentional and
record that decision.

## Output and video layouts

A completed run commonly contains:

```text
run/
├── rollouts/<clipgt-id>/<rollout-id>/
│   ├── rollout.asl
│   ├── metrics.parquet
│   ├── _complete
│   └── <clip>_<rollout>_<camera>_<layout>.mp4
├── eval/...
├── aggregate/
│   ├── metrics_results.txt
│   ├── metrics_results.parquet
│   ├── metrics_unprocessed.parquet
│   ├── results-summary.json
│   ├── metrics_results.png
│   └── videos/{all,violations}/...
└── eval-config.yaml
```

The default video layout is a BEV map, camera, and metrics table. The reasoning
overlay layout shows a first-person image with reasoning text and a trajectory
chart. `video_layouts` selects one or both; `camera_id_to_render` names the
camera; `render_every_nth_frame` bounds rendering cost. The default video
filename is composed from clip id, rollout id, camera id, and layout id.

Video rendering needs camera records, compatible image codecs/ffmpeg, and (for
BEV/offroad content) map geometry. A successful metrics parquet does not imply
that a video can be rendered. Review the renderer log and the boolean result
from `render_video_from_eval_result()` separately.
