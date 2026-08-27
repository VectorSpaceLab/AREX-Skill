# Physics and CATK traffic workflows

## Ground-mesh physics

The physics service constrains the predicted pose of ego and other objects to an
environment mesh. It does not perform collision handling and does not propagate
vehicle dynamics. The backend constructor is:

```python
PhysicsBackend(
    env_mesh_ply: bytes,
    visualize: bool = False,
    profile: bool = False,
)
```

`update_pose(predicted_pose, aabb, timestamp)` accepts a 4x4 pose matrix, a
three-element `[length, width, height]` AABB, and a timestamp used for tracing or
visualization. It returns `(updated_pose, GroundIntersectionStatus)`. The
implementation samples a grid of points on the AABB bottom, sends upward and
downward Z rays to the Warp mesh, fits a plane from successful intersections,
and estimates a translation plus rotation. The bounded default tolerances are
1.5 m translation and 10 degrees rotation. If a fit is accepted, the correction
is applied; the final implementation restores the predicted X/Y to avoid
lateral drift while retaining ground Z and rotation corrections.

Statuses are:

- `SUCCESSFUL_UPDATE`: correction was accepted.
- `INSUFFICIENT_POINTS_FITPLANE`: too few valid intersections for a plane.
- `HIGH_TRANSLATION`: estimated correction exceeded 1.5 m.
- `HIGH_ROTATION`: estimated rotation exceeded 10 degrees.

The service CLI is:

```bash
physics_server --artifact-glob '/data/artifacts/*.usdz' \
  [--host HOST] [--port PORT] [--use-ground-mesh BOOL] \
  [--visualize BOOL] [--cache-size N] [--log-level LEVEL]
```

`--artifact-glob` is required and must discover artifacts with the appropriate
mesh data. A scene is loaded on the first request and cached by scene ID; set
the cache at least as high as the number of concurrent scenes if avoiding cache
thrash matters. `--visualize` requires the optional visualization dependency and
should not be enabled for a headless smoke test.

Safe physics validation uses a small planar PLY mesh and checks that a pose
above or below the plane converges in Z, that X/Y remain unchanged, and that the
utility conversions preserve quaternion ordering. A Warp import or a CUDA
availability probe alone does not execute `update_pose`.

## CATK service configuration

The Hydra-resolved typed configuration has this shape:

```yaml
server:
  host: 0.0.0.0
  port: 6200
  max_workers: 8
  log_file: null
catk:
  device: cuda
  filter_distance_th: 100.0
  predict_static: false
  min_valid_history_steps: 5
  loader:
    usdz_folder: /data/scenes
    num_history_steps: 16
    prediction_steps: 5
    time_step: 0.1
  model:
    config_path: /models/catk/config.yaml
    ckpt_path: /models/catk/latest.ckpt
    token_pkl_dir: /models/tokens
```

The loader also controls map element names, polyline length/resampling,
filtering mode, ego-distance cutoff, and per-category polyline limits. The model
options control sub-polyline handling and downsampled lines. Keep model paths,
scene mounts, and port overrides in the deployment-owned config rather than
hard-coding them into client code.

The service entry point is `catk_trafficsim_server`. A local Hydra invocation
has this shape:

```bash
catk_trafficsim_server \
  --config-path=/path/to/config-dir \
  --config-name=server.yaml \
  server.port=6200 \
  catk.loader.usdz_folder=/data/scenes
```

Startup rejects a missing/non-directory USDZ folder or one with no recursive
`.usdz` files before the gRPC server starts. CATK construction then additionally
requires the model config, checkpoint, token data, CUDA, and matching compiled
PyG extensions.

## Session and handover timeline

`start_session` validates a non-empty `session_uuid`, `scene_id`, and logged
object trajectories. The logged set must contain a non-empty `EGO` trajectory;
`handover_time_us` must be positive. The scene adapter produces environment data
with ego, agents, map, timing, and object metadata. The service resamples a
history window ending at the initial session time:

```text
first EGO timestamp + (num_history_steps - 1) * time_step
```

For `simulate(session_uuid, time_query_us, object_trajectory_updates)`:

1. Merge incoming updates into the maintained closed-loop history.
2. If `time_query_us <= handover_time_us`, resample logged history and return
   replay. No model inference is expected.
3. Otherwise, rebuild the latest history window, populate the requested ego
   future, preprocess map geometry, and calculate future step indices.
4. Reject a request that needs more future steps than `prediction_steps`.
5. Run CATK, apply predicted agent XYZ/heading/valid masks, correct agent Z from
   nearby lane lines when possible, and carry static/sparse-history agents as
   configured.
6. Build the response, merge future and forecast trajectories, and advance the
   session's current time to the exact requested timestamp.

The service serializes `simulate` calls for one session using a session lock.
Different sessions can enter the inference batcher concurrently. The batcher
collates variable agent/map graph sizes, records per-request non-ego split sizes,
and de-collates model outputs. A missing `rb_polylines` field or malformed graph
input is a data-contract error, not a reason to fabricate predictions.

## Status and recovery map

| Observation | Meaning | Next action |
|---|---|---|
| `INVALID_ARGUMENT` on start | missing UUID/scene/trajectory/EGO or non-positive handover | fix request fields and time anchor |
| `NOT_FOUND` on start | scene ID cannot be loaded | use a scene advertised by the service and verify its USDZ data |
| `ALREADY_EXISTS` | UUID is already registered | close it or choose a new UUID |
| `INVALID_ARGUMENT` on simulate | query needs more than configured prediction steps, or ego future is insufficient | shorten the query/request or increase configured horizon and provide ego poses |
| `FAILED_PRECONDITION` after handover | CATK could not produce predictions, commonly no usable map geometry | inspect map radius, scene adapter output, model/backend availability; do not static-fallback |
| `INTERNAL` on simulate | unexpected exception in the inference/data path | inspect server logs and input shapes; reproduce with a focused fixture |
| `NOT_FOUND` on simulate/close | session is absent or was closed | start a valid session before simulating |

A request just after handover must exercise CATK even if the logged trajectory
exists. A successful replay before handover does not prove that the post-handover
path, scene map, compiled PyG kernels, or model weights work.
