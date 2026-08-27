# Streaming, frame mapping, and `.MNSession` persistence

This reference records the MolecularNodes 5.2.0 behavior for ordinary
MDAnalysis trajectories, IMD streaming trajectories, and the Blender session
sidecar. It intentionally does not promise random access to IMD frames or
reconstruction of a stream when its server/source is unavailable.

## Normal trajectory frame mapping

`Molecule.frame` is the Blender/object frame property. `Molecule.uframe` is the
current zero-based `MDAnalysis.Universe.trajectory.frame`. They are not the same
coordinate system.

For a normal `Molecule` whose `update_with_scene` is true, the frame manager
uses this mapping:

```text
scene = max(scene_frame - offset, 0)
if subframes == 0:
    uframe_current = scene
else:
    uframe_current = floor(scene / (subframes + 1))
```

`FrameManager.get_positions_at_frame()` clamps `uframe_current` to the final
finite trajectory frame. With `subframes > 0` and `interpolate=True`, it loads
both the current and next universe frames and uses:

```text
t = (scene_frame % (subframes + 1)) / (subframes + 1)
position = lerp(current, next, t)
```

At the final finite frame, current and next are the same. With subframes but
`interpolate=False`, the current mapped trajectory frame is held until the next
mapping boundary. `average > 0` uses the inclusive window from
`uframe-average` through `uframe+average`, clipped to valid trajectory bounds,
and returns the mean. `reset_playback()` sets `subframes`, `offset`, and
`average` to zero and disables interpolation and periodic correction.

When `update_with_scene=False`, the frame manager bypasses mapping,
interpolation, and averaging and directly requests the supplied entity frame.
The scene handler itself chooses `scene.frame_current` when
`update_with_scene=True`, otherwise the entity's own `frame` property.

Periodic correction is a separate position operation. It requires all three
box angles to be approximately 90 degrees; `correct_periodic_positions()`
raises for a non-orthorhombic cell. Triclinic dimensions can still be displayed
by the simulation-box annotation, but they are not valid input for this
correction helper.

The lower-level `frame_mapper()` accepts an optional list/NumPy mapping and
repeats each mapped value `subframes + 1` times. The current MolecularNodes
frame manager calls it without a custom mapping. An invalid mapping type raises
`ValueError`; a mapping too short for the requested scene frame can still fail
at indexing, so validate custom mappings before using the helper directly.

## IMD loading and streaming semantics

Use the streaming subclass for an IMD URL; do not pass an IMD endpoint to the
ordinary local-file workflow:

```python
from molecularnodes.entities.molecule import StreamingTrajectory

stream = StreamingTrajectory.load(
    topology="topology.pdb",
    coordinates="imd://localhost:8889",
    name="live",
)
```

`StreamingTrajectory.load()` normalizes `imd:/host:port` to
`imd://host:port`, constructs `MDAnalysis.Universe(topology, url)`, and wraps
connection/reader construction failures in `ValueError` with the connection
failure as its cause. A live Blender object is created and the optional style
is added only when `create_object=True`.

The streaming contract differs from normal trajectories:

- `StreamingTrajectory.n_frames` is `None`; the number of future frames is not
  known in advance.
- `_update_trajectory_positions(frame)` ignores the requested scene/entity
  frame and calls `universe.trajectory.next()`. A successful call replaces the
  object positions with the newly received frame.
- A scene frame change therefore means “advance the stream once,” not “load
  this frame number.” Going backward, repeating a scene frame, or scrubbing
  does not provide random access to an older stream frame. The source has no
  position cache for this override.
- `StopIteration` is logged as an ended/lost stream and re-raised. Other reader
  or connection exceptions are logged and re-raised. A failed update can
  therefore interrupt the frame-change path; it is not silently converted to a
  static last frame.
- After positions advance, the normal `Molecule.set_frame()` path still updates
  selections, calculations, annotation geometry, and periodic-box node inputs.
  Dynamic selections and annotations must therefore tolerate changing stream
  timesteps and empty/invalid groups.

The IMD tutorial marks this integration experimental. It discusses a
simulation that may pause while Blender is paused, but that is a property of the
simulation/IMD protocol setup, not a MolecularNodes guarantee. No promise is
made here about sending forces, controlling the simulation, caching old frames,
or interactive timeline behavior.

## What a `.MNSession` file contains

When the MolecularNodes addon is registered, Blender's `save_post` handler calls
`MNSession.pickle(filepath)`. The sidecar path is exactly:

```python
Path(f"{filepath}.MNSession")
```

For `/work/run.blend`, this is `/work/run.blend.MNSession`. The sidecar is not
written when the session has no live entities, and entities that cannot be
pickled are skipped with a warning. One unpicklable entity does not discard all
other picklable entities.

For an on-disk trajectory, the session code temporarily makes the trajectory
reader path relative where possible, writes a temporary sidecar, atomically
replaces the target, and restores the in-memory trajectory path/frame in a
`finally` block. `_has_ondisk_trajectory()` only treats a `str`/`Path` filename
that does not start with `imd://` as relocatable on-disk data. Non-path readers
and IMD URLs are not converted by this path pass.

The object also stores source fields through `_save_filepaths_on_object()`:
`mn.filepath_topology` and `mn.filepath_trajectory` are populated from string or
`Path` reader filenames after `bpy.path.abspath` resolution. These object fields
support the Blender reload operator; they are not a copy of the coordinate
files.

## Loading and source-path requirements

On file load, the registered `load_post` handler calls `MNSession.load(filepath)`
and reads `<blend path>.MNSession`. If that sidecar is absent, the handler's
quiet mode ignores only the missing-sidecar `FileNotFoundError`; it does not
create a replacement trajectory or invent source data.

For a pickled file-backed `Molecule`, `Molecule.__setstate__()` reconstructs an
`MDAnalysis.Universe` from the saved topology/trajectory paths, restores the
saved universe frame, then recreates the frame manager, selection manager,
annotation manager, DSSP manager, and calculations as needed. If the source
paths cannot recreate the universe, it raises a descriptive `RuntimeError`
containing the paths and original error. Keep the topology and coordinate files
available at the recorded/resolved paths; no missing-file recovery is promised.

The separate `reload_entity(obj)` helper uses the source paths stored on the
Blender object and relinks a new Python entity to the existing object. It calls
`Molecule.load()` for ordinary MD entities and sets the entity to the current
Blender scene frame. `can_reload()` explicitly does **not** include
`md-streaming`, because a live IMD connection has no ordinary source-file
reloader. A streaming endpoint should therefore be treated as a live runtime
input, not as a durable local trajectory source.

Annotation property entries are restored from `object.mn_annotations` when a
new annotation manager is constructed. A custom annotation class that is not
registered at that time cannot be reconstructed and its property entry is
removed. Register/import required custom classes before recovery. The saved
Blender property representation also does not guarantee restoration of an
arbitrary in-memory Python `AtomGroup`; use a selection string or recreate the
runtime group after loading.

## Draw-handler and load ordering

The addon registers these relevant handlers:

- `load_pre`: remove existing annotation draw handlers;
- `load_post`: load the `.MNSession` sidecar;
- `frame_change_pre`: call `update_entities(scene)`;
- `save_post`: write the `.MNSession` sidecar.

`MNSession.remove_draw_handlers()` and `add_draw_handlers()` are explicit
repair operations. `add_draw_handlers()` prunes dead entities and adds handlers
only for entities whose annotation manager is visible. Extension
re-registration also schedules a one-shot timer to restore visible handlers.
Do not retain a handler token after an entity/object has been deleted; let the
session prune it or remove the handler through the session/manager methods.

## Blender-context requirements

The session and frame paths are Blender-integrated, not pure MDAnalysis APIs:

- `MNSession` is obtained from `bpy.context.scene.MNSession` (or an explicit
  context), which exists only after the addon properties have been registered.
- `Molecule.create_object=False` is suitable for limited preparation, but frame
  updates, mesh attributes, selections, annotations, and handler restoration
  require an existing Blender object and a registered scene/session.
- `update_entities(scene)` calls `scene.MNSession.prune()` and then
  `entity.set_frame(...)`; a stale/deleted object can be removed from the
  session before updating.
- Annotation viewport drawing requires a valid `VIEW_3D` region and
  `RegionView3D`; background mode does not install the viewport draw handler.
  Blender operators additionally require a suitable context. Prefer direct
  object/session APIs where they provide the needed operation, and repair the
  context before invoking an operator.

## Evidence consulted

- `molecularnodes/utils.py`
- `molecularnodes/entities/molecule/helpers.py`
- `molecularnodes/entities/molecule/imd.py`
- `molecularnodes/entities/molecule/base.py`
- `molecularnodes/session.py`
- `molecularnodes/entities/reload.py`
- `molecularnodes/entities/base.py`
- `molecularnodes/handlers.py`
- `molecularnodes/ui/addon.py`
- `molecularnodes/blender/utils.py`
- `docs/api/trajectories.qmd`
- `docs/tutorials/trajectories.qmd`
- `docs/tutorials/streaming-trajectories.qmd`
- `tests/test_trajectory.py` and `tests/test_session.py` (read only; native tests
  were not run)
