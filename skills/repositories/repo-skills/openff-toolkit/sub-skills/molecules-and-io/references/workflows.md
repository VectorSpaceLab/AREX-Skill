# Molecule Workflows

These recipes are self-contained starting points for common `openff.toolkit.Molecule` tasks. They intentionally avoid relying on source-repository examples at runtime.

## Create a Molecule from SMILES

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("CCO", name="ethanol")
print(molecule.n_atoms, molecule.n_bonds)
print(molecule.to_smiles(isomeric=True, explicit_hydrogens=True))
```

Guidance:

- Use `allow_undefined_stereo=False` by default for chemistry-sensitive work.
- If a user provides non-isomeric SMILES for a chiral molecule, try the strict parse first, catch the stereo error, and explain the risk before using `allow_undefined_stereo=True`.
- Use `hydrogens_are_explicit=True` only when the input explicitly lists every hydrogen and missing hydrogens should be considered an error.

## Recover from Undefined Stereochemistry

```python
from openff.toolkit import Molecule
from openff.toolkit.utils import UndefinedStereochemistryError

smiles = "CC([NH3+])C(=O)[O-]"
try:
    molecule = Molecule.from_smiles(smiles)
except UndefinedStereochemistryError:
    molecule = Molecule.from_smiles(smiles, allow_undefined_stereo=True)
    stereoisomers = molecule.enumerate_stereoisomers(undefined_only=True, max_isomers=8)
    print(f"Accepted undefined stereo; {len(stereoisomers)} possible stereoisomers found")
```

Use this pattern when the task is exploratory or the user explicitly permits ambiguity. For parameterization, docking, or data generation, prefer obtaining a fully stereospecified SMILES instead of silently accepting undefined stereochemistry.

## Preserve Atom Ordering with Mapped SMILES

```python
from openff.toolkit import Molecule

mapped = "[H:1][O:2][H:3]"
molecule = Molecule.from_mapped_smiles(mapped)
assert molecule.atom(0).atomic_number == 1
assert molecule.atom(1).atomic_number == 8
print(molecule.to_smiles(mapped=True))
```

Important details:

- Mapped SMILES atom maps are 1-indexed; Python atom indices are 0-indexed.
- Use `from_mapped_smiles()` when atom order matters.
- Do not rely on `from_smiles()` to order atoms from map labels; it stores maps as metadata only.
- For partial mapping of selected atoms, parse with `from_smiles()`, read `molecule.properties["atom_map"]`, then use `molecule.remap()` if needed.

## SDF Round-Trip and Isomorphism Check

```python
from pathlib import Path
from openff.toolkit import Molecule

molecule = Molecule.from_mapped_smiles("[H:1][C:2]([H:3])([H:4])[O:5][H:6]")
molecule.generate_conformers(n_conformers=1)

path = Path("methanol.sdf")
molecule.to_file(path, "SDF")
loaded = Molecule.from_file(path, file_format="SDF")

assert molecule.is_isomorphic_with(loaded)
print(loaded.n_conformers)
```

Use `SDF` for round-trips where molecular graph and coordinates both matter. If a multi-record SDF is read, `Molecule.from_file()` returns a list; validate each molecule or collapse conformers only after confirming that all records are isomorphic.

## Read Files Safely

```python
from openff.toolkit import Molecule

loaded = Molecule.from_file("ligands.sdf", file_format="SDF", allow_undefined_stereo=True)
molecules = loaded if isinstance(loaded, list) else [loaded]

for molecule in molecules:
    print(molecule.name, molecule.n_atoms, molecule.to_smiles())
```

Format guidance:

- `SDF`, `MOL`, and `SMI` are practical RDKit-backed read formats in a minimal environment.
- Provide `file_format` for file-like objects and when suffixes are ambiguous.
- Avoid `XYZ` for reading molecules because it lacks chemical graph data.
- Avoid bare `PDB` for small-molecule graph perception; use `Molecule.from_pdb_and_smiles()` only for molecule-level legacy needs, or route broader PDB loading to `../topology-and-systems/SKILL.md`.

## Convert to and from RDKit

```python
from openff.toolkit import Molecule
from rdkit import Chem

rdmol = Chem.MolFromSmiles("CCO")
molecule = Molecule.from_rdkit(rdmol)
roundtrip_rdmol = molecule.to_rdkit()
print(Chem.MolToSmiles(roundtrip_rdmol))
```

Use RDKit conversion for integration with RDKit descriptors, depictions, or custom SMARTS work. Catch backend import errors if the runtime may not have RDKit. For OpenEye conversions, use the analogous `from_openeye()` and `to_openeye()` calls only when OpenEye is installed and licensed.

## Generate Conformers

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("CCO")
molecule.generate_conformers(n_conformers=3)
print(molecule.n_conformers)
```

Guidance:

- Keep `n_conformers` small for smoke tests and agent-generated examples.
- Use `clear_existing=True` when replacing coordinates and `False` only when the intended behavior is to retain existing conformers.
- `n_conformers=0` is a safe way to clear conformers when `clear_existing=True`.
- If conformer generation fails, reduce molecule complexity, check undefined stereochemistry, or use a different installed toolkit.

## Assign Partial Charges

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("CCO")
molecule.assign_partial_charges("gasteiger")
print(molecule.partial_charges)
```

Minimal-environment choices:

- `gasteiger` or `mmff94` with RDKit.
- `formal_charge` or `zeros` with the BuiltIn wrapper.

Method selection guidance:

- Use `molecule.get_available_charge_methods()` to discover available methods in the current registry.
- Use `use_conformers=molecule.conformers` only when you deliberately want to supply coordinates to the charge method.
- Leave `normalize_partial_charges=True` unless the user has a specific reason not to normalize to formal charge.
- Route force-field-level charge assignment and `ForceField.get_partial_charges()` to `../smirnoff-force-fields/SKILL.md`.

## Enumerate Stereoisomers

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("CC(F)Cl", allow_undefined_stereo=True)
isomers = molecule.enumerate_stereoisomers(undefined_only=True, max_isomers=4)
for isomer in isomers:
    print(isomer.to_smiles(isomeric=True))
```

Use `undefined_only=True` when filling in unspecified stereochemistry. Use `undefined_only=False` when the user asks for all stereoisomers from a scaffold. Always set a small `max_isomers` unless the user explicitly requests exhaustive enumeration.

## Enumerate Tautomers

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("CC(=O)NC")
tautomers = molecule.enumerate_tautomers(max_states=10)
print([tautomer.to_smiles(isomeric=True) for tautomer in tautomers])
```

Tautomer enumeration is backend-dependent. Treat the returned structures as candidates for inspection rather than a universal canonical tautomer set.

## SMARTS Matching

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("CCO")
matches = molecule.chemical_environment_matches("[#6:1]-[#8:2]-[#1:3]", unique=True)
print(matches)
```

Guidance:

- Use atom-map tags in the SMARTS to control tuple order.
- Use `unique=True` for human-facing counts and `False` when multiplicity matters.
- If SMARTS behavior depends on aromaticity model or backend quirks, note the selected toolkit.

## Graph and Isomorphism Validation

```python
from openff.toolkit import Molecule

left = Molecule.from_smiles("CCO")
right = Molecule.from_smiles("OCC")
assert left.is_isomorphic_with(right)

graph = left.to_networkx()
print(graph.number_of_nodes(), graph.number_of_edges())
```

Use isomorphism checks instead of direct SMILES string equality when comparing molecules created by different routes or toolkits. Disable stereochemistry matching only when the task explicitly allows stereochemical ambiguity.

## Visualize Molecules

```python
from openff.toolkit import Molecule

molecule = Molecule.from_smiles("c1ccccc1")
molecule.visualize(backend="rdkit", show_all_hydrogens=False)
```

Notebook guidance:

- `backend="rdkit"` is the practical default when RDKit is installed.
- `backend="nglview"` requires conformers and `nglview`; call `generate_conformers()` first.
- `backend="openeye"` requires OpenEye.
- Visualization returns display objects; scripts should not depend on it for validation.

## Tiny Smoke Validation Pattern

For agent-generated code, validate a molecule workflow with the bundled script:

```bash
python scripts/smoke_molecule_workflow.py --smiles CCO
python scripts/smoke_molecule_workflow.py --smiles CCO --generate-conformers --output ethanol.sdf
python scripts/smoke_molecule_workflow.py --smiles CCO --charge-method gasteiger
```

The script prints JSON with atom count, canonical SMILES, conformer count when requested, charge status when requested, available charge methods, and optional SDF round-trip isomorphism.
