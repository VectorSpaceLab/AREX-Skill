# Data, Pandas, DB, and CLI Troubleshooting

## Missing RDKit Data Files

Symptoms:

- `FileNotFoundError` for `BaseFeatures.fdef`, `FunctionalGroups.txt`, sample `NCI` files, or SQLite data files.
- `ChemicalFeatures.BuildFeatureFactory(...)` raises an I/O error for a path that worked on another machine.
- `RDConfig.RDDataDir` points somewhere unexpected.

Diagnosis:

```python
import os
from rdkit import RDConfig

print(RDConfig.RDDataDir)
print(os.path.isdir(RDConfig.RDDataDir))
print(os.path.exists(os.path.join(RDConfig.RDDataDir, "BaseFeatures.fdef")))
```

Fixes:

- Use `RDConfig.RDDataDir` instead of hard-coded source checkout paths.
- Check whether `RDBASE` is set; it overrides installed-package path derivation in `RDConfig`.
- Run outside an unbuilt source checkout if `import rdkit` is resolving to local source files instead of the installed package.
- Reinstall a complete RDKit package if the installed distribution lacks `Data/` files.
- For custom FDef work, pass an explicit existing `.fdef` path or use `BuildFeatureFactoryFromString` with bundled text.

## Feature Factory Failures

Symptoms:

- Missing feature families or zero results from `GetFeaturesForMol`.
- Exceptions while parsing a custom FDef block.
- Feature coordinates that look unphysical.

Fixes:

- Confirm the molecule parsed successfully before calling feature APIs.
- Use `includeOnly` only for known feature families such as `Donor`, `Acceptor`, `Aromatic`, `Hydrophobe`, `LumpedHydrophobe`, `NegIonizable`, `PosIonizable`, or the family names present in the active FDef.
- Validate custom FDef syntax with a tiny molecule before running a batch.
- Generate conformers first, then pass `confId`, when coordinates need to represent a real 3D geometry; route conformer generation to `conformers-drawing`.

## Pandas Optional Behavior

Symptoms:

- `ImportError: No module named pandas` or limited `PandasTools` functionality.
- Molecule images do not render in HTML output.
- XLSX export fails despite SDF/SMILES export working.
- Substructure filtering with `frame[frame["Molecule"] >= query]` gives unexpected results.

Fixes:

- Treat pandas as an optional dependency; catch `ImportError` and offer a pure-RDKit supplier/writer fallback for non-tabular tasks.
- Set `PandasTools.molRepresentation = "svg"` or `"png"` before HTML export and use `ChangeMoleculeRendering` for frame-scoped behavior.
- Install an Excel writer such as `xlsxwriter` only when XLSX export is required.
- Use `includeFingerprints=True` when adding molecule columns for repeated substructure filters.
- Check for `None` molecules after `AddMoleculeColumnToFrame`; invalid SMILES become unusable molecule values.
- Ensure query molecules are SMARTS/SMILES parsed successfully before applying the patched `>=` substructure operator.

## Database Dependency and Scope Issues

Symptoms:

- `rdkit.Dbase.DbModule` cannot find SQLite or PostgreSQL support.
- Legacy `Projects/DbCLI` examples fail because descriptor calculator files or project-relative paths are missing.
- Confusion between `rdkit.Dbase` utilities and PostgreSQL cartridge functionality.

Fixes:

- Prefer standard-library `sqlite3` workflows for local databases.
- Use `RDConfig.RDDataDatabase` and `RDConfig.RDTestDatabase` only after verifying the referenced `.sqlt` files exist.
- Avoid relying on `Projects/DbCLI` scripts as installed command-line entry points; reimplement the needed workflow with installed modules.
- Route server-side PostgreSQL chemistry search, cartridge installation, and SQL operator/index questions to cartridge-specific docs; `rdkit.Dbase` is not the PostgreSQL cartridge.

## Checkout Shadowing

Symptoms:

- `import rdkit` succeeds but compiled modules fail to import.
- APIs behave differently in the repository directory than outside it.
- `rdkit.__file__` points at a local checkout instead of site-packages.

Diagnosis:

```python
import rdkit
print(rdkit.__file__)
```

Fixes:

- Run scripts from a neutral working directory, not from the root of an unbuilt RDKit source checkout.
- Remove the checkout path from `PYTHONPATH` when using an installed RDKit package.
- Do not set `RDBASE` to an unrelated or incomplete source tree while using binary RDKit.
- In CI, print `rdkit.__version__`, `rdkit.__file__`, and `RDConfig.RDDataDir` before running integration checks.
