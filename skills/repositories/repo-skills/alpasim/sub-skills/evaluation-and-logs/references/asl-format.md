# ASL format and inspection

## Record model

An AlpaSim Log (`.asl`) is a stream of protobuf `LogEntry` messages. Each record
is encoded as a four-byte big-endian unsigned length followed by exactly that
many serialized protobuf bytes. There is no magic header. A partial length
prefix or a short payload is therefore a truncated stream, not an empty
rollout.

The logging schema groups records in a `oneof` named `log_entry`. Common
variants are:

- `rollout_metadata`: session UUID, scene id, step count, timing, component
  versions, actor AABBs, the rig-to-AABB transform, force-GT duration, render
  anchor, and recorded EGO ground-truth trajectory.
- `actor_poses`: a `timestamp_us` and poses for actors, including `EGO`, in
  global/AABB coordinates.
- Driver, controller, physics, traffic, renderer, and video-model requests and
  returns. These are the evidence needed for replay-style diagnosis and for
  rebuilding evaluation input.
- `driver_camera_image`, route requests, camera calibration returns, and
  traffic-session/traffic-return records used by image, route, and prediction
  metrics.

`rollout_metadata.session_metadata.start_timestamp_us` is the egomotion-context
origin. `render_start_timestamp_us` is the first camera-frame shutter-close
render anchor. The policy handover is the render anchor plus
`force_gt_duration`. Do not substitute one timestamp for the other when
explaining a prerun or force-GT interval.

## Streaming API

```python
from alpasim_utils.logs import async_read_pb_log, read_trajectory

async for entry in async_read_pb_log("rollout.asl"):
    kind = entry.WhichOneof("log_entry")
    print(kind)

scene_id_and_trajectory = await read_trajectory("rollout.asl")
```

`async_read_pb_log(path, raise_on_malformed=False)` yields
`alpasim_grpc.v0.logging_pb2.LogEntry`. The default reader logs a warning and
stops at a short final payload; strict mode raises `IOError`. A complete file
can still contain semantically incomplete data, so also check for metadata,
EGO poses, actor definitions, and ground truth.

`read_trajectory()` collects actor-pose messages and currently takes the first
actor pose in each message. It returns `(scene_id, Trajectory)` only when it
finds both a scene id and at least one actor-pose timestamp. For an EGO-only
analysis, ensure the first actor is actually `EGO` or use the accumulator path
that keys actors by id.

## Inspection procedure

1. Confirm the file exists, is non-empty, and is the expected rollout's
   `rollout.asl` rather than a similarly named partial file.
2. Run the bundled printer with `--just-types` and a small `--end` value. This
   exposes ordering and whether the stream has metadata, actor poses, driver
   pairs, camera images, and returns without dumping payloads.
3. Select a small message window and a few `--message-types` to inspect fields.
   Image bytes and video-model payloads are redacted by the helper.
4. Repeat with `--strict` if the final record appears cut off or if a result is
   being used as a reproducibility artifact.
5. Compare record timestamps with `session_metadata.control_timestep_us` and
   camera/request timestamps. Use timestamp joins, not positional assumptions.

## Safe expectations

A valid ASL is not required to contain every oneof variant. A replay-oriented
log may contain service requests and returns but not evaluation camera images;
a minimal unit fixture may contain metadata and actor poses only. Conversely,
video extraction needs camera-image or video-model-return records and may fail
when a rollout has no `RolloutMetadata` or `DriveSessionRequest`.

Do not print raw image, HD-map, or video-model bytes into shared logs. Keep
strict parsing and any copied ASL outside untrusted output locations when
possible, and treat a successful protobuf parse as syntax validation—not proof
that scene maps, metric inputs, or service responses are complete.
