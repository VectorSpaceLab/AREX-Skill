---
name: rendering
description: "Configure robosuite rendering, camera observations, transforms,
  offscreen capture, domain randomization, and optional USD/Isaac export paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Rendering

Use this sub-skill for rendering and camera-adjacent tasks in robosuite:

- choose `has_renderer` vs `has_offscreen_renderer`
- select `renderer="mujoco"` or `renderer="mjviewer"`
- request camera RGB, depth, and segmentation observations
- read and back-project camera transforms
- record short offscreen videos
- randomize cameras, lighting, textures, dynamics, and sensor noise
- follow optional USD / Isaac Sim export paths

Start with:

- [references/rendering-and-cameras.md](references/rendering-and-cameras.md)
- [references/domain-randomization.md](references/domain-randomization.md)
- [references/video-and-usd.md](references/video-and-usd.md)
- [references/troubleshooting.md](references/troubleshooting.md)

Bundled helpers:

- [scripts/offscreen_camera_smoke.py](scripts/offscreen_camera_smoke.py)
- [scripts/camera_transform_smoke.py](scripts/camera_transform_smoke.py)
- [scripts/record_random_video.py](scripts/record_random_video.py)

Do not handle here:

- `../environments` for task setup, horizons, reward flow, and general env creation
- `../teleoperation` for keyboard/SpaceMouse/DualSense capture and teleop video/USD collection
- `../modeling` for camera XML tuning and MJCF camera placement

Core rules:

1. `use_camera_obs=True` requires `has_offscreen_renderer=True`.
2. Depth observations are normalized; convert them with `get_real_depth_map` before metric use.
3. Segmentation observations appear only when `camera_segmentations` is enabled, with keys like `frontview_segmentation_instance`.
4. Set `robosuite.macros.IMAGE_CONVENTION = "opencv"` before env creation when writing video with `imageio` or OpenCV-style consumers.
5. Treat USD/Isaac export as optional and environment-dependent, not as a core verified runtime path.
