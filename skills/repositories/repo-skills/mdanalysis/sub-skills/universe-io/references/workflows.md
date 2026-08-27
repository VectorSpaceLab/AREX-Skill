# Universe I/O Workflows

These workflows are self-contained patterns for MDAnalysis Universe loading, synthetic construction, trajectory iteration, in-memory coordinates, merging, and basic writing.

## Load a Topology and Coordinates

1. Identify whether the first input is a topology-only file, a coordinate file that also contains topology records, or a topology object.
2. Use explicit format keywords when inference is ambiguous:

```python
import MDAnalysis as mda

u = mda.Universe(
    topology_file,
    trajectory_file,
    topology_format="PSF",  # only when extension/content inference is ambiguous
    format="DCD",           # only when coordinate inference is ambiguous
)
```

3. Validate the loaded system before analysis or writing:

```python
assert len(u.atoms) > 0
assert u.trajectory.n_atoms == len(u.atoms)
ts = u.trajectory.ts
assert ts.positions.shape == (len(u.atoms), 3)
```

4. If only one coordinate/topology file is supplied, remember that MDAnalysis may use it as both topology source and single-frame coordinate source when the format supports both.

## Load Multiple Coordinate Files

Use a list or tuple when consecutive coordinate files should behave as one virtual trajectory:

```python
u = mda.Universe(topology_file, [traj_a, traj_b, traj_c])
print(len(u.trajectory))
```

Guidelines:

- A one-item list is treated as a single coordinate file rather than a chained trajectory.
- For a multi-file chain, each member must be a compatible coordinate file for the same topology atom count.
- If different files need different readers or optional dependencies, troubleshoot them independently with explicit `format=` or route to `../formats-converters/SKILL.md`.

## Build a Synthetic Universe

Use `Universe.empty` when there is no input file or when testing a workflow without repository data files.

```python
import numpy as np
import MDAnalysis as mda

u = mda.Universe.empty(
    n_atoms=4,
    n_residues=2,
    n_segments=1,
    n_frames=3,
    atom_resindex=np.array([0, 0, 1, 1]),
    trajectory=True,
)
u.add_TopologyAttr("names", ["A1", "A2", "B1", "B2"])
u.add_TopologyAttr("types", ["A", "A", "B", "B"])
u.add_TopologyAttr("resnames", ["RA", "RB"])
u.add_TopologyAttr("resids", [1, 2])
u.add_TopologyAttr("segids", ["SYS"])

for frame_index, ts in enumerate(u.trajectory):
    ts.positions[:] = frame_index + np.arange(12, dtype=np.float32).reshape(4, 3)
    ts.dimensions = np.array([20, 20, 20, 90, 90, 90], dtype=np.float32)
```

Validation checklist:

- `len(atom_resindex) == n_atoms`.
- `atom_resindex.max() < n_residues` and all values are non-negative.
- `len(residue_segindex) == n_residues` when provided.
- `residue_segindex.max() < n_segments` and all values are non-negative.
- Topology attributes are supplied at the right level: atom-level lists match `n_atoms`, residue-level lists match `n_residues`, segment-level lists match `n_segments`.

Route deeper topology attribute design to `../selections-topology/SKILL.md`.

## Attach a NumPy Trajectory to an Existing Universe

Use `MemoryReader` explicitly when replacing coordinates with arrays.

```python
import numpy as np
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

u = mda.Universe.empty(3, trajectory=False)
u.add_TopologyAttr("names", ["A", "B", "C"])
coords = np.zeros((5, 3, 3), dtype=np.float32)  # fac: frames, atoms, xyz
coords[:, :, 0] = np.arange(5, dtype=np.float32)[:, None]

u.load_new(coords, format=MemoryReader, order="fac")
assert len(u.trajectory) == 5
assert u.trajectory.n_atoms == 3
```

Use `Universe(..., in_memory=True)` or `u.transfer_to_memory()` when an existing disk-backed trajectory should be copied into memory for faster repeated access or in-place coordinate edits.

## Iterate a Trajectory Safely

```python
frame_summaries = []
for ts in u.trajectory:
    positions = ts.positions.copy()
    box = None if ts.dimensions is None else ts.dimensions.copy()
    frame_summaries.append((ts.frame, positions.shape, box))
```

Guidelines:

- Copy positions if you need stable values after the loop; `u.atoms.positions` and `u.trajectory.ts` update as the current frame changes.
- Check whether `len(u.trajectory)` is available before relying on progress bars or random indexing; stream readers may not know length.
- Use `u.trajectory[start:stop:step]` for readers with random access. For stream readers, only one-pass forward iteration may be supported.
- Treat unit cell dimensions as optional. Some files have no box, some have zeros, and some have per-frame boxes.

## Replace Coordinates with `load_new`

```python
result = u.load_new(new_coordinate_file, format="XTC", in_memory=False)
assert result is u
assert u.trajectory.n_atoms == len(u.atoms)
```

Troubleshooting tips:

- If `load_new` raises `TypeError`, first check extension and explicit `format=`.
- If it raises `ValueError` about atom counts, the topology and coordinate source do not describe the same number of atoms.
- If the input is an array, confirm shape/order and pass `format=MemoryReader` plus `order=`.

## Merge Atom Groups and Preserve Coordinates

`Merge` creates a new topology and current-frame structure. It does not automatically preserve a full trajectory.

```python
import numpy as np
import MDAnalysis as mda
from MDAnalysis.coordinates.memory import MemoryReader

subset = u.atoms[:10]
merged = mda.Merge(subset)

coords = np.array([subset.positions.copy() for _ in u.trajectory], dtype=np.float32)
merged.load_new(coords, format=MemoryReader, order="fac")
```

Use cases:

- Reorder atoms before a write: `mda.Merge(u.atoms[[2, 0, 1]])`.
- Combine groups from separate Universes into one single-frame system.
- Create a protein-only Universe before writing a focused trajectory.

Caveats:

- Empty groups are invalid.
- Topology attributes that are not common to all merged groups can be dropped.
- Full subsystem trajectory preservation requires extracting coordinates and attaching them with `MemoryReader`.

## Basic Writing with `AtomGroup.write`

Write the current frame:

```python
u.atoms.write("snapshot.pdb")
```

Write every frame if the target format supports multiple frames:

```python
u.atoms.write("trajectory.xtc", frames="all")
```

Write selected frames:

```python
u.atoms.write("every_other.pdb", frames=u.trajectory[::2])
```

Guidelines:

- Use an explicit filename and extension or `file_format=`.
- Do not call `write` on an empty atom group.
- Do not pass a scalar integer to `frames`; move to the frame and write the current frame, or pass a one-frame slice/iterator.
- Ensure the writer supports the requested number of frames and atom count.
- For transformed output, wrap/unwrap/fit/center pipelines, or output trajectory recipes, route to `../transformations-writing/SKILL.md`.

## Direct Writer Factory Pattern

Use direct writers when you need control over a loop:

```python
from MDAnalysis.coordinates import writer

with writer("out.pdb", n_atoms=len(u.atoms), multiframe=True) as out:
    for ts in u.trajectory:
        out.write(u.atoms)
```

Guidelines:

- Pass `n_atoms` for trajectory writers.
- Write an `AtomGroup` or `Universe` as supported by the writer; many writers do not accept bare `Timestep` objects.
- Match `multiframe` to the intended output: `True` for trajectories, `False` for a single snapshot, `None` when fallback is acceptable.

## Minimal Validation Before Handing Off

Before routing to analysis, selections, transformations, or converters, collect:

```python
summary = {
    "n_atoms": len(u.atoms),
    "n_residues": len(u.residues),
    "n_segments": len(u.segments),
    "trajectory_class": type(u.trajectory).__name__ if hasattr(u, "trajectory") else None,
    "n_frames": getattr(u.trajectory, "n_frames", None),
    "coordinate_atoms": getattr(u.trajectory, "n_atoms", None),
    "position_shape": tuple(u.trajectory.ts.positions.shape),
    "dimensions": None if u.trajectory.ts.dimensions is None else u.trajectory.ts.dimensions.tolist(),
}
```

Then verify:

- `summary["n_atoms"] == summary["coordinate_atoms"]`.
- Required topology attributes exist for the next task.
- Box dimensions are present and nonzero before periodic calculations or wrapping.
- The coordinate source is in memory only when memory cost is acceptable.
