---
name: custom-environments
description: "Build custom ManiSkill tasks, custom robots, and reusable scene
  builders from public templates and runtime APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Custom Environments

Use this sub-skill when the task is to author a new ManiSkill task, custom robot, or reusable scene builder. It distills the public custom-task templates and representative task patterns into self-contained operating guidance, plus a bundled scaffold helper.

Start here:

- [references/task-authoring.md](references/task-authoring.md) for the custom-task lifecycle, batched reset rules, and replay-safe state design.
- [references/api-notes.md](references/api-notes.md) for `BaseEnv`, `register_env`, builders, sensors, robots, and controller surfaces.
- [references/troubleshooting.md](references/troubleshooting.md) for collisions, batching, replay, sensor, robot/controller, and GPU-memory failures.
- [scripts/scaffold_custom_task.py](scripts/scaffold_custom_task.py) to emit or validate a bundled tabletop custom-task scaffold.

Use this for:

- `BaseEnv` subclassing and `@register_env` setup
- scene loading, robot loading, reset randomization, reward shaping, success/fail evaluation, and replay-safe state
- custom cameras/sensors, observation augmentation, and robot/controller selection
- reusable `SceneBuilder` layouts, actor builders, and articulation builders
- writing a custom robot before using it in a task

Do not use this for:

- running built-in demos, inspecting a live environment, or benchmark execution -> [../environment-usage/](../environment-usage/)
- trajectory recording, replay/conversion, teleoperation, or motion planning -> [../trajectories-and-datasets/](../trajectories-and-datasets/)
- baseline training or benchmark-scale learning workflows -> [../learning-and-baselines/](../learning-and-baselines/)

Authoring loop:

1. Start from the bundled scaffold helper or the lifecycle checklist in the task-authoring reference.
2. Subclass `BaseEnv` and register it with `@register_env(...)`.
3. Declare supported robots with `SUPPORTED_ROBOTS` and choose the default `robot_uids`.
4. Load the robot in `_load_agent`; load actors, articulations, and reusable layouts in `_load_scene`.
5. Put only batched reset-time state changes in `_initialize_episode(env_idx, options)`.
6. Return batched `success` / `fail` keys from `evaluate`; keep extra info batched too.
7. Add task observations in `_get_obs_extra(info)` and gate privileged state with `self.obs_mode_struct.use_state`.
8. Add dense reward only when useful and normalize it in `compute_normalized_dense_reward`.
9. Override `get_state_dict` / `set_state_dict` for any non-simulation task state.
10. Move shared layouts into a `SceneBuilder` and call `initialize(env_idx)` on every reset.
11. Validate the skeleton before any runtime/demo/replay workflow; route those tasks to the sibling sub-skills.

Minimum implementation shape:

- `BaseEnv` subclass
- `register_env`
- `_default_sim_config`
- `_default_sensor_configs`
- `_default_human_render_camera_configs`
- `_load_agent`
- `_load_scene`
- `_initialize_episode`
- `evaluate`
- `_get_obs_extra`
- `compute_dense_reward`
- `compute_normalized_dense_reward`
- `get_state_dict`
- `set_state_dict`

Rules of thumb:

- Spawn every asset with a safe initial pose.
- Prefer static bodies when the object never needs to move; use kinematic only when you must reposition it later.
- Use `Pose.create_from_pq` for batched reset poses; it broadcasts single `p` or `q` inputs.
- Use `self._batched_episode_rng` for scene sampling that must be consistent across CPU/GPU and vectorized resets.
- Use `torch.device(self.device)` inside reset code when creating tensors.
- Keep `evaluate` and reward logic batched over `self.num_envs`.
- Use `SceneBuilder` for shared floors/tables/counters and call `initialize(env_idx)` on reset.
- For heterogeneous per-env assets, use `set_scene_idxs`, then `Actor.merge` / `Articulation.merge`, and register the merged object in the state dict registry.
- Tune `SimConfig.gpu_memory_config` and scene solver settings when contact counts grow.
- Avoid mixing partial reset with frequent reconfiguration unless the task is intentionally single-env or CPU-only.

Robot and controller selection:

- Use `SUPPORTED_ROBOTS` to declare which robots the task accepts.
- If authoring a custom robot, define its `uid`, URDF/MJCF path, keyframes, controller configs, mounted sensors, and link materials before using it in a task.
- Common controller families include `PDJointPosControllerConfig`, `PDJointPosMimicControllerConfig`, `PDEEPoseControllerConfig`, `PDEEPosControllerConfig`, `PassiveControllerConfig`, and `PDBaseVelControllerConfig`.
- For floating or mobile embodiments, cover every active joint group in the controller dictionary and only disable passive-force balancing when the embodiment needs it.

Bundled scaffold:

- `scripts/scaffold_custom_task.py emit --out OUT_DIR --env-id MyTask-v1 --class-name MyTaskEnv` writes a self-contained starter task and scene-builder skeleton.
- `scripts/scaffold_custom_task.py validate --path OUT_DIR` checks that the generated task has the expected hooks.
- The helper writes bundled template text; it does not read from or require the original repository checkout.

Troubleshooting summary:

- Bad initial poses or collisions during load/reset: set safe `initial_pose` values before build, keep reset-time randomization in `_initialize_episode`, and prefer static geometry when possible.
- Replay breaks because state is missing: override `get_state_dict` / `set_state_dict` for custom goals, sampled geometry metadata, or other non-sim state.
- Unsupported robot/controller choice: update `SUPPORTED_ROBOTS`, cover every active joint with controllers, and inspect the action-space layout.
- Missing `success` / `fail` keys or wrong batching: return batched tensors of shape `(self.num_envs,)`; `evaluate` may return `{}` only when the task truly has no termination semantics.
- Camera/sensor setup mistakes: define `_default_sensor_configs` and `_default_human_render_camera_configs`, use `CameraConfig`, and mount robot cameras on the intended link frame when the robot owns the sensor.
- GPU memory or contact buffer overflow: raise the relevant `GPUMemoryConfig` limits and, if needed, reduce collision complexity, solver iterations, or the number of simultaneously moving objects.
- Partial reset pitfalls: use `env_idx` as the batch selector and do not assume a full reset when only part of the vectorized env is being initialized.

Routes out:

- Environment creation, demo running, and visual inspection -> [../environment-usage/](../environment-usage/)
- Trajectories, datasets, teleoperation, replay, and motion planning -> [../trajectories-and-datasets/](../trajectories-and-datasets/)
- Learning baselines and benchmark training -> [../learning-and-baselines/](../learning-and-baselines/)
