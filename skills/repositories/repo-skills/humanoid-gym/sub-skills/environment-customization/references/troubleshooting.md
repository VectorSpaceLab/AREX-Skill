# Troubleshooting reference

Evidence used: `humanoid/envs/base/legged_robot.py`, `humanoid/envs/custom/humanoid_env.py`, `humanoid/envs/base/legged_robot_config.py`, the robot assets, and the installed inspection notes.

| Symptom | Likely cause | What to check | Fix |
|---|---|---|---|
| `Task with name: ... was not registered` | The module that calls `task_registry.register(...)` was never imported, the task name is wrong, or the CLI still uses the helper default `XBotL_free` | `humanoid/envs/__init__.py` and the task id passed to `--task` | Import the module that registers the task and pass the exact task id; keep `humanoid_ppo` registered |
| URDF/asset file not found | The asset path is wrong or the package install did not preserve `resources/` | `asset.file` resolution against the repo root and the `resources/robots/XBot/` tree | Use a fresh editable checkout or a package build that keeps the resource files |
| Foot/knee/base contact logic is wrong | The body-name substrings do not match the asset bodies or match too few/many bodies | `foot_name`, `knee_name`, `penalize_contacts_on`, and `terminate_after_contacts_on` | Make the substrings match the link names in the asset; these are substring filters, so inspect the full match set. For XBot-L the intended patterns are `ankle_roll`, `knee`, and `base_link` |
| `KeyError` on `default_joint_angles[name]` | A DOF name changed or the new asset has a joint not covered by the dict | The non-fixed joint list and the default-angle keys | Add exact default-angle keys for every actuated joint or collapse/fix the extra joint |
| PD gain prints `... were not defined, setting them to zero` | A DOF name does not match any stiffness/damping substring | `control.stiffness` and `control.damping` substring keys | Add a substring key for the new joint family so every actuated joint gets a gain |
| Observation or critic shape mismatch | `num_single_obs`, `frame_stack`, `num_observations`, `single_num_privileged_obs`, `c_frame_stack`, `num_privileged_obs`, or the noise slices were not updated together | `XBotLFreeEnv._init_buffers()`, `_get_noise_scale_vec()`, and `compute_observations()` | Update the full observation stack and the noise vector as one change |
| Reward scale exists but no term is applied | The scale name has no `_reward_<name>` method | `cfg.rewards.scales` versus the env methods | Add the method or zero the scale; `termination` is the special exception |
| `Terrain mesh type not recognised` | `mesh_type` is not one of the supported branches | `terrain.mesh_type` and `create_sim()` | Use `plane`, `heightfield`, or `trimesh` |
| `ModuleNotFoundError: No module named 'isaacgym'` | Isaac Gym Preview 4 is missing | The runtime import path versus static config parsing | Do static parsing with the bundled scripts; report runtime env instantiation as `BLOCKED_REQUIRED_BACKEND` until Isaac Gym is installed |
| Asset works in checkout but not after install | The install omitted robot resources | `resources/robots/XBot/{urdf,mjcf,terrain,meshes}` | Prefer an editable checkout or a package build that ships resource files |

## Quick recovery order

1. Run `scripts/summarize_xbot_config.py --repo-root <repo>` to confirm the config and resource layout.
2. Fix the asset names or config keys.
3. Re-run the summary script and, if needed, the gait solver.
4. Only after that, hand the task to the training/evaluation or sim2sim sub-skill if runtime execution is actually needed.
