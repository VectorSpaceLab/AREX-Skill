---
name: core-driving-stack
description: "Use the OpenCDA core driving stack knowledge for single-vehicle
  lifecycle, sensing, geometry, map rasterization, route and behavior planning,
  PID control, and safety integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core driving stack

Use this sub-skill for a **single CAV** built from OpenCDA 0.1.3 core modules. It is a routing file: load the references below rather than inferring contracts from memory.

## Choose the relevant reference

- **Construction and signatures:** [api-reference.md](references/api-reference.md)
- **GNSS/IMU/Kalman, sensor data, and matrix geometry:** [sensing-and-geometry.md](references/sensing-and-geometry.md)
- **Map, route/behavior/local planning, PID, and safety:** [planning-and-control.md](references/planning-and-control.md)
- **Import/config/API failures and backend boundaries:** [troubleshooting.md](references/troubleshooting.md)

## Operating workflow

1. Prepare a valid merged scenario configuration. The `world` block must provide a synchronous CARLA world and `fixed_delta_seconds`; the single-vehicle config must provide `sensing`, `map_manager`, `behavior`, `controller`, `v2x`, and `safety_manager` blocks. Preserve the units in the references.
2. Create `CavWorld(apply_ml=False)` unless the ML detector is intentionally available. Construct `ScenarioManager` with `scenario_params`, the chosen `apply_ml`, an explicit CARLA version, and either `town` or `xodr_path`; pass the same `cav_world`.
3. Call `create_vehicle_manager(application=['single'])`. Set the returned manager's destination with CARLA `Location` objects before entering the loop.
4. On every synchronous tick, call `scenario_manager.tick()`, then `VehicleManager.update_info()`, then `VehicleManager.run_step()`, and apply the returned `carla.VehicleControl` to the managed vehicle. The update order is localization → perception → map → safety → V2X → behavior → controller.
5. Tear down sensors and actors with the vehicle manager, then restore the world with `ScenarioManager.close()`. Use `CavWorld.destroy()` when its registered managers are no longer needed; do not assume the manager's `tick()` advances `CavWorld.global_clock`.

## Hard boundaries

- The inspected environment passed imports for OpenCDA core dependencies, the CARLA 0.9.12 client, OmegaConf, NumPy/SciPy/matplotlib/networkx/OpenCV/Open3D/Shapely, and core managers. It did **not** verify a running CARLA server, SUMO, ScenarioRunner, torch, or YOLOv5. Treat live simulation, co-simulation, scenario-runner integration, and active ML perception as conditional—not verified behavior.
- `apply_ml=True` dynamically loads the ML manager and active perception requires a loaded detector. Keep `activate: false` for server-ground-truth perception unless the ML runtime and model are actually provisioned.
- The native KF and sensor-transformation tests are pure/mock-oriented candidates. They do not prove sensor spawning, traffic, map topology, controller application, or a live server.
- This sub-skill covers the core single-vehicle path. Platooning, V2X protocol behavior, SUMO bridge details, and data-dump production are only mentioned where they constrain single-vehicle setup.
