# Geometry API reference

This reference records the observable contracts in the historical `utils.py`.
The functions below are mathematical/data helpers; they do not connect to a
camera or robot. Inputs are shown with NumPy-style shapes. The source performs
little validation, so callers should validate before invoking it.

## `get_pointcloud`

```python
def get_pointcloud(color_img, depth_img, camera_intrinsics):
    # returns cam_pts, rgb_pts
```

Contract:

- `depth_img`: `(H,W)` numeric array. Its values are interpreted as camera Z
  distances in metres by the projection formula; the function does not scale
  integers, reject NaN, or reject zero/negative values.
- `color_img`: `(H,W,3)` array whose first three dimensions correspond to the
  depth image. Source channel order is RGB. A mismatch can fail while slicing
  or while constructing the output; there is no explicit check.
- `camera_intrinsics`: array-like with the usual 3x3 pinhole matrix entries
  `fx = K[0,0]`, `fy = K[1,1]`, `cx = K[0,2]`, `cy = K[1,2]`. The source uses
  those entries and assumes nonzero focal lengths. Distortion is ignored.
- return `cam_pts`: `(H*W,3)`, in row-major pixel order, columns
  `[X_camera,Y_camera,Z_camera]`.
- return `rgb_pts`: `(H*W,3)`, row-matched source RGB values. With a `uint8`
  RGB input, this remains an integer color array; arbitrary float colors are
  not normalized or clipped.

For pixel `(u,v)` with depth `z`, the exact source equations are:

```text
X_camera = (u - cx) * z / fx
Y_camera = (v - cy) * z / fy
Z_camera = z
```

`u` increases to the right, `v` downwards, and the flattening follows the
usual `(row, column)` C-order. NaN depth creates NaN point coordinates and
usually disappears during heightmap bounds comparisons; zero depth creates a
zero point and is **not** automatically discarded by this helper.

## `get_heightmap`

```python
def get_heightmap(color_img, depth_img, cam_intrinsics, cam_pose,
                  workspace_limits, heightmap_resolution):
    # returns color_heightmap, depth_heightmap
```

Inputs are the same RGB-D/K inputs plus:

- `cam_pose`: 4x4 homogeneous matrix. Only `cam_pose[0:3,0:3]` and
  `cam_pose[0:3,3]` are used. It maps camera coordinates to robot coordinates:
  `p_robot = R @ p_camera + t`.
- `workspace_limits`: 3x2 `[x,y,z]` matrix in robot-frame metres, each row
  `[min,max]`.
- `heightmap_resolution`: positive scalar in metres/pixel.

The source computes:

```python
heightmap_size = np.round(
    ((y_max-y_min)/resolution, (x_max-x_min)/resolution)
).astype(int)
```

and returns `color_heightmap` with shape `(heightmap_size[0],
heightmap_size[1],3)` and `depth_heightmap` with shape `(heightmap_size[0],
heightmap_size[1])`. The color map is initialized as `uint8` zero arrays.
The depth map is initialized as NumPy's default floating dtype.

Rasterization is exactly:

```text
x_pixel = floor((X_robot - x_min) / resolution)
y_pixel = floor((Y_robot - y_min) / resolution)
depth_heightmap[y_pixel,x_pixel] = Z_robot - z_min
```

Before assignment, points are sorted in ascending `Z_robot`. Therefore a
higher point at the same pixel overwrites a lower point. Bounds are:

```text
x_min <= X_robot < x_max
 y_min <= Y_robot < y_max
 Z_robot < z_max
```

There is no source-side `Z_robot >= z_min` test. After rasterization the
source subtracts `z_min`, clamps negative values to zero, and changes values
equal to `-z_min` to NaN. With the repository's usual negative `z_min`, a
zero-depth point becomes the sentinel `-z_min` and is marked NaN. Unwritten
cells also start at zero, become `-z_min`, and are marked NaN. If `z_min ==
0`, the equality step marks all zero-valued cells NaN. Do not use an exact
zero/nonzero test as a substitute for `np.isnan`.

## Rigid rotation helpers

```python
def euler2rotm(theta):
    # theta: length-3 sequence of radians; returns (3,3) ndarray

def rotm2euler(R):
    # R: (3,3) rotation matrix; returns length-3 ndarray of radians

def angle2rotm(angle, axis, point=None):
    # angle: scalar radians, axis: NumPy vector, point: optional length>=3
    # returns (4,4) homogeneous ndarray

def rotm2angle(R):
    # R: (3,3) rotation matrix; returns [angle, axis_x, axis_y, axis_z]
```

`euler2rotm([rx,ry,rz])` constructs elementary X/Y/Z matrices and returns
`Rz @ (Ry @ Rx)`. `rotm2euler` calls `isRotm` first; `isRotm` checks
`||R.T @ R - I|| < 1e-6`, but does not explicitly check determinant. The
non-singular result is `[atan2(R[2,1],R[2,2]), atan2(-R[2,0],sy),
atan2(R[1,0],R[0,0])]`, with a gimbal-lock branch that sets z to zero.
Angles are radians and Euler representations are not unique.

`angle2rotm` normalizes `axis`, builds Rodrigues rotation, places it in the
upper-left 3x3 of identity, and returns identity translation unless `point`
is provided. For a rotation about `point`, translation is `point - R@point`.
A zero-length axis raises from normalization; a Python list axis is not
supported by the source's division expression, so pass `np.asarray(axis)`.
`rotm2angle` asserts `isRotm`, returns a Python list, and has special cases
for identity and 180 degrees. It is not a substitute for a calibrated pose.

## Normalization boundary

The separately reviewed application applies the loaded calibration depth
scale from `<CALIBRATION_OUTPUT_DIR>/camera_depth_scale.txt` before calling
`get_heightmap`. Geometry returns RGB values (normally `uint8` 0..255) and
metre-valued relative height. The application copies the depth map and
replaces NaN with zero before `Trainer.forward`; historical `main.py` behavior
is source evidence only.

`Trainer.forward` then nearest-neighbor upsamples both maps by 2, zero-pads
for rotation, divides RGB by 255, and applies channel-wise
`mean=[0.485,0.456,0.406]`, `std=[0.229,0.224,0.225]`. It repeats the depth
heightmap into three channels and applies `mean=[0.01,0.01,0.01]`,
`std=[0.03,0.03,0.03]`. This route must not apply those model transforms to
point-cloud or heightmap API inputs. See [data and calibration](data-and-calibration.md)
for file encodings and [troubleshooting](troubleshooting.md) for validation.
