# Trajectory and sensor contracts

## Sensor history

OpenScene exposes eight camera modalities (`cam_f0`, `cam_l0`, `cam_l1`,
`cam_l2`, `cam_r0`, `cam_r1`, `cam_r2`, `cam_b0`) and one merged point-cloud
modality (`lidar_pc`). The released observation history is 2 seconds at 2 Hz,
represented by four history indices. In the normal four-frame input, index `3`
is the current frame and `[-1]` selects the same item.

`SensorConfig` stores a boolean or list of history indices for each modality:

- `False` means do not load that modality;
- `True` means load every available history frame;
- `[3]` means load only the current frame;
- an explicit list such as `[0, 2, 3]` means load those history positions.

`get_sensors_at_iteration(i)` converts this declaration into sensor names for
one history iteration. Use the builders rather than hand-writing all nine
fields:

```python
SensorConfig.build_no_sensors()             # all nine fields False
SensorConfig.build_all_sensors()            # all nine fields True
SensorConfig.build_all_sensors(include=[3]) # current frame only
```

Sensor loading affects disk access, CPU time, and memory. A blind agent should
return `build_no_sensors()`. A temporal agent should request only the history
it actually consumes. Never request a sensor and then assume it is non-empty:
inspect the loaded `Camera.image` or `Lidar.lidar_pc` before preprocessing.

## TransFuser and latent TransFuser

The standard `TransfuserAgent.get_sensor_config()` requests only
`cam_l0`, `cam_f0`, and `cam_r0` at history index `[3]`; all other cameras are
false, and `lidar_pc=[3]`. Its feature builder reads the latest three camera
images, crops the side views, stitches the three front-facing views, and
resizes the result to the model's configured image resolution. Its LiDAR path
turns the latest merged point cloud into a clipped 2-D histogram in the
configured BEV bounds.

With `TransfuserConfig.latent=True`, the agent deliberately changes two linked
contracts:

1. `get_sensor_config()` sets `lidar_pc=False`, so no LiDAR blob is loaded.
2. `TransfuserFeatureBuilder` omits the `"lidar_feature"` key, and the backbone
   supplies a learned `lidar_latent` tensor in its place.

Do not enable `latent=True` while retaining code that unconditionally requests
or indexes LiDAR. Conversely, do not remove `lidar_feature` from a normal
(non-latent) run. A latent checkpoint is a model/config family choice, not a
switch that makes a LiDAR-trained checkpoint interchangeable.

The learned model also predicts auxiliary BEV semantic and agent-detection
outputs. These outputs must remain aligned with the target-builder keys and
with the loss configuration even if only the trajectory is used at evaluation.

## Trajectory representation

`Trajectory` is a dataclass containing:

- `poses`: a floating NumPy array in the current ego rear-axle local frame;
- `trajectory_sampling`: a `TrajectorySampling` object describing the sample
  count and interval.

Each pose is exactly `(x, y, heading)` in BEV/local coordinates. The array is
rank two with shape `(sampling.num_poses, 3)`. The dataclass rejects a wrong
rank, wrong row count, or a last dimension other than three. Future poses are
not global coordinates, and they do not include an extra current pose.

The built-in default requests a **4-second horizon at 0.5-second intervals**.
That is the agent's output contract and is intentionally not the same sampling
as the PDM proposal, which is configured for a **4-second horizon at 0.1-second
intervals** (40 poses in the standard evaluation config). The evaluator can
interpolate an agent's declared sampling, but it cannot repair a wrong pose
count, wrong coordinate frame, or a sampling object that lies about the array.
Always derive the output reshape and target-builder frame count from the same
`TrajectorySampling` instance.

A safe construction is:

```python
sampling = TrajectorySampling(time_horizon=4, interval_length=0.5)
poses = np.zeros((sampling.num_poses, 3), dtype=np.float32)
return Trajectory(poses, sampling)
```

If a custom interval is used, construct a new sampling object and return the
matching number of rows. Do not hard-code `40` in an agent that is configured
for the 0.5-second default, and do not use a 10 Hz array while leaving the
sampling object at 0.5 seconds.

## Submission boundary

Submission and test-server input exposes sensor data plus ego status, not
annotated maps, future poses, tracks, or occupancy. Therefore submission agents
must have `requires_scene=False` and must compute from `AgentInput`. A
privileged agent that reads `Scene` can be useful for a diagnostic upper bound,
but submission creation rejects it. Keep ground-truth target construction in
training only and do not accidentally reuse it in inference.
