# Molecule I/O Troubleshooting

## `MolFromSmiles` returns `None`

Symptoms:

- `AttributeError: 'NoneType' object has no attribute ...`
- Empty canonical SMILES output where an error should have been reported.
- Supplier iteration yields `None` for some rows or records.

Fix:

```python
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    raise ValueError(f"invalid SMILES: {smiles!r}")
```

Do not pass `None` into descriptors, fingerprints, drawing, writers, or substructure searches. Report invalid input with row/record identifiers.

## Sanitization exceptions

Symptoms:

- Valence errors while parsing or sanitizing.
- Aromaticity, kekulization, or property-cache errors.
- Molecules parse with `sanitize=False` but fail later.

Fix:

1. Prefer default sanitized parsing when possible.
2. If using `sanitize=False`, call `Chem.SanitizeMol(mol)` before chemistry operations.
3. Use `Chem.SanitizeMol(mol, catchErrors=True)` to find the first failed stage.
4. Only skip sanitization stages when the workflow has a chemistry-specific reason and documents downstream limitations.

Example:

```python
mol = Chem.MolFromSmiles(text, sanitize=False)
if mol is None:
    raise ValueError("parse failed")
failed = Chem.SanitizeMol(mol, catchErrors=True)
if failed != Chem.SanitizeFlags.SANITIZE_NONE:
    raise ValueError(f"sanitization failed at {failed}")
```

## Empty or invalid supplier entries

`Chem.SDMolSupplier`, `Chem.ForwardSDMolSupplier`, `Chem.SmilesMolSupplier`, and related supplier helpers can yield `None`. This means a record could not be parsed under the supplier settings.

Fix:

```python
valid = []
errors = []
for index, mol in enumerate(supplier, start=1):
    if mol is None:
        errors.append(f"record {index}: parse failed")
        continue
    valid.append(mol)
```

For SDF files, check whether the record delimiter is correct and whether property blocks contain malformed text. For SMILES tables, check delimiter, header handling, `smilesColumn`, and `nameColumn`.

## File encodings and line endings

Symptoms:

- SMILES files fail only on some systems.
- Names or property fields contain garbled characters.
- A file read as text fails while binary streaming works.

Fix:

- Open plain text SMILES files with an explicit encoding such as `encoding="utf-8"`.
- Prefer `Chem.SmilesMolSupplier` for conventional delimited SMILES files.
- Use binary file handles for `Chem.ForwardSDMolSupplier`, especially with compressed or streamed SDF data.
- Keep molecule names/properties as strings before writing SDF.

## Kekulization failures

Symptoms:

- `KekulizeException` or aromaticity-related sanitization failure.
- `MolToSmiles(..., kekuleSmiles=True)` fails for an aromatic molecule.

Fix:

```python
copy = Chem.Mol(mol)
try:
    Chem.Kekulize(copy, clearAromaticFlags=True)
except Exception as err:
    raise ValueError(f"could not kekulize molecule: {err}") from err
```

Keep the original aromatic molecule if downstream tasks do not require Kekule form. Many RDKit workflows work best with the default aromatic representation.

## Hydrogens change results

Symptoms:

- Atom counts change unexpectedly.
- Substructure matches differ before and after `AddHs`.
- 3D workflows need hydrogens but graph workflows did not.

Fix:

- Remember that `Chem.AddHs(mol)` returns a new molecule.
- Use explicit hydrogens only when needed by the workflow.
- Remove hydrogens with `Chem.RemoveHs` before comparing to hydrogen-suppressed canonical SMILES.
- Rebuild atom-index mappings after adding or removing hydrogens.

## MolBlock or SDF round-trips lose information

Possible causes:

- Properties were never set on the molecule object.
- A newly edited molecule did not copy properties from the original.
- SDF writer was not closed or flushed.
- Stereochemistry or hydrogens were changed during parsing because of `removeHs` or sanitization settings.

Fix:

```python
copy = Chem.Mol(mol)
for prop_name in original.GetPropNames():
    copy.SetProp(prop_name, original.GetProp(prop_name))
```

Use `removeHs=False` when explicit hydrogens are meaningful and must survive parsing.

## SMARTS query returns no matches

Checklist:

- Parse the query with `Chem.MolFromSmarts`, not `Chem.MolFromSmiles`.
- Confirm the target molecule parsed and sanitized successfully.
- Check whether explicit hydrogens are required by the query.
- Print atom indexes and symbols from `mol.GetAtoms()` to debug assumptions.
- Use a simpler SMARTS first, then add constraints one at a time.

## Editing creates invalid molecules

Symptoms:

- Sanitization fails after `RWMol` or `EditableMol` edits.
- Atom indexes no longer point to expected atoms.
- Output SMILES has unexpected charge, valence, or aromaticity.

Fix:

1. Work on a copy: `rw_mol = Chem.RWMol(mol)`.
2. Make the smallest edit that expresses the intended graph change.
3. Convert with `GetMol()`.
4. Run `Chem.SanitizeMol` and handle failures.
5. Verify with `Chem.MolToSmiles` and atom/bond inspection.
