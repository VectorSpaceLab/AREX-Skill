# Trajectory API and frame semantics

This reference distills the trajectory tutorial/API pages and the source
contracts in `molecularnodes/entities/molecule/base.py`, `helpers.py`,
`selections.py`, `molecularnodes/utils.py`, and the trajectory tests. It assumes
MolecularNodes 5.2.0, MDAnalysis 2.10.0, databpy 0.8.0, nodebpy 520.11.0, and a
Blender/bpy 5.2 host.

## Construction and topology/coordinates

```python
mn.Molecule(
    universe: mda.Universe,
    name: str = "NewUniverseObject",
    world_scale: float = 0.1,
    create_object: bool = True,
) -> mn.Molecule

mn.Molecule.load(
    topology: Path | str,
    coordinates: Path | str | None = None,
    name: str | None = None,
    style: str | None = None,
    selection: str | None = None,
    create_object: bool = True,
    **kwargs,
) -> mn.Molecule
```

With `coordinates` present, `load` passes topology, coordinates, and `**kwargs`
to `MDAnalysis.Universe`; the resulting Universe is attached to the Molecule.
With only `topology`, `load` follows the single-structure reader route and is
outside this trajectory workflow except when its result is later multi-frame.
Constructing `mn.Molecule(u, create_object=False)` is useful for preparation,
but object-backed operations, attributes, selections, annotations, and handlers
need `create_object=True` in a valid Blender context.

After construction, check:

```python
assert mol.universe.atoms.n_atoms > 0
n = mol.universe.trajectory.n_frames
assert mol.uframe == mol.universe.trajectory.frame  # zero-based
print(mol.universe.filename, mol.universe.trajectory.filename)
print(mol.universe.dimensions)  # (a,b,c,alpha,beta,gamma) or None
```

The mesh stores positions scaled by `world_scale` (default 0.1 in this version)
and standard attributes such as `atomic_number`, `vdw_radii`, `mass`, `res_id`,
`res_name`, `atom_name`, `Color`, `is_backbone`, `is_side_chain`, `is_solvent`,
`is_nucleic`, `is_peptide`, `is_hetero`, `is_lipid`, `entity_id`, and
`sec_struct`. Missing MDAnalysis topology data may cause individual attributes
to be skipped with a log warning; inspect `mol.list_attributes()` rather than
assuming every optional field exists.

## Playback properties

The public Blender-synchronized properties are:

| Property | Meaning and validation |
|---|---|
| `frame` | Scene/Blender frame property; do not confuse with `uframe`. |
| `subframes` | Non-negative number of interpolation slots inserted between trajectory frames. |
| `offset` | Scene-frame offset before mapping; positive values hold the initial trajectory frame longer, negative values advance earlier. |
| `average` | Non-negative radius for a centered moving average. `1` uses current plus adjacent valid frames. |
| `interpolate` | Enables linear interpolation only when `subframes > 0`. |
| `correct_periodic` | Corrects boundary crossings only for orthorhombic dimensions. |

`mol.reset_playback()` restores zero subframes/offset/average, disables
interpolation and periodic correction. `mol.set_frame(scene_frame)` is the
normal update entry point. The Blender frame-change handler normally calls it;
manual callers should use it after a context-safe scene frame change.

## Exact frame mapping

`molecularnodes.utils.frame_mapper(frame, subframes=0, offset=0, mapping=None)`
first computes `max(frame - offset, 0)`. Without a custom mapping, the current
Universe frame is the integer scene frame when `subframes=0`, otherwise
`floor(scene_frame/(subframes+1))`. The frame manager clamps it to the final
valid frame for finite trajectories. A supplied mapping must be a `list` or
NumPy array; it is repeated `subframes + 1` times before indexing.

When `subframes > 0 and interpolate=True`, the manager loads current and next
Universe positions and returns a databpy linear interpolation with
`t = (scene_frame % (subframes+1))/(subframes+1)`. The final trajectory frame is
used for both sides at the end. With subframes but interpolation disabled, the
mapped current frame is held until the next trajectory frame boundary.

When `average > 0`, `frames_to_average(frame, upper_bound, average)` requests
`frame-average` through `frame+average`, clipped to valid bounds. The position
cache retains recent frame positions and returns their mean. With both averaging
and periodic correction, each cached frame is corrected relative to the first
before averaging.

`mol.frame_manager._position_at_frame(u_frame)` is a low-level helper: it sets
`mol.uframe` and returns scaled current positions. Prefer `set_frame` or
`frame_manager.get_positions_at_frame(scene_frame)` for normal playback. A
trajectory with `n_frames <= 1` intentionally does not reset manually moved
positions on scene frame changes.

## Periodic boxes and correction

`mol.universe.dimensions` and `mol.universe.trajectory.ts.dimensions` use
`(a, b, c, alpha, beta, gamma)`. `mol._is_orthorhombic` is true only if all
angles are approximately 90 degrees. `correct_periodic_positions(pos1, pos2,
dimensions)` raises `ValueError` for non-orthorhombic dimensions; it corrects
coordinate jumps independently along x/y/z. Therefore:

```python
if mol.correct_periodic and mol._is_orthorhombic:
    # safe for interpolation or averaging
    ...
```

`mol._update_box()` updates Geometry Nodes groups named `Periodic Box` or
`Periodic Array` only when their `Update` input is enabled. It writes the six
timestep dimensions each frame. For visible annotation geometry, use
`mol.annotations.add_simulation_box()` as described in
[annotations.md](annotations.md); dimensions missing from the timestep produce
no box rather than a fabricated unit cell.

## Selections and styles

```python
mol.add_style(
    style="spheres",
    selection: str | mda.AtomGroup | None = None,
    material="MN Default",
    **style_kwargs,
) -> mn.Molecule

mol.selections.from_string(
    string: str,
    *, updating: bool = True,
    periodic: bool = True,
    name: str | None = None,
) -> TrajectorySelectionItem

mol.selections.from_atomgroup(
    atomgroup: mda.AtomGroup,
    *, name: str | None = None,
) -> TrajectorySelectionItem
```

`add_style` checks a string against existing mesh attributes first. Otherwise it
validates it through `Universe.select_atoms()` and creates a managed selection;
an invalid string raises a `UserWarning` and returns no selection restriction,
so the style is still added and may apply broadly rather than safely selecting
nothing. `AtomGroup` input always becomes a managed selection. Use
`mol.selections[name]`/`named_attribute(name)` to inspect the boolean mesh
attribute.

The selection manager keeps a Blender collection as its source of truth and
caches groups in `atomgroups`. `from_string` records the MDAnalysis phrase,
`updating`, and `periodic`, then creates a boolean attribute. Updating groups
(e.g. distance-based `around`) are recomputed on frame updates; a static group
is not. `from_atomgroup` marks the UI item as sourced from an AtomGroup and the
stored string is display-only. `mol.selections.remove(name_or_index)` removes
the named attribute and cached group; invalid names/types raise `ValueError` or
an out-of-range index error.

## Baking positions (optional)

`mol.frames_to_collection(start=0, stop=None, step=1, name=None)` creates or
replaces a collection of per-frame objects. `step` must be positive; `stop` is
exclusive and clipped to the finite trajectory length. The current Universe
frame is restored in a `finally` block. This is data baking, not a final render
recipe; hand off scene setup to `../scene-and-rendering/SKILL.md`.

## Verification-oriented failure cues

- `n_frames`/`filename` access can raise for streaming readers; treat an unknown
  count as expected for `StreamingTrajectory`.
- A missing topology/coordinates file normally fails while creating the
  Universe or during unpickle, not during a later style call. Preserve the
  original error and repair the local path.
- A valid selection may still select zero atoms. For COM, dihedral, or atom-label
  annotations, check the group/residue before drawing.
- A wrong scene frame can appear to work while `uframe` remains unchanged if a
  single-frame object is used; test with at least two local frames.
