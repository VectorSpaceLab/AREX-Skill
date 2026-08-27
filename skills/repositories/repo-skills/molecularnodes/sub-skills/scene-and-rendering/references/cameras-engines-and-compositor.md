# Cameras, engines, and compositor

This reference describes the scene-side public API in MolecularNodes 5.2.0 on a
Blender/bpy 5.2 host. It assumes that an upstream skill has already created a
molecule, density object, ensemble, or other renderable object. It does not load
structures, create styles, or create annotations.

## Canvas lifecycle and scene ownership

`mn.Canvas` is a controller for the active `bpy.context.scene`. Its constructor:

1. registers MolecularNodes and installs its assets;
2. calls `scene_reset(template=...)` when `template` is truthy;
3. selects the requested engine and resolution;
4. creates a `Camera` helper, sets film transparency, and prepares the default
   annotation compositor.

The default `template="Molecular Nodes"` therefore replaces the current scene.
A `.blend` path may be supplied instead. A path must exist and have the exact
`.blend` suffix. An invalid template or path raises `ValueError`.

There is an important distinction between constructor and method behavior:

- `mn.Canvas(template=None)` skips `scene_reset` and keeps the current active
  scene. It is not an implicit factory-startup reset in the current
  implementation.
- `canvas.scene_reset(template=None)` explicitly loads Blender's factory
  startup file, then selects the requested engine.
- `canvas.scene_reset(template="Molecular Nodes")` loads the named template.
- `canvas.load(path)` opens an existing `.blend` file and replaces the active
  scene.
- `canvas.clear()` removes registered MolecularNodes entities only. It leaves
  lighting, world, compositor, camera, and render settings in place; it does not
  mean “factory reset”.

Treat `scene_reset()` and `load()` as destructive. Save or duplicate important
work first. After either operation, reacquire MolecularNodes entities, active
scene objects, camera data, node sockets, and any other Blender datablock
references. A previously materialized `canvas.world` or `canvas.compositor`
wrapper can be bound to the old scene/node group; use a fresh controller or
explicitly rebuild the scene-side graph rather than assuming those wrappers are
still valid. A reset/load also does not recreate the constructor's compositor
setup for an already-existing `Canvas`; restore the desired compositor and
annotation overlay explicitly.

## Camera and framing

`canvas.camera` reads the camera assigned to the active scene. It exposes:

```python
canvas.camera.lens         # millimetres
canvas.camera.clip_start   # near clipping distance
canvas.camera.clip_end     # far clipping distance
canvas.camera.rotation     # XYZ Euler angles in degrees
```

The `rotation` property converts to and from degrees. In contrast,
`camera.set_viewpoint()` treats a custom three-value sequence as Blender's
native Euler values in **radians**. Do not pass `(90, 0, 0)` to
`set_viewpoint()` when degrees were intended; use either a named viewpoint or
`camera.rotation = (90, 0, 0)`.

Named viewpoints are case-insensitive:

| Name | Template XYZ rotation in degrees |
| --- | ---: |
| `default` | `(70.402, 0, 0)` |
| `front` | `(90, 0, 0)` |
| `back` | `(90, 0, -180)` |
| `top` | `(0, 0, 0)` |
| `bottom` | `(-180, 0, 0)` |
| `left` | `(-270, 0, -90)` |
| `right` | `(-270, 0, -270)` |

These are orientation presets, not promises about camera distance or framing.
`frame_object()` and `frame_view()` then use Blender's camera-to-selection
operation to place and aim the camera. They do not change molecular geometry.
`frame_object()` accepts a Blender object or `MolecularEntity`; `frame_view()`
accepts an entity, an eight-vertex bounding box, or a combined view prepared by
an upstream entity workflow.

A reliable interactive recipe is:

```python
canvas.camera.lens = 50
canvas.camera.clip_start = 0.01
canvas.camera.clip_end = 1000
canvas.frame_view(entity.get_view(), viewpoint="front")
```

Lens changes alter field of view but do not move the camera. Re-run the frame
helper after changing the lens when the subject should be reframed. Increase
`clip_end` for a distant or unusually large subject; reduce `clip_start` only
when the near plane is clipping the subject. Check that `scene.camera` is not
`None` before using any camera property.

## EEVEE and Cycles

Use an engine instance when sample, ray-tracing, device, or denoising settings
must be explicit:

```python
canvas.engine = mn.scene.EEVEE(samples=64, raytracing=True)
canvas.engine = mn.scene.Cycles(
    samples=256, device="CPU", denoise=True, denoise_gpu=True
)
```

The public string forms are `"EEVEE"` and `"CYCLES"` (case-insensitive). The
implementation also accepts Blender's EEVEE engine identifiers when they are
available on the host. Read back `canvas.engine.name` and `scene.render.engine`
after assignment.

- **EEVEE** is the fast preview-oriented engine. Its MolecularNodes settings
  include render samples and a ray-tracing toggle. It is a good starting point
  for a smoke render, but visual output still depends on the host and the
  material/style graph.
- **Cycles** is path-traced and usually slower, but is required by some
  Cycles-only styles and can provide different lighting. The string
  `canvas.engine = "CYCLES"` constructs the default Cycles configuration, whose
  default device is `GPU`.
- For a host-safe Cycles configuration, request `device="CPU"` explicitly and
  verify `canvas.engine.device == "CPU"`. This is a device-selection claim,
  not a claim that every material, render, or machine is fast or guaranteed to
  succeed.
- Do not infer GPU availability from package installation or from an EEVEE or
  Cycles object. GPU selection is optional and host-specific; no GPU device or
  performance claim belongs in a portable workflow.

An object can be invisible because its style or material was authored for the
other engine. Check the active engine and the style's material/geometry options
before changing molecule data. The `Style Spheres Cycles` and `Style Spheres
EEVEE` assets are deliberately different compatibility choices.

## Render settings, passes, and color management

Set the settings that affect reproducibility before framing and rendering:

```python
canvas.resolution = (320, 240)
canvas.render_scale = 100
canvas.fps = 24
canvas.frame_range = (1, 1)
canvas.frame = 1
canvas.transparent = False
canvas.samples = 16
canvas.view_transform = "Standard"  # or an intentional AgX target
canvas.exposure = 0.0
canvas.gamma = 1.0
canvas.passes = ["combined"]
```

The flat properties map to the active scene: `resolution` is `(x, y)` pixels,
`render_scale` is `resolution_percentage`, `transparent` is
`film_transparent`, `frame` uses `scene.frame_set()`, and `fps`/frame range
control animation output. `render_scale` changes output pixel dimensions; it
does not change camera framing. Restore it to `100` for final output after a
preview.

`canvas.passes` is a replacement set, not an additive update. The supported
names are:

`combined`, `z`, `mist`, `normal`, `position`, `vector`, `diffuse_color`,
`emit`, `environment`, and `ambient_occlusion`.

Every supported pass not listed is disabled. Unknown names raise `ValueError`
before any pass toggle is changed. Enable only passes consumed by a compositor
or downstream output because extra passes increase work and storage. The
current wrapper does not provide a Cryptomatte pass name; do not copy a generic
Blender pass list into this property.

`view_transform` accepts the `ViewTransform` enum or a case-insensitive full or
short name: `Standard`, `Khronos PBR Neutral`, `AgX`, `Filmic`, `Filmic Log`,
`False Color`, and `Raw`. `look` is transform-dependent, so set it only to a
value offered by the active host. Exposure and gamma are scene color-management
settings, not substitutes for changing world strength or a material. If white
annotation text or colors look compressed, inspect the view transform, look,
exposure, and gamma before editing annotation colors.

## World and lighting

`canvas.world` is a `WorldTree` for the active scene world. With the standard
MolecularNodes template, the convenience properties address the
`MN_world_shader` node:

```python
canvas.world.background = (0.02, 0.02, 0.04, 1.0)
canvas.world.hdri_strength = 2.0
```

`background` is an RGBA value and `hdri_strength` is the template's world
lighting-strength input. The latter does not download or load an HDRI by
itself. A transparent film can still use the world for lighting; transparency
controls the rendered film alpha, not whether world lighting exists.

For a clean world graph, use the reset context manager and rebuild a shader:

```python
from nodebpy import shader as s

with canvas.world.reset() as surface:
    s.Background(color=(0.05, 0.05, 0.08, 1.0), strength=1.0) >> surface
```

`WorldTree.reset()` deletes the existing nodes, including
`MN_world_shader`. Until that node is rebuilt or a template is reloaded,
`canvas.world.background` and `canvas.world.hdri_strength` raise `ValueError`.
This is an intentional destructive graph reset, not a temporary edit.

## Compositor and annotation overlays

A newly constructed `Canvas` prepares a compositor graph that passes the render
layers through and alpha-composites the MolecularNodes image named
`mn_annotations` on top. The image node and overlay wiring do not create
annotation content: content is produced only when upstream annotations exist,
are visible/valid, and the render handler can draw them for the current frame.

`CompositorTree.reset()` is a context manager. Calling the method without
entering it does not perform the reset. Use:

```python
from nodebpy import compositor as c

with canvas.compositor.reset() as (image, output):
    image >> c.Glare.bloom(strength=0.4) >> output
canvas.compositor.add_annotations()
```

Resetting removes the default annotation overlay as well as all other nodes.
Call `add_annotations()` after the custom chain if annotations should be on top.
The helper takes the current output source and inserts an alpha-over operation;
it is safer than manually depending on the image-node layout. A custom effect
that consumes `z`, `mist`, or another render layer must also enable that name in
`canvas.passes` before rendering.

If the compositor is intentionally plain, reset it with `with ...: pass` and
leave annotations disabled. If the compositor is reset after a scene load, make
sure the active scene has a compositor graph and re-add the overlay explicitly.
Do not mutate node topology while a render or animation is in progress.
