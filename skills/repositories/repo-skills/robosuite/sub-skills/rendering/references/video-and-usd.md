# Video Recording and USD Export

This reference covers the safe offscreen video path and the optional USD / Isaac Sim export path.

## Offscreen video capture

The verified video pattern is:

1. create the env with `has_renderer=False`, `has_offscreen_renderer=True`, and `use_camera_obs=True`
2. set `robosuite.macros.IMAGE_CONVENTION = "opencv"` before env creation if the frames will be written with `imageio` or OpenCV-style consumers
3. read `obs[f"{camera}_image"]` from the observation dict
4. write MP4 output with `imageio`

Safe defaults for short debug clips:

- low image resolution
- a small number of timesteps
- a required explicit output path
- random actions within `env.action_spec`

The bundled `record_random_video.py` helper follows this pattern.

If you need a short reset-state clip, adapt the same offscreen pattern rather than relying on an external script.

## USD export and Isaac / Omniverse

USD export is optional and environment-dependent. Treat it as a reference path, not as a required core runtime capability.

Requirements and caveats:

- install `usd-core`, `pillow`, and `tqdm`
- use an external USD-capable app such as Isaac Sim or Blender to view the exported scene
- keep `online` and `shareable` mutually exclusive in `USDExporter`
- `camera_names` must refer to fixed cameras defined in the MuJoCo model
- if you are collecting human demos for USD export, route the capture workflow to `../teleoperation`
- `mujoco==3.1.1` plus `numpy<2` is called out by the demo script as a compatibility warning for correct USD rendering

Common USD entry points:

- `robosuite.utils.usd.exporter.USDExporter`
- `update_scene(data, camera=...)`
- `save_scene(filetype="usd")`

If you only need a quick visualization clip, prefer the offscreen video path over USD export.
