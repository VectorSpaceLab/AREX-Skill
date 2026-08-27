---
name: molecules-and-io
description: "Build, inspect, convert, serialize, charge, conformer-generate,
  visualize, and validate OpenFF Molecule objects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# OpenFF Molecules and IO

Use this sub-skill when a task is centered on `openff.toolkit.Molecule` creation, inspection, conversion, serialization, conformer generation, partial charges, stereochemistry or tautomer enumeration, SMARTS matching, graph/isomorphism checks, or molecule visualization.

## Start Here

- Read `references/api-reference.md` for verified constructor, conversion, matching, conformer, charge, and visualization API details.
- Read `references/workflows.md` for self-contained recipes covering SMILES, mapped SMILES, files, conformers, charges, stereochemistry, tautomers, SMARTS, round-trips, and visualization.
- Read `references/troubleshooting.md` when molecule creation, file IO, toolkit backend, stereochemistry, partial charge, conformer, or PDB handling fails.
- Run `scripts/smoke_molecule_workflow.py --help` to inspect the bundled smoke workflow, then try a tiny molecule with `--smiles CCO`.

## Best-Fit Tasks

- Create molecules from SMILES or mapped SMILES and preserve or validate atom ordering.
- Read or write small-molecule `SDF`, `MOL`, `SMI`, or `PDB` outputs through `Molecule.from_file()` and `Molecule.to_file()`.
- Convert between OpenFF `Molecule`, RDKit molecules, and OpenEye molecules when the corresponding backend is available.
- Generate conformers, assign supported molecule-level partial charges, enumerate stereoisomers or tautomers, and inspect the resulting molecules.
- Match SMARTS patterns, compare molecules by isomorphism, export a NetworkX graph, or visualize molecules in notebooks.

## Boundaries

- For multi-molecule systems, `Topology.from_molecules()`, `Topology.from_pdb()`, `Topology.to_file()`, hierarchy iteration, OpenMM/MDTraj conversion, or system export, use `../topology-and-systems/SKILL.md`.
- For `ForceField` loading, SMIRNOFF parameter assignment, `create_interchange()`, `create_openmm_system()`, or parameter handler modification, use `../smirnoff-force-fields/SKILL.md`.
- For optional toolkit installation, backend registry ordering, wrapper availability, or advanced toolkit selection policy, use `../toolkit-backends/SKILL.md`.

## Safe Defaults

- Prefer `Molecule.from_smiles(smiles, allow_undefined_stereo=False)` when stereochemistry matters; explicitly explain any fallback to `allow_undefined_stereo=True`.
- Prefer `Molecule.from_mapped_smiles()` for atom-order-sensitive work; ordinary `from_smiles()` stores atom maps but does not use them for ordering.
- Prefer `SDF` for file round-trips that need molecular graph information; avoid treating bare `PDB` or `XYZ` as sufficient graph sources.
- In environments with RDKit and BuiltIn wrappers only, expect `RDKit` conformers and `mmff94`/`gasteiger` charges plus BuiltIn `zeros`/`formal_charge`; do not promise OpenEye, AmberTools, or NAGL-only methods.
