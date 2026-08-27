# Geometry API reference

This reference distills the box/point geometry conventions used by the runtime sub-skill. It is limited to synthetic checks and does not require model execution.

## Core convention map

| Object | Default origin | Yaw axis | Main BEV axes | Key notes |
| --- | --- | --- | --- | --- |
| `BaseInstance3DBoxes` | `(0.5, 0.5, 0)` | n/a | bottom-center contract | `center` aliases `bottom_center`; `gravity_center` adds half the box height on the gravity axis. |
| `LiDARInstance3DBoxes` | `(0.5, 0.5, 0)` | z (`axis=2`) | `x/y` | Front is `+x`, left is `+y`, up is `+z`. Height is `dz`. |
| `CameraInstance3DBoxes` | `(0.5, 1.0, 0.5)` | y (`axis=1`) | `x/z` | Right is `+x`, down is `+y`, front is `+z`. Height is `dy`. `local_yaw` is the KITTI-style alpha angle. |
| `DepthInstance3DBoxes` | `(0.5, 0.5, 0)` | z (`axis=2`) | `x/y` | Right is `+x`, front is `+y`, up is `+z`. Height is `dz`. |
| `LiDARPoints` | n/a | z (`rotation_axis=2`) | `x/y` | Horizontal flip negates `y`; vertical flip negates `x`. |
| `CameraPoints` | n/a | y (`rotation_axis=1`) | `x/z` | Horizontal flip negates `x`; vertical flip negates `z`. |
| `DepthPoints` | n/a | z (`rotation_axis=2`) | `x/y` | Horizontal flip negates `x`; vertical flip negates `y`. |

## Box-origin and center rules

- The box tensor is always stored as `[x, y, z, dx, dy, dz, yaw, ...]`.
- `BaseInstance3DBoxes.center` returns the bottom center, not the gravity center.
- `gravity_center` is the better choice when comparing boxes across modes or when plotting scene geometry.
- Passing a non-default `origin` to a constructor shifts the stored center to the class default origin.
- `CameraInstance3DBoxes` defaults to a bottom-center equivalent of `(0.5, 1.0, 0.5)` because camera `y` points downward.
- `with_yaw=False` produces axis-aligned boxes with a fake zero yaw while preserving the rest of the tensor.

## Yaw rules to remember

- All supported box classes use right-handed yaw conventions.
- LiDAR and Depth boxes rotate around the z axis.
- Camera boxes rotate around the y axis.
- A camera box with yaw `0` points along `+x` and the positive yaw direction moves toward `+z`.
- A LiDAR or Depth box with yaw `0` points along `+x` and positive yaw moves toward `+y`.
- Use `limit_period` when you need to normalize angles before comparing or logging them.
- `CameraInstance3DBoxes.local_yaw` gives the local angle used by monocular workflows.

## Mode conversion helpers

### `Box3DMode.convert(box, src, dst, rt_mat=None, with_yaw=True, correct_yaw=False)`

Use this when you have a box tensor or box object and want a different geometry mode.

Behavior highlights:

- Accepts a list/tuple, `numpy.ndarray`, `torch.Tensor`, or a box object.
- Returns the same container family when possible.
- Preserves extra tensor columns after the first 7 values.
- Uses default axis-remap matrices when `rt_mat` is omitted.
- Accepts 3x3, 3x4, or 4x4 transform matrices; a 3x4/4x4 matrix applies translation through homogeneous coordinates.
- If `correct_yaw=False`, yaw is remapped by the built-in source/destination rule.
- If `correct_yaw=True`, the heading vector is rotated through `rt_mat` and converted back to yaw.

The default matrix-free conversions are:

- LiDAR → Camera: centers map as `[x_cam, y_cam, z_cam] = [-y_lidar, -z_lidar, x_lidar]`, sizes reorder, and yaw changes by `-yaw - π/2`.
- Camera → LiDAR: centers map as `[x_lidar, y_lidar, z_lidar] = [z_cam, -x_cam, -y_cam]`, sizes reorder, and yaw changes by `-yaw - π/2`.
- Camera → Depth: `[x_d, y_d, z_d] = [x_c, z_c, -y_c]`, and yaw flips sign.
- Depth → Camera: `[x_c, y_c, z_c] = [x_d, -z_d, y_d]`, and yaw flips sign.
- LiDAR → Depth: `[x_d, y_d, z_d] = [-y_l, x_l, z_l]`, and yaw shifts by `+π/2`.
- Depth → LiDAR: `[x_l, y_l, z_l] = [y_d, -x_d, z_d]`, and yaw shifts by `-π/2`.

### `Coord3DMode.convert(input, src, dst, rt_mat=None, with_yaw=True, correct_yaw=False, is_point=True)`

Use this when the input may be a point object, a box object, or a raw tensor/list.

Behavior highlights:

- Boxes and points are dispatched to the correct conversion path automatically.
- Point conversions preserve any extra attributes after the first 3 coordinates.
- Box conversions preserve any extra box features after the first 7 values.
- `Coord3DMode.convert_box` is just a thin wrapper over `Box3DMode.convert`.

### Quick conversion patterns

```python
cam_boxes = lidar_boxes.convert_to(Box3DMode.CAM)
cam_points = lidar_points.convert_to(Coord3DMode.CAM)
```

```python
cam_points_3d = points_cam2img(cam_points_xyz, cam2img, with_depth=True)
xyz = points_img2cam(cam_points_2d_depth, cam2img)
```

## Projection helpers

### `points_cam2img(points_3d, proj_mat, with_depth=False)`

- Projects camera-space 3D points to image space.
- Accepts 3x3, 3x4, or 4x4 projection matrices.
- Returns `[u, v]` when `with_depth=False`.
- Returns `[u, v, depth]` when `with_depth=True`.
- The input points must already be in camera coordinates.
- Positive depth is required for a meaningful image projection.

### `points_img2cam(points, cam2img)`

- Inverts a camera projection when the input is `[u, v, depth]`.
- Uses the supplied camera intrinsic matrix after padding it to homogeneous form.
- The natural round-trip is `points_img2cam(points_cam2img(..., with_depth=True), cam2img)`.

### `get_lidar2img(cam2img, lidar2cam)`

- Composes a LiDAR-to-image transform from camera intrinsics and LiDAR-to-camera extrinsics.
- Useful for checking LiDAR box or point projection helpers with synthetic calibration.

### `get_proj_mat_by_coord_type(img_meta, coord_type)`

- Maps `LIDAR` -> `lidar2img`.
- Maps `DEPTH` -> `depth2img`.
- Maps `CAMERA` -> `cam2img`.
- This is the safest way to pick the correct image projection matrix from metadata.

### Legacy helper

`mono_cam_box2vis` is a legacy monocular visualization helper. It exists for compatibility, but it is not the preferred path for new geometry reasoning.

## Sanity checks worth remembering

- LiDAR and Camera conversions should round-trip to the same tensor up to floating-point tolerance and angle wrapping.
- Point conversions should preserve extra point attributes.
- `points_cam2img` followed by `points_img2cam` should recover the original camera-space point when the depth is preserved.
- If a projected box looks wrong, check the source mode first, then the origin, then the yaw convention.
- If the yaw differs by `2π`, normalize before comparing it.
- If the yaw differs by `π`, the box direction may be reversed even when the box footprint is identical.
