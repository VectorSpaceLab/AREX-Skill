---
name: scene-and-rendering
description: "Configure MolecularNodes Blender scenes, cameras, engines,
  materials, compositor/world settings, and still or animation renders with
  host-aware recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Scene and rendering

Use this sub-skill when the scene already contains MolecularNodes entities and the
next task is to make a reproducible Blender view, render, snapshot, animation, or
annotation overlay. The runtime is a Blender 5.2-compatible `bpy` host; ordinary
Python is useful for planning and validation but is not a substitute for Blender.

## Route before editing

- For installation, add-on registration, or package/backend diagnosis, use
  [setup-and-import](../setup-and-import/SKILL.md).
- For loading molecules, styles, selections, or direct style-node edits, use
  [molecules-and-styles](../molecules-and-styles/SKILL.md); this skill only shows
  the material and render settings needed after a style exists.
- For trajectory playback or annotation creation, use
  [trajectories-and-annotations](../trajectories-and-annotations/SKILL.md).
- For density, CellPack, or ensemble-specific scene contents, use
  [density-and-ensembles](../density-and-ensembles/SKILL.md).

The detailed contracts are in [Canvas API](references/canvas-api.md),
[engines and compositor](references/cameras-engines-and-compositor.md), and
[rendering recovery](references/rendering-troubleshooting.md).

## Operating contract

**Inputs**

- A live Blender scene and active camera, plus a `bpy.types.Object`,
  `MolecularEntity`, or entity view/bounding box to frame.
- Optional render choices: engine (`"EEVEE"`, `"CYCLES"`, `mn.scene.EEVEE`, or
  `mn.scene.Cycles`), `(width, height)`, transparency, frame/range, output path,
  image format, world/compositor edits, and an existing style material socket.
- An explicit host mode: interactive UI, Blender background mode, or the
  headless `bpy` module. Do not assume a viewport or a GPU from package facts.

**Outputs**

- A configured `mn.Canvas` and camera whose settings can be read back from
  `canvas.scene`, `canvas.camera`, and the engine object.
- A still copied to the exact requested `snapshot()` path, or an MP4 copied to
  the exact requested `animation()` path; callers create parent directories and
  validate non-zero output. With no path, display is notebook-dependent.
- A validated compositor/world graph and, when enabled, a composited
  `mn_annotations` overlay.

## Safe default workflow

1. Make the host mode explicit and create `canvas = mn.Canvas(engine="EEVEE",
   resolution=(320, 240), transparent=False, template="Molecular Nodes")`.
   The default/template constructor path is destructive. `template=None` on the
   constructor preserves the current scene; call `canvas.scene_reset(None)` only
   for an intentional Blender factory-startup reset. Canvas registers the add-on,
   installs assets, selects the engine, creates a camera helper, and installs the
   annotation compositor.
2. Obtain the already-created entity from the molecule/style workflow. Do not
   import structure or trajectory data here.
3. Set reproducible settings before framing: `canvas.fps`,
   `canvas.frame_range`, `canvas.frame`, `canvas.render_scale`,
   `canvas.samples`, color management, `canvas.world.background`,
   `canvas.transparent`, and the required `canvas.passes`.
4. In an interactive context with a valid 3D View, frame with
   `canvas.frame_object(entity, viewpoint="front")` or
   `canvas.frame_view(entity.get_view(...), viewpoint="front")`. In background
   or headless mode, prepare the camera with the data API or a saved scene;
   these helpers depend on Blender's view3d operator. Re-frame after changing
   the lens if a new camera distance is desired.
5. Create the output parent, render with
   `canvas.snapshot(path, frame=..., file_format="PNG")`, and validate a
   non-zero file plus the scene/camera/frame read-back. Use
   `canvas.animation(path, frame_start=..., frame_end=..., render_scale=...)`
   for MP4 output and apply the same file validation.

## Camera and engine decisions

- Named viewpoints are `default`, `front`, `back`, `top`, `bottom`, `left`, and
  `right` (case-insensitive). `canvas.camera.rotation` is an XYZ degree tuple;
  `canvas.camera.set_viewpoint()` accepts a named view or a custom Euler sequence
  in radians. Prefer the degree property when writing human-readable angles.
- Use EEVEE for a fast preview with explicitly set samples/ray-tracing and
  color settings. Use Cycles when path-traced lighting or a Cycles-only style is
  required; request `mn.scene.Cycles(device="CPU")` and read back the device for
  a CPU device selection. This does not claim GPU availability, speed, or
  universal material compatibility.
- Materials are independent node graphs. Choose a preset or custom material only
  after the style socket exists. See [engines and compositor](references/cameras-engines-and-compositor.md).

## Validation and recovery gates

- Read back `canvas.resolution`, `canvas.render_scale`, `canvas.frame_range`,
  `canvas.frame`, `canvas.engine.name`, `canvas.samples`, camera rotation/lens,
  and `canvas.passes` before rendering.
- `canvas.passes = [...]` is a replacement set, not an additive update; unknown
  pass names must be corrected after the resulting `ValueError`.
- `canvas.compositor.reset()` is a context manager; enter it with `with ...`.
  Its reset removes annotations until `canvas.compositor.add_annotations()` is
  called. After `canvas.world.reset()`, the `background` and `hdri_strength`
  convenience sockets are unavailable until the template world node is rebuilt
  or reloaded.
- In background/headless mode, do not use viewport OpenGL rendering or UI
  redraw operators, and do not assume camera framing helpers have a 3D View.
  Prefer a prepared data-API camera plus `snapshot()`/`animation()`. In an
  interactive area, use context overrides only for operators that truly require
  a window/area/region; UI/viewport behavior remains host-specific.
- If an engine, material, or annotation is invisible, verify the active camera,
  engine compatibility, frame, material socket, compositor output, and render
  mode before changing molecule data. See [rendering recovery](references/rendering-troubleshooting.md).

## Non-goals

This skill does not define structure/trajectory/density import, selection
semantics, or the depth of `add_style()`. It owns only the scene, camera, render,
material-selection, compositor/world, snapshot/animation, and Blender context
boundary after those upstream objects exist.
