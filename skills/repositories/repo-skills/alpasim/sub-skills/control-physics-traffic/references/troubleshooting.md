# Control, physics, and traffic troubleshooting

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named alpasim_controller` or `alpasim_physics` | The relevant workspace package is not installed in the active environment | Use the repository's supported package workflow or container, then rerun the read-only diagnostic; do not copy source paths into runtime code |
| `No module named do_mpc` / `casadi` | Nonlinear MPC extra is absent | Install the package variant that supplies those dependencies, or choose linear MPC for a CPU QP check |
| CATK servicer import fails with `No module named torch_cluster` | Required compiled PyG extension is absent or mismatched | Install the extension built for the active PyTorch/CUDA pair in the deployment environment; do not claim CATK works on CPU |
| `warp` imports but update fails | CUDA runtime/device or kernel compatibility is incomplete | Verify the supported CUDA/container pairing and run the tiny mesh check; a Python import alone is insufficient |
| `polyscope` import fails with visualization enabled | Optional visualization dependency is absent | Disable visualization for headless operation or install the optional visualization extra |

Run `python scripts/check_backend.py` after any dependency change. The script
has no installer or download behavior.

## Optional backends and data

- Controller linear tests can run with NumPy/SciPy/OSQP. Nonlinear tests need
  do_mpc/CasADi and may take longer on first solver setup.
- Physics needs a valid mesh-bearing scene artifact and CUDA-capable Warp for
  `update_pose`. Missing mesh data, empty artifact discovery, or an AABB with
  invalid dimensions is not fixed by changing MPC settings.
- CATK needs a recursive `.usdz` scene directory, model `config_path`,
  `ckpt_path`, `token_pkl_dir`, CUDA, and matching compiled PyG extensions.
  These are deployment inputs; this skill never downloads them.
- If map filtering yields no geometry, inspect the scene adapter's map element
  names, `filter_distance_th`, and the requested scene. Do not convert a
  `FAILED_PRECONDITION` into a replay or frozen-agent result.

## Config and CLI misuse

| Error or observation | Check |
|---|---|
| Physics server exits before listening | `--artifact-glob` is required; verify it discovers `.usdz` artifacts with mesh data |
| CATK server rejects `catk.loader.usdz_folder` | It must be an existing directory containing `.usdz` files recursively |
| CATK Hydra config has unresolved `???` values | Supply the model and loader paths in the resolved config or explicit overrides |
| Controller uses unexpected defaults | A controller YAML is only loaded when `--config` is supplied; otherwise `ControllerConfig` defaults are used |
| `future_time_us` is not later than current time | Advance the request timestamp; do not use zero-duration controller steps |
| timestamp mismatch | Preserve the exact returned timestamp and send requests in session order |
| empty planned trajectory | Supply time-stamped poses in the current rig frame |
| unknown controller session | Call `start_session` once before running and close it once after use |

The controller server's public flags are `--host`, `--port`, `--log_dir`,
`--log-level`, and optional `--config`. The physics server's flags are listed
in [physics and traffic](physics-and-traffic.md). CATK uses Hydra's
`--config-path`, `--config-name`, and `key=value` overrides.

## CATK handover and status failures

A replay response before or at `handover_time_us` proves only logged-history
resampling. For a request after handover:

1. Confirm the session contains a non-empty `EGO` trajectory and the query's
   ego update covers the requested future.
2. Confirm the query requires no more than `prediction_steps` future steps.
3. Confirm the scene map survives the configured filter radius.
4. Confirm CATK imports, model files, CUDA, and compiled PyG extensions.
5. Read the gRPC status rather than inspecting only an empty response.

Interpret statuses as follows:

- `INVALID_ARGUMENT`: malformed start request, insufficient ego trajectory, or
  query beyond the configured prediction horizon.
- `FAILED_PRECONDITION`: CATK could not produce a required post-handover
  prediction, commonly because no usable map geometry was available.
- `INTERNAL`: an unexpected exception in the service/model/data path.
- `NOT_FOUND`: unknown scene or session.

There is no static fallback after handover. A static agent policy may be a CATK
configuration choice for eligible agents, but it is not permission to return a
fake world-model result when the predictor itself is unavailable.

## Workflow failures and recovery

- **Solver returns `solved_inaccurate` or `failed:`:** capture
  `ControllerOutput.status` and `solve_time_ms`, check reference timestamps,
  state finiteness, horizon, gains, and bounds. Reduce the problem only as a
  diagnostic; do not silently replace the selected implementation.
- **Controller lateral sign looks wrong:** verify whether the reference is in
  the current rig frame and whether the state lateral component is CG-frame or
  rig-frame. Check the positive-offset straight-trajectory fixture before
  changing gains.
- **Physics reports high translation/rotation repeatedly:** inspect pose units,
  AABB dimensions, scene mesh alignment, and whether upstream propagation is
  producing a discontinuity. Preserve the status and investigate; do not retry
  forever.
- **Traffic requests race:** requests for one session are serialized. If a
  client reuses a session UUID concurrently, preserve order or use separate
  sessions. Different sessions may batch together, so model outputs must be
  split by request.
- **Prediction horizon exceeded:** shorten the query interval or configure a
  horizon that covers the requested number of service time steps. Do not assume
  the model will extrapolate.
- **No response after close:** close removes the session and its lock; a queued
  request can become `NOT_FOUND`. Treat that as lifecycle behavior and avoid
  reusing the UUID.

If the failure is in protobuf shape/stub generation, route it to the generic
gRPC/developer workflow. If it is in deployment composition, route it to the
wizard workflow. Keep this sub-skill focused on component contracts and
backend/data diagnosis.
