---
name: rendering-viewer-assets
description: "Choose and troubleshoot dm_control rendering backends, viewers,
  pixel observations, camera APIs, and optional Blender exporter workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# rendering-viewer-assets

Use this sub-skill when a task needs dm_control offscreen rendering, pixel observations, camera control, the interactive viewer, or safe guidance for the optional Blender MuJoCo exporter.

Do not use this sub-skill for non-rendering Control Suite rollouts; route those to [`../suite-rl-workflows/SKILL.md`](../suite-rl-workflows/SKILL.md). Route raw MJCF/MuJoCo model construction to [`../mjcf-mujoco-models/SKILL.md`](../mjcf-mujoco-models/SKILL.md), and custom Composer environment/task lifecycle work to [`../composer-environments/SKILL.md`](../composer-environments/SKILL.md).

## First decisions

1. Identify the rendering target:
   - Offscreen RGB/depth/segmentation arrays: use `physics.render(...)` and probe `MUJOCO_GL` before building the workflow.
   - RL pixel observations: validate a backend first, then wrap with `dm_control.suite.wrappers.pixels.Wrapper`.
   - Interactive window: use `dm_control.viewer.launch(...)`; it requires GLFW and a real display.
   - Blender export: treat as optional, external-Blender, documentation-only unless the user explicitly accepts Blender add-on installation risks.
2. Choose a backend before importing dm_control rendering modules. If `MUJOCO_GL` is unset, dm_control tries GLFW, then EGL, then OSMesa. Explicit values are `glfw`, `egl`, and `osmesa`; EGL also accepts `MUJOCO_EGL_DEVICE_ID` for selecting a GPU device.
3. Do not promise that every backend is installed. During construction, a headless EGL render probe passed, OSMesa failed because the OSMesa/OpenGL library was missing or unusable, and GLFW failed in a display-less headless session.
4. Install public packages only: use `pip install dm_control` for released packages, or `pip install git+https://github.com/google-deepmind/dm_control.git` for unreleased source snapshots. Editable installs are not supported by dm_control.

## Bundled operating files

- Read [`references/rendering-viewer-reference.md`](references/rendering-viewer-reference.md) when choosing a backend, calling `physics.render`, adding pixel observations, or adapting a viewer launcher.
- Read [`references/blender-exporter-reference.md`](references/blender-exporter-reference.md) when a user asks about exporting Blender assets to MuJoCo/MJCF, or before deciding that Blender work should be avoided.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when rendering, PyOpenGL, pixel-wrapper, viewer, EGL/OSMesa/GLFW, or Blender add-on errors appear.
- Run [`scripts/render_backend_probe.py`](scripts/render_backend_probe.py) in a fresh Python process to test `default`, `egl`, `osmesa`, or `glfw` with a tiny installed-package render.
- Run [`scripts/viewer_launch_template.py`](scripts/viewer_launch_template.py) as a safe dry-run template for suite or manipulation viewer launchers; it opens a GUI only when `--launch` is explicitly supplied.

## Minimal operating pattern

```bash
python scripts/render_backend_probe.py --backend egl --height 48 --width 64
```

If the probe succeeds, use the same backend selection for the downstream render/pixel-observation process. If it fails, follow the failure-specific route in [`references/troubleshooting.md`](references/troubleshooting.md) instead of changing unrelated suite, MJCF, or Composer logic.
