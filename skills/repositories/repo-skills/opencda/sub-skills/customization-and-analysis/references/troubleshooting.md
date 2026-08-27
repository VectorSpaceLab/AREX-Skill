# Troubleshooting customization and analysis

## Import path or class errors

**Symptoms:** `ModuleNotFoundError`, `ImportError`, or a replacement appears
never to run.

- Confirm the package is imported from the intended installation or project
  root, and that every package directory on the chosen path has the expected
  `__init__.py` files.
- Use the exact public module spelling. The example filter module is
  `opencda.customize.core.sensing.localization.extented_kalman_filter` and the
  class is `ExtentedKalmanFilter`; `extended` is not the source spelling.
- A localization/perception/behavior subclass is not auto-discovered. The
  stock `VehicleManager` binds default classes through imports. Change the
  binding in a project-specific vehicle manager or construct a custom manager;
  a new module alone cannot alter that binding.
- Do not add a dotted path to the controller `type` and expect the stock
  loader to accept it. Its import target is always
  `opencda.core.actuation.<type>` and it looks for `Controller`.
- Prefer a public import probe that does not spawn actors, for example importing
  the replacement class and printing its module/name. Do not instantiate a
  sensor-backed manager merely to diagnose an import.

## Contract mismatch

**Symptoms:** downstream `KeyError`, `AttributeError`, invalid geometry, or a
controller failing after a seemingly successful override.

- Localization: verify `localize()` takes no arguments, sets `_ego_pos` to a
  `carla.Transform`, sets `_speed` to a numeric km/h value, and leaves
  `get_ego_pos`, `get_ego_spd`, and `destroy` usable.
- Filter: verify initialization is `[x, y, yaw, v]` with shape `(4, 1)`, inputs
  are five scalars, yaw is radians, velocity is m/s, and the return order is
  four scalar values.
- Perception: always return a dictionary containing `vehicles` and
  `traffic_lights`, each a list. Behavior and safety code index the vehicle
  list even when it is empty.
- Behavior: accept a `carla.Transform`, km/h speed, and object dictionary in
  `update_information`; return a numeric target speed plus a
  `carla.Location` or `None` from `run_step`. `(0, None)` is a valid stop path.
- Controller: accept `args` in the constructor, update with pose and km/h
  speed, and return `carla.VehicleControl` from `run_step`. Preserve the
  `target_speed == 0`/`waypoint is None` stop behavior unless an equivalent is
  explicitly tested.
- Use assertions on type, keys, shape, units, and finiteness at the boundary
  in a synthetic test. Avoid assertions that require a live CARLA actor when
  the test is intended to be a filter-only check.

## Invalid YAML controller name

**Symptoms:** configuration load succeeds, then `ControlManager` fails during
construction with a module or `Controller` attribute error.

1. Read the final merged `vehicle_base.controller.type` value, not a nearby
   comment or an unmerged scenario fragment.
2. Make it the exact filename stem under `opencda/core/actuation`; for the
   default implementation it is `pid_controller`.
3. Ensure the module exports exactly `class Controller`, and that its
   constructor accepts the mapping under `vehicle_base.controller.args`.
4. Ensure all required nested PID/custom keys are present and scalar values are
   compatible with the implementation.
5. Probe the import and `getattr(module, "Controller")` before starting a
   simulator. The loader does not validate a custom `Controller` contract
   until `update_info` or `run_step` is called.

The YAML type selects only the controller object. It does not select a
localizer, perception manager, or behavior agent.

## Plot backend and headless execution

**Symptoms:** Tk/Qt display errors, a hang in `run_step`, or a test trying to
open a window.

- Set `MPLBACKEND=Agg` before Python imports matplotlib/OpenCDA.
- Set the debug configuration `show_animation: false` for automated runs.
- Call `evaluate()` to obtain a figure and text, then close the figure; do not
  call `plt.show()`.
- If animation itself is under investigation, use a real display and treat
  TkAgg/Qt availability as an environment prerequisite. The helper's fallback
  catches missing Tk in some cases but does not make every GUI backend safe.
- Keep plotting checks separate from CARLA checks. `test_drive_profile_plotting`
  and the localization debug test can be run with mocked CARLA and Agg.

## External backend failures

**Symptoms:** sensor spawning, active detector, co-simulation, or scenario
startup fails even though filter tests pass.

- A live CARLA 0.9.12 server and compatible map are required for GNSS/IMU,
  camera/LiDAR actors, `carla.Map`, and `VehicleManager` integration.
- Active perception additionally requires `apply_ml`/a populated
  `cav_world.ml_manager` and the YOLOv5 runtime; those dependencies were not
  verified locally.
- SUMO and ScenarioRunner are separate backend gates and were not verified.
- Do not label these failures as filter or contract regressions until a
  backend-enabled test is available. Record the missing backend and keep the
  deterministic filter/debug evidence separate.
