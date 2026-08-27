# Core API and lifecycle reference

This reference records the inspected OpenCDA 0.1.3 interfaces at source commit `72b17e7b7fa0d67da1bf11a4083c90737eb1225f`. Names below are public module/class names; examples intentionally use repository-relative or user-chosen paths only.

## Scenario construction

`opencda.scenario_testing.utils.sim_api.ScenarioManager` is the CARLA-only scenario constructor:

```text
ScenarioManager(
    scenario_params, apply_ml, carla_version,
    xodr_path=None, town=None, cav_world=None
)
```

The constructor reads `scenario_params['world']`, connects to `localhost` at `world.client_port`, enforces synchronous mode, applies `world.fixed_delta_seconds` and weather, and gets the CARLA map. Supply exactly one usable map choice (`town`, `xodr_path`, or an already usable current world). `carla_version` is required by the source even though some older tutorial snippets omit it.

Useful methods and return contracts:

- `create_vehicle_manager(application, map_helper=None, data_dump=False)` returns a list of `VehicleManager` objects for `scenario.single_cav_list`. For a single CAV use `application=['single']`.
- `create_platoon_manager(map_helper=None, data_dump=False)` is outside this single-vehicle path, but it also creates vehicle managers internally.
- `create_traffic_carla()` returns `(traffic_manager, background_vehicle_list)` and consumes `carla_traffic_manager`.
- `tick()` calls the CARLA world's `tick()` once.
- `destroyActors()` destroys all actors in the world; use only when global actor teardown is intended.
- `close()` restores the original CARLA world settings. It does not replace explicit vehicle/sensor cleanup.

The source examples follow this loop shape:

```text
scenario_manager.tick()
vehicle_manager.update_info()
control = vehicle_manager.run_step()
vehicle_manager.vehicle.apply_control(control)
```

A separate `CavWorld.tick()` increments `global_clock`; `ScenarioManager.tick()` does not call it. This matters if consuming the safety status queue's clock.

## CavWorld registry

`opencda.core.common.cav_world.CavWorld(apply_ml=False)` initializes:

- `vehicle_id_set: set`
- private vehicle, platoon, and RSU manager dictionaries
- `ml_manager`, initially `None`
- `global_clock`, initially `0`
- `sumo2carla_ids`, initially `{}`

Verified methods:

- `update_vehicle_manager(vehicle_manager)` registers `vehicle_manager.vehicle.id` and stores the manager by its UUID `vid`.
- `update_platooning(platooning_manger)` and `update_rsu_manager(rsu_manager)` register cooperative managers.
- `update_sumo_vehicles(sumo2carla_ids)` replaces the SUMO-to-CARLA ID map.
- `get_vehicle_managers()` returns the vehicle-manager dictionary.
- `get_platoon_dict()` returns the platoon dictionary.
- `locate_vehicle_manager(loc)` compares exact `x` and `y` values against localized ego poses; it is not a nearest-neighbor query.
- `get_ego_vehicle_manager()` selects the manager whose CARLA actor ID is the minimum registered ID. It raises if no vehicle IDs are registered.
- `tick()` increments `global_clock` by one.
- `destroy()` calls `destroy()` on registered vehicle and RSU managers. It does not itself restore a ScenarioManager world.

With `apply_ml=True`, construction dynamically imports the ML manager. That path is not verified in the inspected environment.

## VehicleManager composition and lifecycle

`opencda.core.common.vehicle_manager.VehicleManager` has the verified constructor:

```text
VehicleManager(
    vehicle, config_yaml, application, carla_map, cav_world,
    current_time='', data_dumping=False
)
```

The constructor expects `config_yaml` to expose `sensing`, `map_manager`, `behavior`, `controller`, and `v2x`; `safety_manager` is also required by the safety manager. It creates, in order, `V2XManager`, `LocalizationManager`, `PerceptionManager`, `MapManager`, `SafetyManager`, either `BehaviorAgent` (single) or a platoon behavior agent, and `ControlManager`. It registers itself in `cav_world` before returning. `data_dumping=True` additionally creates a `DataDumper` and causes semantic LiDAR creation inside perception.

Verified methods:

- `set_destination(start_location, end_location, clean=False, end_reset=True)` forwards the two CARLA `Location` objects to the behavior agent.
- `update_info()` performs the complete sensing-to-control-input update. It returns `None` and stores no control command.
- `run_step(target_speed=None)` returns a `carla.VehicleControl`; it runs map visualization, behavior planning, control, and optional data dumping.
- `destroy()` destroys perception sensors, localization sensors, the vehicle actor, and map windows. Call it before or alongside broader world cleanup.

`update_info()` passes the following safety dictionary: `ego_pos`, `ego_speed`, `objects`, `carla_map`, `world`, `static_bev`, and `vis_bev`. The perception return object always has `vehicles` and `traffic_lights` keys in the normal path.

## Sensing and planning signatures

- `LocalizationManager(vehicle, config_yaml, carla_map)`; call `localize()`, then `get_ego_pos()` and `get_ego_spd()`, and finally `destroy()`.
- `KalmanFilter(dt)`; call `run_step_init(x, y, heading, velocity)` once, then `run_step(x, y, heading, velocity, yaw_rate_imu)`. The returned tuple is `(x, y, heading, velocity)`.
- `PerceptionManager(vehicle, config_yaml, cav_world, data_dump=False, carla_world=None, infra_id=None)`; call `detect(ego_pos)` and `destroy()`.
- `MapManager(vehicle, carla_map, config)`; call `update_information(ego_pose)`, `run_step()`, and `destroy()`.
- `BehaviorAgent(vehicle, carla_map, config_yaml)`; call `set_destination(start_location, end_location, clean=False, end_reset=True, clean_history=False)`, `update_information(ego_pos, ego_speed, objects)`, and `run_step(target_speed=None, collision_detector_enabled=True, lane_change_allowed=True)`. The last method returns `(target_speed, target_location)` rather than a CARLA control object.
- `LocalPlanner(agent, carla_map, config_yaml)`; `set_global_plan()` consumes `(waypoint, RoadOption)` pairs. `run_step(rx, ry, rk, target_speed=None, trajectory=None, following=False)` returns the next speed and target transform.
- `GlobalRoutePlannerDAO(wmap, sampling_resolution)` feeds `GlobalRoutePlanner(dao)`. Call `setup()` before `trace_route(origin, destination)`; `trace_route()` returns `(carla.Waypoint, RoadOption)` pairs.

## Control signatures

`ControlManager(control_config)` dynamically imports `opencda.core.actuation.<control_config['type']>` and instantiates its `Controller` with `control_config['args']`. Call `update_info(ego_pos, ego_speed)` and `run_step(target_speed, waypoint)`.

The verified PID implementation is `pid_controller.Controller(args)`. Required `args` keys are:

```text
max_brake, max_throttle, max_steering,
lat: {k_p, k_d, k_i},
lon: {k_p, k_d, k_i},
dt, dynamic
```

`Controller.run_step(target_speed, waypoint)` returns `carla.VehicleControl`. A target speed of exactly numeric `0`, or `waypoint is None`, takes the emergency branch: `steer=0.0`, `throttle=0.0`, `brake=1.0`, `hand_brake=False`, and returns immediately. It does not require a live server to reason about, but importing the PID module requires the CARLA Python package.
