# Troubleshooting trajectories and annotations

Use this as a diagnosis sequence for MolecularNodes 5.2.0. Preserve the
original exception and inspect the source path, Blender context, and live
manager state before changing settings. These checks are static/API-oriented;
no native repository tests or examples are required for the diagnosis.

## First classify the runtime

| Symptom | Check | Meaning / repair |
|---|---|---|
| `bpy` or `scene.MNSession` is missing | `bpy.context.scene` and `hasattr(scene, "MNSession")` | The addon is not registered in the current Blender file/context. Register it in the supported host before creating object-backed entities. |
| `mol.object` is absent | `mol.object` and `mol.create_object` path | `create_object=False` is not enough for mesh attributes, selections, annotations, handlers, or session draw recovery. Create/link the Blender object in a valid context. |
| No annotation output | `mol.annotations.visible`, `object.visible_get()`, object membership in `bpy.context.scene.objects`, and presence of a VIEW_3D region | Manager visibility, object visibility/scene membership, and a valid region are independent gates. Background mode does not install the viewport handler. |
| Frame update is skipped | `mol.frame_manager.n_frames`, `mol.universe.trajectory.n_frames`, and `mol.update_with_scene` | A finite one-frame `Molecule` intentionally keeps manually moved positions during scene changes. Streaming has `n_frames=None` and is not skipped. |

Do not use a successful MDAnalysis-only object as proof that Blender mesh,
property, handler, annotation, or session behavior is working. Those paths need
a registered Blender addon and a live object/session.

## Local trajectory and frame failures

### The frame appears wrong or unchanged

Inspect both coordinate systems:

```python
print("scene:", bpy.context.scene.frame_current)
print("entity frame:", mol.frame)
print("universe frame:", mol.uframe)
print("n_frames:", mol.frame_manager.n_frames)
print("update_with_scene:", mol.update_with_scene)
```

For a normal trajectory, `frame_change_pre` uses the scene frame when
`update_with_scene=True`; otherwise it uses `mol.frame`. The finite frame
manager clamps mapped frames at the last universe frame. `subframes`, `offset`,
and `interpolate` can intentionally hold or interpolate positions. Use
`mol.reset_playback()` before comparing raw frames. If the object has only one
frame, `Molecule.set_frame()` returns early by design.

For a direct raw-frame check on a finite trajectory, set `mol.uframe` to a
valid zero-based universe frame and compare the resulting positions. Do not use
an arbitrary scene frame as if it were a universe frame when subframes or offset
are active. A custom `frame_mapper()` mapping must be a list or NumPy array and
must cover the requested expanded scene-frame range.

### Periodic correction fails or looks discontinuous

`correct_periodic_positions()` only accepts orthorhombic dimensions with three
angles close to 90 degrees. Inspect:

```python
print(mol.universe.trajectory.ts.dimensions)
print(mol._is_orthorhombic)
```

Leave `correct_periodic` disabled for triclinic cells. A simulation-box
annotation can still display a triclinic cell; displaying the cell does not
make coordinate correction valid. Also distinguish missing dimensions (`None`)
from an invalid non-orthorhombic box.

## Selection failures

### A managed selection has an error

`mol.selections.from_string(...)` creates a Blender selection item and then
synchronizes it. If `Universe.select_atoms()` raises, the exception text is
stored in `item.message`; the item remains visible to the manager/UI layer and
its boolean named attribute is not successfully refreshed. Inspect and repair:

```python
item = mol.selections.get("my_selection")
print(item.message if item else "missing")
item.string = "name CA"  # only after checking the item exists
item.updating = True
item.periodic = True
mol.selections.update_attributes()
print(item.message)
```

An `AtomGroup` created by `from_atomgroup()` is cached by name and its displayed
string is informational; changing that string is not a way to replace the
underlying group. Dynamic `UpdatingAtomGroup` selections are recomputed on
frame updates. Static selections are not recomputed merely because the frame
changed.

### A style is unexpectedly broad or empty

`Molecule.add_style()` treats a string as an existing mesh attribute first. If
there is no such attribute, it validates the string as an MDAnalysis selection.
For an invalid phrase it emits a `UserWarning`, returns no selection
restriction, and still adds the style. The style can consequently apply to all
atoms rather than being safely empty. Repair the phrase or create/use a valid
named boolean attribute; do not infer a useful selection from the presence of
the style node.

### An annotation selection fails

`add_atom_info`, `add_com`, and `add_com_distance` validate string selections
through `Universe.select_atoms()`, or require an `AtomGroup`. Invalid types and
invalid selection phrases raise while adding or changing the annotation. A
valid phrase that selects zero atoms can still fail later when `draw()` calls
atom iteration or `center_of_mass()`. Check `n_atoms` and the relevant residue
or atom existence before drawing. The manager may record the failure as
`_invalid_inputs` or `_draw_error`, so inspect both rather than only checking
`len(mol.annotations)`.

## Annotation registration, visibility, and drawing

### `add_<type>` is missing

Check the manager registry and the class registration path:

```python
print([x for x in dir(mol.annotations) if x.startswith("add_")])
print(mol.annotations._classes.keys())
```

A custom class must derive from `MoleculeAnnotation`, define a unique
`annotation_type`, and override `draw()`. Registration rejects non-annotation
classes, duplicate types, and classes that inherit the abstract base draw
without implementing it. All annotation inputs are keyword-only; missing
required inputs and unknown keyword names raise before an instance is committed.

### Visibility changes do not show immediately

Check both layers:

```python
print(mol.annotations.visible)
print(annotation.visible)
```

The manager property maps to `object.mn.annotations_visible`; the individual
property maps to the corresponding `object.mn_annotations` entry. The manager
setter tags VIEW_3D areas for redraw, but a hidden entity, an object not in the
current scene, invalid inputs, missing viewport region, or a stale draw handler
can still prevent output.

Annotation `draw()` exceptions are isolated and stored in
`annotation._instance._draw_error`. Invalid inputs are skipped before draw.
A non-empty diagnostic is a failure to repair, not an alternate visibility
state. When mesh geometry is being collected, 2D helpers intentionally return
without creating mesh geometry; use 3D helpers for geometry and reserve 2D
helpers for a valid overlay/render context.

### A custom annotation disappears after load

Custom classes are not serialized as source code. During annotation restoration,
if `prop.type` is not present in the registered manager class map, the manager
removes that property entry because it cannot construct the instance. Import and
register the class before loading/restoring the session. Also re-create runtime
`AtomGroup` values when their persisted Blender property is not a sufficient
selection source.

## Stale draw handlers and deleted objects

The annotation manager removes its handler when `_is_valid_entity()` catches a
`LinkedObjectError`. Session pruning removes entities whose Blender object is no
longer valid. If a stale or duplicate handler remains after file/extension
lifecycle operations, use the session lifecycle rather than keeping an old
handler token:

```python
session = bpy.context.scene.MNSession
session.remove_draw_handlers()
session.prune()
session.add_draw_handlers()
```

`add_draw_handlers()` adds handlers only for visible annotation managers. The
addon itself runs `load_pre` removal before a file load and has a timer-based
restore path for extension re-registration. A loaded session still needs its
custom annotation classes registered and its objects in a valid scene.

Do not call a draw callback with a fabricated context. The handler obtains a
viewport region and `RegionView3D` from Blender's current context; if either is
unavailable it returns. Operators also depend on area/region/active-object
context, so repair or explicitly override the context before invoking one.

## IMD connection and stream errors

Use `StreamingTrajectory.load()` for `imd:` URLs. It normalizes the URL and
wraps initial reader construction failures as `ValueError`. After construction,
frame updates call `universe.trajectory.next()` and ignore the requested frame
number. Consequently:

- a repeated/backward scene frame still advances the live stream;
- `StopIteration` means the stream ended or was lost and is re-raised;
- other reader errors are re-raised after logging; and
- `n_frames` is `None`, so finite-trajectory frame bounds do not apply.

There is no promise of random access, rewind, cached historical frames, or
recovery from a server that is unavailable. If the stream must be analyzed or
rendered repeatedly, acquire a finite local trajectory separately rather than
assuming the IMD endpoint is a file.

## `.MNSession` and source paths

For a saved `/path/file.blend`, check for `/path/file.blend.MNSession`. The
sidecar is produced by the registered `save_post` handler and loaded by
`load_post`. An absent sidecar is reported only in verbose handler mode; the
quiet handler returns without reconstructing entities.

A file-backed trajectory restore reconstructs the MDAnalysis universe from the
stored topology/trajectory paths and saved universe frame. If a source file is
moved, deleted, or corrupted, restore raises a descriptive `RuntimeError`; do
not replace the error with a guessed path or an online download. The separate
`reload_entity()` helper supports ordinary file-backed `md` entities but not
`md-streaming`. Keep source files at the recorded/resolved paths and treat a
live IMD URL as a runtime endpoint, not as a local source file.

## Evidence consulted

- `molecularnodes/handlers.py`
- `molecularnodes/session.py`
- `molecularnodes/entities/molecule/base.py`
- `molecularnodes/entities/molecule/helpers.py`
- `molecularnodes/entities/molecule/imd.py`
- `molecularnodes/entities/molecule/selections.py`
- `molecularnodes/entities/reload.py`
- `molecularnodes/annotations/manager.py`
- `molecularnodes/blender/utils.py`
- `docs/api/blender.qmd`
- `docs/tutorials/streaming-trajectories.qmd`
- `tests/test_trajectory.py`, `tests/test_annotations.py`, and
  `tests/test_session.py` (read only; native tests/examples were not run)
