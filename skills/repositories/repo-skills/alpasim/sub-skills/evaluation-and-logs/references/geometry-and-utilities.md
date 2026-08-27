# Geometry and shared utilities

## Coordinate and quaternion conventions

The evaluation path stores actor trajectories in the AABB-center frame. ASL
metadata provides the active rig-to-AABB-center transform and the recorded EGO
ground-truth trajectory in the rig frame. The accumulator transforms the ground
truth into the AABB-center frame before building evaluation input. Preserve
that transform when joining poses, routes, map elements, and vehicle boxes.

`alpasim_utils.geometry` uses Rust-backed `Pose`, `Polyline`, `Trajectory`, and
`DynamicTrajectory` types. Internal quaternion arrays follow the SciPy order
`(x, y, z, w)`. gRPC messages expose named fields and conversion helpers write
or read them as `(w, x, y, z)` in the protobuf representation. A yaw-only gRPC
quaternion has components `(w, x, y, z) = (cos(yaw/2), 0, 0, sin(yaw/2))`.
Never compare raw quaternion arrays without normalizing the representation.

## Useful APIs

```python
from alpasim_utils.geometry import (
    Pose, Polyline, Trajectory,
    pose_from_grpc, pose_to_grpc,
    trajectory_from_grpc, trajectory_to_grpc,
)

pose = pose_from_grpc(grpc_pose)
trajectory = trajectory_from_grpc(grpc_trajectory)
positions = trajectory.positions
poses = trajectory.interpolate_poses_list(target_timestamps)
```

`Trajectory` is timestamped in microseconds and supports interpolation,
clipping, transforms, append, and native finite-difference derivatives. The
Python helpers `trajectory_velocities_cubic`,
`trajectory_accelerations_cubic`, and `trajectory_yaw_rates_cubic` require
`csaps`; they return derivatives in seconds-based units (m/s, m/s², and
rad/s). Cubic derivative helpers fail clearly when `csaps` is unavailable.

`Polyline` conversion is three-dimensional. Converting a non-3-D polyline to a
route raises `ValueError`; an empty gRPC route becomes an empty 3-D polyline.
Dynamic-state helpers map four 3-vectors—linear and angular velocity, then
linear and angular acceleration—to an `(N, 12)` float64 array.

## Timestamp discipline

- Use `uint64` microsecond timestamps for trajectory construction.
- Sort timestamped protobuf poses before constructing a trajectory when input
  order is not guaranteed.
- Interpolation is inclusive at the endpoints and rejects requests outside the
  available range; an empty trajectory cannot be interpolated.
- A single-pose trajectory accepts only its exact timestamp.
- For derived rates, use the actual timestamp spacing, not an assumed control
  rate. Unwrap yaw before differentiating across ±π.
- Match camera `frame_end_us`, driver request/return times, actor-pose times,
  and metric times explicitly. Do not align arrays just because their lengths
  match.

## Map and artifact boundary

Evaluation passes a dictionary of scene `Artifact` objects keyed by scene id.
An artifact is a USDZ archive and lazily exposes metadata, rig trajectories,
traffic objects, mesh data, and a vector map. Map loading may use packaged map
parquets or XODR and may require `trajdata`; it can take seconds and can fail
independently of ASL parsing.

`ShapelyMap` converts a vector map into renderable line strings and points for
BEV videos. It can filter road-lane centers/edges, road edges, stop/other
lines, crosswalks, road areas/islands, walkways, traffic signs, routes,
trajectories, agents, predictions, and IDs. Geometry queries are two-
dimensional unless a metric explicitly includes z.

If no map is available, the evaluation input can still support collision,
ground-truth, and some plan metrics, but offroad detection and meaningful BEV
map rendering are unavailable. Report this distinction.

## Native boundary checks

Before using geometry or gRPC packing in a new environment, verify imports for
`alpasim_grpc.v0.common_pb2`, `alpasim_grpc.v0.logging_pb2`,
`alpasim_utils.geometry`, and `utils_rs`. The native boundary tests exercise
pose/trajectory packing, sorted timestamps, protobuf serialization, and shape
mismatch rejection. Missing generated stubs or an unbuilt `utils_rs` extension
is an environment gap; do not replace it with hand-written serialization in a
result claim.
