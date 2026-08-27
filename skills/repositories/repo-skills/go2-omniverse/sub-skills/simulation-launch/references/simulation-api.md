# Simulation API and configuration

These facts are distilled from the repository's source modules. They are not a
replacement for a matching IsaacLab runtime inspection.

## Runtime flow

The launcher invokes `main.py`, which imports `omniverse_sim.run_sim`. The app
launcher is constructed before Isaac-dependent imports. The runtime then enables
selected OmniGraph/sensor extensions, creates a Gym environment from the task
and `UnitreeGo2CustomEnvCfg` or `G1RoughEnvCfg`, wraps it with the RSL-RL vector
environment, locates a checkpoint, and runs the policy loop.

The shipped inference path rebuilds an MLP actor from legacy RSL-RL checkpoint
keys under `model_state_dict` (`actor.*`). The configured hidden dimensions are
`[512, 256, 128]` with ELU activation for both Go2 and G1. A checkpoint from a
different architecture is not interchangeable merely because its filename
matches.

## Robot and terrain

- Go2 uses the IsaacLab Unitree asset and the custom environment overrides its
  joint-position action scale to `0.25`.
- G1 uses the bundled `robots/g1/g1.usd` through the local G1 articulation
  configuration. Its original configuration contains a machine-specific USD
  fallback; prefer the bundled asset path when operating the generated skill.
- Flat terrain uses a plane. Rough terrain uses the generated stair mix from
  the bundled terrain configuration. The scene also creates a height scanner,
  contact sensor, distant light, and an optional studio HDRI dome.
- `robot_amount` controls scene environment count; each instance gets its own
  ROS namespace and command entry.

## Control inputs

`cmd_vel` subscriptions map `linear.x`, `linear.y`, and `angular.z` into the
per-robot command dictionary. In the GUI, keyboard bindings use W/S/A/D/Q/E
for robot 0 and I/K/J/L/U/O for robot 1; key release zeros commands.

## Honest unknowns

The repository has no package metadata and no native test suite. IsaacLab
0.54.3 was unavailable during creation, so imports, task registration, policy
checkpoint compatibility, and full GPU launch behavior remain pending until a
matching stack is supplied.
