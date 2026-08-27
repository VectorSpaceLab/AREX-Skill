# Molecule IO And Preparation Troubleshooting

## Invalid SMILES Returns `None`

Symptoms:
- `dm.to_mol(smiles)` returns `None`.
- `dm.to_smiles(mol)` later fails because `mol` is `None`.

Fix:
1. Check the input type first; `dm.to_mol` accepts only strings or RDKit `Mol` objects and raises `ValueError` for other types.
2. Retry plausible but unsanitized chemistry with `dm.to_mol(smiles, sanitize=False)`.
3. Pass the permissive molecule to `dm.sanitize_mol` or `dm.fix_mol`.
4. Drop or report entries still returning `None` before downstream tasks.

```python
mol = dm.to_mol(smiles)
if mol is None:
    mol = dm.sanitize_mol(dm.to_mol(smiles, sanitize=False))
if mol is None:
    raise ValueError(f"Could not parse molecule: {smiles!r}")
```

## Sanitization Or Aromaticity Repair Fails

Symptoms:
- `dm.sanitize_mol(...)` returns `None`.
- RDKit emits valence, kekulization, or aromaticity warnings.

Fix:
- Use `sanitize=False` only long enough to run a repair path.
- Try `dm.fix_mol(mol, n_iter=1)` for valence/dummy cleanup.
- For salts/fragments, try `dm.fix_mol(mol, largest_only=True)` or `dm.remove_salts_solvents(mol)` after checking that the largest fragment is the desired parent.
- Use `dm.standardize_mol(mol, disconnect_metals=True, uncharge=True)` when metal disconnection and charge state normalization are requested.
- If repair still fails, keep the original row metadata and record the molecule as invalid rather than silently fabricating chemistry.

## Missing Optional IO Engines

Symptoms:
- Excel reads/writes fail with missing `openpyxl` or a similar engine error.
- Parquet reads/writes fail with missing `pyarrow` or `fastparquet`.
- Remote paths fail because an fsspec backend is missing.

Fix:
- For Excel, pass an installed engine explicitly when needed, for example `dm.read_excel(path, engine="openpyxl")`.
- For parquet, install or select a pandas parquet engine in the user's environment, or use CSV/SDF when that is acceptable.
- For remote files, install the matching fsspec extra or copy the file locally before calling datamol.
- Do not hide dependency failures; report which backend is missing and offer a local-format alternative.

## RDKit Parsing Issues With SDF, Mol2, MolBlock, Or PDB

Symptoms:
- `dm.read_sdf` returns fewer molecules than expected.
- `dm.read_mol2file` returns `None` entries.
- `dm.read_molblock("...")` returns `None` or raises with `fail_if_invalid=True`.

Fix:
- For SDF, set `discard_invalid=False` to preserve failed records as `None`, then inspect row counts.
- For SDF, use `strict_parsing=False` only when accepting lax syntax is appropriate.
- For Mol2, use `fail_if_invalid=True` during validation to stop on the first damaged molecule.
- For mol blocks, keep `fail_if_invalid=False` in tolerant pipelines and explicitly check for `None`.
- For PDB, ensure a conformer exists before expecting meaningful 3D output from `dm.to_pdbblock`.

## Properties Disappear Or Duplicate

Symptoms:
- Properties are missing after converting through mol blocks.
- A dataframe has duplicate `smiles` columns.
- Atom-level annotations disappear after sanitization.

Fix:
- Use SDF or dataframe workflows when molecule properties must roundtrip; mol blocks do not preserve properties.
- Use `dm.set_mol_props`, `dm.copy_mol_props`, and `dm.clear_mol_props` deliberately around repair steps.
- If a molecule property is named `smiles`, `dm.to_df(..., smiles_column="smiles")` can create duplicate column names; choose a different SMILES column or clear that property.
- Remember that `dm.sanitize_mol` preserves molecule-level properties and the first conformer, but atom properties are lost.
- Use `conserve_smiles=True` in `dm.from_df` only when the original SMILES string must become a molecule property.

## SDF Row Counts Change

Symptoms:
- Writing a dataframe or molecule list to SDF produces fewer records than the input row count.

Fix:
- Check for `None` molecules before `dm.to_sdf`; datamol filters invalid molecules.
- If using a dataframe, ensure `mol_column` points to valid RDKit `Mol` objects or `smiles_column` points to valid SMILES.
- Read back with `dm.read_sdf(path, as_df=True, mol_column="mol")` and compare counts and canonical SMILES.

## Salts, Solvents, Or Fragments Are Removed Incorrectly

Symptoms:
- `dm.keep_largest_fragment` keeps a solvent or counterion instead of the compound.
- `dm.remove_salts_solvents` removes all fragments.

Fix:
- Use `dm.remove_salts_solvents(mol, dont_remove_everything=True)` when at least one fragment must remain.
- Provide custom removal definitions with `defn_data="..."` and `defn_format="smiles"` or `"smarts"` when the default salts/solvents list is not enough.
- Compare canonical SMILES before and after cleanup so accidental parent loss is visible.

## fsspec Or Remote Path Failures

Symptoms:
- `dm.read_sdf`, `dm.to_sdf`, or `dm.open_df` fails for `s3://`, `gs://`, HTTP, or another remote path.
- A remote `.smi` read is unexpectedly slow or fails around temporary copies.

Fix:
- Confirm the target protocol is supported by installed fsspec plugins.
- Prefer explicit local staging for `.smi` files because RDKit's SMILES supplier expects a local path.
- Avoid credentials in URLs; use the user's configured filesystem credentials.
- Validate with a small non-destructive read/write before running a large conversion.
- If suffix inference fails on a signed or extensionless URL, use a specific datamol reader/writer or pandas call instead of `dm.open_df`/`dm.save_df`.

## Molar Unit Errors

Symptoms:
- `dm.molar.molar_to_log` or `dm.molar.log_to_molar` raises `ValueError` for a unit.

Fix:
- Use only `M`, `mM`, `uM`, `nM`, `pM`, or `fM`.
- Convert other units before calling datamol.
- Keep assay direction and unit labels in dataframe columns so p-scale values remain interpretable.
