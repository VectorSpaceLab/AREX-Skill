# Molecule IO and Preparation API Reference

Import datamol as `dm`. The package exposes most functions lazily at the top level, so prefer `dm.to_mol(...)`, `dm.read_sdf(...)`, and `dm.data.freesolv(...)` over importing internal modules. The public API does not expose `from_smiles`; use `dm.to_mol(smiles, ...)` for SMILES-to-`Mol` parsing.

## Construction And String Conversion

| API | Verified signature | Use when | Key guidance |
| --- | --- | --- | --- |
| `dm.to_mol` | `to_mol(mol, add_hs=False, explicit_only=False, ordered=False, kekulize=False, sanitize=True, allow_cxsmiles=True, parse_name=True, remove_hs=True, strict_cxsmiles=True)` | Parse SMILES or pass through an RDKit `Mol`. | Returns `None` for invalid SMILES; raises `ValueError` for non-string/non-`Mol` inputs. Set `sanitize=False` only when you plan a follow-up `dm.sanitize_mol` or `dm.fix_mol`. Use `ordered=True` for stable atom order. |
| `dm.from_inchi` | `from_inchi(inchi, sanitize=True, remove_hs=True)` | Convert InChI to `Mol`. | Returns `None` for `None` or unparseable input. Keep `sanitize=True` for normal workflows. |
| `dm.from_selfies` | `from_selfies(selfies, as_mol=False)` | Decode SELFIES. | Returns SMILES by default; set `as_mol=True` to return a `Mol`. |
| `dm.from_smarts` | `from_smarts(smarts)` | Build query molecules from SMARTS. | Returns a query `Mol` suitable for substructure matching; returns `None` for `None`. |
| `dm.to_smiles` | `to_smiles(mol, canonical=True, isomeric=True, kekulize=False, ordered=False, explicit_bonds=False, explicit_hs=False, randomize=False, cxsmiles=False, allow_to_fail=False, with_atom_indices=False)` | Convert `Mol` to SMILES or CXSMILES. | Defaults to canonical, isomeric SMILES. `randomize=True` disables canonicalization. `allow_to_fail=False` returns `None` on conversion errors; `True` raises. |
| `dm.to_selfies` | `to_selfies(mol)` | Encode a SMILES or `Mol` as SELFIES. | Returns `None` for invalid input or failed encoding. |
| `dm.to_inchi` | `to_inchi(mol)` | Standard InChI conversion. | Accepts SMILES or `Mol`; returns `None` for invalid input. Prefer standard InChI unless the task explicitly requests non-standard layers. |
| `dm.to_inchikey` | `to_inchikey(mol)` | Standard InChIKey conversion. | Accepts SMILES or `Mol`; returns `None` for invalid/query molecules. |
| `dm.to_inchi_non_standard` | `to_inchi_non_standard(mol, fixed_hydrogen_layer=True, undefined_stereocenter=True, reconnected_metal_layer=True, tautomerism_keto_enol=True, tautomerism_15=True, options=None)` | Non-standard InChI with extra layers. | Do not mix standard and non-standard identifiers in the same deduplication key. |
| `dm.to_inchikey_non_standard` | `to_inchikey_non_standard(mol, fixed_hydrogen_layer=True, undefined_stereocenter=True, reconnected_metal_layer=True, tautomerism_keto_enol=True, tautomerism_15=True, options=None)` | Non-standard InChIKey with extra layers. | Same caution as non-standard InChI. |

## Block And File IO

| API | Verified signature | Use when | Key guidance |
| --- | --- | --- | --- |
| `dm.read_sdf` | `read_sdf(urlpath, sanitize=True, as_df=False, smiles_column='smiles', mol_column=None, include_private=False, include_computed=False, strict_parsing=True, remove_hs=True, max_num_mols=None, discard_invalid=True, n_jobs=1)` | Load SDF or `.sdf.gz` files from local or fsspec-supported paths. | Returns `list[Mol]` by default or a dataframe with `as_df=True`. `discard_invalid=True` drops failed records; set `False` to preserve `None` placeholders. `max_num_mols` bounds reads. |
| `dm.to_sdf` | `to_sdf(mols, urlpath, smiles_column='smiles', mol_column=None)` | Write a `Mol`, sequence of mols, or dataframe to SDF. | When passing a dataframe, `mol_column` takes precedence over `smiles_column`; rows that convert to `None` are filtered. |
| `dm.read_smi` | `read_smi(urlpath)` | Read simple `.smi` files. | `.smi` is CSV-like; prefer `dm.read_csv` or `pandas.read_csv` when separators, headers, or metadata matter. |
| `dm.to_smi` | `to_smi(mols, urlpath, error_if_empty=False)` | Write simple SMILES files. | Prefer `dm.save_df`/CSV for metadata. Set `error_if_empty=True` to guard accidental empty writes. |
| `dm.read_molblock` | `read_molblock(molblock, sanitize=True, strict_parsing=True, remove_hs=True, fail_if_invalid=False)` | Parse an in-memory MDL mol block string. | Molecule properties are not read from mol blocks. `fail_if_invalid=True` raises instead of returning `None`. |
| `dm.to_molblock` | `to_molblock(mol, include_stereo=True, conf_id=-1, kekulize=True, force_V3000=False)` | Serialize a molecule to an MDL mol block string. | Molecule properties are lost in the block string. Use SDF when properties must roundtrip. |
| `dm.read_mol2file` | `read_mol2file(urlpath, sanitize=True, cleanup_substructures=True, remove_hs=True, fail_if_invalid=False)` | Load MOL2 files. | Returns a list and can include `None` for damaged entries; `fail_if_invalid=True` raises on invalid blocks. |
| `dm.to_pdbblock` | `to_pdbblock(mol, conf_id=-1)` | Serialize a molecule with coordinates to a PDB block. | Use when 3D conformers already exist. PDB is not the best format for arbitrary molecule properties. |
| `dm.read_pdbblock` | `read_pdbblock(molblock, sanitize=True, remove_hs=True, flavor=0, proximity_bonding=True)` | Parse a PDB block string. | Useful for small in-memory examples; route conformer generation to structure-generation before expecting 3D coordinates. |

## Dataframe IO

| API | Verified signature | Use when | Key guidance |
| --- | --- | --- | --- |
| `dm.read_csv` | `read_csv(urlpath, smiles_column=None, mol_column='mol', **kwargs)` | Load CSV into a dataframe. | Pass `smiles_column='smiles'` to add a molecule column with RDKit/PandasTools. Any extra kwargs go to `pandas.read_csv`. |
| `dm.read_excel` | `read_excel(urlpath, sheet_name=0, smiles_column=None, mol_column='mol', **kwargs)` | Load Excel into a dataframe. | Requires a pandas-compatible Excel engine such as `openpyxl`. Pass `smiles_column` to add molecules. |
| `dm.open_df` | `open_df(path, **kwargs)` | Auto-load CSV, Excel, parquet, JSON, SDF, and compressed variants by extension. | Supported extensions are listed in [data-formats.md](data-formats.md). Unsupported extensions raise `ValueError`. For SDF, it calls `dm.read_sdf(..., as_df=True)`. |
| `dm.save_df` | `save_df(data, path, **kwargs)` | Auto-save dataframe to CSV, Excel, parquet, JSON, or SDF by extension. | CSV/Excel default to `index=False`. For SDF, it calls `dm.to_sdf(data, path, **kwargs)`. Unsupported extensions raise `ValueError`. |
| `dm.to_df` | `to_df(mols, smiles_column='smiles', mol_column=None, include_private=False, include_computed=False, render_df_mol=True, render_all_df_mol=False, n_jobs=1)` | Convert molecules and their properties to a dataframe. | Set `mol_column='mol'` to keep RDKit objects. Properties become columns. Use `n_jobs=1` for deterministic/simple runs; `-1` uses all cores. |
| `dm.from_df` | `from_df(df, smiles_column='smiles', mol_column=None, conserve_smiles=False, sanitize=True)` | Convert dataframe rows to molecules. | Requires either a SMILES column or a molecule column. `mol_column` takes precedence; if omitted, datamol detects a `Mol` column from the first row. Empty dataframes return `[]`. |

## Cleanup And Validation

| API | Verified signature | Use when | Key guidance |
| --- | --- | --- | --- |
| `dm.sanitize_mol` | `sanitize_mol(mol, charge_neutral=False, sanifix=True, verbose=True, add_hs=False)` | Repair aromaticity/sanitization issues after permissive parsing. | Returns `None` when repair fails. Preserves molecule properties and the first conformer, but atom properties are lost. `charge_neutral=True` calls neutralization first. |
| `dm.standardize_mol` | `standardize_mol(mol, disconnect_metals=False, normalize=True, reionize=True, uncharge=False, stereo=True)` | Apply RDKit MolStandardize operations. | Use `disconnect_metals=True` for metal salts and `uncharge=True` when neutral parent forms are required. Returns a copy. |
| `dm.standardize_smiles` | `standardize_smiles(smiles)` | Standardize a SMILES string directly. | Useful for quick tautomer/functional-group normalization before deduplication. |
| `dm.fix_mol` | `fix_mol(mol, n_iter=1, remove_singleton=False, largest_only=False, inplace=False)` | Greedily repair valence/dummy/singleton issues. | By default returns a copy. Use `largest_only=True` when salts/fragments must collapse to a parent; use with care if the largest fragment might be a solvent or counterion. |
| `dm.remove_salts_solvents` | `remove_salts_solvents(mol, defn_data=None, defn_format='smarts', dont_remove_everything=False, sanitize=True)` | Strip salts and solvents using datamol defaults or custom definitions. | Provide custom `defn_data` when default largest-fragment logic would remove the wrong component. Set `dont_remove_everything=True` to retain one unit if all fragments match removal definitions. |
| `dm.to_neutral` | `to_neutral(mol)` | Neutralize formal charges in place. | Returns `None` unchanged; mutates the molecule passed in. Copy first if the original charged form is needed. |
| `dm.keep_largest_fragment` | `keep_largest_fragment(mol)` | Keep the largest component after parsing multi-fragment input. | Not always correct for solvates where the solvent is larger than the compound; use custom salt/solvent removal for those cases. |

## Molecule Properties

| API | Verified signature | Use when | Key guidance |
| --- | --- | --- | --- |
| `dm.set_mol_props` | `set_mol_props(mol, props, copy=False)` | Add scalar metadata to a molecule. | Non-string values are stored through RDKit property handling; unsupported objects may be stringified. Set `copy=True` to avoid mutating the input. |
| `dm.copy_mol_props` | `copy_mol_props(source, destination, include_private=False, include_computed=False)` | Copy properties between molecules. | Use before replacing/standardizing molecules when metadata must follow the parent record. |
| `dm.clear_mol_props` | `clear_mol_props(mol, property_keys=None, copy=True, include_private=False, include_computed=False)` | Remove all or selected properties. | `property_keys` can be a string or list. Defaults to returning a copy. |
| `mol.GetPropsAsDict()` | RDKit `Mol` method | Read molecule properties. | Use `includePrivate` and `includeComputed` only when those internal/computed fields are intentionally needed. |

## Bundled Data And Molar Helpers

| API | Verified signature | Use when | Key guidance |
| --- | --- | --- | --- |
| `dm.data.freesolv` | `freesolv(as_df=True)` | Small FreeSolv toy dataset. | Dataframe columns: `iupac`, `smiles`, `expt`, `calc`. Returns 642 rows in the tested bundle. |
| `dm.data.cdk2` | `cdk2(as_df=True, mol_column='mol')` | RDKit CDK2 SDF toy dataset. | `as_df=True` includes a molecule column by default; pass `mol_column=None` to drop it. |
| `dm.data.solubility` | `solubility(as_df=True, mol_column='mol')` | RDKit solubility train/test toy data. | Includes a `split` column distinguishing train/test. |
| `dm.data.chembl_drugs` | `chembl_drugs(as_df=True)` | Approved-drug sample table. | Includes ChEMBL metadata and SMILES; treat as bundled sample data, not as authoritative live ChEMBL access. |
| `dm.data.chembl_samples` | `chembl_samples(as_df=True)` | Small ChEMBL SMILES sample. | Dataframe column: `smiles`. |
| `dm.molar.molar_to_log` | `molar_to_log(values, unit)` | Convert concentration values to p-scale values. | Supported units: `M`, `mM`, `uM`, `nM`, `pM`, `fM`; unsupported units raise `ValueError`. |
| `dm.molar.log_to_molar` | `log_to_molar(values, unit)` | Convert p-scale values back to concentration units. | Accepts scalars, lists, and numpy arrays; unsupported units raise `ValueError`. |
