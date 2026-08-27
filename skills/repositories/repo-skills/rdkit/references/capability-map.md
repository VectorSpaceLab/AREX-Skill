# RDKit Capability Map

Use this map to route user requests to the right part of the skill.

| User request or symptom | Runtime owner | Useful bundled file | Validation signal |
| --- | --- | --- | --- |
| Parse SMILES/SMARTS/SDF, canonicalize molecules, handle supplier rows, edit molecules | `sub-skills/molecule-io-core/` | `sub-skills/molecule-io-core/scripts/molecule_io_smoke.py` | invalid inputs are reported and valid molecules round-trip |
| Explain sanitization, kekulization, aromaticity, hydrogens, substructure matching | `sub-skills/molecule-io-core/` | `sub-skills/molecule-io-core/references/sanitization-and-queries.md` | molecule validation happens before downstream APIs |
| Calculate descriptors, QED/Lipinski/Crippen/TPSA, feature tables | `sub-skills/descriptors-fingerprints/` | `sub-skills/descriptors-fingerprints/references/descriptors.md` | descriptor rows retain input identifiers and invalid rows are handled |
| Generate fingerprints, similarity scores, nearest neighbors, Butina clusters | `sub-skills/descriptors-fingerprints/` | `sub-skills/descriptors-fingerprints/scripts/fingerprint_similarity.py` | Morgan generator fingerprints and Tanimoto scores are reproducible |
| Embed 3D conformers, optimize with UFF/MMFF, compute RMSD/alignment | `sub-skills/conformers-drawing/` | `sub-skills/conformers-drawing/scripts/conformer_draw_smoke.py` | conformer count/status is checked before geometry use |
| Draw molecules, reactions, or grids as SVG/PNG | `sub-skills/conformers-drawing/` | `sub-skills/conformers-drawing/references/drawing.md` | output file exists and invalid inputs are reported |
| Run reaction SMARTS/RXN transforms and sanitize products | `sub-skills/reactions-standardization/` | `sub-skills/reactions-standardization/scripts/standardize_react_smoke.py` | product sets are checked and products are sanitized or failures are explained |
| Cleanup, normalize, uncharge, choose parent fragments, enumerate tautomers | `sub-skills/reactions-standardization/` | `sub-skills/reactions-standardization/references/standardization-rgroups-stereo.md` | chemistry policy is explicit before changing structures |
| R-group decomposition or stereochemistry/CIP after transformations | `sub-skills/reactions-standardization/` | `sub-skills/reactions-standardization/references/standardization-rgroups-stereo.md` | unmatched cores/molecules and stereo assumptions are surfaced |
| Locate RDKit data files or use `BaseFeatures.fdef` | `sub-skills/data-cli-integration/` | `sub-skills/data-cli-integration/scripts/feature_finder.py` | `RDConfig.RDDataDir` and target files exist |
| Use `PandasTools`, SDF/DataFrame/HTML/XLSX flows, lightweight database helpers | `sub-skills/data-cli-integration/` | `sub-skills/data-cli-integration/references/pandas-and-database.md` | optional pandas/DB dependencies are checked before use |
| Use SA Score, NP Score, NIBR filters, Fraggle, MMPA, FreeWilson, MolVS-derived recipes | `sub-skills/contrib-utilities/` | `sub-skills/contrib-utilities/scripts/contrib_scores_smoke.py` | module/data availability is reported; missing optional files are not fatal |
| Edit/build/test RDKit itself or diagnose source-checkout imports | `sub-skills/repo-development/` | `sub-skills/repo-development/scripts/check_checkout_shadowing.py` | local checkout shadowing and missing compiled extensions are identified |

## Cross-Skill Workflows

- **Mini screening pipeline:** `molecule-io-core` validates molecules, `reactions-standardization` normalizes structures, `descriptors-fingerprints` builds fingerprints and similarity matrices, and `conformers-drawing` renders final hits.
- **Data integration pipeline:** `molecule-io-core` parses input, `data-cli-integration` attaches molecules to tables or features, and `descriptors-fingerprints` adds feature columns.
- **Source checkout failure:** root troubleshooting and `repo-development` diagnose import/build issues, then user workflows return to the relevant end-user sub-skill after RDKit imports cleanly.
