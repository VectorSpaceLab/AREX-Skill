# Universe I/O Troubleshooting

Use this guide for MDAnalysis load, construct, iterate, and basic write failures. For selection syntax and topology attribute design, route to `../selections-topology/SKILL.md`; for analysis algorithm failures, route to `../analysis-workflows/SKILL.md`; for transformation/output pipeline failures, route to `../transformations-writing/SKILL.md`; for optional converters and specialized format extras, route to `../formats-converters/SKILL.md`.

## Fast Diagnosis Checklist

1. Print the exact `Universe(...)`, `load_new(...)`, reader, writer, or `AtomGroup.write(...)` call.
2. Check whether format inference is relying on a filename extension, a file-like object, a NumPy array, or a custom object.
3. Confirm topology atom count and coordinate atom count match.
4. Confirm required topology attributes exist before writing or downstream work.
5. Confirm the current `Timestep` has positions and meaningful dimensions if the task needs coordinates or periodic boxes.
6. If a format requires optional dependencies, isolate that format and route optional dependency decisions to `../formats-converters/SKILL.md`.

## Symptoms, Causes, Fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `TypeError: Topology argument required to make Universe` | `Universe()` was called without a topology. | Use `Universe.empty(n_atoms, ...)` for synthetic systems or pass a real topology/source file. |
| `FileNotFoundError`, `OSError`, or parser-specific open error | Topology or coordinate filename does not exist or is unreadable. | Validate path existence outside runtime skill content; in generated examples prefer synthetic data. |
| `ValueError` saying a file is not a valid topology format | Topology parser inference failed. | Pass `topology_format=...` or choose an input that contains topology records. |
| `TypeError` from `load_new` saying no coordinate reader was found | Coordinate reader inference failed or `format=` is unsupported. | Pass explicit `format=...`, use `MemoryReader` for arrays, or check supported coordinate formats. |
| Unknown coordinate trajectory format | Extension or explicit `format` does not map to a registered reader. | Correct the extension, pass a supported `format`, or route optional format dependencies to `../formats-converters/SKILL.md`. |
| Topology and trajectory atom counts differ | Topology file and coordinate file describe different systems or a NumPy array has the wrong atom axis/order. | Use matching files; for arrays, verify shape and `order`; for subsets, create a matching topology with `Merge` before `load_new`. |
| `Universe.empty` warning about residues or segments | Multiple residues/segments were requested without mapping arrays. | Provide `atom_resindex` and `residue_segindex` with valid lengths and indexes. |
| `Universe.empty` raises mapping/index errors | Mapping arrays have wrong lengths or out-of-range values. | Validate `len(atom_resindex) == n_atoms`, `max(atom_resindex) < n_residues`, `len(residue_segindex) == n_residues`, and `max(residue_segindex) < n_segments`. |
| Missing attribute error or `NoDataError` for names, masses, bonds, dimensions, velocities, or forces | The topology or trajectory does not contain that data, or it was not added to a synthetic Universe. | Add required topology attributes for synthetic systems; route attribute design/guessing to `../selections-topology/SKILL.md`. |
| `ts.dimensions` is `None`, zeros, or changes unexpectedly | Input lacks unit cell data, uses single-frame/format-specific box behavior, or per-frame dimensions differ. | Check each frame; set dimensions on synthetic trajectories; route periodic transformations to `../transformations-writing/SKILL.md`. |
| Direct writer raises no writer for format | Output extension/format has no registered writer or wrong `multiframe` mode was requested. | Use a supported output extension, pass `format=...`, and choose `multiframe=True`, `False`, or `None` correctly. |
| Writer complains about atom count | Writer was initialized with wrong `n_atoms`, or the written object has a different atom count. | Initialize writer with `n_atoms=len(ag)` and write the same-size AtomGroup each frame. |
| `AtomGroup.write` rejects empty group | The selected AtomGroup has zero atoms. | Check `len(ag) > 0`; route selection debugging to `../selections-topology/SKILL.md`. |
| `AtomGroup.write` rejects scalar `frames` | `frames` cannot be a single integer. | Move the trajectory to that frame and write current frame, or pass a one-frame slice/iterator. |
| `AtomGroup.write` says frame iterator belongs to another trajectory | `frames=` came from a different Universe/trajectory. | Use frames from the same `u.trajectory` as the AtomGroup. |
| Bare `Timestep` writing fails for a writer | Many writers expect a `Universe` or `AtomGroup`, not a direct `Timestep`. | Write `u.atoms`, a compatible `AtomGroup`, or use a writer documented to accept the object. |
| In-memory load consumes too much memory | `in_memory=True` or `transfer_to_memory()` copied a large trajectory. | Keep disk-backed reader, use `in_memory_step`, or process frames streaming. |
| Stream reader cannot seek, slice backward, or report length | Streaming readers are one-pass and may not know `n_frames`. | Use forward iteration only or convert to memory/disk-backed format when safe. |

## Format Inference Problems

MDAnalysis uses separate registries for topology parsers, coordinate readers, and writers. A filename extension that works for a topology parser does not necessarily imply a coordinate reader or writer.

Recommended fixes:

- Use `topology_format=` for the topology/parser side.
- Use `format=` for the coordinate reader side.
- Use `file_format=` or writer `format=` for output side.
- For file-like objects such as `StringIO`, supply explicit formats because extension inference is unavailable.
- For NumPy arrays, prefer `format=MemoryReader` and explicit `order=`.

## Atom Count Mismatches

Common mismatch patterns:

- The topology comes from a full system but coordinates come from a protein-only or solvent-only trajectory.
- A `MemoryReader` coordinate array uses `afc` order but is loaded as `fac`, causing the frame/atom axes to be misread.
- A writer was opened with `n_atoms=len(u.atoms)` but a subset AtomGroup was written, or the reverse.
- `Merge` created a subset topology but coordinates from the original full system were attached.

Recovery pattern:

```python
assert len(topology_universe.atoms) == expected_coordinate_atoms
assert coords.shape[1] == len(subset)  # for fac arrays
subset_universe = mda.Merge(subset)
subset_universe.load_new(coords, format=MemoryReader, order="fac")
```

## Missing Topology Attributes

Synthetic or minimal inputs often lack names, types, masses, charges, bonds, residues, or segment identifiers. Some writers and downstream workflows may require specific attributes.

Recovery pattern for synthetic systems:

```python
u.add_TopologyAttr("names", ["A", "B"])
u.add_TopologyAttr("types", ["A", "B"])
u.add_TopologyAttr("resnames", ["MOL"])
u.add_TopologyAttr("resids", [1])
u.add_TopologyAttr("segids", ["SYS"])
```

If the task involves choosing, guessing, or manipulating topology attributes, route to `../selections-topology/SKILL.md`.

## Unit Cell and Timestep Surprises

- `u.dimensions` proxies the current timestep's unit cell; changing frames can change dimensions.
- MemoryReader dimensions can be one `(6,)` box broadcast to frames or per-frame `(n_frames, 6)` values.
- Some file formats do not store dimensions; others store dimensions but not angles or full triclinic information.
- Periodic analysis, wrapping, unwrapping, and `NoJump` need meaningful dimensions; route those workflows to `../transformations-writing/SKILL.md`.

## Writer Mode Mismatches

When a write fails, identify whether the writer is single-frame, multiframe, or selected by fallback:

```python
from MDAnalysis.coordinates import writer

with writer("out.pdb", n_atoms=len(u.atoms), multiframe=True) as out:
    for ts in u.trajectory:
        out.write(u.atoms)
```

Fixes:

- Use `multiframe=True` when writing many frames.
- Use `multiframe=False` or `frames=None` for a current-frame snapshot.
- Pass `n_atoms=len(ag)` for the AtomGroup you will write.
- Use `AtomGroup.write(..., frames="all")` only when the target format supports multiple frames.

## Optional Format Dependencies

Some formats and converters require optional packages such as `netCDF4`, `h5py`, `chemfiles`, `pytng`, `gsd`, `pyedr`, `rdkit`, `parmed`, or OpenMM-related dependencies. Do not install broad extras unless the user asks. First isolate whether the failing call is a basic Universe I/O problem or a format-specific optional dependency problem, then route dependency selection to `../formats-converters/SKILL.md`.
