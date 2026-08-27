# Datamol Capability Map

Use this map when a task mentions datamol but does not name the exact module.

| User task signal | Start here | Why |
| --- | --- | --- |
| Parse SMILES, InChI, SMARTS, SELFIES, molblocks, PDB blocks, or RDKit `Mol` inputs | `sub-skills/molecule-io-prep/` | Owns molecule construction and conversion APIs. |
| Read or write SDF, SMI, CSV, Excel, parquet, JSON, dataframe, or remote fsspec paths | `sub-skills/molecule-io-prep/` | Owns `read_*`, `to_sdf`, `open_df`, `save_df`, `from_df`, and `to_df`. |
| Sanitize, standardize, neutralize, remove salts/solvents, keep largest fragment, or fix valence | `sub-skills/molecule-io-prep/` | Owns input cleanup before downstream chemistry. |
| Use bundled FreeSolv, CDK2, solubility, ChEMBL sample, or ChEMBL drug data | `sub-skills/molecule-io-prep/` | Owns `dm.data` loaders and small dataset expectations. |
| Compute fingerprints, fingerprint arrays, descriptors, or feature matrices | `sub-skills/fingerprints-similarity/` | Owns `to_fp`, descriptors, folding, and supported fingerprint types. |
| Compute pairwise/cross distances, cluster molecules, pick diverse molecules, assign centroids | `sub-skills/fingerprints-similarity/` | Owns `pdist`, `cdist`, Butina clustering, and picker workflows. |
| Find maximum common substructure or compare molecular graphs | `sub-skills/fingerprints-similarity/` | Owns MCS and graph correspondence utilities. |
| Generate conformers, calculate SASA, align molecules, reorder atoms from templates | `sub-skills/structure-generation/` | Owns 3D and alignment workflows after molecules are prepared. |
| Fragment molecules, assemble fragments, compute scaffolds, fuzzy scaffolds, ring systems | `sub-skills/structure-generation/` | Owns structure transformation workflows. |
| Apply reactions, parse reaction SMARTS/RXN, handle attachment points, enumerate isomers/tautomers | `sub-skills/structure-generation/` | Owns generated chemistry and combinatorial safeguards. |
| Save molecule grids, SVG/PNG images, lasso highlights, substructure highlights | `sub-skills/visualization-utilities/` | Owns rendering and highlight APIs. |
| Render dataframes, silence RDKit logs, use datamol parallel/fs/testing/perf helpers | `sub-skills/visualization-utilities/` | Owns utility helper workflows and diagnostics. |

## Multi-Step Routing Patterns

- **Clean library then cluster**: `molecule-io-prep` parses and standardizes inputs, then `fingerprints-similarity` computes fingerprints and clusters.
- **React products then depict**: `molecule-io-prep` validates reactants, `structure-generation` applies reactions or enumerates products, then `visualization-utilities` renders products.
- **Scaffold or conformer workflow with output files**: `molecule-io-prep` reads inputs, `structure-generation` generates scaffold/conformer results, then `molecule-io-prep` writes SDF/dataframes or `visualization-utilities` writes images.
- **Notebook-style exploration**: use `molecule-io-prep` for input tables, `fingerprints-similarity` for feature selection, and `visualization-utilities` for deterministic SVG artifacts instead of relying on notebook display state.
