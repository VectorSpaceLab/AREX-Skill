---
name: molecule-io-prep
description: "Guides agents using datamol to construct, standardize, convert,
  validate, read, write, and tabularize molecules from SMILES, InChI, SMARTS,
  SELFIES, SDF, CSV, Excel, and dataframe inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Molecule IO and Preparation

Use this sub-skill when a task asks for datamol molecule loading, conversion, cleanup, tabular IO, bundled toy datasets, molecule properties, salts/solvents, neutralization, or molar unit conversion.

## Route By Task

- Build molecules from strings or RDKit `Mol` objects with `dm.to_mol`, `dm.from_inchi`, `dm.from_selfies`, and `dm.from_smarts`; use `dm.to_mol` for SMILES because no public `dm.from_smiles` API is exported.
- Convert molecules with `dm.to_smiles`, `dm.to_inchi`, `dm.to_selfies`, `dm.to_molblock`, `dm.to_pdbblock`, `dm.to_df`, and `dm.from_df`.
- Read or write molecule tables and files with `dm.read_csv`, `dm.read_excel`, `dm.read_sdf`, `dm.to_sdf`, `dm.read_smi`, `dm.read_molblock`, `dm.read_mol2file`, `dm.open_df`, and `dm.save_df`.
- Clean molecules with `dm.sanitize_mol`, `dm.standardize_mol`, `dm.fix_mol`, `dm.remove_salts_solvents`, `dm.keep_largest_fragment`, and `dm.to_neutral`.
- Manage molecule properties with `dm.set_mol_props`, `dm.copy_mol_props`, `dm.clear_mol_props`, and `Mol.GetPropsAsDict()`.
- Load small bundled datasets with `dm.data.freesolv`, `dm.data.cdk2`, `dm.data.solubility`, `dm.data.chembl_drugs`, and `dm.data.chembl_samples`.
- Convert concentration units with `dm.molar.molar_to_log` and `dm.molar.log_to_molar`.

## Local References

- API signatures and parameter choices: [references/api-reference.md](references/api-reference.md)
- End-to-end recipes: [references/workflows.md](references/workflows.md)
- Format, dataframe, and property rules: [references/data-formats.md](references/data-formats.md)
- Common failures and fixes: [references/troubleshooting.md](references/troubleshooting.md)
- Safe executable smoke check: [scripts/molecule_io_smoke.py](scripts/molecule_io_smoke.py)

## Boundaries

- Stay in this sub-skill for molecule construction, format conversion, file IO, molecule cleanup, properties, bundled data, and molar helper functions.
- Route fingerprints, arrays, distance matrices, clustering, and diversity picking to the `fingerprints-similarity` sub-skill after this sub-skill returns clean `Mol` objects or canonical SMILES.
- Route conformers, alignment, scaffolds, fragments, reactions, and isomers to the `structure-generation` sub-skill after this sub-skill handles parsing and standardization.
- Route rendering, molecule images, and highlight images to the `visualization-utilities` sub-skill.
