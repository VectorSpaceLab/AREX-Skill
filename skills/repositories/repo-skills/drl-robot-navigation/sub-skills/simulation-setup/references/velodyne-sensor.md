# Velodyne sensor readiness

## Distilled configuration

The active robot xacro includes `velodyne_description/urdf/VLP-16.urdf.xacro` with a
`VLP-16` macro mounted to `base_link` and named `velodyne`. In this repository's call,
the material parameters are:

| Parameter | Active value | Diagnostic meaning |
|---|---:|---|
| `topic` | `/velodyne_points` | The navigation subscriber expects this absolute name |
| `hz` | `10` | A live cloud should update around this rate when simulation keeps up |
| `samples` | `360` | Reduced from the vendor macro's 1875 default |
| vertical lasers | `16` | VLP-16 vertical count |
| `gpu` | `false` | Loads the CPU ray sensor and `libgazebo_ros_velodyne_laser.so` |
| horizontal angles | `-1.57` to `1.57` | The active scan covers the forward half-plane |
| `min_range` | `0.1` m | The repository overrides the macro's 0.9 m default |
| `max_range` | `130.0` m | Macro default; effective ray bound is plugin/sensor intersection |
| mount origin | `0.125 0 0.25` | Relative to `base_link` |

The vendor macro's CPU and GPU branches use different shared-library names. GPU mode
uses `libgazebo_ros_velodyne_gpu_laser.so`; it is not the active baseline and the vendored
README warns that the Gazebo version shipped with ROS can give incorrect GPU ranges.
Prefer CPU mode when diagnosing the documented baseline unless a user has explicitly
prepared and verified a compatible modern Gazebo build.

The plugin publishes `sensor_msgs/PointCloud2` with `x`, `y`, `z`, `intensity`, `ring`,
and `time` fields. The plugin subscribes to the underlying Gazebo sensor only when the
ROS PointCloud2 publisher has subscribers. An apparently idle sensor can therefore be
normal until the navigation node or a diagnostic subscriber is present.

## Diagnostic order

After a deliberate, bounded simulator startup and after sourcing both ROS and workspace
setups, check from least invasive to most specific:

```bash
rospack find velodyne_description
rospack find velodyne_gazebo_plugins
rostopic list | grep -E 'velodyne|r1/(odom|cmd_vel)'
rostopic type /velodyne_points
rostopic info /velodyne_points
rostopic hz /velodyne_points
```

Stop rate monitoring deliberately; it is not a background or automatic skill script. The
expected type is `sensor_msgs/PointCloud2`. If the topic is absent, inspect the xacro,
spawn, and Gazebo plugin load logs in that order. If it exists but has no messages, check
subscriber count (on-demand activation), simulation clock/progress, and plugin library
loading. If messages exist but the navigation process reports no usable data, hand the
message fields, frame, z filtering, and angular binning to the navigation-environment
skill rather than changing the simulator topic.

A single sample can be inspected with a bounded command such as:

```bash
rostopic echo -n 1 /velodyne_points
```

Look for a non-empty `fields` list including `x`, `y`, and `z`, a plausible frame such as
`velodyne`, and a progressing header stamp. Do not infer scan quality solely from RViz:
RViz can be unavailable in a headless run while the PointCloud2 path is healthy.

## Common sensor faults

- **`velodyne_description` not found:** ROS setup or workspace setup is missing, or the
  vendored package did not enter the catkin build. Fix package discovery before xacro.
- **Plugin `.so` not found:** `velodyne_gazebo_plugins` was not built, the runtime setup is
  stale, or the CPU/GPU branch does not match the available plugin. Check build output and
  Gazebo's first load error; do not install an unrelated laser plugin as a substitute.
- **Xacro expands but robot has no sensor:** verify that the active robot path is
  `pioneer3dx.gazebo.launch` -> `pioneer3dx.xacro` and that the VLP-16 include was not
  replaced by the commented 2-D/GPU alternatives.
- **Cloud topic differs:** the macro's topic is absolute. A namespace or external remap
  can change the resolved name; either restore the documented contract or explicitly
  update the consumer as a coordinated change.
- **Slow or crashing Gazebo:** the vendor notes that large point clouds can prevent 10 Hz
  and that full-resolution HDL-32E can crash. The active VLP-16 already uses 360 samples;
  lower rate or samples only as an explicit performance experiment and record the changed
  sensor contract.
- **GPU range anomalies:** the vendor warns about default ROS Gazebo GPU ranges. Return to
  CPU mode for baseline diagnosis before treating the result as a navigation defect.

The source environment did not contain ROS message modules or Gazebo, so none of these
live checks has been natively verified here.
