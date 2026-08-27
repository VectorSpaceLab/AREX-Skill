---
name: trajectory-data
description: "Routes evo_traj workflows, trajectory file formats, converters,
  synchronization, alignment, export, and bag/MCAP loading."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# trajectory-data

Use this sub-skill for trajectory files, conversion helpers, synchronization, export, and the `evo_traj` CLI.

## Route here when the user asks for
- `evo_traj` or trajectory inspection / export
- TUM, KITTI, EuRoC, ROS bag, ROS2 bag, or MCAP trajectories
- `PosePath3D`, `PoseTrajectory3D`, `TrajectoryBundle`, or `load_transform`
- timestamp association, `--ref`, `--sync`, `--merge`, `--downsample`, `--motion_filter`
- converting KITTI pose/timestamp pairs to TUM or scaling TUM timestamps
- duplicate timestamp checks or trajectory-file validation failures

## Do not route here when the task is mainly about
- APE/RPE metric math or result zip creation
- saved-result comparison, tables, or pandas exports
- package settings, logs, or IPython shell setup
- notebook plotting or custom Python embedding

## Start with
1. [references/data-formats.md](references/data-formats.md)
2. [references/cli-reference.md](references/cli-reference.md)
3. [references/workflows.md](references/workflows.md)
4. [references/troubleshooting.md](references/troubleshooting.md)
5. [scripts/trajectory_io_smoke.py](scripts/trajectory_io_smoke.py)

## Rules of thumb
- TUM rows are timestamp + xyz + quaternion; KITTI rows are the first 3 rows of a 4x4 pose matrix; EuRoC CSV timestamps are in nanoseconds and become seconds.
- `PoseTrajectory3D` requires timestamps and they must be ascending and unique.
- `bag2` and `mcap` are the same route in evo; bag-based routes require topics or `--all_topics`.
- `--sync` and `--ref` matter for timestamped workflows; `motion_filter` on path-only data is invalid in metrics workflows.
- `load_transform` accepts JSON, `.npy`, or text 4x4 matrices and rejects anything that is not a valid SE(3) or Sim(3) matrix.
- The safe conversion helpers in this sub-skill write to an explicit output path instead of silently mutating source files in place.
