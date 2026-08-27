---
name: topology-and-systems
description: "Assemble OpenFF Topology objects, load PDB/biopolymer systems,
  manage hierarchy metadata, constraints, OpenMM/MDTraj conversion, PDB export,
  and hand off to Interchange/OpenMM system creation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Topology and Systems

Use this sub-skill when the task is about OpenFF `Topology` objects rather than single-molecule construction or SMIRNOFF parameter editing.

## Read First

- `references/api-reference.md` for verified `Topology` method signatures, return shapes, and behavior details.
- `references/pdb-and-biopolymers.md` for PDB loading requirements, `unique_molecules`, proteins, HETATM small molecules, metadata, and hierarchy differences.
- `references/workflows.md` for common recipes: molecule lists, PDB load, OpenMM/MDTraj conversion, constraints, PDB export, and Interchange/OpenMM handoff.
- `references/troubleshooting.md` for common diagnostics and fixes around missing unique molecules, PDB chemistry assignment, atom names, optional packages, and metadata surprises.
- `scripts/smoke_topology_workflow.py` for a small self-contained smoke helper that builds a multi-copy topology and optionally writes a PDB.

## Scope

Handle requests involving:

- `Topology.from_molecules`, `add_molecule`, `add_molecules`, `unique_molecules`, and `identical_molecule_groups`.
- `Topology.from_pdb`, `from_openmm`, `from_mdtraj`, `to_openmm`, and `to_file`.
- PDB/biopolymer assumptions: explicit hydrogens, valid chemical connectivity, `CONECT`, standard residue/atom names, waters, supported ions, and custom substructure caveats.
- Hierarchy metadata and iterators: residues, chains, atom names, insertion codes, and OpenFF/OpenMM/RDKit/OpenEye differences.
- Constraints with `add_constraint`, environment matching with `chemical_environment_matches`, graph distance queries with `nth_degree_neighbors`, and visualization with `visualize`.
- Handoff boundaries between `Topology`, `ForceField.create_interchange`, `ForceField.create_openmm_system`, and downstream engine exporters.

## Route Elsewhere

- For constructing, reading, writing, charging, converting, or stereochemistry-handling individual `Molecule` objects, read `../molecules-and-io/SKILL.md`.
- For SMIRNOFF force field loading, parameter assignment details, handler edits, or force field XML authoring, read `../smirnoff-force-fields/SKILL.md`.
- For toolkit registry setup, backend availability, RDKit/OpenEye/AmberTools/NAGL installation, or charge backend troubleshooting, read `../toolkit-backends/SKILL.md`.

## Fast Decision Rules

- If the input is a list of OpenFF `Molecule` objects, start with `Topology.from_molecules(molecules)` or an empty `Topology()` plus `add_molecules`.
- If the input is a PDB with nonstandard HETATM molecules, prepare exact OpenFF `Molecule` objects and pass them through `unique_molecules`; require explicit elements and `CONECT` records for those molecules.
- If converting from OpenMM or MDTraj, pass every chemically distinct species exactly once in `unique_molecules`; the topology can contain zero, one, or many copies of each species.
- If writing or converting to OpenMM/PDB, keep `ensure_unique_atom_names="residues"` unless the task specifically needs molecule-wide uniqueness (`True`) or original names (`False`).
- If assigning force field parameters or exporting simulation files, build and validate the `Topology` here, then hand off to the force field or Interchange sub-skill boundary.
