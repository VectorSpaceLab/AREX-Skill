# Troubleshooting

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `Camera observations require an offscreen renderer` | `use_camera_obs=True` without `has_offscreen_renderer=True` | Enable offscreen rendering or disable camera observations. |
| Missing `*_image`, `*_depth`, or `*_segmentation_*` keys | Camera arguments were not enabled or were named incorrectly | Verify `camera_names`, `camera_depths`, and `camera_segmentations`, and match the camera name exactly. |
| Video frames look upside-down | OpenGL orientation was written directly to a video consumer that expects OpenCV orientation | Set `robosuite.macros.IMAGE_CONVENTION = "opencv"` before env creation or flip frames manually with `[::-1]`. |
| Depth values are in `[0, 1]` instead of metric units | Raw MuJoCo depth was used directly | Convert with `get_real_depth_map(sim, depth_map)` before geometric calculations. |
| Camera backprojection does not match the original point | Depth image orientation or transform inversion was inconsistent | Follow the `depth_map[::-1]` pattern from the camera transform smoke and invert `world_to_camera` before backprojection. |
| Segmentation keys are absent | `camera_segmentations` is `None` | Use one of `instance`, `class`, or `element`. |
| Segmentation masks show unexpected visual sites | Segmentation mode is active | Sites are shrunk away automatically in segmentation runs; do not expect site visualization in the same pass. |
| On-screen render smoke is skipped | No display is available | On-screen rendering requires a display-backed OpenGL session; use an offscreen smoke instead when `DISPLAY` and `WAYLAND_DISPLAY` are unavailable. |
| `TextureModder requires mujoco version 3.1.1` | Version mismatch with color randomization | Set `randomize_color=False` or use the supported MuJoCo version for this repo branch. |
| USD import or export fails | Optional `usd-core` / external app dependency is missing | Treat USD as optional, install the extra packages, and use a USD-capable viewer externally. |
| `invalid value for environment variable MUJOCO_GL` | Backend was set to an unsupported value | Use a valid platform-specific backend such as `egl` or `osmesa` on Linux, or a display-backed default when available. |

Quick diagnosis sequence:

1. print the env flags: `has_renderer`, `has_offscreen_renderer`, `renderer`, `use_camera_obs`
2. print the camera observation keys actually returned by `env.reset()`
3. check `robosuite.macros.IMAGE_CONVENTION`
4. verify the offscreen backend with the bundled smoke script
