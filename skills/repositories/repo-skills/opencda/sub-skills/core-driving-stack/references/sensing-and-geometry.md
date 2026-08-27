# Sensing, localization, and sensor geometry

## Localization data flow and units

`VehicleManager.update_info()` calls `LocalizationManager.localize()` before perception. With `sensing.localization.activate: false`, localization returns the vehicle's server transform and `get_speed(vehicle)` in **km/h**. With activation enabled, it spawns GNSS and IMU actors, converts GNSS latitude/longitude/altitude to an ESU-like CARLA world coordinate using `geo_to_transform`, injects configured heading and speed noise, and fuses the result with a four-state Kalman filter.

The public state is `[x, y, heading, velocity]`:

- `x`, `y`: CARLA world/map coordinates in meters.
- `heading`: radians inside `KalmanFilter`; `LocalizationManager` converts the returned heading back to degrees for `carla.Rotation.yaw`.
- Kalman velocity: m/s.
- `LocalizationManager._speed` and `get_ego_spd()`: km/h. It converts noisy speed to m/s before the filter and multiplies the filtered result by `3.6` afterward.
- IMU gyroscope `z`: rad/s. Accelerometer values are m/s², although the default localizer only supplies gyroscope `z` to the filter.
- GNSS noise standard deviations follow the CARLA sensor attributes; `dt` is seconds and should match `world.fixed_delta_seconds`.

The first active-localization sample is used as the KF initial state and uses the true server speed. Later samples call:

```text
kf.run_step(x_gnss, y_gnss, radians(noisy_heading),
            noisy_speed_m_per_s, imu.gyroscope[2])
```

The inspected `KalmanFilter` has `Q.shape == (4, 4)`, `R.shape == (3, 3)`, `xEst.shape == (4, 1)`, and `PEst.shape == (4, 4)`. `motion_model(x, u)` expects `x.shape == (4, 1)` and `u.shape == (2, 1)` where `u=[current_velocity_m_per_s, imu_yaw_rate_rad_per_s]`. `run_step()` returns four Python floats.

The localization module assumes callbacks have populated `gnss` and `imu`. A live CARLA sensor stream is therefore required for active localization; the pure KF test does not validate this stream.

## Perception modes

`PerceptionManager.detect(ego_pos)` returns:

```text
{
    'vehicles': [ObstacleVehicle, ...],
    'traffic_lights': [TrafficLight, ...]
}
```

With `activate: false`, vehicle actors are read from the server, filtered by distance (50 m normally; 120 m for data dump), wrapped as `ObstacleVehicle`, and traffic lights are selected from the current road/direction. Obstacle speeds are then matched from server vehicles. This is the safest verified path for an environment without ML.

With `activate: true`, the manager waits for camera frames, calls the shared ML manager's detector, projects LiDAR into each camera, fuses detections, and adds traffic lights from the server. This path needs `CavWorld.ml_manager`, camera and LiDAR data, Open3D fusion, and a compatible detector; YOLOv5/torch execution was not verified.

Sensor creation rules that affect configuration:

- RGB cameras are created if perception is active **or** `camera.visualize` is nonzero.
- LiDAR is created if perception is active **or** `lidar.visualize` is true.
- Camera `positions` length must equal `camera.num`; otherwise construction asserts.
- `data_dump=True` creates semantic LiDAR and is rejected when perception activation is also true, because precise labels need server-side ground truth.
- Semantic LiDAR records structured fields `(x, y, z, CosAngle, ObjIdx, ObjTag)` and exposes `points`, `obj_idx`, and `obj_tag`.
- Regular LiDAR raw bytes are float32 and reshape to `(N, 4)` as `(x, y, z, intensity)`.
- Camera raw bytes reshape to `(image_height, image_width, 4)` and discard alpha, yielding an image of shape `(H, W, 3)`.

## Homogeneous transform conventions

`x_to_world_transformation(transform)` returns a numeric **4×4** homogeneous matrix. Points are column vectors. The translation occupies column 3 and the bottom-right element is `1`.

```text
world_points = x_to_world_transformation(sensor_transform) @ sensor_points
sensor_points = inv(x_to_world_transformation(sensor_transform)) @ world_points
```

The tested and supported shapes are:

| Function | Input shape | Output shape |
|---|---:|---:|
| `create_bb_points(vehicle)` | vehicle extents | `(8, 4)` |
| `bbx_to_world(cords, vehicle)` | `cords` `(8, 4)` | `(4, 8)` |
| `world_to_sensor(cords, transform)` | `(4, N)` | `(4, N)` |
| `sensor_to_world(cords, transform)` | `(4, N)` | `(4, N)` |
| `vehicle_to_sensor(cords, vehicle, sensor_transform)` | `(N, 4)` | `(4, N)` |
| `get_bounding_box(vehicle, camera, transform)` | CARLA actors | `(8, 3)` |
| `p3d_to_p2d_bb(p3d_bb)` | `(N, 2+)` | `[[min_x,min_y],[max_x,max_y]]`, `(2, 2)` |
| `get_2d_bb(vehicle, camera, transform)` | CARLA actors | `(2, 2)` |
| `project_lidar_to_camera(...)` | point cloud `(N, 4)` | image unchanged in shape; returned `points_2d` `(N, 3)` |

The asymmetric `(N,4)` versus `(4,N)` convention is intentional: bounding-box vertices are created row-wise, then transformed as columns. Do not pass a transposed `(4,N)` array to `vehicle_to_sensor()`.

## Camera projection details

`get_camera_intrinsic(sensor)` uses integer image width/height and integer FOV:

```text
K = [[f, 0, width/2],
     [0, f, height/2],
     [0, 0, 1]]
f = width / (2*tan(FOV*pi/360))
```

For CARLA/UE coordinates the projection changes `(x, y, z)` to `(y, -z, x)` before multiplying by `K`. The third component is depth. Bounding-box projection divides each first and second component by depth and does not clip points to the image. LiDAR projection filters points to positive depth and the image rectangle, colors valid pixels, but returns the full normalized `(N,3)` projection array. Zero/negative depths therefore need to be handled by the caller when using projected arrays.

`bbx_to_world()` composes the vehicle transform with a transform made from the bounding-box location; `create_bb_points()` uses the axis-aligned extent and homogeneous `1`. This is sufficient for the inspected tests but is not a general rotated-bounding-box estimator.

## Map raster geometry

When `MapManager` is active, `update_information(ego_pose)` makes the ego transform the raster center. `pixels_per_meter` controls scale, `raster_size` is `[width, height]` in configuration but arrays are allocated `(height, width, 3)`, and `lane_sample_resolution` samples map centerlines in meters. World points are moved to the ego frame with `world_to_sensor`, then axes are swapped/reverted to image coordinates and translated to the image center.

`static_bev`, `dynamic_bev`, and `vis_bev` are RGB `uint8` arrays when rasterization has run. A disabled map manager leaves them `None`; safety's off-road detector treats a `None` static map as no off-road decision.
