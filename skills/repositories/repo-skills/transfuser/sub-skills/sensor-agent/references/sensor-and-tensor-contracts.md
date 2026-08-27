# Sensor And Tensor Contracts

## Sensor Suite

Six core sensors are always declared:

| ID | CARLA sensor type | Default geometry/rate | Runtime use |
| --- | --- | --- | --- |
| `rgb_front` | `sensor.camera.rgb` | position `[1.3, 0.0, 2.3]`, rotation `[0, 0, 0]`, 960×480, FOV 120° | Front image |
| `rgb_left` | `sensor.camera.rgb` | same position, yaw -60°, 960×480, FOV 120° | Left image |
| `rgb_right` | `sensor.camera.rgb` | same position, yaw +60°, 960×480, FOV 120° | Right image |
| `imu` | `sensor.other.imu` | origin, sensor tick 0.05 s | Compass is the final IMU element |
| `gps` | `sensor.other.gnss` | origin, sensor tick 0.01 s | Latitude/longitude pair |
| `speed` | `sensor.speedometer` | reading frequency 20 Hz | Scalar speed in the `speed` field |

The learned LiDAR-fusion backbones add a seventh sensor:

| ID | CARLA sensor type | Default geometry | Runtime use |
| --- | --- | --- | --- |
| `lidar` | `sensor.lidar.ray_cast` | position `[1.3, 0.0, 2.5]`, rotation `[0, 0, -90]` degrees | Raw XYZ point cloud |

`latentTF` intentionally omits this physical LiDAR sensor and receives a dummy
zero BEV tensor internally.

When the `SAVE_PATH` environment variable is non-empty at module import, the
agent creates that directory and adds an optional debug camera:

| ID | Type | Geometry |
| --- | --- | --- |
| `rgb_back` | `sensor.camera.rgb` | position `[-4.5, 0, 2.3]`, pitch -15°, 960×480, FOV 100° |

The extra camera is for visualization only. Setting `SAVE_PATH` changes the
sensor suite even when config debug output is disabled, so use it deliberately.
It is not one of the six core sensors.

Each `input_data` item follows the Leaderboard convention
`(sensor_timestamp_or_frame, payload)`. The agent reads the payload at index
`1`; a test double that supplies bare arrays will fail even if array shapes are
correct.

## Camera Preprocessing

For each camera in order left, front, right:

1. take the first three channels of the CARLA image payload;
2. convert BGR to RGB;
3. with default `scale=1`, crop a 320×160 region starting at pixel `(x=320,
   y=160)` from the 960×480 image;
4. concatenate the three crops horizontally in left/front/right order, producing
   an HWC RGB array of shape `[160, 960, 3]`.

Before inference, that panorama is converted back to a PIL image and passed to
the shifted center crop. With the only configured test-time augmentation angle
of 0°, it:

1. resizes according to `scale`;
2. center-crops to `img_resolution=(160, 704)`;
3. transposes HWC to CHW;
4. adds a batch/augmentation dimension and moves to CUDA float32.

The resulting default image tensor is `[1, 3, 160, 704]`. Nonzero augmentation
would shift the horizontal crop by `degree / 60 * img_width` before scaling,
but the runtime list is `[0]` unless adapted.

Changing camera width, `scale`, `img_width`, or `img_resolution` independently
can make either crop partial or empty. Validate all crop bounds as a coupled
geometry contract; do not treat these as independent tuning knobs at runtime.

## LiDAR Preprocessing

The runtime reads `input_data["lidar"][1][:, :3]` for ordinary processing.
Coordinate preparation depends on the encoder:

### Histogram BEV

- copy XYZ points and multiply Y by -1;
- bin points into a two-channel 256×256 histogram grid;
- use 8 pixels per meter;
- add a batch dimension and move the tensor to CUDA float32.

The default LiDAR-to-BEV homogeneous transform uses:

```text
[[ 0, -1, 16],
 [-1,  0, 32],
 [ 0,  0,  1]] * 8 on its first two rows
```

This exchanges/negates planar axes and converts meters to BEV pixels. Keep the
LiDAR mounting offset `[1.3, 0, 2.5]` consistent with waypoint and bounding-box
conversions.

### Point Pillars

When `use_point_pillars=true`, the agent copies the raw cloud, flips Y, and
builds:

- a one-element list containing a CUDA float32 point tensor;
- a one-element list containing its CUDA int32 point count.

The model's point-pillar encoder consumes these lists and rotates the produced
BEV grid for consistency with voxelization. Preserve the configured point range
(`x` -16 to 16, `y` -32 to 0), input feature count, and maximum-point
assumptions used in training.

### Geometric Fusion

`geometric_fusion` needs both the prepared BEV input and raw LiDAR points. It
computes BEV-to-camera correspondence arrays, adds a batch dimension, converts
them to CUDA int64, and supplies them to `forward_ego`. Supplying only a BEV
raster is insufficient for this backbone.

### Latent Image-Only Path

For `latentTF`, do not request or read `input_data["lidar"]`. The runtime creates
a CUDA float32 zero tensor `[1, 2, 256, 256]` as the model's placeholder. A
configuration combining the image-only path with LiDAR-specific point-pillars
is suspicious and should be reconciled with the checkpoint provenance rather
than guessed.

If `use_target_point_image=true`, the model concatenates the target-point image
onto the LiDAR-like input channel dimension. This field must match training for
all backbones, including the latent placeholder path.

## GPS, Route Planner, And Local Target Point

The tick pipeline extracts:

- `gps = input_data["gps"][1][:2]`;
- `speed = input_data["speed"][1]["speed"]`;
- `compass = input_data["imu"][1][-1]`.

CARLA 0.9.10 can produce a NaN compass value; the agent substitutes `0.0`.
This avoids propagating NaNs but may briefly point the local target in the wrong
direction, so repeated NaNs remain an upstream sensor fault.

The route planner converts GPS route coordinates to planar meters with:

```text
mean  = [0.0, 0.0]
scale = [111324.60662786, 111319.490945]
position = (gps - mean) * scale
```

A deque keeps up to 100 transformed GPS positions. The current position is
appended and the entire buffer is averaged to denoise it. On skipped inference
frames and after each new control, a kinematic bicycle model propagates every
buffered position using the issued control, compass, and speed.

The planner is initialized from `_global_plan` and retains route points between
7.5 and 50 meters according to its pruning logic. It selects the second route
point when available, otherwise the first. The corresponding route-command enum
value is stored as `next_command`, though the shown model forward call uses the
target point rather than that command value directly.

To obtain the target point:

1. subtract the denoised ego position from the selected route point;
2. set `theta = compass + pi/2`;
3. build the 2D rotation matrix for `theta`;
4. multiply the route delta by its transpose.

This yields a local `(x, y)` target tuple. The preparation stage builds a
CUDA float32 target tensor `[1, 2]` and a target-point raster. For augmentation,
that point is rotated by the same degree before both representations are made.
The waypoint GRU then negates target Y internally and later offsets predicted
waypoint X by the LiDAR mount position, so ad-hoc coordinate flips in caller
code will double-transform the goal.

## Velocity And Output Contracts

Ground-truth ego speed becomes:

- controller input `gt_velocity`: CUDA float32 shape `[1]`;
- model input `velocity`: reshaped to `[1, 1]`.

The model predicts four future planar waypoints by default. The controller
expects a single batch (`waypoints.size(0) == 1`) and uses the first two points.
The final return is a `carla.VehicleControl` with float steer, throttle, and
brake values. The Leaderboard base sets `manual_gear_shift` to false after
`run_step` returns.

## Contract Checklist

Before simulator-backed evaluation, verify:

- sensor IDs match exactly, including lowercase names;
- every payload is wrapped as a Leaderboard `(frame, data)` tuple;
- camera geometry permits both crop stages;
- the selected backbone's LiDAR requirement matches the declared sensor suite;
- `use_point_pillars` and target-point-image fields match training;
- all model tensors and model weights resolve to the intended CUDA device;
- `_global_plan` is populated before first route-planner initialization;
- GPS ordering is latitude then longitude, not local XY;
- coordinate flips are performed once, inside the distilled runtime pipeline.
