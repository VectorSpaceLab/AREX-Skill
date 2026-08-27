---
name: rdkit
description: "Use for RDKit cheminformatics tasks: molecule parsing and
  validation, descriptors and fingerprints, conformers and drawing, reactions
  and standardization, data integrations, optional Contrib utilities, or RDKit
  repository development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# RDKit Skill

Use this repo skill when a task involves RDKit, the open-source C++/Python cheminformatics toolkit. RDKit is commonly used for molecule I/O, structure validation, descriptors, fingerprints, similarity, conformers, drawing, reactions, standardization, R-group decomposition, feature definitions, tabular cheminformatics, optional Contrib utilities, and maintaining the RDKit source tree.

## Install and Import Check

For normal Python use, prefer the documented binary install route:

```bash
conda install -c conda-forge rdkit
python - <<'PY'
from rdkit import Chem
mol = Chem.MolFromSmiles('c1ccccc1O')
assert mol is not None
print(Chem.MolToSmiles(mol))
PY
```

Use `scripts/check_rdkit_env.py` when an agent needs a quick installed-package smoke check, module availability report, or diagnosis for a local source checkout that shadows an installed RDKit package.

## Route by Task

- `sub-skills/molecule-io-core/` handles molecule creation, SMILES/SMARTS/MolBlock/SDF I/O, sanitization, hydrogens, atom/bond/ring queries, substructure matching, and editable molecules.
- `sub-skills/descriptors-fingerprints/` handles scalar descriptors, QED/Lipinski/Crippen/TPSA properties, Morgan/RDKit/atom-pair/topological-torsion fingerprints, `DataStructs` similarity, feature tables, and Butina clustering.
- `sub-skills/conformers-drawing/` handles ETKDG conformer generation, UFF/MMFF optimization, 3D alignment/RMSD, 2D coordinates, and SVG/PNG/grid rendering.
- `sub-skills/reactions-standardization/` handles reaction SMARTS/RXN workflows, product sanitization, MolStandardize cleanup/normalization/fragment/tautomer workflows, R-group decomposition, and stereochemistry/CIP handling.
- `sub-skills/data-cli-integration/` handles `RDConfig` data files, feature-definition files, chemical feature factories, `PandasTools`, lightweight DB helpers, and installed-package CLI-style helpers.
- `sub-skills/contrib-utilities/` handles optional community Contrib utilities such as SA Score, NP Score, NIBR filters, Fraggle, MMPA, FreeWilson, and MolVS-derived recipes.
- `sub-skills/repo-development/` handles editing, building, testing, formatting, wrapper boundaries, generated stubs/docstrings, and source-checkout diagnostics for RDKit itself.

## Shared References

- `references/capability-map.md` maps common user requests to sub-skills, bundled scripts, and verification evidence.
- `references/troubleshooting.md` covers cross-cutting install/import, source-checkout shadowing, optional dependency, data-file, and compiled-extension failures.
- `references/repo-provenance.md` records the source snapshot, selected evidence paths, dirty state, and inspection-package facts for future refresh decisions.

## Quick Decision Rules

- If a task starts with invalid SMILES, suppliers, `None` molecules, properties on atoms/bonds, or substructure matching, start with `molecule-io-core` before any downstream chemistry.
- If a task asks for feature vectors, similarity search, clustering, or descriptor columns, start with `descriptors-fingerprints` and cross-link back to molecule validation when inputs are untrusted.
- If a task mentions 3D coordinates, RMSD, force fields, or images, start with `conformers-drawing`; do not treat 2D depiction coordinates as 3D conformers.
- If a task transforms molecules chemically, standardizes salts/tautomers, runs reactions, or decomposes analog series into R groups, start with `reactions-standardization`.
- If a task asks where RDKit data lives, how to use `BaseFeatures.fdef`, how to attach molecules to a DataFrame, or how to make a tiny CLI around installed RDKit, start with `data-cli-integration`.
- If a task mentions `Contrib`, SA/NP score, Fraggle, MMPA, FreeWilson, or optional community scripts, start with `contrib-utilities` and check availability before assuming modules/data are installed.
- If a task is about changing this repository or an import fails from an unbuilt checkout with `rdBase` missing, start with `repo-development`.

## Working Safely

- Prefer installed RDKit package APIs for user workflows; only use source-tree instructions for repository-development tasks.
- Validate molecule creation before passing objects to descriptors, fingerprints, reactions, conformer embedding, or drawing.
- Treat optional wrappers and integrations such as PostgreSQL cartridge, Java/C# wrappers, FreeSASA, InChI, Avalon, CoordGen, Contrib tools, and database helpers as availability-dependent.
- Keep long-running native tests, benchmarks, fuzzers, full CMake builds, and database workflows out of routine user tasks unless the user explicitly asks for maintainer validation.
- Do not depend on original RDKit repository examples or scripts at runtime; use the bundled references and scripts in this skill tree.
