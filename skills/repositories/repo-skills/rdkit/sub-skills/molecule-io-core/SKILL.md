---
name: molecule-io-core
description: "Use for RDKit molecule creation, file/string I/O, validation,
  sanitization, atom/bond/ring queries, substructure matching, hydrogens, and
  editable molecule workflows. Route descriptors/fingerprints,
  conformers/drawing, reactions/standardization, and R-group workflows to their
  dedicated RDKit sub-skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Molecule I/O Core

Use this sub-skill when a task asks an agent to parse, validate, inspect, edit, serialize, or round-trip RDKit molecules from SMILES, SMARTS, MolBlocks, SDF, or delimited SMILES files.

## Route here

- Parse strings with `Chem.MolFromSmiles`, `Chem.MolFromSmarts`, `Chem.MolFromMolBlock`, or supplier classes.
- Write canonical/isomeric SMILES, MolBlocks, SDF, or SMILES files with `Chem.MolToSmiles`, `Chem.MolToMolBlock`, `Chem.SDWriter`, or `Chem.SmilesWriter`.
- Validate invalid SMILES and empty supplier entries without silently passing `None` molecules downstream.
- Control sanitization, kekulization, aromaticity, valence handling, and explicit/implicit hydrogens.
- Query atoms, bonds, rings, properties, and substructure matches.
- Make small structural edits with `Chem.RWMol` or `Chem.EditableMol` and re-sanitize the result.

## Route elsewhere

- Descriptors, fingerprints, bit vectors, similarity, and clustering: `descriptors-fingerprints`.
- 3D conformers, force-field optimization, 2D coordinates, and drawing: `conformers-drawing`.
- Reaction SMARTS, product sanitization after reactions, molecule standardization, tautomer handling, stereochemistry workflows, and R-groups: `reactions-standardization`.
- Pandas, database, RDKit data-file location, and CLI integration: `data-cli-integration`.

## Start with these references

- `references/molecule-io.md` for parsing, suppliers, writers, and round-trip patterns.
- `references/sanitization-and-queries.md` for sanitization, hydrogens, atom/bond/ring queries, substructure matching, and molecule editing.
- `references/troubleshooting.md` for common failures and safe recovery patterns.
- `scripts/molecule_io_smoke.py` for a tiny standalone smoke test that canonicalizes SMILES and round-trips SDF.

## Core workflow

1. Parse input and immediately check for `None` before doing any chemistry.
2. Canonicalize with `Chem.MolToSmiles(mol, isomericSmiles=True)` when comparing or de-duplicating molecules.
3. Use suppliers defensively: iterate with indexes, skip or report `None`, and preserve molecule names/properties when writing SDF.
4. If using `sanitize=False`, run a deliberate `Chem.SanitizeMol` step before relying on valence, aromaticity, rings, descriptors, or substructure behavior.
5. For structural edits, edit a copy, call `GetMol()`, update property cache if needed, then sanitize or report the sanitization failure.

## Minimal examples

```python
from rdkit import Chem

mol = Chem.MolFromSmiles("CC(=O)O")
if mol is None:
    raise ValueError("invalid SMILES")
canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
```

```python
query = Chem.MolFromSmarts("[CX3](=O)[OX2H1]")
matches = mol.GetSubstructMatches(query)
```

```python
edited = Chem.RWMol(mol)
atom_index = edited.AddAtom(Chem.Atom("Cl"))
edited.AddBond(0, atom_index, Chem.BondType.SINGLE)
new_mol = edited.GetMol()
Chem.SanitizeMol(new_mol)
```

## Bundled check

Run the bundled helper in any environment where RDKit is importable:

```bash
python scripts/molecule_io_smoke.py --smiles "CCO" "c1ccccc1" --include-invalid
```

It asserts that valid SMILES parse, invalid SMILES are reported, canonical SMILES are stable after a second parse, and a tiny SDF round-trip preserves molecule count and properties.
