# Rendering, viewer, pixel, and Blender troubleshooting

Rendering failures are usually backend/environment issues, not Control Suite, MJCF, or Composer logic issues. Set `MUJOCO_GL` before imports, run a small probe in a fresh process, and only then debug higher-level code.

## Quick triage

```bash
python scripts/render_backend_probe.py --backend egl
python scripts/render_backend_probe.py --backend osmesa
python scripts/render_backend_probe.py --backend glfw
```

Use the first successful backend for offscreen rendering. Use GLFW only when an interactive window and display are available.

## Symptom matrix

| Symptom | Likely cause | What to do |
|---|---|---|
| `GLFWError` mentioning missing `DISPLAY`, X11, or context initialization | GLFW was selected or tried on a headless machine | For offscreen work, run a fresh process with `MUJOCO_GL=egl` or `MUJOCO_GL=osmesa`. For `dm_control.viewer`, provide a real display/windowing setup; the viewer requires GLFW. |
| `RuntimeError: No OpenGL rendering backend is available` | No backend imported successfully, or an invalid backend was selected | Check `MUJOCO_GL` spelling. Probe `egl`, `osmesa`, and `glfw` separately. Install the required system OpenGL/EGL/OSMesa/GLFW libraries for the selected backend. |
| OSMesa import failure with `NoneType` / `glGetError` | OSMesa/OpenGL library is missing or incompatible | Do not expect pip to fix the system library. Use EGL if available, or install the host's OSMesa/OpenGL packages. Run the probe again in a new process. |
| EGL fails to initialize | EGL driver or device selection problem | Set `MUJOCO_GL=egl` before import. If multiple devices exist, set `MUJOCO_EGL_DEVICE_ID=0` or another valid ID. Check that the host driver supports headless EGL/`EXT_platform_device`. |
| Changing `MUJOCO_GL` inside a notebook or long-running process has no effect | Backend was already imported and cached | Restart the Python process/kernel. Backend selection must happen before importing dm_control rendering, `mujoco`, or PyOpenGL modules. |
| PyOpenGL imports the wrong platform | `PYOPENGL_PLATFORM` or previous imports conflict with the intended backend | Start a fresh process. Prefer `MUJOCO_GL=<backend>` and avoid setting `PYOPENGL_PLATFORM` manually unless the host's OpenGL stack requires it. |
| `ValueError` about image width/height greater than framebuffer dimensions | Requested render size exceeds the model's offscreen buffer | Reduce `height`/`width`, or increase MJCF `<visual><global offwidth="..." offheight="..."/></visual>` before compiling the model. |
| `ValueError` from overlays or render flags with depth/segmentation | Incompatible `physics.render` options | Use overlays and `render_flag_overrides` only for RGB renders. Run separate renders for depth or segmentation. |
| `ValueError` for invalid `camera_id` | Camera index/name does not exist in the model | Use `camera_id=-1` for the free camera, or inspect the model's camera names/IDs and select a valid fixed camera. |

## GLFW and viewer failures

`dm_control.viewer.launch(...)` is an interactive GUI path. It can hang or fail in CI, SSH sessions without display forwarding, containers, and notebooks.

Actions:

1. Run `python scripts/viewer_launch_template.py ...` without `--launch` first. Dry-run validates loader and policy shape without importing the viewer.
2. Only add `--launch` on a machine with a real display/windowing setup.
3. Use `MUJOCO_GL=glfw` only for the launched viewer process.
4. If the process appears to hang, check whether a GUI window is open or blocked behind another window. Close the window to terminate the event loop.
5. For noninteractive output, replace the viewer with `physics.render(...)` under EGL or OSMesa.

## EGL device selection

Use EGL for headless hardware rendering when the driver supports it.

```bash
MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=0 python scripts/render_backend_probe.py --backend egl
```

Notes:

- Device IDs are host-specific. Try another ID only if the current one fails and you know multiple EGL-capable devices exist.
- If a process already imported rendering modules with another backend, start a new process.
- If EGL fails even on device 0, inspect driver/container GPU visibility before changing dm_control code.

## Pixel wrapper failures

`dm_control.suite.wrappers.pixels.Wrapper` calls `env.physics.render(...)` during initialization to construct the observation spec. A backend failure can therefore occur before `env.reset()`.

Actions:

1. Probe the intended backend with `scripts/render_backend_probe.py`.
2. In the pixel-wrapper process, set the same backend before imports.
3. Start with small dimensions such as `height=84, width=84` and `camera_id=-1`.
4. If a fixed camera is required, verify that the selected suite/manipulation model defines that camera.
5. If `pixels_only=False`, ensure `observation_key` does not collide with an existing observation key.
6. If the user needs RL rollout logic after rendering works, route to `../suite-rl-workflows/SKILL.md`.

## PyOpenGL import issues

Common patterns:

- Errors importing `OpenGL.EGL`, `OpenGL.osmesa`, or GL functions usually indicate a missing system library or a platform mismatch.
- Pip packages can provide Python wrappers, but the host still needs the native OpenGL/EGL/OSMesa/GLFW libraries.
- Reusing the same Python process across backend attempts can keep stale module state.

Actions:

1. Test each backend in a fresh command-line process.
2. Keep `MUJOCO_GL` as the main selector.
3. Avoid mixing notebook cells that import dm_control before backend variables are set.
4. Prefer a deterministic backend (`egl` or `osmesa`) for headless jobs instead of relying on default auto-selection.

## Blender add-on risks

The Blender exporter is optional and external to normal dm_control rendering.

Risks:

- The exporter preparation script mutates an add-on folder by copying files and rewriting imports.
- Installing/enabling a Blender add-on can modify the user's Blender preferences or add-on directory.
- Exporting with scaling transforms can modify the Blender scene and is not automatically undone.
- Mesh splitting, double-sided materials, and legacy mesh formats can affect mass, inertia, and compatibility.

Actions:

1. Do not run exporter preparation by default.
2. Ask for explicit user consent before any Blender add-on installation or mutation.
3. Work only on disposable copies of Blender files and output folders.
4. Validate generated MJCF with dm_control/MuJoCo before using it in RL or control tasks.
5. If the user only needs offscreen rendering, pixel observations, or a viewer, avoid Blender entirely.
