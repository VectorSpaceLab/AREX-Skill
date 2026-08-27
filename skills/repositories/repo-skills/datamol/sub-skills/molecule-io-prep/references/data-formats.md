# Data Formats, Molecule Columns, And Properties

## Supported DataFrame Extensions

`dm.open_df(path)` and `dm.save_df(data, path)` choose their backend from the filename suffix.

| Family | Supported suffixes | Reader/writer behavior |
| --- | --- | --- |
| CSV | `.csv`, `.csv.gz`, `.csv.bz2`, `.csv.zip`, `.csv.xz`, `.csv.zst`, `.csv.tar`, `.csv.tar.gz`, `.csv.tar.xz`, `.csv.tar.bz2` | Uses pandas CSV methods. `dm.save_df` defaults `index=False`. |
| Excel | `.xlsx` | Uses pandas Excel methods. Reading/writing may require an installed engine such as `openpyxl`. `dm.save_df` defaults `index=False`. |
| Parquet | `.parquet` | Uses pandas parquet methods. Requires a parquet engine such as `pyarrow` or `fastparquet`. |
| JSON | `.json`, `.json.gz`, `.json.bz2`, `.json.zip`, `.json.xz`, `.json.zst`, `.json.tar`, `.json.tar.gz`, `.json.tar.xz`, `.json.tar.bz2` | Uses pandas JSON methods. Pick an explicit JSON orientation if interoperability matters. |
| SDF | `.sdf`, `.sdf.gz` | `dm.open_df` calls `dm.read_sdf(..., as_df=True)` and `dm.save_df` calls `dm.to_sdf(...)`. |

Unsupported suffixes raise `ValueError`. When extension inference is too implicit for the task, call the specific reader/writer directly.

## SMILES, SMI, And CSV

- `dm.to_mol(smiles)` is the SMILES parser; there is no public `dm.from_smiles` API.
- `dm.read_smi` and `dm.to_smi` handle simple `.smi` files, but `.smi` is CSV-like and intentionally minimal.
- Prefer `dm.read_csv(..., smiles_column="smiles")` or `pd.read_csv` when a file has headers, separators, IDs, assay values, or extra metadata.
- `dm.to_smiles` returns canonical isomeric SMILES by default; set `randomize=True`, `explicit_bonds=True`, `explicit_hs=True`, or `cxsmiles=True` only when the downstream task requires those forms.

## SDF And Molecule Properties

- `dm.read_sdf(path)` returns `list[Mol]`; `dm.read_sdf(path, as_df=True)` returns a dataframe of molecule properties plus optional `smiles` and `mol` columns.
- `dm.read_sdf(..., mol_column="mol")` preserves RDKit molecule objects in the dataframe; omit it when only property columns and SMILES are needed.
- `dm.to_sdf(df, path, mol_column="mol")` writes molecules from an existing molecule column; `smiles_column="smiles"` rebuilds molecules from SMILES when no molecule column is provided.
- `dm.to_sdf` filters out `None` molecules before writing, so compare row counts if invalid records must be preserved.
- SDF preserves molecule properties and conformers in normal datamol roundtrips; mol block strings do not preserve molecule properties.
- `read_sdf(..., discard_invalid=False)` retains `None` entries for failed records, which is useful when row positions must stay aligned with external metadata.

## MolBlock, Mol2, And PDB Blocks

- `dm.to_molblock` and `dm.read_molblock` are for in-memory MDL mol block strings; properties are not read from mol blocks.
- `dm.read_molblock(..., fail_if_invalid=True)` raises `ValueError`; otherwise invalid blocks return `None`.
- `dm.read_mol2file` returns a list and may include `None` for damaged molecules unless `fail_if_invalid=True` is set.
- `dm.to_pdbblock` serializes an existing conformer; generate conformers in the structure-generation sub-skill before expecting meaningful 3D coordinates.

## DataFrame Molecule Columns

- `dm.read_csv` and `dm.read_excel` can add a molecule column with `smiles_column="smiles", mol_column="mol"`.
- `dm.from_df(df, mol_column="mol")` uses an existing molecule column and copies other row values into molecule properties.
- If `mol_column` is omitted, `dm.from_df` can detect a molecule column from the first row; specify the column explicitly for clarity.
- If `smiles_column` is used, that column is removed from molecule properties by default; set `conserve_smiles=True` when the original SMILES must remain a property.
- `dm.to_df(mols, mol_column="mol")` can keep molecule objects in the dataframe; otherwise it writes SMILES and molecule properties.
- `dm.to_df(..., include_private=True, include_computed=True)` exposes RDKit private/computed properties; keep defaults for user-facing tables unless those fields are requested.

## Property Handling

- Add metadata with `dm.set_mol_props(mol, props, copy=True)` if you need to keep the original molecule unchanged.
- Copy metadata after replacement or repair with `dm.copy_mol_props(source, destination)` when a workflow creates a new molecule object.
- Remove metadata with `dm.clear_mol_props(mol)` or selected keys with `property_keys="key"` or `property_keys=[...]`.
- `dm.sanitize_mol` preserves molecule-level properties and the first conformer, but atom-level properties are lost.
- `dm.to_molblock` output loses molecule properties; use SDF or dataframe formats for metadata-preserving exchange.

## Bundled Data

- `dm.data.freesolv()` returns a toy FreeSolv dataframe with `iupac`, `smiles`, `expt`, and `calc` columns.
- `dm.data.cdk2()` returns a CDK2 dataframe with a molecule column and SDF-derived properties by default.
- `dm.data.solubility()` returns a solubility dataframe with train/test split metadata.
- `dm.data.chembl_drugs()` and `dm.data.chembl_samples()` load bundled local samples, not live remote ChEMBL queries.
- Use bundled datasets for examples, smoke checks, and tutorials; do not present them as current benchmark datasets.

## Remote Path Cautions

- Many IO functions use fsspec-compatible paths, but backend support depends on installed fsspec extras and credentials.
- Avoid embedding credentials in paths. Prefer environment- or filesystem-level credentials managed outside skill content.
- `dm.read_smi` may copy non-local paths to a temporary local file because RDKit's SMILES supplier expects a path.
- For remote writes, validate with a tiny file first and prefer explicit readers/writers over extension inference when the remote filesystem has unusual suffixes or compression behavior.
- Use local temporary output directories for examples and smoke tests; avoid destructive overwrites unless the user explicitly requested a destination.
