# Extension contracts

OpenCDA's customization guidance favors inheritance and package-local
replacements, but only a few selections are dynamic. Keep each replacement's
public signature and downstream data shape stable. The stock
`VehicleManager` imports the default localization, perception, behavior, and
control-manager classes directly, so a subclass is not active merely because
its module exists.

## Localization

### Whole-manager seam

The default seam is:

```text
LocalizationManager(vehicle, config_yaml, carla_map)
```

`vehicle` is a `carla.Vehicle`, `config_yaml` is the localization mapping, and
`carla_map` is a `carla.Map`. A manager must provide:

```text
localize() -> None
get_ego_pos() -> carla.Transform
get_ego_spd() -> float       # km/h at the VehicleManager boundary
destroy() -> None             # release GNSS/IMU actors when present
```

`localize()` is called with no arguments by `VehicleManager.update_info()`. It
must refresh `_ego_pos` and `_speed`; those values are then sent to the map
manager, safety manager, V2X manager, behavior agent, and controller. A custom
manager that changes preprocessing may keep the rest of the lifecycle, but it
must still publish a `carla.Transform` and a numeric speed in km/h.

### Filter-only seam

The least disruptive localization change is to inherit the default manager,
call its initializer, and replace `self.kf` with an object implementing the
same filter interface. The repository's example uses these exact public names:

```text
opencda.customize.core.sensing.localization.localization_manager
  CustomizedLocalizationManager(LocalizationManager)

opencda.customize.core.sensing.localization.extented_kalman_filter
  ExtentedKalmanFilter
```

`extented` is misspelled in the existing public module and class name; preserve
that spelling when importing the example. The replacement manager still needs
to be wired into the vehicle-manager construction path, typically by changing
that import binding in a project-specific vehicle manager or by using a custom
vehicle-manager subclass. Do not rely on a localization YAML `type` key: the
stock manager does not read one.

If only the filter is replaced, preserve the default manager's conversion
boundary: GNSS coordinates are in the ESU/world coordinate convention, heading
is converted from degrees to radians before the filter, and speed is converted
from km/h to m/s. Filter output heading is converted back to degrees and speed
back to km/h before constructing the `carla.Transform` and publishing
`_speed`.

## Perception

The default constructor accepts the following seam (the final optional
arguments are useful for infrastructure managers):

```text
PerceptionManager(
    vehicle, config_yaml, cav_world,
    data_dump=False, carla_world=None, infra_id=None)
```

A vehicle replacement should preserve at least the first four arguments and
return from:

```text
detect(ego_pos: carla.Transform) -> dict
```

The stable keys consumed by behavior and safety code are:

```text
{
    "vehicles": list[ObstacleVehicle],
    "traffic_lights": list[TrafficLight],
}
```

The lists may be empty. Additional categories are allowed only if all
consumers tolerate them; never remove `vehicles` or `traffic_lights` without
updating every consumer. `ego_pos` is also stored as the current ego pose. The
active detector path requires a loaded `cav_world.ml_manager`; that path is not
locally verified without the external ML stack. The inactive path uses server
information and still requires a live CARLA world when real actors are used.

## Behavior planning

Subclass the default:

```text
BehaviorAgent(vehicle, carla_map, config_yaml)
```

The two key override seams are:

```text
update_information(
    ego_pos: carla.Transform,
    ego_speed: float,          # km/h
    objects: dict) -> None

run_step(
    target_speed=None,
    collision_detector_enabled=True,
    lane_change_allowed=True
) -> (number, carla.Location | None)
```

The normal return is a target speed and a target `carla.Location`. The
emergency/traffic-light paths can return `(0, None)`, so callers must not
assume the location is always non-null. `objects["vehicles"]` is consumed by
collision and following logic. For platooning, remember that
`PlatooningBehaviorAgent` is itself a `BehaviorAgent` subclass with a broader
constructor and additional run-step behavior; replacing the base agent without
considering the application mode can break platoon control.

## Control and YAML-selected controllers

`ControlManager` is the built-in dynamic seam. It reads the merged vehicle
configuration's controller mapping:

```yaml
vehicle_base:
  controller:
    type: pid_controller
    args: ...
```

`ControlManager` performs the equivalent of:

```text
module = importlib.import_module("opencda.core.actuation." + type)
Controller = getattr(module, "Controller")
controller = Controller(args)
```

Therefore `type` must be the exact Python module basename under
`opencda.core.actuation`, and that module must export a class named
`Controller`. A custom controller object must implement:

```text
__init__(args: dict)
update_info(ego_pos: carla.Transform, ego_spd: float) -> None
run_step(target_speed: number,
         waypoint: carla.Location | None) -> carla.VehicleControl
```

The controller's speed boundary is km/h, and `waypoint` is the target location
passed through from the behavior agent. A dotted module path, a class name, or
a file placed only under `opencda/customize` will not be found by this import
expression. To keep a custom implementation in a customization package, add a
small supported package-level adapter or replace/wire `ControlManager`
explicitly; do not silently change the YAML contract.

The stock PID controller also treats `target_speed == 0` or `waypoint is None`
as an emergency stop and returns a `carla.VehicleControl`. A replacement
should preserve that safety behavior or document and test an equivalent policy.
