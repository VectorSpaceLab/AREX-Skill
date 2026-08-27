# Trajectory data formats

This reference captures the public file layouts and object rules behind `evo_traj`, the trajectory loaders/writers, and the bundled converters.

## TUM trajectory format

- One line per pose.
- Eight whitespace-separated fields:
  `timestamp tx ty tz qx qy qz qw`
- Comments beginning with `#` are ignored.
- `read_tum_trajectory_file()` returns `PoseTrajectory3D`.
- `write_tum_trajectory_file()` writes the same layout back out.

Common failure signals:
- too few or too many columns
- trailing whitespace at the end of a row
- non-numeric values

## KITTI pose format

- One line per pose.
- Twelve whitespace-separated floats.
- Each row is the first three rows of a 4x4 pose matrix flattened left-to-right.
- `read_kitti_poses_file()` returns `PosePath3D`.
- `write_kitti_poses_file()` writes the same flattened pose rows back out.

Common failure signals:
- row count mismatch with a companion timestamp file
- trailing delimiter at the end of a row
- fewer or more than 12 values

## EuRoC MAV CSV

- Ground-truth CSV input uses the EuRoC state ground-truth layout.
- The first column is a nanosecond timestamp that evo converts to seconds.
- The next three columns are position xyz.
- The next four columns are quaternion wxyz in evo's internal ordering.
- `read_euroc_csv_trajectory()` returns `PoseTrajectory3D`.

Common failure signals:
- fewer than 8 columns
- non-numeric rows
- wrong companion file passed to the CLI route

## ROS bag, ROS2 bag, and MCAP

Supported trajectory message types include:
- `geometry_msgs/msg/PoseStamped`
- `geometry_msgs/msg/TransformStamped`
- `geometry_msgs/msg/PoseWithCovarianceStamped`
- `geometry_msgs/msg/PointStamped`
- `nav_msgs/msg/Odometry`
- TF identifiers such as `/tf:map.base_link`

Important rules:
- `evo_traj bag` works on ROS bag files.
- `evo_traj bag2` and `evo_traj mcap` work on ROS2 bags or MCAP.
- Bag-based routes require explicit topics unless `--all_topics` is used.
- `--all_channels` is an alias of `--all_topics` on the ROS2 route.

## Trajectory objects

### `PosePath3D`
- No timestamps.
- Suitable for pose-only data such as KITTI pose files.
- Supports transform, scale, projection, downsample, motion filtering, and splitting.

### `PoseTrajectory3D`
- Adds timestamps to `PosePath3D`.
- Requires ascending unique timestamps.
- Supports time-range cropping, time-gap splitting, speed calculation, and timestamp-aware synchronization.

### `TrajectoryBundle`
- Bundles multiple named trajectories plus an optional reference.
- Supports merge, sync, align, align_origin, apply_time_offset, downsample, motion_filter, and projection.
- Synchronization populates per-trajectory matched reference tracks.

## Transformation files

`load_transform()` accepts:
- `.json` with keys `x`, `y`, `z`, `qx`, `qy`, `qz`, `qw`, and optional `scale`
- `.npy` files containing a 4x4 matrix
- plain text 4x4 matrices saved with `numpy.savetxt`

The resulting matrix must be a valid SE(3) or Sim(3) transform.
