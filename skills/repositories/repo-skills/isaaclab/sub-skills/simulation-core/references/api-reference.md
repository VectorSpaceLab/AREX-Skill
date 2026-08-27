# Simulation Core API Reference

## Core launcher objects

- `isaaclab.app.AppLauncher`
  - `__init__(launcher_args: argparse.Namespace | dict | None = None, **kwargs)`
  - `add_app_launcher_args(parser: argparse.ArgumentParser) -> None`
  - `app` property returns the launched simulation app.
- `isaaclab.app.SettingsManager`
  - standalone settings manager that mimics `carb.settings` when Isaac Sim is not active.
- `isaaclab.app.get_settings_manager() -> SettingsManager`
- `isaaclab.app.initialize_carb_settings() -> None`

## Simulation configuration

- `isaaclab.sim.SimulationCfg`
  - `device`
  - `dt`
  - `gravity`
  - `physics`
  - `render`
  - `use_fabric`
  - `render_interval`
  - `enable_scene_query_support`
  - `use_newton_actuators`
  - `create_stage_in_memory`
  - `logging_level`
  - `save_logs_to_file`
  - `log_dir`
  - `visualizer_cfgs`
- `isaaclab.physics.PhysicsCfg`
- `isaaclab_physx.physics.PhysxCfg`
- `isaaclab_newton.physics.NewtonCfg`
- `isaaclab_newton.physics.MJWarpSolverCfg`
- `isaaclab_ovphysx.physics.OvPhysxCfg`
- `isaaclab.renderers.renderer_cfg.RendererCfg`

## Runtime helpers

- `isaaclab_tasks.utils.sim_launcher.add_launcher_args(parser)`
- `isaaclab_tasks.utils.sim_launcher.launch_simulation(env_cfg, launcher_args=None)`
- `isaaclab_tasks.utils.sim_launcher.validate_runtime_compatibility(env_cfg, launcher_args=None)`
- `isaaclab_tasks.utils.sim_launcher.compute_kit_requirements(env_cfg, launcher_args=None)`

## Launcher and environment variables

- `HEADLESS=1` forces headless mode.
- `LIVESTREAM=1` or `LIVESTREAM=2` enables livestreaming and implies headless mode.
- `ENABLE_CAMERAS=1` enables camera rendering in headless workflows that need image output.
- `PUBLIC_IP` is used with livestreaming.
- `EXP_PATH` and `ISAACLAB_PATH` are part of the Isaac Sim environment setup for Kit-based launches.

## Visualizer modes

Supported visualizer names are `kit`, `newton`, `rerun`, `viser`, and `none`.

- Omit `--viz` for the default headless path when no visualizer is needed.
- Use `--viz none` to disable visualizers explicitly.
- `--headless` still works for compatibility, but it is deprecated and overrides visualizer selection.
- `kit` visualizer is not compatible with `ovrtx` or `ovphysx` backends in the same process.

## Practical facts

- `AppLauncher` resolves the experience file when `experience=""`.
- `SimulationCfg.physics` chooses the active backend; user code should not import backend implementations directly.
- `SettingsManager` lets non-Kit workflows persist launcher state without requiring Omniverse.
