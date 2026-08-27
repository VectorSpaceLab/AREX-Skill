# Troubleshooting

This sub-skill covers safety-gated real robot collection and evaluation. When a run fails, identify whether the blocker is manual safety confirmation, RealSense, SpaceMouse, RTDE, timing, or data conversion.

## Safety gate blocked

**Symptoms**
- The prereq checker reports that `--robot-ip` was not supplied, or the workflow is stopped before live motion.
- The run is stopped because the emergency-stop, camera connection, or SpaceMouse presence was not manually confirmed.

**Likely cause**
- The real robot session has not been safety-cleared yet.

**What to check**
- Robot IP is known and belongs to the intended UR5.
- Emergency-stop is reachable before any live motion.
- RealSense cameras are physically connected and visible.
- SpaceMouse is connected and `spacenavd` is active.

**What to do**
- Do not start demo or evaluation until the manual safety checks are complete.
- Use the prereq checker only for software/service/socket inspection; it cannot confirm the emergency-stop or USB cabling.

## RealSense / librealsense missing

**Symptoms**
- `ModuleNotFoundError: pyrealsense2`
- `SingleRealsense.get_connected_devices_serial()` returns no usable D400 cameras
- `realsense-viewer` cannot see the camera
- Camera workers never become ready

**Likely cause**
- The RealSense Python bindings or librealsense userland stack is missing.
- The cameras are not connected, not recognized as D400 devices, or blocked by permissions/cabling.

**What to check**
- `pyrealsense2` imports cleanly.
- `realsense-viewer` is installed and can see the cameras.
- The cameras are D400-series devices.
- USB cables, hubs, and permissions are correct.

**What to do**
- Fix the RealSense stack before attempting `demo_real_robot.py` or `eval_real_robot.py`.
- If camera enumeration is empty, treat it as a hardware issue, not a dataset issue.

## SpaceMouse / spnav / spacenavd issues

**Symptoms**
- `ModuleNotFoundError: spnav`
- Motion events stay zero or button states never change
- The robot does not react to teleop input

**Likely cause**
- The `spnav` Python package is missing.
- `spacenavd` is inactive.
- The SpaceMouse is not visible to the OS or lacks permissions.

**What to check**
- `spnav` imports cleanly.
- `systemctl status spacenavd` reports the daemon as active.
- The device is connected and recognized by the host.

**What to do**
- Fix the daemon and device state before trying to debug robot motion.
- Do not auto-start `spacenavd` from the prereq checker; that script only inspects state.

## UR RTDE / network issues

**Symptoms**
- `ModuleNotFoundError: rtde_control` or `rtde_receive`
- `RTDEControlInterface` or `RTDEReceiveInterface` cannot connect
- `RealEnv.is_ready` never becomes true
- `schedule_waypoint` appears to drop commands

**Likely cause**
- The RTDE Python packages are missing.
- The robot IP is wrong.
- The robot controller is not reachable on the RTDE socket.
- A firewall or network policy is blocking the connection.

**What to check**
- The prereq checker can reach the robot IP when `--robot-ip` is supplied.
- The robot is on the expected network and accepting RTDE commands.
- You are targeting the correct host and not a stale address.

**What to do**
- Fix connectivity before debugging policy logic.
- If the connection works but motion is unstable, verify future-dated action timestamps and the controller frequency.

## Timestamp / control-frequency / latency issues

**Symptoms**
- `Obs latency ...` is large in the evaluation loop.
- `Over budget` appears repeatedly.
- Shared-memory buffers raise `Put executed too fast` or `Get time out`.
- `RealEnv.exec_actions` silently drops actions.
- Robot motion jitters or lags behind the policy output.

**Likely cause**
- `frequency` is too high for the camera/robot loop.
- `command_latency` is too small or the policy inference is too slow.
- `steps_per_inference` is too long for the available control budget.
- Action timestamps are not strictly in the future relative to `time.time()`.
- The shared-memory buffer budget is too small for the current frame size or FPS.

**What to check**
- Demo uses the same control period that the robot loop can actually sustain.
- Evaluation timestamps remain ahead of `receive_time`.
- The policy output is the expected 2D XY action for real Push-T eval, and `RealEnv.exec_actions` receives 6D target poses.
- CPU oversubscription is not inflating conversion or recording latency.

**What to do**
- Lower `frequency` or `steps_per_inference` if the loop cannot keep up.
- Increase `command_latency` only enough to leave room for inference.
- Keep `cv2.setNumThreads(1)` and `threadpoolctl.threadpool_limits(1)` around heavy video conversion.
- Do not bypass the action-timestamp check; future-dated commands are required for safe scheduling.

## Dataset conversion failures

**Symptoms**
- `assert in_zarr_path.is_dir()` or `assert in_video_dir.is_dir()` fails.
- The converter reports `Missing camera X` or `Unexpected camera X`.
- `Failed to encode image!` appears during conversion.
- The output dataset cannot be reopened after conversion.
- Metrics generation does not produce `metrics_agg.json` or `metrics_raw.json`.

**Likely cause**
- The raw capture layout is wrong.
- Episode folders or camera indices do not match the expected set.
- The codec stack is incomplete.
- The resolution requested by conversion does not match the source data assumptions.

**What to check**
- Raw recordings contain `replay_buffer.zarr` and a `videos/` tree.
- Every episode directory has the expected camera MP4 files.
- `av`, `imagecodecs`, `zarr`, and `numcodecs` are available.
- The requested output resolution matches the intended real-image task.

**What to do**
- Fix the raw data layout before rerunning conversion.
- Reduce decode/encode parallelism if the host is overloaded.
- Re-run conversion with read verification enabled.

## Observation-shape mismatch

**Symptoms**
- The policy receives the wrong number of camera keys.
- `get_real_obs_dict` returns unexpected shapes.
- Evaluation fails when a checkpoint expects a different camera layout.

**Likely cause**
- The checkpoint `shape_meta` does not match the real camera names or resolution.
- The task expects RGB keys that the environment does not provide.

**What to check**
- Camera names in the real environment match the checkpoint metadata.
- RGB shapes are consistent across cameras.
- Low-dim pose keys that should be XY really have shape `(2,)` in the task metadata.

**What to do**
- Align the task metadata with the camera layout before retrying evaluation.
- If the layout changed, regenerate the checkpoint or use the correct real-image task spec.
