# Camera, workspace, and calibration data

## Coordinate frames and units

The source treats camera depth and robot geometry as metres. `cam_pose` is a
camera-to-robot/world homogeneous transform, not robot-to-camera:

```text
[p_robot; 1] = cam_pose @ [p_camera; 1]
p_robot = cam_pose[:3,:3] @ p_camera + cam_pose[:3,3]
```

`get_heightmap` uses this convention directly. The calibration script first
fits `world2camera` from robot/tool checkerboard points to observed camera
points with an SVD rigid fit, then stores `camera_pose = inverse(world2camera)`.
The saved pose therefore has the camera-to-robot direction expected by
`get_heightmap`. A valid rigid rotation should have `R.T @ R` near identity
and determinant near +1.

No lens-distortion correction appears in the projection helper. Intrinsics are
pinhole values `[fx, fy, cx, cy]` in pixel units and must match the actual
image width, height, and pixel ordering.

## Runtime workspaces and resolution

`main.py` defines these 3x2 robot-frame metre limits:

| mode | x `[min,max]` | y `[min,max]` | z `[min,max]` |
|---|---:|---:|---:|
| simulation | `[-0.724,-0.276]` | `[-0.224,0.224]` | `[-0.0001,0.4]` |
| real runtime | `[0.3,0.748]` | `[-0.224,0.224]` | `[-0.255,-0.1]` |

The default `heightmap_resolution` is `0.002` m/pixel. The runtime maps are
therefore 224 rows by 224 columns for the listed 0.448 m x/y spans. The first
heightmap axis is y/row; the second is x/column. Pixel centers are not offset
by half a pixel: the source uses `floor((coordinate-min)/resolution)`.

`calibrate.py` deliberately uses different limits for its checkerboard grid:
`[[0.3,0.748],[0.05,0.4],[-0.2,-0.1]]` m, with `calib_grid_step=0.05` m,
`checkerboard_offset_from_tool=[0,-0.13,0.02]`, and tool orientation
`[-pi/2,0,0]`. Keep the checkerboard offset in robot coordinates and account
for its sign; it is not a camera translation.

For x and y, the lower bound is included and upper bound excluded. For z,
only the upper bound is tested by the historical helper. A coordinate exactly
at `x_max` or `y_max` is excluded. A resolution that does not divide the
spans exactly is passed through `round`, not `ceil`; callers should inspect
that the resulting pixel index cannot exceed the allocated map.

## RGB-D acquisition boundary

The real camera client is configured for `im_height=720`, `im_width=1280`.
Each frame received from the TCP camera server contains, in order:

1. 9 little-endian/native `float32` values reshaped to a 3x3 color-camera
   intrinsic matrix;
2. one `float32` depth scale;
3. `1280*720` `uint16` depth samples;
4. `1280*720*3` `uint8` RGB samples.

The client converts depth to floating point and multiplies by the per-frame
scale before returning `(color_img, depth_img)`. The returned depth is thus
intended to be metres. The robot/main path then multiplies by the separately
loaded calibration scale. Simulation instead converts the normalized depth
buffer using `zNear=0.01`, `zFar=10`, flips the image horizontally, and sets
its calibration scale to 1.

This geometry route does not own TCP framing or camera-server setup. It does
own the unit boundary: if a caller already has metre-valued depth, do not
apply a raw `uint16` scale again; if calibration has already been applied, do
not apply the file scalar a second time.

## Calibration and logged file formats

A separately reviewed external calibration application writes space-delimited
text files under an operator-supplied `<CALIBRATION_OUTPUT_DIR>`:

- `<CALIBRATION_OUTPUT_DIR>/camera_pose.txt`: one 4x4 camera-to-robot
  homogeneous matrix;
- `<CALIBRATION_OUTPUT_DIR>/camera_depth_scale.txt`: one optimized scalar z
  multiplier, normally dimensionless, applied after camera-frame depth
  conversion.

The historical `real/` paths and `calibrate.py` are source evidence only. This
graph cannot execute calibration and never requires the original checkout's
`real/` directory.

The runtime logger writes equivalent session metadata under its `info` data:

- `camera-intrinsics.txt`: 3 rows by 3 columns, space-delimited K;
- `camera-pose.txt`: 4 rows by 4 columns, space-delimited camera pose;
- `camera-depth-scale.txt`: one scalar;
- `heightmap-boundaries.txt`: 3 rows by 2 columns `[min,max]` limits;
- `heightmap-resolution.txt`: one scalar in metres/pixel.

Saved image encodings are separate from the in-memory contract. The logger
writes raw depth images after multiplying metres by 10,000 (1e-4 m units) and
heightmap depth after multiplying metres by 100,000 (1e-5 m units), as uint16.
Color images are converted RGB-to-BGR only at OpenCV write time. When reading
these files back, reverse the scale and color convention before geometry.

## Calibration acceptance checks

Before using a new pose/scale pair:

1. load and check exact shapes `(3,3)`, `(4,4)`, and scalar;
2. check finite values, positive focal lengths, homogeneous final row close
   to `[0,0,0,1]`, `det(R)>0`, and `R.T@R` close to identity;
3. project several known points and confirm camera-to-robot direction;
4. confirm checkerboard/tool offset and all robot coordinates are metres;
5. inspect calibration residual/RMSE across the grid, not just one point.

The SVD fit in `calibrate.py` repairs a reflection by flipping the last Vt
row, but it assumes a rigid transform. A scale factor is optimized only on
observed camera Z before refitting the rigid pose; it cannot make a nonrigid,
misregistered, or distorted calibration valid. High residuals require new
measurements or corrected conventions, not an arbitrary affine matrix.

See [API details](api-reference.md) and [failure diagnosis](troubleshooting.md).
