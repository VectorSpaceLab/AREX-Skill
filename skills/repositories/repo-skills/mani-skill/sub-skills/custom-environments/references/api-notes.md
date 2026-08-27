# API Notes

This page captures the concrete API surfaces that matter for custom ManiSkill task and robot authoring.

## Environment registration and base class

| API | Notes |
| --- | --- |
| `register_env(uid, max_episode_steps=None, override=False, asset_download_ids=[], **kwargs)` | Registers a `BaseEnv` subclass for gym creation. The decorator requires JSON-dumpable keyword defaults. |
| `BaseEnv.__init__(...)` | Common authoring inputs include `num_envs`, `obs_mode`, `reward_mode`, `control_mode`, `render_mode`, `sensor_configs`, `human_render_camera_configs`, `viewer_camera_configs`, `robot_uids`, `sim_config`, `reconfiguration_freq`, `sim_backend`, `render_backend`, `parallel_in_single_scene`, and `enhanced_determinism`. |
| `BaseEnv._load_agent(options, initial_agent_poses=None, build_separate=False)` | Default robot loading entry point. Use a safe pose that does not collide with scene objects. |
| `BaseEnv._load_scene(options)` | Load actors, articulations, lights, and reusable layouts here; do not put reset-time randomization here. |
| `BaseEnv._initialize_episode(env_idx, options)` | Reset only the selected vectorized envs and update states for `env_idx`. |
| `BaseEnv.evaluate()` | Return batched termination info. `success` and/or `fail` drive `terminated`. Returning `{}` is valid for tasks with no termination semantics. |
| `BaseEnv._get_obs_extra(info)` | Add task-specific observation fields. Gate privileged state with `self.obs_mode_struct.use_state`. |
| `BaseEnv.compute_dense_reward(obs, action, info)` | Optional dense shaping reward. |
| `BaseEnv.compute_normalized_dense_reward(obs, action, info)` | Normalize dense reward by a known max. |
| `BaseEnv.get_state_dict()` / `BaseEnv.set_state_dict(...)` | Add custom non-simulation state for exact replay and state restoration. |
| `BaseEnv.add_to_state_dict_registry(...)` / `remove_from_state_dict_registry(...)` | Needed for heterogeneous tasks that merge per-env objects into a single view. |
| `BaseEnv._default_sensor_configs` / `_default_human_render_camera_configs` | Camera definitions for task observations and human rendering. |
| `BaseEnv._default_sim_config` | Return `SimConfig`; use it to tune GPU memory and solver settings. |

## Building objects

| API | Notes |
| --- | --- |
| `scene.create_actor_builder()` | Create a batched actor builder for primitive or custom rigid objects. |
| `ActorBuilder.initial_pose` | Set before build to avoid load-time collisions. |
| `ActorBuilder.set_scene_idxs(...)` | Restrict an object to selected sub-scenes for heterogeneous tasks. |
| `ActorBuilder.build(name)` / `build_dynamic` / `build_static` / `build_kinematic` | Build the actor. Static bodies require a meaningful initial pose. |
| `scene.create_articulation_builder()` | Create a batched articulation builder for custom multi-link objects. |
| `ArticulationBuilder.create_link_builder(...)` | Add links and joints programmatically. |
| `ArticulationBuilder.initial_pose` | Set before build for safe loading. |
| `ArticulationBuilder.set_scene_idxs(...)` | Build per-scene articulation variants. |
| `ArticulationBuilder.build(name, fix_root_link=...)` | Build the articulation and register it. |
| `Pose.create_from_pq(p, q)` | Broadcasts a single pose component across a batch or combines batched `p` and `q`. |
| `Actor.merge(...)`, `Articulation.merge(...)`, `Link.merge(...)` | Create a single batched view over heterogeneous per-env objects. |

## Reusable scene builders

| API | Notes |
| --- | --- |
| `SceneBuilder.build(...)` | One-time layout construction. |
| `SceneBuilder.initialize(env_idx, ...)` | Reset-time state for selected envs only. |
| `SceneBuilder.build_configs` / `init_configs` | Optional layout variant lists that can be sampled per env. |
| `register_scene_builder(uid)` | Optional registration hook if you want to reuse a scene builder by id. |

## Camera and sensor notes

| API | Notes |
| --- | --- |
| `CameraConfig(uid, pose, width, height, fov, near, far, mount=None, shader_pack=...)` | Camera configuration used for sensors and human render views. |
| `sapien_utils.look_at(eye, target)` | Convenience helper for camera poses. |
| `_default_sensor_configs` | Use for task observation cameras. |
| `_default_human_render_camera_configs` | Use for render-only cameras. |

## Robot authoring notes

| API | Notes |
| --- | --- |
| `BaseAgent` | Base class for custom robots. |
| `register_agent()` | Exposes the robot by uid. |
| `uid` | Unique robot identifier. |
| `urdf_path` / `mjcf_path` | Source model to import. |
| `keyframes` | Named pose/qpos/qvel snapshots for setup and debugging. |
| `_controller_configs` | Dict of control modes to controller groups. Every active joint must be covered. |
| `_sensor_configs` | Mounted sensors and robot-relative cameras. |
| `urdf_config` | Link materials, collision tweaks, and friction tuning. |
| `fix_root_link` | Set `False` for floating/mobile embodiments when needed. |
| `disable_self_collisions` | Available, but simplify collisions first when possible. |

## Common controller families

- `PDJointPosControllerConfig`
- `PDJointPosMimicControllerConfig`
- `PDEEPoseControllerConfig`
- `PDEEPosControllerConfig`
- `PassiveControllerConfig`
- `PDBaseVelControllerConfig`

## Batching and reset notes

- `evaluate` and reward functions must return batched tensors.
- Use `env_idx` as the selection mask during partial resets.
- Use `self._batched_episode_rng` for reproducible randomization across CPU/GPU and vectorized resets.
- Use `torch.device(self.device)` when creating reset-time tensors.
- Keep `reconfiguration_freq` conservative unless the task really needs repeated rebuilds.
