# Task Authoring Notes

This reference turns the public custom-task tutorials and representative task code into a compact workflow for authoring new ManiSkill environments.

## Start point
- Use the bundled scaffold helper when you want a starter file that already includes the common hooks.
- Use this lifecycle checklist when you want the smallest supported hook set.
- Use the public package's cube-push, cube-pick, and peg-insertion task patterns as canonical tabletop examples.
- Use the robot-authoring notes in the API reference when the task needs a new robot or a mounted sensor.

## Canonical lifecycle

| Hook / property | Purpose | What belongs here |
| --- | --- | --- |
| `__init__` | Choose defaults and task constants | `robot_uids`, `robot_init_qpos_noise`, reward scale constants, scene-builder knobs, `reconfiguration_freq` |
| `_load_agent` | Spawn the robot in a safe pose | Call `super()._load_agent(...)` with a collision-free pose |
| `_load_scene` | Build static layout and task objects | Actor/articulation builders, scene builders, initial poses, hidden visual goals |
| `_initialize_episode` | Reset selected envs only | Batched randomization, pose/qpos changes, `self.table_scene.initialize(env_idx)` |
| `evaluate` | Decide success/fail and stash info | Batched boolean termination keys plus auxiliary info |
| `_get_obs_extra` | Add task observations | Goal/object poses, robot task-state, privileged info gated by `self.obs_mode_struct.use_state` |
| `compute_dense_reward` | Optional shaping reward | Reaching, placement, grasping, stability, staged rewards |
| `compute_normalized_dense_reward` | Normalize dense reward | Divide by the known max reward |
| `get_state_dict` / `set_state_dict` | Replay support | Custom goals, random geometry metadata, other non-sim state |
| `_default_sensor_configs` / `_default_human_render_camera_configs` | Observation and render cameras | `CameraConfig`, `sapien_utils.look_at`, mounted sensors |
| `_default_sim_config` | Simulation stability and memory | GPU memory limits, solver iterations, contact offsets |

## Good task patterns
- Primitive objects: `build_cube`, `build_box`, `build_sphere`, `build_red_white_target`, `build_twocolor_peg`.
- Dataset-backed assets: `actors.get_actor_builder(...)` and `articulations.get_articulation_builder(...)`.
- Shared layouts: subclass `SceneBuilder`, then split one-time build work from per-reset initialization.
- Heterogeneous simulation: build per-scene assets with `set_scene_idxs`, merge them with `Actor.merge` or `Articulation.merge`, and register the merged object in the state dict registry.
- Replay-safe tasks: store any goal parameters or geometry-derived metadata that do not live in simulation state.

## Reset and replay rules
- Randomize only in `_initialize_episode(env_idx, options)`.
- Use `len(env_idx)` as the batch size for partial resets.
- Use `Pose.create_from_pq` for batched object poses.
- Use `self._batched_episode_rng` when object identity or sampled geometry must be reproducible across CPU/GPU.
- Keep any Python-only cache synchronized with `set_state_dict`.
- If a task reconfigures frequently, avoid partial reset unless the task is intentionally single-env or CPU-only.

## Robot notes
- Declare the accepted robot set with `SUPPORTED_ROBOTS`.
- If you need a custom robot, author it first with `BaseAgent`, `register_agent`, keyframes, controllers, sensors, and link materials.
- Active joints must all be covered by the controller configuration.
- For floating or mobile robots, do not assume the default passive-force behavior is correct.

## Sensor notes
- Task cameras belong in `_default_sensor_configs`.
- Human-only cameras belong in `_default_human_render_camera_configs`.
- Mounted robot cameras are configured on the robot side with a `mount=` link.
- Keep sensor placement focused on the useful workspace; blank background and far-away geometry are often poor observation choices.

## Quick checklist
1. Safe initial poses.
2. Batched reset logic.
3. Batched `success` / `fail`.
4. Replay-safe custom state.
5. Camera placement validated.
6. GPU memory tuned if contacts grow.
