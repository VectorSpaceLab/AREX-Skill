# Rendering and viewer troubleshooting

Use the symptom to choose a branch. Keep model loading, physics stepping, and
pixel rendering separate: a successful model step does not prove that a display
or graphics backend is available.

## Headless machine opens no window

**Symptom:** a server/CI job hangs, raises a display/GL error, or never produces
an image after calling `env.mj_render()`.

**Cause:** `env.mj_render()` is the onscreen path. The base renderer calls
MuJoCo's passive viewer; it is not an offscreen API.

**Recovery:** use the safe bundled checker and explicitly choose offscreen:

```bash
python scripts/check_mujoco_xml.py \
  --xml MODEL.xml --render offscreen --frames 4 \
  --output-dir ./mujoco-check
```

This path never calls `mujoco.viewer`, writes `frame-0000.ppm` and subsequent
frames below the requested directory, and prints each output path. Keep
`--render none` for model-load/step-only checks. If offscreen construction still
fails with a GL/EGL/OSMesa error, the physics path may be healthy while the
machine lacks a usable MuJoCo rendering backend; install/configure the platform
rendering dependency according to the deployment environment, or classify
pixel rendering as blocked rather than switching to a window call.

## Raw XML fails before rendering

**Symptom:** `MjModel.from_xml_path` or the checker reports an XML parse,
missing include, missing mesh/texture, or asset-path error.

**Cause:** the XML is not self-contained in the current working context, an
include/asset is unavailable, or the model requires package assets that were
not installed/initialized.

**Recovery:** first rerun with `--render none`; this isolates model resolution
from graphics. Confirm the XML and all referenced assets are readable from the
consumer's intended working environment. For a MyoSuite environment, make sure
the installed package includes its model assets before debugging cameras. Do
not silently download or mutate optional assets from a runtime skill. Route
model XML generation or edits to model-editing/kinematics.

## Requested camera cannot be found

**Symptom:** a named-camera render raises a MuJoCo camera lookup error, or a
camera view is not the expected scene.

**Cause:** camera names are model-specific. `camera_id=-1` is the free camera;
it is not an alias for every named camera.

**Recovery:** use `camera_id=-1` to prove the renderer, then inspect the model's
camera names and pass an exact string. For the checker, use `--camera -1` or
`--camera NAME`. Do not reuse camera names from a different task family.

## Image shape or output is wrong

**Symptom:** a downstream encoder rejects an image, depth has the wrong shape,
or a file exists but is empty.

**Cause:** width/height are ordered as `width, height` in the render call but
arrays are shaped `(height, width, ...)`; depth/segmentation are separate
passes; a stale cached renderer may still use its initial viewport size.

**Recovery:** assert `rgb.shape[:2] == (height, width)` and inspect `dtype`.
Request only the passes needed. Use a fresh renderer/environment when changing
viewport sizes. For the checker, verify every printed PPM path has non-zero
size and that the PPM header reports the requested width and height.

## Depth or segmentation is unexpectedly a tuple

**Symptom:** code expects one image but receives `(rgb, depth)` or
`(rgb, depth, segmentation)`.

**Cause:** `MJRenderer.render_offscreen` returns a tuple whenever depth or
segmentation is requested, even if `rgb=False` (the RGB slot is then `None`).

**Recovery:** destructure based on requested flags:

```python
rgb, depth = renderer.render_offscreen(
    width=320, height=240, rgb=True, depth=True
)
```

Treat segmentation as labels, not as an RGB frame. Do not pass the declared
`RenderMode` enum as a `mode=` keyword to the current `MJRenderer`.

## State/time appears one step out of sync

**Symptom:** `env.time`, observations, and rendered geometry do not appear to
match after manually changing arrays or restoring a snapshot.

**Cause:** MyoSuite may maintain separate ground-truth and observed model/data
handles. `env.time` reads observed data. Direct qpos/qvel edits do not refresh
MuJoCo's derived buffers until forward dynamics; `set_env_state` also performs a
MuJoCo step while restoring.

**Recovery:** use `env.get_env_state()`/`set_env_state()` as the supported base
snapshot path; after raw edits call `mujoco.mj_forward` on the corresponding
model/data; compare `env.mj_data.time` and `env.obsd_mj_data.time` explicitly
when partial observation is enabled. Capture state after a known reset or step,
not midway through a callback.

## Visual observations are empty or stale

**Symptom:** `env_info["visual_dict"]` is `{}`, or a requested camera image is
missing even though rendering works directly.

**Cause:** visual extraction is opt-in for efficiency. `get_obs()` defaults to
`update_exteroception=False`; visual keys must also be configured, and learned
encoders require their optional packages.

**Recovery:** call `env.get_obs(update_exteroception=True)` or
`env.get_visuals(renderer=env.mj_renderer, visual_keys=...)`. Ensure keys follow
`rgb:CAMERA:HxW:ENCODER` and pair depth with `d:`. If only a direct RGB frame is
needed, bypass encoders and use `render_offscreen`.

## Onscreen viewer is paused or closes unexpectedly

**Symptom:** the viewer is visible but simulation does not continue, or Escape
causes cleanup and later rendering fails.

**Cause:** `MJRenderer.key_callback` toggles pause on the space key and marks a
user exit on Escape. `refresh_window()` synchronizes and waits while paused.

**Recovery:** press space to resume when a window is intentionally used; treat
Escape as terminal for that renderer and create a new environment for another
run. Never use this interactive path as a CI assertion.

## macOS `launch_passive` / `mjpython` error

**Symptom:** on macOS, a script that reaches `mujoco.viewer.launch_passive`
(or the MyoSuite environment viewer) fails with a message that the script must
run under `mjpython`, or the native viewer cannot initialize.

**Diagnostic branch:**

1. If a window is required, rerun the same entry point with the MuJoCo launcher,
   for example:
   `mjpython -m myosuite.utils.examine_env --env_name myoElbowPose1D6MRandom-v0`.
2. Ensure the `mjpython` executable and the Python environment containing
   MyoSuite/MuJoCo are the same installation; then retry from a GUI-capable
   session.
3. If no window is required, do not try to repair `launch_passive`: switch to
   the checker with `--render offscreen` (or `--render none`) and validate file
   output instead.

This is the documented macOS branch. Do not infer that `mjpython` is required
on Linux or that a Linux display failure has the same cause. A headless GL
failure and a macOS native-launcher failure are separate diagnoses.

## Offscreen pixels succeed but shutdown prints an EGL warning

**Symptom:** an offscreen frame and output file are valid, but process exit
prints an ignored `EGL`/`OpenGL` exception from a MuJoCo renderer destructor.

**Cause:** some MuJoCo graphics backends report cleanup errors while a renderer
or GL context is being garbage-collected after successful rendering. This is a
resource-cleanup symptom, not evidence that the pixels were never produced.

**Recovery:** explicitly close a renderer that your code created, keep rendering
objects in a controlled scope, and validate output shape and file size before
classifying the run. The bundled checker closes its renderer in a `finally`
block. If warnings persist in a long-lived service, treat backend cleanup as an
environment-specific gap and isolate rendering in a short worker process rather
than weakening the artifact check.

## MJX/JAX/CUDA confusion

**Symptom:** a CPU offscreen test is reported as proof of MJX/CUDA support, or
an import fails while trying to use an accelerator renderer.

**Cause:** base `mujoco.MjModel`/`MjData` and `MJRenderer` are not the MJX/JAX
execution path. Optional accelerator dependencies and device behavior have
separate contracts.

**Recovery:** record base CPU rendering as verified only for the tested model and
backend. Route JAX/MJX/CUDA installation, device probes, and performance checks
to the MJX sub-skill. Do not add an accelerator dependency merely to fix a
window or offscreen issue.
