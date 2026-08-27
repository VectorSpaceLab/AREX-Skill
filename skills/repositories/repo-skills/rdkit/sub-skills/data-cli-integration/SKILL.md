---
name: data-cli-integration
description: "Use for RDKit data-file discovery, pharmacophore
  feature-definition files, PandasTools molecule DataFrames, lightweight
  database helpers, and public CLI-style integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Data, CLI, and Integration

Use this sub-skill when a task asks an agent to connect RDKit chemistry code to package data files, tabular data, pandas workflows, feature-definition files, SQL/database helpers, or small command-line workflows around installed RDKit.

## Route Here

- Locate package data with `rdkit.RDConfig.RDDataDir`, including `BaseFeatures.fdef`, `FunctionalGroups.txt`, `Salts.txt`, `RDData.sqlt`, `RDTests.sqlt`, and sample `NCI/` files.
- Build pharmacophore feature factories with `rdkit.Chem.ChemicalFeatures.BuildFeatureFactory` or `BuildFeatureFactoryFromString`.
- Annotate molecules from SMILES with feature families, types, atom ids, and coordinates using the bundled `scripts/feature_finder.py` helper.
- Use `rdkit.Chem.PandasTools` for SDF-to-DataFrame, SMILES-to-molecule columns, substructure filtering, SDF/SMILES/XLSX export, and HTML molecule rendering.
- Use `rdkit.Dbase` helpers for SQLite-style RDKit data tables or for understanding legacy DB utility boundaries.
- Triage installed-package integration issues such as missing data files, optional pandas/XLSX dependencies, database backend availability, or local checkout shadowing.

## Route Elsewhere

- Basic molecule parsing, SDF/SMILES suppliers, sanitization, and molecule validation: `../molecule-io-core/`.
- Descriptor calculation, fingerprints, similarity, clustering, or ML feature engineering: `../descriptors-fingerprints/`.
- 2D/3D coordinates, conformers, drawing APIs, and image generation outside pandas export: `../conformers-drawing/`.
- Reactions, standardization, salt stripping chemistry policy, tautomer handling, or R-group workflows: `../reactions-standardization/`.
- Optional contributed utilities and standalone contributed scorers: `../contrib-utilities/`.

## Start With These References

- `references/data-files-and-features.md` for `RDConfig`, installed data files, FDef feature factories, and feature-finder usage.
- `references/pandas-and-database.md` for `PandasTools`, SDF/SMILES table round-trips, HTML/XLSX export, and DB helper boundaries.
- `references/troubleshooting.md` for missing data, pandas optional behavior, DB backend problems, and checkout-shadowing diagnostics.
- `scripts/feature_finder.py` for a safe installed-package CLI that reports RDKit chemical features for SMILES strings.

## Common Patterns

- Prefer `os.path.join(RDConfig.RDDataDir, "BaseFeatures.fdef")` for the default pharmacophore feature-definition file instead of hard-coding install paths.
- Check `os.path.isdir(RDConfig.RDDataDir)` and `os.path.exists(...)` before assuming sample data or `.fdef` files are present in minimal packages.
- Import `PandasTools` only when pandas-backed behavior is needed, and catch `ImportError` for environments without pandas.
- Keep database examples SQLite-oriented unless the task explicitly asks for legacy PostgreSQL/DbCLI behavior; RDKit PostgreSQL cartridge work is outside this sub-skill's runtime scope.
- Treat `Projects/DbCLI` as historical/reference-only guidance unless the installed RDKit distribution exposes the same modules and dependencies.

## Quick Smoke

Run the bundled feature helper in any environment where RDKit is importable:

```bash
python scripts/feature_finder.py --smiles "CC(=O)O" "c1ccncc1" --summary
```

Use an explicit feature-definition file when testing custom pharmacophore rules:

```bash
python scripts/feature_finder.py --fdef custom.fdef --smiles "CCO"
```
