---
name: datamol
description: "Guides agents using the datamol Python package for RDKit-first
  molecular IO, preparation, fingerprints, similarity, structure generation,
  visualization, and utility workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datamol Repo Skill

Use this skill when a task names `datamol`, asks for RDKit-first molecule processing in Python, or needs practical guidance for molecular IO, standardization, fingerprints, descriptors, clustering, conformers, scaffolds, reactions, isomers, visualization, or datamol utility helpers.

Datamol is a Python layer on top of RDKit. Assume user-facing objects are usually `rdkit.Chem.Mol` instances, SMILES strings, pandas dataframes, NumPy arrays, or small molecule files such as SDF/SMI/CSV/XLSX.

## Install And Import

Prefer the public package install used by the project:

```bash
mamba install -c conda-forge datamol
# or, when conda is unavailable:
python -m pip install datamol
```

Minimal import check:

```python
import datamol as dm
mol = dm.to_mol("CCO")
assert dm.to_smiles(mol) == "CCO"
```

Run [scripts/check_datamol_environment.py](scripts/check_datamol_environment.py) when an environment, RDKit install, optional dependency, or basic API smoke check is uncertain.

## Choose A Sub-Skill

- Use [sub-skills/molecule-io-prep/SKILL.md](sub-skills/molecule-io-prep/SKILL.md) for molecule construction, SMILES/InChI/SMARTS/SELFIES conversion, SDF/CSV/XLSX/dataframe IO, standardization, sanitization, salts/solvents, properties, bundled toy datasets, and molar unit helpers.
- Use [sub-skills/fingerprints-similarity/SKILL.md](sub-skills/fingerprints-similarity/SKILL.md) for fingerprints, descriptors, fingerprint arrays, pairwise or cross-distance matrices, clustering, diversity/centroid picking, MCS, and molecular graph matching.
- Use [sub-skills/structure-generation/SKILL.md](sub-skills/structure-generation/SKILL.md) for conformers, 3D features, alignment, atom reordering, fragmentation, assembly, scaffolds/fuzzy scaffolds, reactions, attachments, tautomers, stereoisomers, and structural isomers.
- Use [sub-skills/visualization-utilities/SKILL.md](sub-skills/visualization-utilities/SKILL.md) for molecule grids, SVG/PNG rendering, substructure or lasso highlighting, dataframe rendering, existing conformer display, filesystem helpers, parallel jobs, RDKit log control, and diagnostics.

## Common Workflow Order

1. Start in `molecule-io-prep` to parse inputs, sanitize/standardize molecules, preserve properties, and choose dataframe/file formats.
2. Move to `fingerprints-similarity` when the next step needs numeric descriptors, distance matrices, clusters, diversity selection, MCS, or graph correspondence.
3. Move to `structure-generation` when the task creates new chemistry or 3D structures through conformers, fragments, scaffolds, reactions, or isomer enumeration.
4. Move to `visualization-utilities` when the output needs images, highlights, notebook/file rendering, parallel utility helpers, fsspec checks, or RDKit logging control.

Read [references/capability-map.md](references/capability-map.md) for natural task phrases and the owning sub-skill. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, RDKit, file-format, optional dependency, and workflow routing failures.

## Safety Defaults

- Keep examples small and deterministic until molecule parsing, sanitization, and output formats are verified.
- Bound expensive or combinatorial chemistry with small `n_confs`, `n_variants`, `timeout`, `timeout_seconds`, `depth`, `max_n_mols`, `num_threads=1`, and `n_jobs=1` first.
- Treat network files, cloud URIs, notebook widgets, and optional renderers as environment-specific; validate them with the nearest troubleshooting reference before relying on them.
- Prefer SVG output for deterministic visual artifacts and use PNG/Pillow only when the caller explicitly needs raster output.
- Preserve row identifiers, molecule properties, and invalid-row handling explicitly when converting between dataframes and molecule files.

## Bundled Checks

- Root environment smoke: [scripts/check_datamol_environment.py](scripts/check_datamol_environment.py)
- IO/prep smoke: [sub-skills/molecule-io-prep/scripts/molecule_io_smoke.py](sub-skills/molecule-io-prep/scripts/molecule_io_smoke.py)
- Fingerprint/similarity smoke: [sub-skills/fingerprints-similarity/scripts/fingerprint_similarity_smoke.py](sub-skills/fingerprints-similarity/scripts/fingerprint_similarity_smoke.py)
- Structure-generation smoke: [sub-skills/structure-generation/scripts/structure_generation_smoke.py](sub-skills/structure-generation/scripts/structure_generation_smoke.py)
- Visualization/utility smoke: [sub-skills/visualization-utilities/scripts/visualization_utility_smoke.py](sub-skills/visualization-utilities/scripts/visualization_utility_smoke.py)

Each script supports `--help` and uses only tiny local examples by default.

## Provenance And Refresh

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a datamol checkout. If the current commit, dirty state, package metadata, or major evidence paths differ from that snapshot, run `refresh-repo-skill` before relying on stale API details.
