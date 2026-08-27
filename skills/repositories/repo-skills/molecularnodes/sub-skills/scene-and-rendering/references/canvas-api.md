# Canvas API and reproducible render workflow

Return to [scene-and-rendering](../SKILL.md) for routing. This reference owns the
public `Canvas`, camera, framing, and output contracts. It intentionally does not
define molecule loading, trajectory semantics, density parsing, or the full
`add_style()` API.

## Construction and scene lifecycle

```python
mn.Canvas(
    engine: mn.scene.EEVEE | mn.scene.Cycles | Literal["EEVEE", "CYCLES"] = "EEVEE",
    resolution: tuple[int, int] = (1280, 720),
    transparent: bool = False,
    template: pathlib.Path | str | None = "Molecular Nodes",
) -> mn.Canvas
```

The constructor registers the add-on, installs package assets, loads an app
template or `.blend` when `template` is truthy, selects the engine, writes the
resolution and film transparency, creates the `Camera` helper, and calls the
compositor setup. The active Blender scene is available as `canvas.scene`. The
default template is the Molecular Nodes template. In the current
implementation, `mn.Canvas(template=None)` skips the reset and preserves the
current active scene; use `canvas.scene_reset(template=None)` when an explicit
Blender factory-startup reset is intended. A string template must be a known
app-template name or a valid existing `.blend` path.

```python
canvas.scene_reset(
    template: pathlib.Path | str | None = "Molecular Nodes",
    engine: mn.scene.EEVEE | mn.scene.Cycles | Literal["EEVEE", "CYCLES"] = "EEVEE",
) -> None
canvas.load(path: str | pathlib.Path) -> None
canvas.clear() -> None
```

`scene_reset()` replaces the current scene and reselects the requested engine;
invalid template paths/names raise `ValueError`. `scene_reset(template=None)`
explicitly loads Blender's factory startup file. `load()` accepts only an
existing path with the exact `.blend` suffix and raises `ValueError` otherwise.
`clear()` removes registered MolecularNodes entities but deliberately leaves
lighting, world, compositor, camera, and render settings unchanged. Treat scene
reset/load as destructive operations: save first, then reacquire entities,
active-scene objects, node sockets, and other Blender datablock references. If a
world or compositor wrapper was already materialized, prefer a fresh controller
or explicitly rebuild it against the new active scene.

## Flat settings and read-back validation

All of these properties read and write the active Blender scene directly:

| Property | Contract |
| --- | --- |
| `resolution` | `(width, height)` integer pixels; maps to `scene.render.resolution_x/y`. |
| `transparent` | Boolean; maps to `scene.render.film_transparent`. |
| `fps` | Scene render frames per second; accepts a numeric value. |
| `frame_start`, `frame_end` | Integer scene animation bounds. |
| `frame` | Integer current frame; setter calls `scene.frame_set(value)` so animation data updates. |
| `frame_range` | `(start, end)` pair; setter writes both bounds. |
| `render_scale` | Integer resolution percentage; `100` is full resolution, lower values are previews. |
| `samples` | Delegates to the active engine's sample count. |
| `exposure`, `gamma`, `look` | Color-management view settings; valid `look` values depend on the active transform. |
| `view_transform` | `ViewTransform` or case-insensitive full/short name. |
| `passes` | Replacement list of enabled view-layer passes. |

A reproducible preview should explicitly set all values that matter to the
comparison, rather than relying on template or loaded-file defaults:

```python
canvas.resolution = (320, 240)
canvas.render_scale = 100
canvas.fps = 24
canvas.frame_range = (1, 1)
canvas.frame = 1
canvas.transparent = False
canvas.samples = 16                 # EEVEE preview example
canvas.view_transform = "Standard" # or "AgX" when that is the intended target
canvas.exposure = 0.0
canvas.gamma = 1.0
canvas.passes = ["combined"]
```

`passes` accepts only `combined`, `z`, `mist`, `normal`, `position`, `vector`,
`diffuse_color`, `emit`, `environment`, and `ambient_occlusion`. It disables
every listed pass not in the assigned list. An unknown name raises `ValueError`
and leaves the existing toggles untouched because validation happens first.
There is no Cryptomatte name in this Canvas allow-list. Extra passes may
increase render cost and are useful only when a compositor or consumer reads
them.

`ViewTransform` members are `STANDARD`, `KHRONOS`, `AGX`, `FILMIC`,
`FILMIC_LOG`, `FALSE_COLOR`, and `RAW`, with Blender string values `Standard`,
`Khronos PBR Neutral`, `AgX`, `Filmic`, `Filmic Log`, `False Color`, and `Raw`.
The setter normalizes full values and short names case-insensitively. If a
white annotation or color looks unexpectedly compressed, check the view
transform and color management before editing the annotation color.

## Camera setup and framing

`canvas.camera` wraps the active `scene.camera` and exposes:

```python
camera.lens: float                 # getter/setter, millimetres; default 50
camera.clip_start: float           # near clipping distance; default 0.01
camera.clip_end: float             # far clipping distance; default 1000
camera.rotation: tuple[float, float, float]  # XYZ degrees
camera.set_viewpoint(
    viewpoint: mn.scene.Viewpoint | str | Sequence[float]
) -> None
```

Named `Viewpoint` values are `default`, `front`, `back`, `top`, `bottom`,
`left`, and `right`; names are normalized case-insensitively. `set_viewpoint()`
assigns a custom three-value sequence directly to Blender's Euler rotation, so a
custom sequence is in radians. Prefer `camera.rotation = (x, y, z)` when angles
are specified in degrees. Do not pass degree values to `set_viewpoint()`.

```python
canvas.frame_object(
    obj: bpy.types.Object | MolecularEntity,
    viewpoint: Viewpoint | str | None = None,
) -> None
canvas.frame_view(
    view: list[tuple] | MolecularEntity,
    viewpoint: Viewpoint | str | None = None,
) -> None
```

`frame_object()` unwraps a MolecularEntity to its `.object`, optionally changes
the named viewpoint, then moves/aims the camera at the object. `frame_view()`
accepts an entity (resolved with `get_view()`), a bounding-box list of eight
3-D vertices, or a combined view produced upstream with `view_a + view_b`; it
frames the bounding box. These helpers change camera placement and aim, not
molecular geometry. A selection/view must already be valid before entering this
skill.

A framing recipe is:

```python
canvas.camera.lens = 50
canvas.camera.clip_start = 0.01
canvas.camera.clip_end = 1000
canvas.frame_view(entity.get_view(), viewpoint="front")
canvas.snapshot("preview.png", frame=1, file_format="PNG")
```

Lens changes affect field of view but do not reposition the camera; a later
frame operation recalculates placement. If an object is clipped, enlarge
`clip_end` or reduce `clip_start`; if framing is too tight or loose, change the
lens and call the frame helper again. The framing helpers use Blender's
`view3d.camera_to_view_selected` operator, so they require a suitable
interactive context; do not assume they work in background/headless mode.

## Stills and animation output

```python
canvas.snapshot(
    path: str | pathlib.Path | None = None,
    frame: int | None = None,
    file_format: str = "PNG",
) -> None
```

The method temporarily selects the requested frame, sets Blender image media
type to `IMAGE`, uses the requested `image_settings.file_format`, renders with
`bpy.ops.render.render(write_still=True, animation=False)`, and copies the
result to the exact `path` when one is supplied. `use_file_extension` is enabled
for the temporary file; the method does not create the destination parent or
validate the copied file. With no path, display is attempted only when notebook
`IPython.display` support is available. The method returns `None`.

Common still formats are Blender-supported values such as `PNG`, `JPEG`,
`TIFF`, and `OPEN_EXR`; use the exact enum supported by the host rather than
assuming every format is available. PNG is the safest deterministic choice.
`transparent=True` preserves the film alpha where the chosen format supports
it; a world background still controls lighting even when the film is transparent.

```python
canvas.animation(
    path: str | pathlib.Path | None = None,
    frame_start: int | None = None,
    frame_end: int | None = None,
    render_scale: int = 100,
) -> None
```

Animation chooses the supplied range or the current scene range. An end before
the start raises `ValueError`. It temporarily locks the render interface,
sets the percentage scale, renders each frame to temporary zero-padded PNGs,
creates an image strip in the scene sequence editor, then renders an MPEG-4
(`FFMPEG`/`MPEG4`) video and removes the temporary strip. If `path` is supplied,
the generated MP4 is copied to the exact supplied path; with no path, notebook
video display is attempted. On normal completion, temporary output/frame/range
settings are restored and the temporary image strip is removed. An external
interrupt can occur before strip removal, so inspect and clean the sequence
editor before retrying. The method does not create the destination parent.

`render_scale` changes output pixel dimensions as a percentage of
`resolution`; it does not alter camera framing. Use a low value for smoke tests
and restore `100` for publication output. Annotation rendering receives the
scale through the render/compositor path, so compare annotations at the same
scale as the final image. Animation uses the scene FPS and encodes
MPEG-4/FFMPEG.
