# Rendering troubleshooting and recovery

Use this reference after the upstream molecule/style/annotation workflow has
succeeded. The goal is to isolate scene, host, output, and compositor failures
without rebuilding molecular data unnecessarily. The guidance targets
MolecularNodes 5.2.0 with Blender/bpy 5.2. It does not verify a UI, viewport,
or GPU device.

## Preflight before a render

Record the host mode and read back the scene state. A useful preflight is:

```python
import bpy

scene = bpy.context.scene
assert scene is not None
assert scene.camera is not None
print({
    "background": bpy.app.background,
    "engine": scene.render.engine,
    "camera": scene.camera.name,
    "resolution": (
        scene.render.resolution_x,
        scene.render.resolution_y,
        scene.render.resolution_percentage,
    ),
    "frame": scene.frame_current,
    "range": (scene.frame_start, scene.frame_end),
    "filepath": scene.render.filepath,
})
```

For a `Canvas`, additionally read `canvas.engine.name`, `canvas.samples`,
`canvas.resolution`, `canvas.render_scale`, `canvas.transparent`,
`canvas.frame_range`, `canvas.frame`, `canvas.camera.rotation`,
`canvas.camera.lens`, and `canvas.passes`. Set values explicitly when comparing
renders; template defaults and a previously loaded `.blend` are not a stable
experiment specification.

Before a destructive reset or load, save a copy of the current `.blend` and
record the intended entity names and output destination. After reset/load,
reacquire those objects and rebuild the required world/compositor graph. Do not
keep Python references to datablocks that the operation replaced.

## Context: interactive, background, and headless

There are three useful operating contexts:

- **Interactive UI:** a `VIEW_3D` area is normally available. `frame_object()`
  and `frame_view()` use Blender's `view3d.camera_to_view_selected` operator,
  temporarily change selection, and restore the prior selection. The operator
  still depends on a valid window/area/region context; a different active area
  can make it fail even in an interactive session.
- **Blender background mode:** `bpy.app.background` is true and no viewport
  redraw or OpenGL context should be assumed. Do not use `bpy.ops.render.opengl`
  or UI redraw operators. `snapshot()` and `animation()` use the ordinary
  render operator and can consume a scene whose camera and geometry were
  prepared in advance. The MolecularNodes viewport draw handler for annotations
  is not a background feature; render-time annotation generation is a separate
  path.
- **Headless `bpy` module:** treat it like background mode. It is suitable for
  data inspection and file rendering when the scene is fully configured, but it
  does not prove interactive viewport behavior or GPU availability.

If framing fails in background/headless mode, do not keep retrying the same
viewport operator. Configure the camera through the Blender data API (known
location, lens, clip planes, and an Euler/track-quaternion orientation) or
prepare and save the camera in an interactive session, then render headlessly.
Validate `scene.camera` and its transform before starting output. No viewport
framing or redraw claim should be made from a headless check.

The constructor and the render helpers still need a valid active scene and
camera. `Canvas(template=None)` preserves the current scene; use an explicit
`scene_reset(template=None)` only when a factory reset is intended.

## Failure isolation table

| Symptom | First checks | Recovery |
| --- | --- | --- |
| `Camera` property fails or render is empty | `scene.camera`, camera `type`, clip planes, camera transform, object visibility in the active view layer | Assign/prepare a camera, widen `clip_end`, reframe in a valid UI context or set the transform through data API, then read back the camera |
| `frame_object()` or `frame_view()` poll error | Host is background/headless, no `VIEW_3D` context, object is not linked to the active scene, or the bounding box is invalid | Stop using the viewport operator; prepare a camera data-block and render from it, or run framing in an interactive area and save the scene |
| Molecule/style is invisible in EEVEE or Cycles | Active engine, `hide_render`, current frame, style output socket, and engine-specific style/material compatibility | Switch to a style compatible with the selected engine, set the intended frame, ensure the object is render-visible, and re-read engine/material state |
| Cycles fails before rendering | Device request, unsupported material/node, samples/denoise setting, or missing host feature | Use `mn.scene.Cycles(device="CPU")` for a CPU device selection, verify `canvas.engine.device`, reduce samples for a smoke render, and isolate the material/style. CPU selection does not guarantee all Cycles features succeed |
| Render is black, flat, or unexpectedly dark | World node graph, `background`, `hdri_strength`, lights, exposure/gamma/look, view transform, and transparent film | Confirm the world output is connected, restore or rebuild the expected world graph, choose explicit color management, and only then adjust lighting/materials |
| `background` or `hdri_strength` raises `ValueError` | `WorldTree.reset()` removed `MN_world_shader` | Rebuild a world shader intentionally or reload a template; do not assume the convenience sockets survive a world reset |
| Custom compositor has no effect | The reset context manager was not entered, output is not connected, compositing is disabled, or required render pass is off | Use `with canvas.compositor.reset() as (image, output): ...`, connect the chain, enable needed `canvas.passes`, and add a final output/annotation overlay explicitly |
| Annotation overlay disappears | Compositor was reset, `add_annotations()` was not called, annotation is hidden/invalid, current frame is stale, or render handlers cannot run | Re-add annotations after the custom chain, set the frame with `canvas.frame`, check annotation visibility/input errors, and inspect the saved file rather than a viewport overlay |
| `canvas.passes = ...` raises `ValueError` | A pass name is not in the Canvas allow-list | Use only `combined`, `z`, `mist`, `normal`, `position`, `vector`, `diffuse_color`, `emit`, `environment`, or `ambient_occlusion`; the failed assignment does not partially change toggles |
| Still path copy fails | Destination parent does not exist, destination is not writable, or file format is unsupported by the host | Create the parent directory before `snapshot()`, use an exact Blender image format such as `PNG`, and retry in a writable location |
| Still file is missing or zero bytes | Render operator failed, output copy was interrupted, or the destination was checked before the call returned | Treat the render as failed, inspect the exception/console, rerun after correcting the scene, then validate the destination file |
| Animation rejects the range | `frame_end < frame_start`, non-integer range values, or the entity has no valid frame updates | Use an inclusive integer range, set `canvas.frame_range`, and verify a still at both endpoints before encoding video |
| Animation renders frames but no MP4 | FFmpeg/MPEG-4 encoding failure, disk space, invalid frame images, or an interrupted temporary sequence | Run a short low-scale range, verify PNG output and available encoding support, clean any leftover temporary sequence strip after an interruption, and restore scene output/range settings before retrying |
| Render changes after a reset/load | Entity, camera, world, compositor, or node-socket references point to the old scene | Reacquire every Blender/MolecularNodes reference and explicitly reapply engine, camera, world, compositor, passes, color management, frame, and output settings |

## Still output contract and validation

`canvas.snapshot(path, frame=..., file_format=...)` returns `None`. It renders a
single frame to a temporary host file, temporarily selects `IMAGE` media and the
requested image format, and copies the result to the exact supplied `path`.
Blender's extension handling is used for the temporary file; the destination
path is not a request to append an extension. With no path, the method only
attempts notebook display when display support is available, so a no-path call
is not a durable artifact contract.

Prepare the destination yourself and validate after the call:

```python
from pathlib import Path

out = Path("renders/preview.png")
out.parent.mkdir(parents=True, exist_ok=True)
canvas.snapshot(out, frame=1, file_format="PNG")
if not out.is_file() or out.stat().st_size == 0:
    raise RuntimeError(f"Still output was not written: {out}")
```

Use a format supported by the active Blender host. PNG is the portable smoke
render choice. If alpha matters, set `canvas.transparent` and use a format that
preserves alpha; a transparent film does not disable world lighting. For a
stronger check, decode the finished file with an available image reader and
confirm its dimensions/format. The written file is authoritative; do not use a
viewport screenshot or assume a raw `Render Result` pixel read is identical to
the encoded file.

A requested frame temporarily drives `scene.frame_set()` so trajectory/entity
state can update during rendering. Read back the current frame and, if later
operations depend on it, explicitly set `canvas.frame` again after the call.

## Animation output contract and cleanup

`canvas.animation(path, frame_start=..., frame_end=..., render_scale=...)` also
returns `None`. It renders inclusive, zero-padded PNG frames in a temporary
directory, creates a temporary image strip, encodes an MPEG-4/FFMPEG video, and
copies the resulting MP4 to the exact supplied `path`. It uses the scene FPS;
set `canvas.fps` before encoding. `render_scale` is a percentage of the base
resolution and does not reframe the camera.

Validate the MP4 just as strictly as a still:

```python
video = Path("renders/preview.mp4")
video.parent.mkdir(parents=True, exist_ok=True)
canvas.animation(video, frame_start=1, frame_end=3, render_scale=25)
if not video.is_file() or video.stat().st_size == 0:
    raise RuntimeError(f"Animation output was not written: {video}")
```

On normal completion, temporary render settings (output path, frame range,
current frame, lock-interface state, and scale) are restored and the temporary
image strip is removed. An external interrupt or render/encoder exception can
occur before strip removal. Recovery is:

1. stop launching new renders;
2. inspect the scene's sequence editor for a leftover temporary image strip and
   remove it through the data API if present;
3. restore the intended `filepath`, `resolution_percentage`, current frame, and
   frame range explicitly;
4. render one still at a low scale; and
5. rerun a short inclusive animation to a new destination.

Do not treat the presence of a partially written file as a successful video.
When available, an independent media probe can verify that the MP4 has readable
streams and the expected frame rate; it is supplemental to the file existence
and non-zero-size gate.

## Minimal recovery loop

For a failed render, return to a known small configuration instead of changing
many variables at once:

```python
import molecularnodes as mn

canvas.engine = mn.scene.EEVEE(samples=8, raytracing=False)
canvas.resolution = (160, 120)
canvas.render_scale = 100
canvas.frame_range = (1, 1)
canvas.frame = 1
canvas.transparent = False
canvas.view_transform = "Standard"
canvas.exposure = 0.0
canvas.gamma = 1.0
canvas.passes = ["combined"]
```

Then verify the camera and render one PNG. If that succeeds, add back one
change at a time: the intended engine, samples, color management, world, custom
compositor, annotations, resolution, and finally animation. Preserve the failed
scene and exception details outside the runtime skill; do not hide unresolved
host, data, or encoding limits behind a claim of success.
