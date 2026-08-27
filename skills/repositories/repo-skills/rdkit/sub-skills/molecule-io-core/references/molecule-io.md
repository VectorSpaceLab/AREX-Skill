# Molecule I/O

## Parse molecules from strings

Common constructors live under `rdkit.Chem`:

- `Chem.MolFromSmiles(smiles)` parses SMILES and returns a `Mol` or `None`.
- `Chem.MolFromSmarts(smarts)` parses query SMARTS and returns a query `Mol` or `None`.
- `Chem.MolFromMolBlock(block, sanitize=True, removeHs=True, strictParsing=True)` parses a MolBlock string.
- `Chem.MolToSmiles(mol, isomericSmiles=True)` serializes a molecule to a canonical SMILES by default.
- `Chem.MolToMolBlock(mol)` serializes a molecule to a MolBlock.

Always validate constructor output before calling molecule methods:

```python
mol = Chem.MolFromSmiles(input_smiles)
if mol is None:
    raise ValueError(f"invalid SMILES: {input_smiles!r}")
```

For comparison, deduplication, or stable output, round-trip canonical SMILES:

```python
canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
assert Chem.MolFromSmiles(canonical) is not None
```

Use `isomericSmiles=True` unless the task explicitly wants stereochemistry stripped. Use `canonical=False` only for randomized or input-order-sensitive workflows.

## Read SDF files

Use `Chem.SDMolSupplier` for ordinary path-backed SDF input:

```python
supplier = Chem.SDMolSupplier("input.sdf", sanitize=True, removeHs=True, strictParsing=True)
for row_index, mol in enumerate(supplier, start=1):
    if mol is None:
        print(f"skipping unreadable SDF record {row_index}")
        continue
    name = mol.GetProp("_Name") if mol.HasProp("_Name") else f"record-{row_index}"
    smiles = Chem.MolToSmiles(mol)
```

Use `Chem.ForwardSDMolSupplier(fileobj, ...)` for streaming from a binary file-like object or compressed input. Supplier entries can be `None`; this is expected for unreadable records and should be reported with record indexes.

## Read delimited SMILES files

Use `Chem.SmilesMolSupplier` for files and `Chem.SmilesMolSupplierFromText` for in-memory text:

```python
supplier = Chem.SmilesMolSupplier(
    "input.smi",
    delimiter="\t",
    smilesColumn=0,
    nameColumn=1,
    titleLine=False,
)
for row_index, mol in enumerate(supplier, start=1):
    if mol is None:
        print(f"invalid SMILES at row {row_index}")
        continue
```

Set `titleLine=True` when the first row is a header. Set `nameColumn=-1` when no name column is present.

## Write SDF and SMILES files

SDF writing preserves molecule properties as data fields:

```python
writer = Chem.SDWriter("output.sdf")
try:
    for mol in mols:
        mol.SetProp("source", "example")
        writer.write(mol)
finally:
    writer.close()
```

SMILES writing is useful for compact canonicalized output:

```python
writer = Chem.SmilesWriter("output.smi", isomericSmiles=True)
try:
    for mol in mols:
        writer.write(mol)
finally:
    writer.close()
```

For small scripts, writing text manually is often simpler and gives explicit control over invalid inputs:

```python
with open("output.smi", "w", encoding="utf-8") as handle:
    for mol in mols:
        handle.write(Chem.MolToSmiles(mol) + "\n")
```

## Preserve names and properties

- `_Name` is the conventional molecule title/name property used by SDF writers.
- `mol.SetProp(key, value)` stores string properties for SDF output.
- `mol.GetPropNames()` lists public string properties; use `includePrivate=True` only when you intentionally want private/internal properties.
- Properties do not automatically survive every transformation; after creating a new molecule from an edited or copied object, copy required properties explicitly when needed.

## Mixed SMILES and SDF canonicalization

When combining SMILES and SDF inputs, normalize each successfully parsed molecule to canonical SMILES and carry source metadata separately:

```python
records = []
for source, mol in parsed_molecules:
    if mol is None:
        records.append({"source": source, "error": "parse failed"})
        continue
    records.append({
        "source": source,
        "canonical_smiles": Chem.MolToSmiles(mol, isomericSmiles=True),
        "name": mol.GetProp("_Name") if mol.HasProp("_Name") else "",
    })
```

This pattern supports workflows that accept both line-oriented SMILES and structure-rich SDF while giving a single comparison key.
