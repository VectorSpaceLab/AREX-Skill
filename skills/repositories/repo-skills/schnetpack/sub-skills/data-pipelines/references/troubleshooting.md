# Data Pipeline Troubleshooting

Use this guide before training when SchNetPack fails while loading a dataset, constructing splits, applying transforms, or converting legacy ASE DB metadata.

## Fast Triage Script

Run this from a directory where the target DB path is valid:

```python
from ase.db import connect
from schnetpack.data import ASEAtomsData

path = "data.db"
with connect(path, use_lock_file=False) as db:
    print("rows", db.count())
    print("metadata", db.metadata)
    if db.count():
        row = db.get(1)
        print("first row data keys", list(row.data.keys()))
        print("first row atoms", row.numbers, row.positions.shape)

dataset = ASEAtomsData(path)
print("available", dataset.available_properties)
print("units", dataset.units)
print("first keys", dataset[0].keys())
```

If this script fails, fix the DB before touching model or trainer settings.

## Missing Unit Metadata

Symptoms:

- `Dataset does not have a distance unit set. Please add units to the dataset using spkconvert!`
- `Dataset does not have a property units set. Please add units to the dataset using spkconvert!`
- `KeyError: '_property_unit_dict'` when inspecting `available_properties`.

Cause: SchNetPack 2 expects `_distance_unit`, `_property_unit_dict`, and `atomrefs` in ASE DB metadata.

Fix:

1. Make a copy of the DB.
2. Inspect row data keys and confirm actual property meanings.
3. Run the bundled helper on the copy:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py data-copy.db \
  --distunit Ang \
  --propunit energy:eV,forces:eV/Ang
```

4. Reload with `ASEAtomsData("data-copy.db")` and print `dataset.units`.

Do not guess property units. If the source data is from an electronic-structure code or external benchmark, confirm whether energies are `Ha`, `eV`, `kcal/mol`, or another unit before conversion.

## Wrong Distance Unit Token: `A` vs `Ang`

Symptoms:

- Conversion helper raises a message that `A` is Ampere and likely should be `Ang` or `Angstrom`.
- Positions look numerically reasonable but unit conversion produces nonsensical scales.

Cause: ASE unit tokens distinguish `A` from `Ang`. Use `Ang` or `Angstrom` for Angstrom distances in public examples and conversion commands.

Fix:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py data.db --distunit Ang
```

For a newly created DB, prefer:

```python
ASEAtomsData.create("data.db", distance_unit="Ang", property_unit_dict={...})
```

## Requested Properties Are Missing

Symptoms:

- `AssertionError: Not all given properties are available in the dataset!`
- `KeyError` for a property during `__getitem__` or transforms.
- Training config names `energy` but the dataset exposes `energy_U0`, `total_energy`, or another benchmark-specific key.

Diagnostics:

```python
from schnetpack.data import ASEAtomsData

dataset = ASEAtomsData("data.db")
print(dataset.available_properties)
print(dataset.metadata.get("_property_unit_dict"))
```

Fix:

- Align `load_properties`, `globals.property`, task output names, and model output keys with the dataset property name.
- For a custom DB, recreate or repair the DB so every row contains every declared property.
- For a built-in dataset, use the class constants or documented names: for example `QM9.U0` is `energy_U0`, `MD17.energy` is `energy`, and `ISO17.energy` is `total_energy`.
- Route output-module changes to `../models-atomistic/SKILL.md` and full training config edits to `../training-configs/SKILL.md`.

## Required Property Missing While Adding Rows

Symptom: `AtomsDataError: Required property missing:<name>` from `add_system` or `add_systems`.

Cause: `_property_unit_dict` defines the complete required schema for every row.

Fix:

- Include all declared properties for every system.
- If some systems do not have a vector/list property such as filtered neighbors, store an empty array/list with the correct shape rather than omitting the key.
- If a property should not be loaded or trained, remove it by creating a new DB with a smaller `property_unit_dict`; do not silently omit it row by row.

## Undeclared Properties Are Ignored

Symptom: logs warn that a property is not defined and will be ignored.

Cause: `add_system` only writes keys listed in `_property_unit_dict` plus required structure keys.

Fix: Recreate the DB with the complete `property_unit_dict` before adding systems, then reload and verify `available_properties`.

## Split Counts or Ratios Fail

Symptoms:

- `If no split_file is given, the sizes of the training and validation partitions need to be set!`
- `Split file was given, but num_train (...) != len(train_idx) (...)!`
- Unexpected zero-size validation or test partitions for tiny datasets.
- `Only one partition may be undefined` or the sum of requested sizes exceeds available data/groups.

Causes:

- Missing `num_train` or `num_val` while no split file exists.
- Existing `split.npz` is stale or belongs to another dataset.
- Relative float sizes are floored after multiplication by dataset length.
- Group-based split sizes are being compared to number of groups, not rows.

Diagnostics:

```python
import numpy as np

split = np.load("split.npz")
for key in ["train_idx", "val_idx", "test_idx"]:
    arr = split[key]
    print(key, len(arr), arr[:10].tolist(), arr.max(initial=-1))
```

Fix:

- Delete or rename stale `split.npz` when changing dataset length or split sizes.
- Use explicit integer counts for tiny datasets.
- Ensure only one of `num_train`, `num_val`, and `num_test` is `None` or negative.
- For `GroupSplit`, check metadata group arrays and count unique groups before choosing sizes.

## Stale Split File Reused Unexpectedly

Symptom: changing `num_train`, `num_val`, or random seed has no effect.

Cause: `AtomsDataModule` loads the existing `split_file` if present. It does not regenerate splits unless the file is absent.

Fix:

```bash
mv split.npz split.old.npz
```

Then rerun `AtomsDataModule.setup()` with the intended split arguments. Preserve the old file if reproducibility matters.

## `data_workdir` Copy and Cleanup Confusion

Symptoms:

- Data appears copied to a scratch/work directory.
- Later stages cannot find the copied data.
- Multiple processes race while copying.

Behavior:

- If `data_workdir` is set, `setup()` copies the DB there under an inter-process lock and reloads from the copy.
- The source DB path remains `datapath`; the active loaded DB may be the copy.
- `teardown(stage)` removes `data_workdir` when `stage == cleanup_workdir_stage`; the default cleanup stage is `test`.

Fix:

- Set `data_workdir=None` for simple local debugging.
- Set `cleanup_workdir_stage=None` if a copied DB must persist across stages.
- Do not edit the copied DB and expect the source DB to change.

## Transform Setup Problems

Symptoms:

- Transform fails because statistics or atomrefs are missing.
- Neighbor keys are absent in a batch.
- CPU-only smoke test is slow or fails due optional neighbor-list backend.

Fix:

- For smoke tests, start with `transforms=[trn.ASENeighborList(cutoff=... ), trn.CastTo32()]` and `num_workers=0`.
- Add `RemoveOffsets` only after `AtomsDataModule.setup()` can load splits and atomrefs correctly.
- If a backend-specific neighbor list fails, try `ASENeighborList` first because it relies on ASE rather than optional compiled backends.
- Keep model postprocessors such as `AddOffsets` aligned with data transforms; route model-level decisions to `../models-atomistic/SKILL.md`.

## Legacy Atomrefs or `atref_labels`

Symptoms:

- `dataset.atomrefs` fails or returns unexpected shape.
- Metadata contains `atomrefs` as a matrix and `atref_labels` rather than a property-keyed dictionary.

Fix: run the bundled helper on a copy. It converts old `atomrefs` plus `atref_labels` into `{property_name: list_of_values}` and removes `atref_labels`.

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py old.db --dry-run
python sub-skills/data-pipelines/scripts/convert_ase_units.py old-copy.db --distunit Ang --propunit energy:eV
```

## Property Shape Problems

Symptoms:

- Scalar energies concatenate incorrectly.
- Old datasets have scalar or vector properties missing the leading dimension expected by downstream code.

Fix:

- Store scalar target values as one-dimensional arrays such as `np.array([energy])`.
- Store force targets as `(n_atoms, 3)` arrays.
- For legacy properties that need a leading dimension, use:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py data.db --expand-property-dims property_name
```

Inspect shapes before and after on a copy.

## Built-in Dataset Download or Credential Failures

Symptoms:

- `prepare_data()` attempts a large download.
- Materials Project complains about missing or invalid API key.
- OMDB raw path is missing.

Fix:

- Do not call `prepare_data()` in a quick diagnosis unless the DB already exists or the user approved downloads.
- For `MaterialsProject`, require a valid current API key and optional packages used by the module.
- For `OrganicMaterialsDatabase`, provide `raw_path` to the downloaded raw archive or use an existing converted DB.
- For local validation, prefer a tiny custom ASE DB rather than a benchmark download.

## Native Lightweight Checks

Safe candidates for future verification:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py --help
python -m py_compile sub-skills/data-pipelines/scripts/convert_ase_units.py
```

Native source-repository tests can be useful during external review, but do not make this runtime skill depend on them. Avoid long benchmark downloads, training runs, GPU molecular dynamics, LAMMPS builds, or broad native test suites for this sub-skill.
