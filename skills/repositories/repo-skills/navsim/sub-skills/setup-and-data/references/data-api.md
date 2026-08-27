# Scene and loader contracts

## Loading model

NAVSIM represents OpenScene metadata and sensors as `Scene` objects. A Scene
contains `SceneMetadata`, a nuPlan `map_api`, and an ordered list of `Frame`
objects. A Frame contains a token, timestamp, roadblock ids, traffic-light
annotations, privileged object annotations, an `EgoStatus`, a `Lidar`, and
`Cameras`.

`SceneLoader` is initialized with:

- an original log metadata directory (`data_path`),
- an original sensor root,
- a `SceneFilter`,
- optional synthetic sensor and synthetic scene-pickle roots, and
- a `SensorConfig` (default: no sensors).

It first filters original log pickles into token-to-frame-list entries. If
`include_synthetic_scenes` is true, `synthetic_scenes_path` is mandatory. The
loader then discovers synthetic Scenes and relates them to the final frame
tokens from stage one unless explicit synthetic tokens are requested.

Useful loader properties are:

- `tokens`: original plus selected synthetic scene identifiers;
- `tokens_stage_one`: original scene identifiers only;
- `reactive_tokens_stage_two` and `non_reactive_tokens_stage_two`: selected
  synthetic tokens for each stage-two policy;
- `reactive_tokens` and `non_reactive_tokens`: originals plus the matching
  synthetic tokens; and
- `get_tokens_list_per_log()`: groups original and synthetic tokens by log.

`get_scene_from_token(token)` returns a privileged `Scene`; use
`get_agent_input_from_token(token)` when the consumer must not receive future
annotations or map/scene privilege. Tokens are assertions, not filesystem
paths: check `token in loader.tokens` before retrieval.

## SceneFilter

A filter's core fields are:

- `num_history_frames` (default 4),
- `num_future_frames` (default 10),
- `frame_interval`,
- `has_route`,
- optional `max_scenes`, `log_names`, and `tokens`,
- `include_synthetic_scenes`, `synthetic_scene_tokens`, and
- optional reactive/non-reactive synthetic initial-token lists.

`num_frames` is history plus future. A `None` frame interval is normalized to
that scene length, producing non-overlapping samples; an explicit interval of
1 produces sliding samples. Filtering skips short frame lists and, when
`has_route` is true, skips the frame whose route has no roadblock ids. Filters
are data/config contracts: do not infer a split by changing only
`data_split`, because the scene filter and stage-two mapping must match it.

## Scene and Frame semantics

- Log-loaded Scene frame ego poses are global and marked
  `EgoStatus.in_global_frame=True`.
- `Scene.get_history_trajectory()` converts the history poses into the local
  rear-axle frame of the last history frame.
- `Scene.get_future_trajectory()` converts future poses into that same local
  frame. NAVSIM's interval is 0.5 seconds (2 Hz), and the returned trajectory
  has `(x, y, heading)` rows.
- `Scene.get_agent_input()` returns only history ego statuses, cameras, and
  LiDAR. Its ego poses are local; future annotations and map privilege stay on
  Scene.
- Scene metadata records log name, scene token, map name, initial token, and
  history/future counts. Synthetic metadata additionally relates a synthetic
  scene to its original scene where supplied.
- The map API is built from the configured map root and map name. A valid log
  directory without a compatible map database can still fail at Scene creation.

A log Scene needs at least `num_history_frames + num_future_frames` frames for
normal filtering and future-trajectory extraction. Do not request more future
poses than the selected filter provides.

## AgentInput and sensors

`AgentInput` has parallel lists `ego_statuses`, `cameras`, and `lidars`, each
covering the history window. `Cameras` exposes eight camera slots:
`cam_f0`, `cam_l0`, `cam_l1`, `cam_l2`, `cam_r0`, `cam_r1`, `cam_r2`, and
`cam_b0`. `Lidar.lidar_pc`, when loaded, is a merged `(6, N)` point array
`(x, y, z, intensity, ring, lidar_id)`; unloaded objects are empty wrappers.

`SensorConfig` has those nine names (eight cameras plus `lidar_pc`). Each value
is either:

- `False`: do not load that sensor;
- `True`: load it at every requested history iteration; or
- a list of history indices: load it only at those iterations.

Use `SensorConfig.build_no_sensors()` for metadata/filter tests and
`SensorConfig.build_all_sensors(include=[...])` or explicit fields for bounded
history. `get_sensors_at_iteration(i)` returns the names enabled at index `i`.
A sensor-enabled load requires every referenced image/point-cloud path under
the corresponding original or synthetic sensor root.

## Disk-backed synthetic Scenes

Synthetic scene pickles are loaded with the synthetic sensor root and the same
sensor configuration. They contain serialized scene metadata and frames, but
sensor images/point clouds remain external. Thus a synthetic pickle directory
can exist while loading still fails because a referenced sensor blob is absent.
Keep the synthetic sensor root paired with its synthetic pickle bundle.

## Cache relationship

Metric caching preprocesses annotations and map geometry and stores results
under `$NAVSIM_EXP_ROOT/metric_cache`. It is not required to construct a
no-sensor Scene or inspect a split, but evaluation may require a cache whose
scene tokens and map/data version match the selected evaluation split. Cache
creation is intentionally not part of the setup validator.

## Safe API smoke test

With dependencies installed, this is a no-data contract check:

```bash
python - <<'PY'
from navsim.common.dataclasses import SceneFilter, SensorConfig
f = SceneFilter(num_history_frames=4, num_future_frames=8, frame_interval=1)
assert f.num_frames == 12
assert SensorConfig.build_no_sensors().get_sensors_at_iteration(0) == []
assert len(SensorConfig.build_all_sensors().get_sensors_at_iteration(0)) == 9
print("DATA API CONTRACT OK")
PY
```

Expected output is `DATA API CONTRACT OK`. This does not prove that a map or
sensor file can be opened.
