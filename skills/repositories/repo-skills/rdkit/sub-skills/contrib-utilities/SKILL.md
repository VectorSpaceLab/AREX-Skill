---
name: contrib-utilities
description: "Use optional RDKit Contrib utilities safely: SA Score, NP Score,
  NIBR substructure filters, Fraggle, MMPA, FreeWilson, and MolVS-derived
  recipes, while distinguishing them from core RDKit APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Contrib Utilities

Use this sub-skill when a task asks about community-contributed or optional RDKit utilities under the `Contrib` umbrella, especially SA Score, NP Score, NIBR substructure filters, Fraggle similarity, MMPA scripts, Free-Wilson decomposition/enumeration, or legacy MolVS-derived command-line recipes.

## Route Here

- Estimate synthetic accessibility with the contributed SA Score implementation when its scorer module and fragment-score data are available.
- Estimate natural-product likeness with the contributed NP Score implementation when its scorer module and model data are available.
- Apply or explain NIBR hit-triage substructure filters, including their pandas/numpy dependency and CSV input/output shape.
- Explain Fraggle’s three-stage workflow: fragment query molecules, run Tversky search, and post-process atom contributions.
- Explain MMPA’s fragmentation, indexing, canonical SMIRKS, transform application, and optional SQLite/SMARTS database search workflows.
- Use or adapt FreeWilson when the optional module and scientific Python dependencies are installed for scaffold decomposition and activity prediction.
- Recognize MolVS-derived contributed utilities as historical/convenience wrappers; prefer core MolStandardize for standardization work.

## Route Elsewhere

- Use `../descriptors-fingerprints/` for core RDKit descriptors, QED, Lipinski, Crippen, MolSurf, Morgan fingerprints, bit-vector similarity, clustering, and feature tables.
- Use `../reactions-standardization/` for core `rdMolStandardize`, reaction SMARTS/RXN workflows, R-group decomposition, tautomer handling, and stereochemistry-preserving transformations.
- Use `../molecule-io-core/` for SMILES/SDF parsing, molecule validation, canonicalization, salts/mixtures, and sanitization before optional contrib tools.
- Use `../conformers-drawing/` for 2D/3D depictions, conformers, shape alignment, RMSD, and drawing similarity maps.

## Start With These References

- `references/scoring-and-filters.md` for SA Score, NP Score, NIBR filters, MolVS-derived utility routing, data files, dependencies, and safe fallback patterns.
- `references/mmpa-fraggle-freewilson.md` for MMPA, Fraggle, FreeWilson, command shapes, input hygiene, output expectations, and optional dependency notes.
- `references/troubleshooting.md` for missing modules/data, binary-package differences, path assumptions, optional pandas/numpy/scipy/sklearn dependencies, and route decisions.
- `scripts/contrib_scores_smoke.py` for a safe availability check that imports RDKit, parses small SMILES, and reports whether contributed SA/NP scorer modules and model data are importable.

## Contrib Safety Principles

1. Treat Contrib utilities as optional examples unless the active environment proves the specific script/module and data file are importable.
2. Do not assume binary RDKit packages install every Contrib script as a Python module; core RDKit imports can succeed while Contrib utilities are absent.
3. Keep model/data files explicit: SA Score needs fragment-score data such as `fpscores.pkl.gz`; NP Score needs model data such as `publicnp.model.gz`; NIBR filters need their CSV filter table.
4. Prefer installed package APIs for core cheminformatics and use Contrib recipes only for the specialized methods they implement.
5. For public agent guidance, report availability and alternatives instead of silently adding source checkout paths to `sys.path`.

## Quick Smoke

Run this from the sub-skill directory or pass it by full path in an environment where RDKit is importable:

```bash
python scripts/contrib_scores_smoke.py --smiles "CCO" "c1ccccc1O"
```

Expected behavior is a compact report: RDKit import status, molecule parse status, and whether SA Score or NP Score contributed modules/data are available. Missing Contrib modules or data are reported as `unavailable`, not as a fatal failure unless core RDKit cannot import or a provided SMILES is invalid.
