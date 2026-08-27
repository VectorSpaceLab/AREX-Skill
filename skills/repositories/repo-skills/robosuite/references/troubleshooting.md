# Troubleshooting

## When to read

Read this for cross-cutting robosuite failures before drilling into a workflow-specific sub-skill. For deeper fixes, route to the relevant sub-skill troubleshooting reference.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: robosuite` | Package is not installed in the active Python | Install `robosuite` or install the local checkout with `python -m pip install -e .`, then rerun `python -c "import robosuite"`. |
| Warnings about missing `macros_private.py` | Optional private macro override file is absent | This is not fatal. Use default macros unless you need local overrides such as image convention or GPU rendering flags. |
| Warning about missing `robosuite_models` | Optional external model package is not installed | Core built-in robots still work. Install `robosuite-models` only when the task explicitly needs external robot assets. |
| Warning about missing `mink` or WholeBodyMinkIK | Optional third-party controller dependency is absent | Core controllers still work. Install `mink==0.0.5` only for the third-party whole-body Mink IK example. |
| `pip check` reports broken requirements | Environment contains incompatible dependency versions | Fix the active environment first; do not debug robosuite behavior until dependency metadata is consistent. |
| Windows error about missing `mujoco.dll` | MuJoCo DLL is not visible where robosuite expects it | Follow the Windows installation guidance: confirm `import mujoco`, locate the MuJoCo package, and copy or expose the DLL as needed. |

## Environment and controller setup

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Environment X not found` | Wrong task name or capitalization | Inspect `suite.ALL_ENVIRONMENTS`; use names like `Lift`, `TwoArmLift`, `PickPlaceCan`. |
| Two-arm env refuses robot list | `robots` and `env_configuration` are inconsistent | Use two separate robot names with `opposed` or `parallel`, or one supported bimanual/single-robot configuration. |
| Action dimension mismatch | Controller config, gripper type, or part name does not match the robot | Use `sub-skills/controllers/scripts/print_action_info.py` to print action split indexes before building actions. |
| Controller JSON fails to load | Missing `type`, `body_parts`, or unknown controller name | Use `sub-skills/controllers/scripts/validate_controller_config.py` and compare the config with `controller-configs-and-actions.md`. |
| `done` does not mean task success | robosuite episodes normally end at the horizon, not success | Inspect rewards or task success conditions separately from `done`. |

## Rendering and cameras

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Camera observations fail | `use_camera_obs=True` without offscreen renderer | Set `has_offscreen_renderer=True` or disable camera observations. |
| EGL/GLFW/OpenGL error on headless host | MuJoCo GL backend is not configured | Try `MUJOCO_GL=egl` for GPU-backed Linux offscreen, or `MUJOCO_GL=osmesa` if a software backend is available. |
| On-screen viewer fails | No display or wrong viewer stack | Use headless smoke first; on macOS, viewer-backed scripts may need `mjpython`. |
| Video writer cannot write MP4 | `imageio` is installed without an FFmpeg backend | Install an FFmpeg-capable backend such as `imageio[ffmpeg]` or choose a supported image output format. |
| Depth values look normalized | Raw MuJoCo depth map was used | Convert with `get_real_depth_map` before metric calculations. |
| Domain randomization color path fails with TextureModder version error | This repo's TextureModder path expects `mujoco==3.1.1` for color randomization | Set `randomize_color=False` unless you intentionally use the compatible MuJoCo version. |

## Teleoperation and demonstrations

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Keyboard input ignored | Viewer window is not focused or viewer path is unsupported | Focus the viewer; on macOS use the documented `mjpython` path when needed. |
| SpaceMouse/DualSense import fails | Optional `hidapi` dependency is missing | Install `hidapi`; confirm the device is visible and not owned by another app. |
| DualSense permission denied on Linux | Missing udev rules or root-only HID access | Add appropriate game-device udev rules or run under a context that can open the controller. |
| Demo HDF5 lacks expected groups or attrs | Dataset is malformed or incomplete | Use `sub-skills/teleoperation/scripts/inspect_demo_hdf5.py` to inspect `data` attrs and demo group datasets. |
| Action playback drifts | Open-loop playback is not portable across machines | Use state playback for exact reproduction. Treat action playback as approximate and same-machine only. |

## Modeling and assets

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MJCF compile error | Invalid XML, missing asset, bad mesh/inertia, or wrong relative path | Use `sub-skills/modeling/scripts/compile_mjcf_model.py` on the XML file and fix the first MuJoCo error. |
| Custom robot gripper fails to mount | Missing end-effector body or wrong naming convention | Use `sub-skills/modeling/scripts/check_custom_robot_model.py` and inspect body-part joint grouping. |
| Object placement behaves oddly | Missing object sites or invalid sampler ranges | Ensure `bottom_site`, `top_site`, and `horizontal_radius_site` exist and sampler ranges are collision-safe. |

## Fast diagnosis order

1. Run `scripts/check_install.py --skip-optional-imports` to verify imports and a headless env.
2. Run `scripts/inspect_registry.py` to confirm the task, robot, gripper, base, and controller names.
3. If actions are involved, run `sub-skills/controllers/scripts/print_action_info.py`.
4. If cameras are involved, run `sub-skills/rendering/scripts/offscreen_camera_smoke.py`.
5. If demonstrations are involved, run `sub-skills/teleoperation/scripts/inspect_demo_hdf5.py`.
6. If MJCF assets are involved, run `sub-skills/modeling/scripts/compile_mjcf_model.py` or `check_custom_robot_model.py`.
