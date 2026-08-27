# Real Robot Operations

This guide covers safety-gated real Push-T collection, evaluation, sensing, and real-data conversion on a UR5 with RealSense cameras and a SpaceMouse.

## Safety preflight

Before any live command:

1. Confirm the robot IP you intend to target.
2. Confirm the emergency-stop is reachable.
3. Confirm the RealSense cameras are physically connected and visible to the OS.
4. Confirm the SpaceMouse is connected and `spacenavd` is active.
5. Run the bundled prereq checker.

The checker only inspects imports, executables, service status, and optional RTDE socket reachability. It never starts the robot, cameras, or `spacenavd`, and it never writes data.

## Command map

The bundled prereq checker is safe to run from this sub-skill directory. Live demo/evaluation/conversion command shapes apply only when the user is operating in a compatible Diffusion Policy project layout that provides the upstream entrypoints and real-robot dependencies.

### Prereq checker

```console
python scripts/check_real_robot_prereqs.py [--robot-ip <ip>]
```

- Checks the live-control import stack needed for real robot use.
- Checks a RealSense userland executable and the `spacenavd` service.
- If `--robot-ip` is given, probes the RTDE socket on port 30004.
- Use this before demo collection, evaluation, or conversion.

### Demo collection

```console
python <real-demo-entrypoint> -o <demo_dir> --robot_ip <ip> \
  [--vis_camera_idx 0] [--init_joints] [--frequency 10] [--command_latency 0.01]
```

Key runtime controls:
- `C`: start recording
- `S`: stop recording
- `Q`: exit
- `Backspace`: drop the previous episode after confirmation
- SpaceMouse buttons: left enables rotation, right unlocks the Z axis

What the demo writes:
- `replay_buffer.zarr` for aligned robot-state/action data
- `videos/<episode_id>/<camera_idx>.mp4` for recorded camera streams

The demo and eval entry points set RealSense `exposure=120`, `gain=0`, and `white_balance=5900` before live use. If the image looks wrong, adjust camera settings before recording or evaluating new episodes.

### Policy evaluation

```console
python <real-eval-entrypoint> -i <ckpt> -o <eval_dir> --robot_ip <ip> \
  [--match_dataset <dataset_dir>] [--match_episode <episode_id>] \
  [--vis_camera_idx 0] [--init_joints] [--steps_per_inference 6] \
  [--max_duration 60] [--frequency 10] [--command_latency 0.01]
```

Key runtime controls:
- `C`: hand control to the policy
- `S`: stop the current policy episode and return control to the human
- `Q`: exit the human-control loop

Checkpoint assumptions:
- The checkpoint must load with `torch.load(..., pickle_module=dill)` and contain `cfg`.
- The workspace class comes from `cfg._target_`.
- The evaluation path branches on `cfg.name` for diffusion, robomimic, or IBC policies.
- Diffusion checkpoints use EMA weights when `cfg.training.use_ema` is true and set DDIM inference steps to 16.
- Robomimic and IBC branches force single-step action execution and may honor `cfg.task.dataset.delta_action`.
- Real-image rollout uses `cfg.task.shape_meta` to derive camera resolution and observation layout.
- The policy runs on CUDA during evaluation.
- The rollout clips XY target poses to the Push-T workspace bounds.

Observation assumptions:
- RGB observations are converted into model-ready `TCHW` arrays.
- Low-dim pose keys with shape `(2,)` are reduced to XY.
- `robot_eef_pose` and `timestamp` must align with the real-time grid used by the robot control loop.

### Raw-data conversion

```console
python <real-dataset-conversion-entrypoint> -i <raw_dataset_dir> \
  [-o <out.zarr.zip>] [-r 640x480] [-nd <decode_threads>] [-ne <encode_threads>]
```

Conversion assumptions:
- Input must contain `replay_buffer.zarr` and `videos/`.
- The default output is `<input>/<resolution>.zarr.zip` if `-o` is omitted.
- The converter decodes MP4 video, optionally resizes frames, and writes a fused ReplayBuffer.
- `verify_read=True` re-reads encoded images to catch codec problems early.
- Keep CPU oversubscription low with `cv2.setNumThreads(1)` and `threadpoolctl.threadpool_limits(1)` when scripting conversion runs.

### Real Push-T metrics

```console
python <real-pusht-metrics-entrypoint> -r <reference_video.mp4> -i <dataset_dir> \
  [--camera_idx 0] [--n_workers 20]
```

Metric assumptions:
- The last frame of the reference video defines the target mask.
- Per-episode videos are compared against that target mask.
- The script saves `metrics_agg.json` and `metrics_raw.json`.
- Aggregated keys include `max/iou`, `last/iou`, `max/coverage`, and `last/coverage`.

## Runtime API map

### Real robot control

- `RealEnv(output_dir, robot_ip, frequency=10, n_obs_steps=2, obs_image_resolution=(640, 480), max_obs_buffer_size=30, obs_float32=False, max_pos_speed=0.25, max_rot_speed=0.6, tcp_offset=0.13, init_joints=False, record_raw_video=True, enable_multi_cam_vis=True, shm_manager=None)`
- `RealEnv.get_obs()` returns aligned camera frames, robot state, and an aligned `timestamp` grid.
- `RealEnv.exec_actions(actions, timestamps, stages=None)` schedules future robot waypoints only; stale timestamps are dropped.
- `RealEnv.start_episode(start_time=None)`, `end_episode()`, and `drop_episode()` manage episode capture.
- `RTDEInterpolationController` queues pose waypoints through UR RTDE and maintains timestamped robot-state buffers.
- `Spacemouse` reads spnav motion and button events from the daemon-backed device.

### Cameras and shared memory

- `SingleRealsense` manages one camera worker process, capture timestamps, and H.264 recording.
- `MultiRealsense` manages one `SingleRealsense` worker per connected camera and exposes per-camera dicts.
- `SharedMemoryRingBuffer` is the lock-free FILO buffer used for camera and robot streams.
- `SharedMemoryQueue` is the lock-free FIFO buffer used for controller commands.
- `TimestampObsAccumulator` and `TimestampActionAccumulator` align observation and action sequences onto the same real-time grid.

### Observation conversion

- `get_real_obs_dict(env_obs, shape_meta)` turns real env observations into the policy input dictionary.
- `get_real_obs_resolution(shape_meta)` derives the camera resolution expected by a real-image checkpoint.

## Expected healthy signals

- The prereq checker reports all live-control imports as present and `spacenavd` as active.
- `RealEnv.is_ready` becomes true after the context starts.
- Demo collection prints `Ready!`, `Recording!`, and `Stopped.` at the expected times.
- Evaluation prints `Warming up policy inference`, `Started!`, and `Submitted N steps of actions.`.
- Conversion prints `Loading lowdim data`, `Loading image data`, and `Saving to disk`.

## Safe validation steps

- Run `scripts/check_real_robot_prereqs.py --json` from this sub-skill directory to inspect imports, executables, service status, and optional robot reachability without commanding hardware.
- Validate timestamp and pose math with a small local unit fixture before live control; these checks do not require cameras or robots.
- Only perform camera capture checks on a machine with the expected RealSense devices attached and after confirming the run will not overwrite data.
- Only perform live UR control checks after an operator confirms robot IP, freedrive/teach-pendant state, emergency stop access, workspace clearance, and payload/tool state.
