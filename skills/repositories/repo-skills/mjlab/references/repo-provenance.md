# Repository provenance

## Source snapshot

- Repository: `mujocolab/mjlab`
- Public remote: `https://github.com/mujocolab/mjlab`
- Commit: `0fb8a681136be94ffc636a3dd423cabb97d91f10`
- Branch: `main`
- Exact tag: `v1.6.0`
- Package version: `1.6.0`
- License: Apache-2.0
- Generation state: dirty checkout because generated skill artifacts were under
  `skills/` during creation. No source-code modifications were used as evidence
  beyond the repository files listed below.

## Evidence paths

Primary evidence distilled into this skill:

- `pyproject.toml`
- `README.md`
- `docs/index.rst`
- `docs/source/installation.rst`
- `docs/source/architecture_overview.rst`
- `docs/source/environment_config.rst`
- `docs/source/actions.rst`
- `docs/source/actuators.rst`
- `docs/source/observations.rst`
- `docs/source/rewards.rst`
- `docs/source/terminations.rst`
- `docs/source/events.rst`
- `docs/source/commands.rst`
- `docs/source/curriculum.rst`
- `docs/source/metrics.rst`
- `docs/source/recorders.rst`
- `docs/source/terrain.rst`
- `docs/source/randomization.rst`
- `docs/source/viewers.rst`
- `docs/source/debugging/export_scene.rst`
- `docs/source/debugging/nan_guard.rst`
- `docs/source/sensors/index.rst`
- `docs/source/sensors/raycast_sensor.rst`
- `docs/source/sensors/rgbd_camera.rst`
- `docs/source/training/rsl_rl.rst`
- `docs/source/training/distributed_training.rst`
- `docs/source/training/motion_imitation.rst`
- `docs/source/training/cloud.rst`
- `docs/source/tutorials/cartpole.rst`
- `src/mjlab/__init__.py`
- `src/mjlab/envs/`
- `src/mjlab/managers/`
- `src/mjlab/scene/`
- `src/mjlab/entity/`
- `src/mjlab/sim/`
- `src/mjlab/actuator/`
- `src/mjlab/envs/mdp/`
- `src/mjlab/sensor/`
- `src/mjlab/terrains/`
- `src/mjlab/tasks/`
- `src/mjlab/rl/`
- `src/mjlab/scripts/`
- `scripts/demos/`
- `scripts/tools/`
- `tests/`

## Runtime inspection baseline

A private inspection environment installed `mjlab` from this checkout with the
CUDA-capable dependency variant and development tools. Private environment
paths and local installation details are intentionally omitted from this public
runtime skill. Verified public facts include:

- `mjlab` imports and reports distribution version `1.6.0`.
- `mujoco` `3.11.0`, `mujoco-warp` `3.11.0`, `warp` `1.14.0`, and `torch`
  with CUDA runtime import successfully in the inspection environment.
- CUDA smoke saw an NVIDIA GPU and allocated a tiny CUDA tensor.
- Built-in registry contained 12 task IDs including cartpole, velocity,
  tracking, and manipulation tasks.
- Installed console scripts included `train`, `play`, `demo`, `list-envs`,
  `viz-nan`, and `export-scene`.

## Refresh triggers

Refresh this skill if any of these change:

- mjlab package version, MuJoCo/MuJoCo Warp version, or torch/CUDA dependency
  variant.
- CLI entry points or Tyro parsing conventions.
- `ManagerBasedRlEnvCfg`, manager config classes, `SceneCfg`, `EntityCfg`,
  `SimulationCfg`, sensor configs, terrain configs, or RSL-RL config signatures.
- Built-in task IDs or task-family command/reward/sensor composition.
- Documentation for installation, distributed training, motion imitation,
  sensors, terrain, randomization, viewers, or NaN guard.
