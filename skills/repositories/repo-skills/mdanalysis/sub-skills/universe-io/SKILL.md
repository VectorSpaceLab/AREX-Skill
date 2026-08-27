---
name: universe-io
description: "Load, construct, inspect, iterate, and write molecular systems
  with MDAnalysis Universe, readers, writers, and synthetic in-memory systems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Universe I/O

Use this sub-skill when an MDAnalysis task starts from creating or loading a molecular system, attaching coordinates, iterating trajectories, validating coordinate/topology compatibility, or writing basic coordinate output.

## Read First

- `references/api-reference.md` for exact entry points, signatures, and object responsibilities.
- `references/workflows.md` for loading, synthetic `Universe.empty`, in-memory trajectories, trajectory iteration, `Merge`, and basic writing recipes.
- `references/troubleshooting.md` for format, atom-count, topology-attribute, timestep, writer, and optional dependency failures.
- `scripts/universe_smoke_check.py` for a self-contained import and synthetic Universe check that does not use external test data files.

## Use This For

- Pairing topology and coordinate inputs with `MDAnalysis.Universe(topology, *coordinates, format=..., topology_format=...)`.
- Constructing small synthetic systems with `Universe.empty(...)` and optional `MemoryReader` trajectories.
- Replacing or attaching coordinates with `Universe.load_new(...)`, including NumPy arrays via `MemoryReader`.
- Iterating `u.trajectory`, reading `Timestep` positions/dimensions/frame/time, and validating frame counts.
- Creating one-structure subsystems with `Merge(...)` and adding a new in-memory trajectory when needed.
- Choosing `MDAnalysis.Writer(...)`, `MDAnalysis.coordinates.reader(...)`, `MDAnalysis.coordinates.writer(...)`, or `AtomGroup.write(...)` for basic output.

## Route Elsewhere

- Selection strings, custom topology attributes, groups, guessing semantics, and topology manipulation belong in `../selections-topology/SKILL.md`.
- RMSD/RDF/contacts/distances/hydrogen-bond and custom `AnalysisBase` workflows belong in `../analysis-workflows/SKILL.md`.
- Transformation pipelines, wrap/unwrap/fit/center operations, and transformed-output recipes belong in `../transformations-writing/SKILL.md`.
- Optional converter interoperability, fetchers, auxiliary data, and format dependency triage belong in `../formats-converters/SKILL.md`.

## Quick Checks

- Confirm `len(u.atoms)` equals `u.trajectory.n_atoms` after load or `load_new`.
- Confirm needed topology attributes exist before writing or downstream work, e.g. names, types, masses, residues, segments, bonds.
- Confirm `u.trajectory.ts.positions.shape == (len(u.atoms), 3)` and `u.trajectory.ts.dimensions` is meaningful before box-dependent operations.
- Prefer explicit `format=` or `topology_format=` for streams, ambiguous extensions, arrays, or filenames that MDAnalysis cannot infer.
