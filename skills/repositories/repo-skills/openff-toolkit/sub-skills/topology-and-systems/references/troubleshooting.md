# Topology Troubleshooting

Use this when `Topology` assembly, PDB loading, conversion, export, or hierarchy handling fails.

## `MissingUniqueMoleculesError`

Typical message:

```text
Topology.from_openmm requires a list of Molecule objects passed as unique_molecules, but None was passed.
```

Cause:

- `Topology.from_openmm(...)` or `Topology.from_mdtraj(...)` was called without reference `Molecule` objects.

Fix:

- Build one OpenFF `Molecule` for each chemically distinct species.
- Pass them as `unique_molecules=[...]`.
- Include species even if they appear many times; include each species only once.

## Duplicate Unique Molecules

Symptom:

- `DuplicateUniqueMoleculeError` when converting from OpenMM/MDTraj.

Cause:

- Two entries in `unique_molecules` are graph-indistinguishable under the matching rules used for the source topology.
- This can happen with differently ordered copies of the same molecule or references that differ only in information not represented by the source topology.

Fix:

- Remove duplicate references.
- If the source topology lacks bond orders/stereochemical detail, do not expect it to distinguish references based on that missing information.

## No Match Found for Molecule

Typical message:

```text
No match found for molecule C6H12
```

Cause:

- A connected component in the source topology is absent from `unique_molecules` or has different element/connectivity.

Fix:

- Add the missing species to `unique_molecules`.
- Check formal charges, protonation, hydrogens, and connectivity in the reference `Molecule`.
- Confirm the source topology has bonds between atoms that should be one molecule.

## Missing `CONECT` Records in PDB

Typical diagnostic:

```text
No match found for molecule C. ... If this molecule is coming from PDB, please ensure that the file contains CONECT records.
```

Cause:

- A HETATM molecule was read as isolated atoms because the PDB did not encode its bonds.

Fix:

- Add valid `CONECT` records for all HETATM/nonstandard molecule bonds.
- Ensure `CONECT` records represent chemical bonds, not constraints or proximity contacts.
- Provide exact reference `Molecule` objects through `unique_molecules`.
- If possible, start from SDF/MOL2 for chemistry and use the PDB only for coordinates.

## Unassigned Chemistry in PDB

Symptom:

- `UnassignedChemistryInPDBError` or a diagnostic that atoms/bonds could not be assigned.

Common causes:

- Missing explicit hydrogens.
- Nonstandard residue names or atom names.
- Unsupported modified residues, covalent ligands, cofactors, or polymer chemistry.
- HETATM molecules missing elements or `CONECT` records.
- Reference `Molecule` is a substructure/superstructure rather than an exact match.
- Incorrect protonation or formal charges in the reference molecule.

Fix order:

1. Confirm the PDB has all hydrogens and correct element columns.
2. Confirm standard protein atom/residue names where templates are expected.
3. Pass exact HETATM references through `unique_molecules`.
4. Add/fix `CONECT` records for HETATM molecules.
5. Only consider experimental custom substructures when the chemistry is truly polymer-like and unsupported by standard templates.

## Atom Name Uniqueness Issues

Symptoms:

- PDB export or downstream tools complain about duplicate atom names.
- Names are blank or repeated after conversion.
- PDB output changes atom names unexpectedly.

Fix:

- Use `ensure_unique_atom_names="residues"` for PDB/protein-style export.
- Use `ensure_unique_atom_names=True` for molecule-wide uniqueness.
- Use `False` only when preserving names is more important than uniqueness.
- Remember that PDB truncates atom names; long generated names can still collide after truncation.

## Missing Positions for PDB Export or Visualization

Symptoms:

- `Topology.to_file(..., positions=None)` fails because molecule conformers are missing.
- `Topology.visualize()` raises a missing-conformers error.

Fix:

- Provide explicit positions with shape `(topology.n_atoms, 3)` and length units.
- Or generate/attach conformers for every molecule before calling `to_file` or `visualize`.
- Use zero coordinates only for smoke tests or topology-only diagnostics, not for physical simulation setup.

## Optional Package Failures

`Topology` methods have optional dependencies:

- `from_pdb`, `from_openmm`, `to_openmm`, and `to_file` require `openmm`.
- `from_mdtraj` requires `mdtraj` and internally uses OpenMM conversion.
- `visualize` requires `nglview` and a notebook-compatible environment.
- SMARTS and PDB substructure perception generally depend on an available cheminformatics toolkit; RDKit and the built-in wrapper were available in the inspected environment.

Fix:

- If the dependency is absent, either install/activate the appropriate backend environment or route to `../toolkit-backends/SKILL.md`.
- Do not claim OpenEye, AmberTools, or NAGL behavior is available unless the active environment proves it.

## Hierarchy Metadata Surprises

Symptoms:

- Residue or chain counts differ after OpenMM conversion.
- `topology.residues` raises `AttributeError`.
- Metadata defaults like `UNK`, `0`, or `X` appear in OpenMM output.
- Residues with the same number are not globally sorted.

Causes:

- OpenFF treats hierarchy metadata as optional interoperability metadata.
- OpenMM requires every atom to belong to a residue and chain, so defaults are filled during conversion.
- `Topology.to_openmm()` groups only contiguous atoms with matching metadata and never spans a residue/chain across OpenFF molecule boundaries.
- `hierarchy_iterator("residues")` skips molecules without residue schemes; dynamic attributes require consistent scheme availability.

Fix:

- Inspect atom metadata directly on representative atoms.
- Use `list(topology.hierarchy_iterator("residues"))` rather than assuming `topology.residues` always exists.
- Keep molecule order as the source of topology ordering; do not expect residue numbers to sort across molecules.
- Avoid manual metadata edits unless the downstream package requirements are understood.

## Constraint Conflicts

Symptoms:

- Re-adding a constraint raises a constraint-exists error.
- A pair appears twice in `constrained_atom_pairs`.

Cause:

- Constraints are stored symmetrically under both `(i, j)` and `(j, i)`.
- Replacing an explicit distance with `True`, or adding the same unspecified constraint twice, is invalid.

Fix:

- Check `topology.is_constrained(i, j)` before adding.
- Remove with `topology.add_constraint(i, j, False)` before changing the distance.
- Treat the dictionary's two entries per constrained pair as implementation detail, not double constraints.

## Interchange/OpenMM Export Boundary Errors

Symptoms:

- `ForceField.create_interchange(topology)` or `ForceField.create_openmm_system(topology)` fails after topology assembly.

Likely causes:

- The topology is chemically valid but not parameterizable by the selected force field.
- Partial charges or toolkit backends are unavailable.
- Required force field files or optional export packages are missing.
- Protein/small-molecule mixed workflows need a compatible protein force field or engine-specific integration path.

Fix:

- Keep topology-level checks here: molecule counts, species identity, metadata, positions, and box vectors.
- Route SMIRNOFF parameter assignment, charge generation, and handler troubleshooting to `../smirnoff-force-fields/SKILL.md`.
- Route backend installation/registry problems to `../toolkit-backends/SKILL.md`.
