# Runtime configuration and timing

Read this before changing cadence, skip flags, caches, renderer kind, or daemon
capacity. Values below are runtime concepts and can be supplied by a resolved
YAML config or by the deployment route that generates one.

## Core fields

| Field | Meaning and safe use |
| --- | --- |
| `simulation_config.control_timestep_us` | Policy/controller/traffic step interval. Must be positive. |
| `simulation_config.pose_reporting_interval_us` | Intermediate egomotion reports; `0` uses the control cadence. |
| `simulation_config.cameras[*].frame_interval_us` | Camera capture cadence in microseconds. Each configured camera is checked independently. |
| `simulation_config.cameras[*].shutter_duration_us` | Exposure interval; keep it compatible with the selected scene/camera. |
| `simulation_config.force_gt_duration_us` | Recorded-trajectory warmup/handover duration. A video-model run needs at least its first plus one regular chunk. |
| `simulation_config.skip_driver_during_force_gt` | Avoids policy calls during force-GT; useful for replay-like operation. |
| `simulation_config.assert_zero_decision_delay` | Asserts that latest camera frames and egopose are current at each policy step. |
| `simulation_config.physics_update_mode` | `NONE`, `EGO_ONLY`, or `ALL_ACTORS`; physics must not be skipped when a non-`NONE` mode is selected. |
| `simulation_config.planner_delay_us` | Models perception/planner delay through a runtime delay buffer. |
| `simulation_config.render_bundling` | Sensorsim RPC choice; `none` renders camera calls separately. Route protobuf details elsewhere. |
| `endpoints.<service>.skip` | Makes a service a no-op/placeholder path; it does not install or start that service. |
| `endpoints.<service>.n_concurrent_rollouts` | Per-address concurrency budget used by runtime pools. Balance it against real service capacity. |
| `endpoints.startup_timeout_s` | Timeout for readiness/version/scenario probes. Increase for cold model/cache startup, not to hide a bad port. |
| `endpoints.do_shutdown` | Whether managed endpoints are asked to shut down after one-shot completion. |
| `nr_workers` | `1` is inline; values above one use spawned workers. |
| `max_rollout_retries` | Retry budget for non-invalid-scene rollout failures. |

## Zero-delay alignment

With `assert_zero_decision_delay: true`, the policy event checks that the latest
estimated egopose timestamp equals the decision timestamp and that every camera
has a frame no later than/current at that timestamp. In the common exact-grid
configuration, use an integer multiple relationship:

```text
control_timestep_us % camera.frame_interval_us == 0
```

For example, a 30 Hz camera grid may use `33_333` microseconds and an 8-frame
control interval of `266_664` microseconds. A 10 Hz camera and control loop may
both use `100_000`. Do not round a frequency in prose and then mix a different
integer interval in YAML. If the cadence is intentionally asynchronous, disable
the assertion only when the policy can handle extrapolation and document why.

The first decision is not necessarily at the recorded scene start. The runtime
seeds context, anchors rendering to the first available camera frame, and
starts policy after force-GT/warmup. Read the resolved timeline from logs when
an offset or camera-range error appears.

## Video-model equations

The built-in video-model wrapper uses integer arithmetic:

```text
frame_interval_us = floor(1_000_000 / fps)
first_chunk_duration_us = first_chunk_frames * frame_interval_us
regular_chunk_duration_us = chunk_frames * frame_interval_us
```

For a nonzero force-GT duration, runtime validation requires:

```text
control_timestep_us == regular_chunk_duration_us
force_gt_duration_us >= first_chunk_duration_us + control_timestep_us
(force_gt_duration_us - first_chunk_duration_us) % control_timestep_us == 0
```

`fps`, `first_chunk_frames`, and `chunk_frames` must be positive. `frame_forwarding_mode`
must be `all` or `subsample`; forwarding HD-map debug frames requires
`return_hdmap_frames: true`. A model server's block size must match the selected
chunk preset. Driver-side `subsample_factor` is a policy input-rate choice and
is separate from renderer frame generation; use the driver route for model
history semantics.

The recorded USDZ seed image, FTheta calibration, rig-to-camera pose, and
HD-map conditioning must describe the same camera. In video-model mode, only
resolution overrides are supported on a recorded camera definition; changing
pose or intrinsics breaks alignment with the seed frame. Missing calibration,
missing first-frame JPEGs, or missing map parquet is a data/asset failure.

## Capacity and scene-affine dispatch

A service's useful capacity is the product of replicas/container or internal
workers and `n_concurrent_rollouts`; renderer implementations may additionally
have a server-side worker limit. Start video-model renderer concurrency at one
and scale only after latency and VRAM headroom are observed.

Optional scene-affine dispatch routes jobs to renderer addresses with a confirmed
scene cache. It keeps bounded scene locations and can refresh cache state
periodically. It requires a renderer implementing cache introspection. If the
renderer returns `UNIMPLEMENTED`, disable scene-affine dispatch rather than
loosening startup timeout. `max_renderers_per_scene` must be positive, and
`max_scenes_per_renderer`, when set, must also be positive.

## Cache families

- USDZ artifact cache: `scene_provider.usdz.artifact_cache_size`; `None` means
  unlimited, `0` disables LRU reuse. A cache key includes scene ID and artifact
  path.
- Force-GT frame cache: sensorsim-only deterministic warmup frames. It requires
  a cache directory and stable scene/camera/render identity; changing launch or
  camera configuration requires a new `extra_key` or cache cleanup.
- Renderer backend cache: external NRE/renderer state managed by the service,
  observed only through supported introspection. It is not the same as the
  Python artifact cache.

Use `scripts/inspect_runtime_config.py` for offline structural checks. It does
not prove that an asset exists, a port accepts gRPC, or a backend has enough
VRAM.
