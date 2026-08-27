---
name: data-pipelines
description: "Create, inspect, convert, split, and validate SchNetPack atomistic
  datasets backed by ASE databases and built-in dataset modules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SchNetPack Data Pipelines

Use this sub-skill when the task is about SchNetPack datasets: creating or loading ASE DB files, checking unit metadata, choosing properties, configuring `AtomsDataModule`, preparing split files, using transforms before batching, converting legacy metadata, or diagnosing data-loading errors.

## Start Here

1. Identify whether the user has a custom ASE DB (`.db`) or a built-in dataset module such as `QM9`, `MD17`, `rMD17`, `MD22`, `ANI1`, `ISO17`, `QM7X`, `MaterialsProject`, `OrganicMaterialsDatabase`, or `TMQM`.
2. Inspect dataset metadata before training: SchNetPack expects `_distance_unit`, `_property_unit_dict`, and `atomrefs` in the ASE DB metadata.
3. Use `ASEAtomsData` or `load_dataset` for direct reads and `AtomsDataModule` for train/validation/test splitting, batching, transforms, and unit conversion.
4. Keep training/Hydra command construction in `../training-configs/SKILL.md`; keep representation/output modules in `../models-atomistic/SKILL.md`; keep calculators, MD, and LAMMPS in `../interfaces-md/SKILL.md`.

## Primary References

- `references/data-formats.md` covers custom ASE DB creation, metadata, built-in dataset modules, split files, transforms, and validation snippets.
- `references/api-reference.md` lists the important classes, signatures, methods, split strategies, loader behavior, stats helpers, and CLI conversion helper usage.
- `references/troubleshooting.md` maps common unit, property, split, workdir, and legacy-conversion errors to concrete diagnostics and fixes.
- `scripts/convert_ase_units.py` updates legacy ASE DB metadata and atomrefs without relying on SchNetPack's source checkout.

## Safe Workflow

- For a tiny custom dataset, create the `.db` with `ASEAtomsData.create(..., distance_unit="Ang", property_unit_dict={...})`, add systems, reload with `ASEAtomsData`, and then wrap it in `AtomsDataModule`.
- For legacy ASE DBs, run `python sub-skills/data-pipelines/scripts/convert_ase_units.py --help` first, then update units on a copy of the database.
- For split problems, inspect the existing `split.npz` arrays before training; stale split files are reused and validated against requested counts.
- Avoid long downloads or training in diagnosis loops. Use tiny DBs and `num_workers=0` or `1` for fast local validation.
