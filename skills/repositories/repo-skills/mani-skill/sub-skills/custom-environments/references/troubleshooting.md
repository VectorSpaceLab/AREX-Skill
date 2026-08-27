# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Objects interpenetrate immediately after load | Initial poses are colliding or too close to the table/robot | Set safe `initial_pose` values before build, move reset-time randomization into `_initialize_episode`, and use static bodies when possible. |
| A static body is drifting or costs too much memory | The object was built as kinematic when it never needs to move | Use `build_static` instead of `build_kinematic` for fixed geometry. |
| Reset state does not replay exactly | A goal, sampled variant, or geometry-derived value was not added to the state dict | Override `get_state_dict` / `set_state_dict` and keep any Python-side cache in sync. |
| Heterogeneous envs break state restoration | Per-env objects were left in the registry instead of the merged view | Remove per-env objects from the state dict registry and register the merged actor/articulation instead. |
| Unsupported robot/controller combination | `SUPPORTED_ROBOTS` and the robot’s controller config do not match the task | Update the accepted robot list, cover every active joint with controllers, and check the action-space layout. |
| `evaluate` causes shape or batching errors | Scalars or unbatched booleans were returned | Return tensors of shape `(self.num_envs,)` for `success`, `fail`, and any info flags. |
| Success is never reached | The success predicate is too strict or uses the wrong frame | Check object/goal frame alignment, batch shapes, and any hidden state used by the reward or termination logic. |
| Camera images look empty or from the wrong angle | The camera pose or mount frame is wrong | Re-check `CameraConfig`, `sapien_utils.look_at`, and any `mount=` link on robot cameras. |
| Sensor observations are missing or mixed up | The sensor property returned the wrong structure | Return the task sensors from `_default_sensor_configs` and render-only cameras from `_default_human_render_camera_configs`. |
| GPU contact or patch buffers overflow | Too many contacts or too-small PhysX buffers | Increase `SimConfig.gpu_memory_config` values and simplify collision geometry if needed. |
| GPU sim becomes unstable after many objects are added | Solver settings or contact complexity are too aggressive | Reduce solver iterations, increase spacing, or simplify collision meshes. |
| Partial reset behaves strangely | Reset-time logic assumes a full env rebuild | Use `env_idx` as the reset mask and keep rebuild work out of `_initialize_episode`. |
| Frequent reconfiguration breaks vectorized resets | Rebuilds and partial resets are being mixed | Keep `reconfiguration_freq` at zero for normal vectorized tasks; only reconfigure when the task genuinely needs it. |
| Scene-builder state is inconsistent | Construction logic and reset logic were mixed | Put one-time object creation in `build()` and per-reset state in `initialize(env_idx)`. |
