# Map, planning, control, and safety

## Configuration contract

OpenCDA's scenario YAML is layered: scenario-specific blocks override `vehicle_base` through OmegaConf merging. The single-vehicle manager consumes a merged vehicle dictionary, not the top-level scenario file directly.

The minimum core blocks and important units are:

- `world`: `sync_mode: true`, `client_port`, `fixed_delta_seconds` (seconds), `seed`, and weather fields. The inspected ScenarioManager rejects asynchronous mode.
- `sensing.perception`: `activate`, `camera.visualize`, `camera.num`, `camera.positions`, and LiDAR attributes (`channels`, `range` in m, `points_per_second`, `rotation_frequency`, FOV angles in degrees, drop-off/noise fields). `traffic_light_thresh` is optional.
- `sensing.localization`: `activate`, `dt` (seconds), GNSS noise fields, and `debug_helper`. Active mode additionally needs `heading_direction_stddev` in degrees and `speed_stddev` in km/h.
- `map_manager`: `pixels_per_meter`, `raster_size: [width,height]`, `lane_sample_resolution` in m, `visualize`, and `activate`.
- `behavior`: `max_speed`, `tailgate_speed`, `speed_lim_dist`, and `speed_decrease` in km/h; `safety_time` in seconds; `emergency_param` is multiplied by current speed in m/s to form the behavior break distance; `ignore_traffic_light`, `overtake_allowed`, `collision_time_ahead` in seconds, `sample_resolution` in m, and `local_planner` settings.
- `behavior.local_planner`: `buffer_size`, `trajectory_update_freq`, `waypoint_update_freq`, `min_dist` in m, `trajectory_dt` in seconds, `debug`, and `debug_trajectory`.
- `controller`: `type: pid_controller`; `args.lat` and `args.lon` PID gains; `dynamic`; `dt` in seconds; and throttle/brake/steering bounds. The source expects the exact module filename after `opencda.core.actuation.`.
- `v2x`: at minimum `enabled` and `communication_range` in m for the V2X manager.
- `safety_manager`: `print_message`, `collision_sensor.history_size`, `collision_sensor.col_thresh`, `stuck_dector.len_thresh` and `speed_thresh` (km/h), `offroad_dector`, and `traffic_light_detector.light_dist_thresh` in m.

Use `${world.fixed_delta_seconds}` for both localization and PID `dt` unless a deliberate, verified timing model says otherwise. `spawn_position` is `[x,y,z,roll,yaw,pitch]` with location in meters and angles in degrees. A `single_cav_list` entry needs a `destination: [x,y,z]` when the scenario driver uses it.

## Behavior and route flow

`BehaviorAgent.set_destination(start_location, end_location, ...)` maps both locations to CARLA waypoints, initializes a `GlobalRoutePlanner` from the vehicle world's map, and queues a route of `(waypoint, RoadOption)` pairs. `RoadOption` values are `VOID`, `LEFT`, `RIGHT`, `STRAIGHT`, `LANEFOLLOW`, `CHANGELANELEFT`, and `CHANGELANERIGHT`.

The global planner builds a directed NetworkX graph from sampled CARLA topology. It localizes origin and destination to road/section/lane edges, uses A* with a Euclidean distance heuristic and edge `length` weights, adds loose ends and legal lane-change links, then emits turn decisions. A route can fail before control if either location cannot be localized or no graph path exists.

On each `BehaviorAgent.run_step(...)`, the source behavior is ordered as follows:

1. Reset transient TTC/overtake/destination-push state and inspect the current waypoint buffer.
2. Treat proximity within approximately 10 m in x and y of the configured end waypoint as destination completion; the current implementation prints and calls `sys.exit(0)`, so callers must not treat this as an ordinary returned stop.
3. Apply traffic-light/stop-sign handling. A red light normally returns `(0, None)`, which the PID controller turns into a full brake. A light already passed into a junction can be placed in `light_id_to_ignore` to avoid stopping in the junction. `ignore_traffic_light: true` changes the agent state to green.
4. Regenerate the global route when a temporary route is exhausted. Near a traffic light/intersection, disable overtaking.
5. Generate a smoothed local path from history/current/queued waypoints using cubic splines at 0.1 m interpolation and clamp sampled curvature to `[-0.2, 0.2]`.
6. Allow a lane change only when its collision check is enabled, the local planner sees both lane-ID and lateral change, there is no active overtake/destination push, and the mean absolute curvature is not above roughly `0.04`. A blocked planned lane change may push the temporary destination forward.
7. Check collisions along the planned path. A close hazard can produce `(0, None)`; otherwise car-following uses TTC and front-vehicle speed. Overtaking is only considered where configured and safe.
8. In normal mode, use `max_speed - speed_lim_dist` unless an explicit target speed is passed. Return `(target_speed_km_h, target_location_or_transform)` to `VehicleManager`.

`LocalPlanner.generate_path()` requires a populated ego pose, map, waypoint buffer, and vehicle bounding box. `LocalPlanner.generate_trajectory()` samples about two seconds ahead at `trajectory_dt`, converts the current speed from km/h to m/s, constrains target speed from mean curvature, and stores `(carla.Transform, target_speed)` pairs. An empty spline path returns `(0, None)` from `LocalPlanner.run_step()`.

## PID actuation and emergency behavior

`ControlManager` is only a dispatcher; the PID `Controller` owns state. Its normal longitudinal input and `get_speed()` are km/h. Lateral control uses the current transform's yaw in degrees and target location in CARLA meters. The output bounds are:

- acceleration is clipped to `[-1, 1]`; positive values become throttle capped by `max_throttle`, negative values become brake capped by `max_brake`;
- steering is rate-limited to a maximum change of `0.2` per step, then clipped to `[-max_steering, max_steering]`;
- `dt` is the controller time step in seconds.

The emergency branch is exact and should be used as a synthetic hard case:

```text
Controller.run_step(0, any_waypoint)
# or
Controller.run_step(nonzero_speed, None)

=> VehicleControl:
   steer == 0.0
   throttle == 0.0
   brake == 1.0
   hand_brake is False
```

This branch occurs before lateral-vector math and is therefore safe when `current_transform` is unset. It bypasses `max_brake` and does not clear PID histories. A negative target speed is not the same as exact zero; it enters normal computation. For non-emergency control, a target point equal to the current location can make the lateral vector norm zero, so avoid that input or handle it before calling the source controller.

The source's `dynamic_pid()` is a no-op (`pass`), so `dynamic: true` does not currently retune gains. Also note that the source appends the longitudinal speed error to `_lat_ebuffer`; do not infer semantics from that private name when diagnosing controller state.

## Safety data flow

`VehicleManager.update_info()` builds the safety input after map update. `SafetyManager.update_info(data_dict)` ticks collision, stuck, off-road, traffic-light, and IMU sensors and appends `(cav_world.global_clock, status_dict)` to `status_queue`. It prints only when a status value is true when `print_message` is enabled; it does not alter the control command or automatically brake the vehicle.

Status meanings and inputs:

- `collision`: callback sets a one-shot flag when impulse magnitude exceeds `collision_sensor.col_thresh`; returned status resets the flag.
- `stuck`: average `ego_speed` remains below `stuck_dector.speed_thresh` for `len_thresh` samples.
- `offroad`: if a raster exists, the center pixel is interpreted against the static BEV; `None` leaves the detector unchanged.
- `ran_light`: traffic-light geometry checks the active light, lane, trigger waypoints, and line intersection. It needs `objects['traffic_lights']`, the localized transform, world, and map.
- `imu`: currently always returns `False`; its callback stores accelerometer, angular velocity, and signed forward acceleration for possible downstream use.

Safety sensors spawn CARLA actors in their constructors and must be destroyed. Safety is observational in this source path; emergency stopping is generated by behavior/PID (`target_speed == 0` or `waypoint is None`), not by `SafetyManager`.
