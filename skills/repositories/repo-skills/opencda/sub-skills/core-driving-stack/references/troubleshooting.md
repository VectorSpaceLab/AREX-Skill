# Troubleshooting and verified limits

## Classify the failure first

Use this split before changing geometry or configuration:

1. **Pure geometry/data-shape issue:** the failure is reproducible with the mock actors and NumPy arrays used by the sensor-transformation tests, without constructing a CARLA client, world, actor, or sensor stream. Check matrix dimensions, homogeneous columns, camera depth, and coordinate-axis conversion first.
2. **CARLA backend mismatch:** the failure occurs while importing `carla`, connecting to a client, reading a world/map/blueprint, spawning/listening to sensors, or using version-specific actor APIs. Check the installed client/server pair and server availability before editing transforms.
3. **Optional backend gap:** the failure requires torch/YOLOv5/ML model files, SUMO/TraCI, ScenarioRunner, or a live simulator that was not verified here. Do not “fix” this by claiming a pure-Python test passed.

The inspected package imports passed with Python 3.8 and compatible pins, including the CARLA 0.9.12 client import, but no CARLA server was running. SUMO, ScenarioRunner, torch, and YOLOv5 runtime paths were not verified.

## CARLA import, client, and server failures

- OpenCDA core modules such as localization, perception, planning, safety, and the PID controller import `carla` at module import time. An import error is an environment/backend prerequisite failure, not a route or sensor-matrix result.
- Keep the Python CARLA client compatible with the server (the inspected client import was 0.9.12). Pass the same supported version string to `ScenarioManager`; the source selects CARLA blueprint names based on that value.
- `ScenarioManager` connects to `localhost` and sets a 10-second client timeout. Connection refused, timeout, missing town, or world-loading failures require starting/provisioning the matching server and map, or using a valid custom OpenDRIVE map; they are not evidence against `KalmanFilter` or `sensor_transformation`.
- Sensor constructors need a real `vehicle.get_world()`, blueprint library, CARLA blueprint IDs, `spawn_actor`, and asynchronous `listen` callbacks. Mocking only `Transform` is insufficient for sensor lifecycle tests.
- Synchronous operation is required by the inspected ScenarioManager. `world.sync_mode` and `carla_traffic_manager.sync_mode` should agree with `world.fixed_delta_seconds`.

## Optional package and mode failures

- `CavWorld(apply_ml=True)` dynamically imports the ML manager. The source documentation says torch/sklearn are needed, and active perception additionally needs a usable detector/model. If the ML manager is absent, active `PerceptionManager` construction exits with a message directing the caller to enable ML.
- `activate: true` and `data_dump=True` are rejected together because data dumping needs precise semantic labels. For ground-truth collection use inactive perception and a valid semantic-LiDAR setup.
- `activate: false` is not “no perception”: it queries nearby actors from the CARLA server and returns wrapped `ObstacleVehicle` objects plus server-selected traffic lights. It still needs a live world for a complete scenario.
- Do not treat successful Open3D/OpenCV imports as proof of an active YOLOv5 detector. No YOLOv5 or torch execution was verified.
- SUMO/co-simulation and ScenarioRunner are external branches. A missing TraCI/SUMO executable, ScenarioRunner package, or bridge map is an external backend gap, not a core single-CAV regression.

## Malformed configuration

Check the merged **vehicle** dictionary, not just the top-level YAML:

- Missing any of `sensing`, `map_manager`, `behavior`, `controller`, or `v2x` fails during `VehicleManager` construction. `safety_manager` is also required for `SafetyManager`.
- The localization manager expects `activate`, `dt`, GNSS noise keys including `heading_direction_stddev` and `speed_stddev`, and a `debug_helper` mapping. `dt` must be numeric and in seconds.
- Perception expects `activate`, camera `visualize`, camera `num`, camera `positions`, and LiDAR `visualize` plus the CARLA LiDAR attributes. `len(camera.positions) == camera.num` is enforced. If both are zero/false, no camera is spawned; if LiDAR visualization and activation are both false, no LiDAR is spawned.
- `controller.type` is a module filename under `opencda.core.actuation` (the default is `pid_controller`), and PID args must include both gain groups, `dynamic`, `dt`, and all three limits.
- `behavior.local_planner` needs buffer/update frequencies, `min_dist`, `trajectory_dt`, and debug flags. A destination also needs nonempty route geometry; an empty route yields a `(0, None)` target.
- `map_manager.raster_size` is configured `[width, height]`, but BEV arrays are `(height, width, 3)`. `pixels_per_meter` must be positive.
- Safety key spelling follows the source, including `stuck_dector` (not `stuck_detector`) and `traffic_light_detector`.
- For a scenario file, `world.sync_mode` must be true in the inspected version, and `carla_version` must be supplied to the ScenarioManager constructor. A `single_cav_list` entry must contain enough spawn/destination data for its scenario driver.

## Sensor API and shape failures

Use these checks when a native or synthetic geometry case fails:

- `x_to_world_transformation()` is 4×4. `world_to_sensor()` and `sensor_to_world()` require homogeneous columns `(4,N)`; append a row of ones to 3-D points before multiplying.
- `create_bb_points()` is `(8,4)`, but `vehicle_to_sensor()` takes row-wise `(N,4)` and returns `(4,N)`. Transposing twice is a common source of silent wrong results.
- A regular LiDAR packet must be decoded as little-endian float32 groups of four: `(x,y,z,intensity)`. A semantic packet is a structured six-field record; do not reshape it as regular LiDAR.
- Camera raw data is BGRA and is reshaped to `(H,W,4)` before dropping alpha. Camera attributes may be strings in a real CARLA blueprint; the source converts dimensions and FOV to integers.
- The camera conversion is `(x,y,z) -> (y,-z,x)`. Projection divides by the third value (depth). Filter nonpositive or nonfinite depth before using projected coordinates; the source's LiDAR function filters positive depth, while bounding-box projection itself does not clip.
- `project_lidar_to_camera()` expects point cloud `(N,4)` and returns normalized points `(N,3)` even though only in-canvas points are painted. Do not expect the returned array length to equal the number of painted pixels.
- The transformation tests use mock actors and assert shapes, including K `(3,3)`, homogeneous matrices `(4,4)`, bounding boxes `(8,3)`, and 2-D boxes `(2,2)`. If those fail without CARLA, inspect arrays/imports first; if mock geometry passes but a live sensor fails, inspect actor transforms and backend coordinates.
- `Controller.lat_run_step()` normalizes the target vector. A target location identical to the current location can produce division by zero; use the emergency branch or choose a nonzero target displacement.

## Safe synthetic checks and difficult cases

The best backend-independent checks are:

1. **Transformation round trip:** with mock transforms and an arbitrary `(4,N)` homogeneous point matrix, verify `sensor_to_world(world_to_sensor(points, T), T)` has the original shape and values within numerical tolerance. Separately verify the tested `(N,4)` bounding-box input convention and output shapes.
2. **PID zero-speed emergency:** instantiate the PID controller with a complete finite args mapping, set no current transform, and call `run_step(0, None)` (or `run_step(0, a_dummy_waypoint)`). Assert exact `steer=0`, `throttle=0`, `brake=1`, `hand_brake=False`. This does not require a CARLA server, but importing the controller still requires the CARLA client module.

Neither check proves CARLA actor spawning, callback freshness, route topology, behavior-agent exit handling, safety sensor events, or live control application.
