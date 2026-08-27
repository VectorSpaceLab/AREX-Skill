---
name: control-physics-traffic
description: "Use when an AlpaSim task concerns vehicle state, controller or MPC
  selection, ground-mesh physics, CATK traffic sessions, handover behavior, or
  backend/data requirements for these services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Control, physics, and traffic

Use this sub-skill for the three simulation components that close the motion
loop:

- **Controller:** planar dynamic-bicycle vehicle state, linear/nonlinear MPC,
  trajectory tracking, and the controller gRPC session.
- **Physics:** Warp ground-mesh intersection that corrects vehicle/object poses;
  it is not a collision engine or a replacement for vehicle dynamics.
- **Traffic:** the CATK-backed traffic gRPC service, including session history,
  logged replay, handover, prediction batching, and failure statuses.

Do not use this sub-skill to compose a wizard deployment, choose a driver policy,
or edit protobufs. Route those to `simulation-wizard`, `drivers-and-plugins`, or
`grpc-and-developer-tools`, respectively. Use `runtime-services` for the
runtime's event loop and service orchestration, and `evaluation-and-logs` for
post-run logs and metrics.

## Start with a capability and backend check

1. Identify the service being changed or queried. Record the simulation time
   unit, coordinate frame, scene identifier, and whether the request is replay
   or closed-loop inference.
2. Run the bundled, read-only probe before debugging imports or optional
   backends:

   Read [backend compatibility](references/backend-compatibility.md), then run
   the bundled [backend checker](scripts/check_backend.py) before debugging
   imports or optional backends:

   ```bash
   python scripts/check_backend.py
   python scripts/check_backend.py --usdz-folder /data/scenes \
       --model-config /models/catk/config.yaml \
       --checkpoint /models/catk/latest.ckpt \
       --token-dir /models/tokens
   ```

   The second form only inspects supplied paths; it never downloads or changes
   them. Treat warnings about CUDA, PyG extensions, USDZ, or model assets as
   capability limits, not as proof of a working CATK service.
3. For a controller-only CPU smoke test, use the package's focused tests or
   instantiate `LinearMPC` with an 8-element state and a time-stamped
   `Trajectory`. For a nonlinear smoke test, ensure `do_mpc` and CasADi are
   importable before the first `compute_control` call.
4. For physics, use a small valid PLY ground mesh and positive AABB dimensions.
   `PhysicsBackend` constructs Warp mesh data and launches CUDA kernels during
   `update_pose`; a successful Python import is not a physics execution test.
5. For CATK, verify the scene directory contains `.usdz` files and that the
   model config, checkpoint, token directory, CUDA device, and matching PyG
   compiled extensions are all available. Never substitute a static traffic
   trajectory for a failed post-handover prediction.

See [backend compatibility](references/backend-compatibility.md) before
installing optional packages and [troubleshooting](references/troubleshooting.md)
when a check fails.

## Choose and use the controller

1. Represent the current vehicle state in the documented order
   `[x, y, yaw, vx_cg, vy_cg, yaw_rate, steering, accel]`. The position and yaw
   are for the rig origin in the temporary inertial frame; `vx_cg` and `vy_cg`
   are body-frame CG velocities. Do not silently treat rig-frame lateral speed
   as CG lateral speed.
2. Use **linear MPC** (`mpc_implementation: linear`) as the normal fast choice.
   It linearizes the bicycle model about the current state and solves an OSQP
   QP. Use **nonlinear MPC** for aggressive maneuvers or tight turns when the
   slower do_mpc/CasADi/IPOPT solve is acceptable. This is a modeling trade-off,
   not a claim that nonlinear is always more stable.
3. Keep `n_horizon` and `dt_mpc` consistent with the trajectory sampling. The
   defaults are 20 steps and 0.1 seconds. Tracking cost begins at
   `gains.idx_start_penalty` (default 10), while actuator regularization applies
   to command changes.
4. In a service session, call `start_session` before the first run, provide a
   non-empty planned trajectory, advance to a strictly later `future_time_us`,
   and close the session exactly once. The first run lazily constructs the
   system and creates a CSV controller log.
5. Set `coerce_dynamic_state` when current ground-truth dynamic state should
   replace the model's velocity, yaw rate, and acceleration before solving. The
   system converts rig-frame velocity to CG-frame velocity and preserves the
   integrated pose origin.

The exact dataclasses, solver bounds, frame conversion, service invariants, and
standalone server flags are in [controller API](references/controller-api.md).

## Apply ground constraints

1. Give the physics service a scene artifact glob ending in `.usdz` and select
   a scene whose ground mesh is available. The command shape is:

   ```bash
   physics_server --artifact-glob '/data/artifacts/*.usdz' \
       --host 0.0.0.0 --port 8080 --cache-size 16
   ```

   `--use-ground-mesh`, `--visualize`, and the cache size affect artifact/backend
   loading; visualization is optional and may require extra packages.
2. For every pose, physics samples the bottom of the AABB, casts ±Z rays into
   the Warp mesh, fits a plane, and applies bounded translation/rotation
   corrections. It deliberately preserves predicted X/Y after correction and
   returns a status for each pose.
3. Handle `SUCCESSFUL_UPDATE`, `INSUFFICIENT_POINTS_FITPLANE`, `HIGH_TRANSLATION`,
   and `HIGH_ROTATION` as distinct observations. Repeated high corrections are
   usually a scene, AABB, timestamp, or upstream pose problem; do not hide them
   by retrying indefinitely.

Physics does not model collisions, full vehicle dynamics, or arbitrary lateral
motion. See [physics and traffic](references/physics-and-traffic.md).

## Run a CATK traffic session

1. Start the service only after its Hydra config resolves. A documented local
   shape is:

   ```bash
   catk_trafficsim_server \
       --config-path=/path/to/config-dir \
       --config-name=server.yaml \
       server.port=6200 \
       catk.loader.usdz_folder=/data/scenes
   ```

   The model paths and timing settings belong in the resolved config. The
   wizard normally writes this config for a container deployment; do not make a
   second deployment recipe here.
2. `start_session` requires a session UUID, scene ID, at least one logged object
   trajectory including `EGO`, and a positive `handover_time_us`. The service
   builds a fixed history window (`num_history_steps`, default 16) sampled at
   `time_step` (default 0.1 s).
3. At or before handover, `simulate` resamples logged trajectories and returns
   replay. After handover, it resamples the latest history, fills the ego future
   from the request/update, runs CATK, and merges predicted agent trajectories.
   Requests are serialized per session but different sessions may reach the
   inference batcher concurrently.
4. Respect the configured `prediction_steps` (default 5). A request beyond the
   fixed prediction horizon is `INVALID_ARGUMENT`; missing usable map/model
   predictions after handover are `FAILED_PRECONDITION`. An unexpected model
   exception is `INTERNAL`. These statuses are actionable distinctions.
5. Close sessions and retry only after fixing the reported scene, trajectory,
   horizon, map, model, or backend issue. There is no valid CPU/static fallback
   for CATK's required post-handover prediction path.

Use [physics and traffic](references/physics-and-traffic.md) for the request
sequence, config fields, batching semantics, and status mapping.

## Verification and handoff

- Run parser/help checks for the bundled script and server commands without
  starting a daemon or downloading assets.
- Run controller system, linear-MPC, nonlinear-MPC, physics-utils, and traffic
  service/batching tests according to their backend markers. Keep CATK
  integration tests skipped unless CUDA, matching PyG extensions, USDZ scenes,
  and model weights are all present.
- Test the difficult cases in the review artifact: aggressive-turn controller
  selection and a CATK `FAILED_PRECONDITION` after handover. The expected answer
  must name the validation signal and must not invent a fallback.
- If a service contract or protobuf message is the issue, hand off rather than
  duplicating generic message definitions. Record unresolved backend/data gaps
  explicitly in the verification report.
