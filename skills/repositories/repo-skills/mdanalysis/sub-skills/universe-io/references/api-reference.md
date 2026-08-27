# Universe I/O API Reference

This reference summarizes the MDAnalysis 2.11.0-dev0 Universe, coordinate reader/writer, and basic output APIs most useful for loading, constructing, iterating, validating, and writing molecular systems.

## Core Entry Points

| Entry point | Signature | Use |
| --- | --- | --- |
| `MDAnalysis.Universe` | `Universe(topology=None, *coordinates, all_coordinates=False, format=None, topology_format=None, transformations=None, guess_bonds=False, vdwradii=None, fudge_factor=0.55, lower_bound=0.1, in_memory=False, context='default', to_guess=('types', 'masses'), force_guess=(), in_memory_step=1, **kwargs)` | Build a system from a topology object/file-like/input plus optional coordinate inputs. |
| `Universe.empty` | `Universe.empty(n_atoms, n_residues=1, n_segments=1, n_frames=1, atom_resindex=None, residue_segindex=None, trajectory=False, velocities=False, forces=False)` | Construct a synthetic topology, optionally with a `MemoryReader` trajectory. |
| `Universe.load_new` | `u.load_new(filename, format=None, in_memory=False, in_memory_step=1, **kwargs)` | Replace or attach coordinates to an existing Universe. Returns `u`. |
| `MDAnalysis.Merge` | `Merge(*args)` | Create a new one-structure Universe from one or more non-empty `AtomGroup` objects. |
| `MDAnalysis.Writer` | `Writer(filename, n_atoms=None, **kwargs)` | Factory for output writers inferred from filename/format. |
| `MDAnalysis.coordinates.reader` | `reader(filename, format=None, **kwargs)` | Instantiate a coordinate reader directly. |
| `MDAnalysis.coordinates.writer` | `writer(filename, n_atoms=None, **kwargs)` | Instantiate a coordinate writer directly. |
| `AtomGroup.write` | `ag.write(filename=None, file_format=None, filenamefmt='{trjname}_{frame}', frames=None, **kwargs)` | Write an atom group as coordinates, a trajectory, or a selection format depending on extension/format. |

## `Universe` Loading Semantics

- `Universe()` without a topology is invalid; use `Universe.empty(...)` for synthetic systems or `Universe(None)` only for advanced cases that intentionally pass no topology.
- `topology` is usually a topology file, coordinate file with topology records, topology object, parser-supported structure, or file-like object. If it is not already a topology object, MDAnalysis chooses a topology parser from `topology_format` or filename/content hints.
- Positional `*coordinates` are coordinate files, lists/tuples of coordinate files, arrays, or reader-supported objects. MDAnalysis resolves them after topology parsing and calls `load_new` when coordinates are present.
- `format` controls coordinate reader selection; `topology_format` controls topology parser selection. Do not assume one implies the other, especially for single files that can serve as both topology and coordinates.
- `all_coordinates=True` treats all positional inputs, including the first, as coordinates when the topology has already been supplied separately.
- `to_guess=('types', 'masses')` guesses common topology attributes by default after parsing. Use `to_guess=()` when a synthetic or minimal topology should remain unguessed.
- `guess_bonds=True` is deprecated behavior; route bond/topology guessing decisions to `../selections-topology/SKILL.md` unless the immediate task is only diagnosing load behavior.
- `transformations=` attaches on-the-fly coordinate transformations during Universe construction; route pipeline design and transformed-output recipes to `../transformations-writing/SKILL.md`.

## `Universe.empty` Details

- `n_atoms`, `n_residues`, and `n_segments` define topology sizes. If `n_atoms` is zero, residues and segments become zero.
- `atom_resindex` maps each atom to a residue index. Its length must match `n_atoms`, and values must reference valid residues.
- `residue_segindex` maps each residue to a segment index. Its length must match `n_residues`, and values must reference valid segments.
- If `n_residues > 1` but `atom_resindex` is omitted, MDAnalysis warns and places all atoms in the first residue.
- If `n_segments > 1` but `residue_segindex` is omitted, MDAnalysis warns and places all residues in the first segment.
- `trajectory=True` or `n_frames > 1` attaches a `MemoryReader` filled with zeros of shape `(n_frames, n_atoms, 3)` and order `fac`.
- `velocities=True` and `forces=True` add zero-filled arrays matching the coordinate shape.
- Add attributes needed for writing or downstream tasks with `u.add_TopologyAttr(...)`; detailed attribute semantics belong in `../selections-topology/SKILL.md`.

## Coordinate Readers and `load_new`

- `load_new(None)` returns the Universe unchanged.
- A single-item list is treated like one coordinate file; a multi-item list uses a chained reader when supported.
- If no coordinate reader can be found, `load_new` raises `TypeError` wrapping the reader lookup failure.
- MDAnalysis passes `n_atoms=len(u.atoms)` to coordinate readers that need an atom count.
- After opening coordinates, MDAnalysis checks `u.trajectory.n_atoms == len(u.atoms)` and raises `ValueError` when topology and trajectory atom counts differ.
- `in_memory=True` transfers coordinates into a `MemoryReader`; `in_memory_step` controls frame subsampling during transfer.
- For NumPy arrays, pass `format=MDAnalysis.coordinates.memory.MemoryReader` or rely on MemoryReader hints when unambiguous. The default coordinate order is `fac` unless an `order=` keyword such as `afc` is required.

## `MemoryReader` Shapes

`MemoryReader` stores coordinates in memory and supports positions, optional velocities, optional forces, and optional unit cell dimensions.

Common coordinate array orders:

| Order | Shape meaning |
| --- | --- |
| `fac` | `(n_frames, n_atoms, 3)`; common for synthetic trajectories. |
| `afc` | `(n_atoms, n_frames, 3)`; common from some timeseries outputs. |
| `acf` | `(n_atoms, 3, n_frames)`; less common, but supported through explicit `order`. |

Validation points:

- Coordinate arrays must be NumPy arrays with exactly one atom axis, one coordinate axis of length 3, and one frame axis.
- Optional velocities and forces must match the coordinate array shape.
- `dimensions` may be a single `(6,)` box or per-frame `(n_frames, 6)` array; invalid shapes raise `ValueError`.
- Changes to `u.atoms.positions` on a MemoryReader-backed frame persist in that in-memory frame.

## Trajectory and `Timestep` Objects

- `u.trajectory` is a reader. It exposes `n_atoms`, `n_frames` when known, `filename`, indexing/slicing where supported, and current `ts`.
- Iterating `for ts in u.trajectory:` updates the Universe's current positions and yields `Timestep` objects.
- `ts.frame` is the current frame index. `ts.positions` has shape `(n_atoms, 3)` when coordinates exist. `ts.dimensions` is a six-value unit cell array when available.
- Stream readers may not support random access, length, rewinding, `Writer`, or `OtherWriter`; design streaming workflows as one-pass operations.
- Reader slicing rejects invalid stream `start`, `stop`, and `step` combinations; positive integer steps are required for streams.

## `Merge` Behavior

- `Merge(*args)` requires one or more non-empty `AtomGroup` objects; it raises `ValueError` for no arguments or empty groups and `TypeError` for non-AtomGroup inputs.
- The merged Universe keeps only topology attributes common to all input groups' universes.
- The result is a single-structure Universe, not a full trajectory. To preserve selected trajectory coordinates, build an array of selected positions and call `merged.load_new(array, format=MemoryReader)`.
- `Merge(single_atomgroup)` is useful for reordering or subsetting atoms before writing.

## Writer APIs

- `MDAnalysis.Writer(filename, n_atoms=None, **kwargs)` and `coordinates.writer(filename, n_atoms=None, **kwargs)` choose writers from extension or explicit `format=`.
- `n_atoms` is required for many multiframe trajectory writers and protects against writing the wrong atom count.
- `multiframe=True` requests a trajectory writer; `multiframe=False` requests a single-frame writer; `None` tries trajectory writers first and falls back to single-frame writers.
- `filename=None` selects a null writer through lower-level writer lookup; use only when deliberately discarding output.
- Writer keywords vary by format. Common ones include `start`, `step`, `dt`, `convert_units`, and format-specific options such as PDB bond handling.

## `AtomGroup.write` Basics

- `ag.write(...)` rejects empty atom groups with `IndexError`.
- `filename=None` creates a name from `filenamefmt` using the current trajectory filename and frame; prefer an explicit filename in agent-written code.
- `file_format=` overrides extension-based detection and is case-insensitive for common format names.
- `frames=None` writes only the current frame. `frames='all'`, a slice, a boolean mask, an index array, or a frame iterator writes multiple frames when the selected writer supports it.
- A scalar integer is not accepted for `frames`; use `u.trajectory[[i]]`, `u.trajectory[i:i+1]`, or set the current frame and keep `frames=None`.
- If `frames` comes from a different trajectory than the atom group, MDAnalysis raises `ValueError`.
- If `frames` requests more than one frame while `multiframe=False`, MDAnalysis raises `ValueError`.

## Direct Factories vs High-Level Universe

Use high-level `Universe(...)` for most user tasks because it binds topology, coordinates, trajectory, and atom groups. Use `coordinates.reader(...)` or `coordinates.writer(...)` when implementing format probes, testing a reader/writer directly, or writing low-level utilities that do not need a full Universe.
