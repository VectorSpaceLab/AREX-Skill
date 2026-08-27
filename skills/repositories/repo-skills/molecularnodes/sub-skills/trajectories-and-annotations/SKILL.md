---
name: trajectories-and-annotations
description: "Operate MolecularNodes Universe-backed trajectories: map Blender
  frames to MDAnalysis frames, manage selections and simulation boxes, stream
  IMD coordinates, add or extend annotations, and persist or recover trajectory
  state safely in Blender."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Trajectories and annotations

Use this sub-skill when a Researcher needs a multi-frame MDAnalysis-backed
`mn.Molecule`, playback controls, trajectory selections, simulation-box display,
IMD streaming, trajectory annotations, or `.MNSession` recovery. The runtime
host is Blender 5.2 (or a compatible `bpy` 5.2 host); MDAnalysis-only checks are
auxiliary and do not prove Blender integration.

## Boundaries

- Own `Molecule` trajectory construction, positions, playback, frame mapping,
  periodic boxes, trajectory selections, streaming, annotation lifecycle, and
  persistence/reload recovery.
- Use the sibling `../scene-and-rendering/SKILL.md` for camera, canvas, render,
  and final scene recipes; this sub-skill only supplies data and annotation state.
- Do not use this route for initial structure installation/download, density or
  ensemble import, or a complete rendering recipe.
- Read [trajectory-api.md](references/trajectory-api.md) for signatures and
  frame math, [annotations.md](references/annotations.md) for annotation APIs,
  [streaming-and-persistence.md](references/streaming-and-persistence.md) for
  IMD and session state, and [troubleshooting.md](references/troubleshooting.md)
  before diagnosing failures.

## Runtime contract

Inputs are a local topology plus optional local coordinate/trajectory file or
an already-created `MDAnalysis.Universe`; for IMD, use
`StreamingTrajectory.load(topology, coordinates="imd://host:port", ...)`.
Optional style and MDAnalysis selection arguments are keyword values. Outputs
are a live `mn.Molecule`/`StreamingTrajectory`, a Blender mesh with molecular
attributes, updated positions and selection attributes, annotation interfaces,
and, for picklable session entities saved through Blender, a
`<blend-path>.MNSession` sidecar. Keep file-backed topology and trajectory files
available at the paths recorded by the object/session.

## Choose the shortest workflow

1. For ordinary local MD files, call
   `mn.Molecule.load(topology, coordinates, name=..., style=...,
   selection=..., create_object=..., **universe_kwargs)`, or construct
   `u = mda.Universe(topology, coordinates)` followed by
   `mn.Molecule(u, name=...)`. Confirm `u.atoms.n_atoms`,
   `u.trajectory.n_frames`, current `u.trajectory.frame`, and dimensions before
   styling. `Molecule.load` with no `coordinates` is the single-structure route.
2. Add style through `mol.add_style(style="spheres", selection=None)` or a
   supported style name. A selection string first resolves as an existing
   named mesh attribute (the style expects a boolean selection), then as an
   MDAnalysis selection; an `AtomGroup` is registered as a managed selection.
   An invalid string emits a `UserWarning` and adds the style without a
   selection restriction, so it can apply broadly rather than safely selecting
   nothing. Inspect the warning and selection manager when a string is invalid.
3. For playback, use `mol.frame` for the Blender scene frame and `mol.uframe`
   for the zero-based MDAnalysis frame. Set `subframes`, `interpolate`,
   `offset`, `average`, and `correct_periodic` before scrubbing. Call
   `mol.set_frame(scene_frame)` when a handler is not driving updates, then
   verify `position`, `uframe`, selections, calculations, annotations, and box.
4. Add text/measurement overlays from `mol.annotations`. Use the dynamic
   keyword-only `add_*` methods and keep returned interfaces for later edits;
   selections may be strings or `MDAnalysis.AtomGroup` objects. Toggle one
   annotation with `a.visible` or all with `mol.annotations.visible`.
5. Use `mol.selections.from_string(...)` to create a named boolean attribute
   from an MDAnalysis selection string, or `from_atomgroup(...)` when the group
   already exists. Verify its UI item `message` is empty and that
   `mol.named_attribute(name)` changes on frame updates when `updating=True`.
6. Use `mol.annotations.add_simulation_box(...)` only when the current timestep
   has dimensions. It updates with frames and supports triclinic, compact, and
   lattice modes; it is not a substitute for trajectory wrapping.
7. For an active IMD server, call `StreamingTrajectory.load(topology,
   coordinates="imd://host:port", ...)`. Treat each Blender frame change as
   “advance to next received frame,” not random access. Stop on `StopIteration`
   or report the connection error; do not promise timeline scrubbing.
8. Save the Blender file through normal Blender save handling so the
   `<blend-path>.MNSession` sidecar is written when there are picklable session
   entities. On reopen, verify the sidecar and file-backed source paths resolve,
   entities are registered, visible draw handlers are present or explicitly
   restored, and a frame change succeeds. Streaming IMD entities are not
   supported by `reload_entity()` and should be treated as live runtime inputs.
   Use `session.load(blend_path)` only when deliberately repairing a session.

## Safety and validation gates

- Do not substitute a pure-Python import for a Blender host: object creation,
  named mesh attributes, handlers, draw geometry, and session restoration need
  `bpy`, `databpy`, and the active Blender context.
- Before committing a selection or annotation, validate its string/group type
  and non-empty result where the operation requires coordinates or a COM.
  Invalid changes should remain visible in the selection item's `message` or
  raise during annotation creation; repair the input rather than hiding it.
- Use `reset_playback()` to return `subframes=offset=average=0`,
  `correct_periodic=False`, and `interpolate=False`.
- Periodic correction is only valid for orthorhombic dimensions (all three
  angles 90°). Leave it off for triclinic cells and inspect the box instead.
- Keep annotation drawing cheap: calculate/cache groups and analyses in
  `defaults()`/`validate()`, and do only lightweight draw calls in `draw()`.
- Treat stale paths, unavailable IMD servers, missing custom annotation class
  definitions, invalid Blender context, and stale draw handlers as explicit
  diagnosis/repair conditions covered in [troubleshooting.md](references/troubleshooting.md);
  do not assume missing source data or a live IMD endpoint can be replaced.

## Minimal verification examples

For a small local trajectory, create `mol`, add two styles with distinct valid
selections, add `mol.annotations.add_com(selection="all", name="COM")`, move
between scene frames 0 and 1 (or the first two valid frames), and assert the
position and COM annotation remain live. Then set an invalid selection string,
confirm an error is recorded, replace it with `name CA` or another valid local
selection, and confirm recovery without network access.

For persistence, save to a temporary Blender path, confirm `<path>.MNSession`,
reopen with the same local files, and advance one frame. Separately call
`MNSession.load()` on a deliberately absent path and verify the expected
`FileNotFoundError`; do not download replacements. See the detailed contracts
in [streaming-and-persistence.md](references/streaming-and-persistence.md).
