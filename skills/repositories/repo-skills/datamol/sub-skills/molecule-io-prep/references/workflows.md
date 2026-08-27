# Molecule IO And Preparation Workflows

All examples assume `import datamol as dm` and use tiny local data. Validate every parser result before passing molecules to downstream fingerprints, clustering, conformer generation, or visualization.

## SMILES To Clean Molecules

1. Parse with `dm.to_mol(smiles)` for normal sanitized SMILES.
2. If parsing returns `None` for a chemically plausible string, retry permissively with `dm.to_mol(smiles, sanitize=False)`.
3. Repair permissive molecules with `dm.sanitize_mol(mol, charge_neutral=False)` or `dm.fix_mol(mol, largest_only=False)`.
4. Standardize with `dm.standardize_mol(mol, disconnect_metals=True, uncharge=True)` when salts, metals, or charge-state normalization matter.
5. Canonicalize with `dm.to_smiles(mol)` and check for `None` before deduplicating or writing.

```python
import datamol as dm

raw = ["CCO", "O=C([O-])c1ccccc1", "bad"]
mols = []
for smiles in raw:
    mol = dm.to_mol(smiles)
    if mol is None:
        mol = dm.sanitize_mol(dm.to_mol(smiles, sanitize=False))
    if mol is not None:
        mol = dm.standardize_mol(mol, uncharge=True)
        mols.append(mol)
canonical = [dm.to_smiles(mol) for mol in mols]
```

## SMILES, InChI, SMARTS, And SELFIES Conversion

- Use `dm.to_mol(smiles)` for SMILES input; there is no public `dm.from_smiles` function.
- Use `dm.to_inchi(mol)` and `dm.from_inchi(inchi)` for standard InChI roundtrips.
- Use `dm.to_selfies(mol_or_smiles)` and `dm.from_selfies(selfies, as_mol=True)` for SELFIES.
- Use `dm.from_smarts(smarts)` for query molecules and `dm.to_smarts(query_mol)` when a SMARTS string is needed.
- Use `dm.to_smiles(mol, cxsmiles=True)` when atom-map or CXSMILES metadata must be represented in the string.

```python
import datamol as dm

mol = dm.to_mol("CC(=O)Oc1ccccc1C(=O)O")
inchi = dm.to_inchi(mol)
assert dm.to_smiles(dm.from_inchi(inchi)) == dm.to_smiles(mol)
selfies = dm.to_selfies(mol)
assert dm.to_smiles(dm.from_selfies(selfies, as_mol=True)) == dm.to_smiles(mol)
query = dm.from_smarts("[OX2H][CX3]=[OX1]")
assert mol.HasSubstructMatch(query)
```

## DataFrame Roundtrip With Properties

1. Build molecules and attach metadata with `dm.set_mol_props` when metadata starts outside a dataframe.
2. Convert molecules to a dataframe with `dm.to_df(mols, smiles_column="smiles", mol_column="mol")`.
3. Convert back with `dm.from_df(df, mol_column="mol")` to prefer the existing molecule column, or `dm.from_df(df, smiles_column="smiles")` to rebuild from SMILES.
4. Use `conserve_smiles=True` only when the input SMILES string should remain a molecule property.
5. Watch for duplicate `smiles` columns if a molecule property is also named `smiles`.

```python
import datamol as dm

mol = dm.to_mol("CCO")
mol = dm.set_mol_props(mol, {"name": "ethanol", "source": "manual"}, copy=True)
df = dm.to_df([mol], smiles_column="smiles", mol_column="mol")
roundtrip = dm.from_df(df, mol_column="mol")
assert roundtrip[0].GetPropsAsDict()["name"] == "ethanol"
```

## CSV And Excel Loading

- Use `dm.read_csv(path, smiles_column="smiles", mol_column="mol")` to load a CSV and add an RDKit molecule column.
- Use `dm.read_excel(path, smiles_column="smiles", mol_column="mol", engine="openpyxl")` when an Excel engine is installed.
- Avoid automatic molecule columns for very large tables until after filtering rows.
- Use `dm.from_df(df, smiles_column="smiles")` when you need list-like molecules with row metadata copied to molecule properties.

```python
import datamol as dm

# CSV with columns: smiles,name
frame = dm.read_csv("molecules.csv", smiles_column="smiles", mol_column="mol")
valid = frame[frame["mol"].notna()].copy()
mols = dm.from_df(valid, mol_column="mol")
```

## SDF Roundtrip

1. Read SDF as molecules with `dm.read_sdf(path)` when you only need `Mol` objects.
2. Read as a dataframe with `dm.read_sdf(path, as_df=True, mol_column="mol")` when properties must be visible as columns.
3. Use `max_num_mols` to inspect a small prefix safely.
4. Set `discard_invalid=False` when preserving record positions matters; then handle `None` molecules explicitly.
5. Write with `dm.to_sdf(mols_or_df, path, smiles_column="smiles", mol_column="mol")`.

```python
import datamol as dm

sample = dm.read_sdf("input.sdf.gz", as_df=True, mol_column="mol", max_num_mols=100)
sample = sample[sample["mol"].notna()].copy()
dm.to_sdf(sample, "clean.sdf", mol_column="mol")
loaded = dm.read_sdf("clean.sdf", as_df=True, mol_column="mol")
assert len(loaded) == len(sample)
```

## Auto Open And Save DataFrames

- Use `dm.open_df(path)` and `dm.save_df(df, path)` when the extension should choose the backend.
- Supported families include CSV, Excel, parquet, JSON, SDF, and documented compressed CSV/JSON/SDF suffixes.
- For SDF, `dm.save_df` calls `dm.to_sdf`; make sure the dataframe has a valid `mol_column` or `smiles_column`.
- Forward backend-specific kwargs, for example `sep=";"` for CSV or `as_df=True` options for SDF reading.

```python
import datamol as dm

frame = dm.data.freesolv().head(5)
dm.save_df(frame, "tiny.csv")
loaded = dm.open_df("tiny.csv")
assert list(loaded.columns) == list(frame.columns)
```

## Cleanup For Salts, Solvents, Charges, And Fragments

Use this sequence for noisy vendor strings or multi-fragment inputs:

1. Parse with `dm.to_mol(smiles, sanitize=False)` if normal parsing fails.
2. Run `dm.sanitize_mol(mol, charge_neutral=False)`.
3. Strip known salts/solvents with `dm.remove_salts_solvents(mol)`.
4. If default removal strips the wrong fragment, pass custom `defn_data` and `defn_format="smiles"` or `"smarts"`.
5. Standardize with `dm.standardize_mol(mol, disconnect_metals=True, normalize=True, reionize=True, uncharge=True)`.
6. Use `dm.to_neutral(dm.copy_mol(mol))` only when simple formal-charge neutralization is desired.

```python
import datamol as dm

mol = dm.to_mol("CN(C)C.Cl.Cl.Br")
parent = dm.remove_salts_solvents(mol)
parent = dm.standardize_mol(parent, uncharge=True)
assert dm.to_smiles(parent) == "CN(C)C"
```

## Bundled Dataset Bootstrap

- Use `dm.data.freesolv()` for tiny dataframe examples with SMILES and scalar properties.
- Use `dm.data.cdk2(as_df=True, mol_column="mol")` when examples need an SDF-derived molecule column and properties.
- Use `dm.data.solubility()` when a train/test split column is useful.
- Use `as_df=False` to get list-like molecules from bundled datasets that support it.
- Treat bundled datasets as examples for tutorials and tests, not benchmark-grade training data.

```python
import datamol as dm

df = dm.data.freesolv().head(10)
mols = dm.from_df(df, smiles_column="smiles")
assert len(mols) == 10
```

## Molar Unit Helpers

Use `dm.molar.molar_to_log(values, unit)` to convert concentration values such as IC50/EC50/XC50 to p-scale values, and `dm.molar.log_to_molar(values, unit)` for the reverse.

```python
import datamol as dm

pxc50 = dm.molar.molar_to_log([1.0, 0.1], unit="uM")
xc50 = dm.molar.log_to_molar(pxc50, unit="uM")
```

## Handoff To Other Datamol Sub-Skills

- For fingerprints, similarity, clustering, or diversity selection, finish here with clean `Mol` objects or canonical SMILES, then route to `fingerprints-similarity`.
- For conformer generation, alignment, scaffold extraction, fragment logic, reactions, or isomer enumeration, finish here with sanitized `Mol` objects, then route to `structure-generation`.
- For images or highlighted molecules, finish here with `Mol` objects and route to `visualization-utilities`.
