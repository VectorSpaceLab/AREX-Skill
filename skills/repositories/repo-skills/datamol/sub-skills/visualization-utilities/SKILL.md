---
name: visualization-utilities
description: "Guides agents using datamol visualization, molecule image
  rendering, lasso highlighting, dataframe display, parallel utilities,
  filesystem helpers, RDKit log controls, and environment diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization Utilities

Use this sub-skill when the task asks to render molecules, save SVG/PNG depictions, highlight substructures, display molecule dataframes, visualize existing conformers, run small datamol utility jobs, inspect fsspec paths, silence RDKit logs, or diagnose datamol/RDKit runtime behavior.

## Route First

- For molecule parsing, cleanup, dataframe construction, SDF/CSV/XLSX IO, or property preservation before rendering, use `../molecule-io-prep/` first.
- For conformer generation, 3D coordinate creation, SASA, alignment, scaffolds, fragments, reactions, tautomers, or isomers, use `../structure-generation/` first.
- For fingerprints, clustering, distance matrices, MCS, graph comparisons, or diversity selection before visualization, use `../fingerprints-similarity/` first.

## What This Covers

- 2D grids with `dm.viz.to_image()` or top-level `dm.to_image()` from SMILES or RDKit molecules.
- SMARTS, query-molecule, and explicit atom-index highlighting with `dm.viz.lasso_highlight_image()` and `dm.viz.match_substructure()`.
- File and notebook output choices, including SVG strings, Pillow PNG objects, and `outfile` paths handled through fsspec.
- Existing-conformer display with `dm.viz.conformers()` when optional notebook widgets are installed and conformers already exist.
- Utility helpers: `dm.parallelized()`, `dm.parallelized_with_batches()`, `dm.JobRunner`, `dm.utils.fs`, `dm.utils.perf.watch_duration`, `dm.utils.decorators.disable_on_os`, and RDKit log/version helpers.

## Reference Map

- Use `references/api-reference.md` for signatures, parameters, return types, utility helper notes, and ownership boundaries.
- Use `references/workflows.md` for SVG/PNG rendering, lasso highlights, dataframe rendering, parallel jobs, fsspec checks, RDKit log control, and diagnostics recipes.
- Use `references/troubleshooting.md` for headless rendering, invalid highlight indices, SVG/PNG/Pillow issues, notebook assumptions, fsspec URI errors, and joblib pickling failures.
- Run `scripts/visualization_utility_smoke.py --help` for a safe executable smoke test, or run it with `--output-dir <dir>` to render a tiny SVG and exercise utility helpers.

## Decision Checklist

1. Normalize input molecules with the root skill or `../molecule-io-prep/` if the task starts from mixed files, tables, or potentially invalid SMILES.
2. Choose `use_svg=True` for deterministic text artifacts and `use_svg=False` only when the caller explicitly needs PNG/Pillow output.
3. Prefer `lasso_highlight_image()` for publication-style outline highlights and `to_image(highlight_atom=..., highlight_bond=...)` or `match_substructure()` for simple RDKit grid highlights.
4. Keep parallel helper callables top-level or otherwise picklable when using process workers; use `scheduler="threads"` or `n_jobs=0/1` for closures and notebook workflows.
5. Wrap noisy parsing or rendering probes in `dm.without_rdkit_log()` and restore global logs with `dm.enable_rdkit_log()` after temporary global muting.
